#!/usr/bin/env python3
"""Export JSON + PNG assets for the GitHub Pages portfolio site."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
CAPSTONE_TEST_START = pd.Timestamp("2020-01-01")
DATA = ROOT / "data"
OUT_DATA = ROOT / "site" / "public" / "data"
OUT_ASSETS = ROOT / "site" / "public" / "assets"
MODEL_DIR = ROOT / "scripts" / "models"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import wc2026_simulation_utils as wu  # noqa: E402
from wc2026_monte_carlo import run_monte_carlo  # noqa: E402

FEATURES = [
    "elo_diff",
    "host_advantage",
    "home_form",
    "away_form",
    "home_gd",
    "away_gd",
    "squad_quality_diff",
]
HOSTS = {"United States", "Mexico", "Canada"}
NAME_MAPPING = {
    "Korea Republic": "South Korea",
    "Republic of Ireland": "Ireland",
    "IR Iran": "Iran",
    "Côte d'Ivoire": "Ivory Coast",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Türkiye": "Turkey",
    "Czech Republic": "Czechia",
}
CURATED_MATCHUPS = [
    ("Argentina", "Spain"),
    ("Argentina", "Uruguay"),
    ("Argentina", "Portugal"),
    ("Brazil", "France"),
    ("Mexico", "Germany"),
]


def ensure_dirs() -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_ASSETS.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_squad_quality() -> pd.DataFrame:
    fc = pd.read_csv(DATA / "FC26.csv", low_memory=False)
    fc_sorted = fc.sort_values(["nationality_name", "overall"], ascending=[True, False])
    top23 = fc_sorted.groupby("nationality_name").head(23)
    sq = top23.groupby("nationality_name")["overall"].mean().reset_index()
    sq.rename(columns={"nationality_name": "team", "overall": "squad_quality"}, inplace=True)
    sq["team"] = sq["team"].replace(NAME_MAPPING)
    return sq


def build_train_df(squad_quality: pd.DataFrame) -> pd.DataFrame:
    matches = pd.read_csv(DATA / "results.csv")
    elo = pd.read_csv(DATA / "eloratings.csv")
    elo["date"] = pd.to_datetime(elo["date"], format="mixed")
    elo = elo.sort_values("date")
    matches["date"] = pd.to_datetime(matches["date"], format="mixed")
    matches = matches.sort_values("date")

    train_df = matches[
        (matches["date"] >= "1998-01-01")
        & (matches["tournament"] != "Friendly")
        & (matches["home_score"].notna())
    ].copy()

    conditions = [
        train_df["home_score"] > train_df["away_score"],
        train_df["home_score"] == train_df["away_score"],
        train_df["home_score"] < train_df["away_score"],
    ]
    train_df["match_outcome"] = np.select(conditions, [2, 1, 0], default=1)
    train_df["host_advantage"] = np.where(
        (train_df["country"] == train_df["home_team"]) & (~train_df["neutral"]),
        1,
        0,
    )

    train_df = pd.merge_asof(
        train_df,
        elo[["date", "team", "rating"]].rename(columns={"team": "home_team", "rating": "home_elo"}),
        on="date",
        by="home_team",
        direction="backward",
    )
    train_df = pd.merge_asof(
        train_df,
        elo[["date", "team", "rating"]].rename(columns={"team": "away_team", "rating": "away_elo"}),
        on="date",
        by="away_team",
        direction="backward",
    )
    train_df = train_df.dropna(subset=["home_elo", "away_elo"])
    train_df["elo_diff"] = train_df["home_elo"] - train_df["away_elo"]

    home_stats = train_df[["date", "home_team", "home_score", "away_score"]].rename(
        columns={"home_team": "team", "home_score": "goals_for", "away_score": "goals_against"}
    )
    home_stats["is_home"] = True
    home_stats["win"] = (home_stats["goals_for"] > home_stats["goals_against"]).astype(int)

    away_stats = train_df[["date", "away_team", "away_score", "home_score"]].rename(
        columns={"away_team": "team", "away_score": "goals_for", "home_score": "goals_against"}
    )
    away_stats["is_home"] = False
    away_stats["win"] = (away_stats["goals_for"] > away_stats["goals_against"]).astype(int)

    team_stats = pd.concat([home_stats, away_stats]).sort_values(["team", "date"])
    team_stats["goal_diff"] = team_stats["goals_for"] - team_stats["goals_against"]
    team_stats["recent_form"] = (
        team_stats.groupby("team")["win"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        .fillna(0)
    )
    team_stats["recent_gd"] = (
        team_stats.groupby("team")["goal_diff"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        .fillna(0)
    )

    home_merge = team_stats[team_stats["is_home"]][["date", "team", "recent_form", "recent_gd"]]
    away_merge = team_stats[~team_stats["is_home"]][["date", "team", "recent_form", "recent_gd"]]

    train_df = train_df.merge(
        home_merge,
        left_on=["date", "home_team"],
        right_on=["date", "team"],
        how="left",
    ).rename(columns={"recent_form": "home_form", "recent_gd": "home_gd"}).drop(columns=["team"])
    train_df = train_df.merge(
        away_merge,
        left_on=["date", "away_team"],
        right_on=["date", "team"],
        how="left",
    ).rename(columns={"recent_form": "away_form", "recent_gd": "away_gd"}).drop(columns=["team"])
    train_df = train_df.drop_duplicates(subset=["date", "home_team", "away_team"]).fillna(0)

    train_df = train_df.merge(squad_quality, left_on="home_team", right_on="team", how="left").rename(
        columns={"squad_quality": "home_squad_quality"}
    ).drop(columns=["team"])
    train_df = train_df.merge(squad_quality, left_on="away_team", right_on="team", how="left").rename(
        columns={"squad_quality": "away_squad_quality"}
    ).drop(columns=["team"])
    train_df["home_squad_quality"] = train_df["home_squad_quality"].fillna(60)
    train_df["away_squad_quality"] = train_df["away_squad_quality"].fillna(60)
    train_df["squad_quality_diff"] = train_df["home_squad_quality"] - train_df["away_squad_quality"]
    return train_df


def build_current_stats(train_df: pd.DataFrame) -> dict:
    stats = {}
    teams = pd.unique(pd.concat([train_df["home_team"], train_df["away_team"]]))
    for team in teams:
        hm = train_df[(train_df["home_team"] == team) | (train_df["away_team"] == team)].sort_values("date")
        if hm.empty:
            continue
        last = hm.iloc[-1]
        if last["home_team"] == team:
            stats[team] = {
                "elo": float(last["home_elo"]),
                "form": float(last["home_form"]),
                "gd": float(last["home_gd"]),
                "squad": float(last["home_squad_quality"]),
            }
        else:
            stats[team] = {
                "elo": float(last["away_elo"]),
                "form": float(last["away_form"]),
                "gd": float(last["away_gd"]),
                "squad": float(last["away_squad_quality"]),
            }
    return stats


def get_stat(current_stats: dict, team: str, stat: str) -> float:
    defaults = {"elo": 1500.0, "squad": 60.0, "form": 0.0, "gd": 0.0}
    return float(current_stats.get(team, {}).get(stat, defaults[stat]))


def feature_row(home: str, away: str, current_stats: dict) -> list[float]:
    host_adv = 1 if home in HOSTS else 0
    return [
        get_stat(current_stats, home, "elo") - get_stat(current_stats, away, "elo"),
        host_adv,
        get_stat(current_stats, home, "form"),
        get_stat(current_stats, away, "form"),
        get_stat(current_stats, home, "gd"),
        get_stat(current_stats, away, "gd"),
        get_stat(current_stats, home, "squad") - get_stat(current_stats, away, "squad"),
    ]


def predict_proba(model, home: str, away: str, current_stats: dict) -> dict:
    X = pd.DataFrame([feature_row(home, away, current_stats)], columns=FEATURES)
    probs = model.predict_proba(X)[0]
    classes = list(model.classes_)
    out = {"p_away": 0.0, "p_draw": 0.0, "p_home": 0.0}
    for i, c in enumerate(classes):
        if c == 0:
            out["p_away"] = float(probs[i])
        elif c == 1:
            out["p_draw"] = float(probs[i])
        elif c == 2:
            out["p_home"] = float(probs[i])
    return out


def knockout_probs(p: dict) -> tuple[float, float]:
    pa, ph = p["p_away"], p["p_home"]
    s = pa + ph
    if s <= 0:
        return 0.5, 0.5
    return pa / s, ph / s


def train_xgboost(X_train, y_train):
    try:
        import xgboost as xgb

        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric="mlogloss",
        )
        model.fit(X_train, y_train)
        return model, "XGBoost"
    except Exception:
        model = HistGradientBoostingClassifier(max_depth=6, random_state=42)
        model.fit(X_train, y_train)
        return model, "HistGradientBoosting"


def simulate_group_from_probs(future: pd.DataFrame, model, current_stats: dict, rng: np.random.Generator):
    groups: dict[str, dict[str, dict]] = {}
    match_results = []

    for _, row in future.iterrows():
        g = row["group"]
        ht = wu.normalize_team_name(row["home_team"])
        at = wu.normalize_team_name(row["away_team"])
        groups.setdefault(g, {})
        for t, ek in [(ht, "home_elo"), (at, "away_elo")]:
            if t not in groups[g]:
                elo = row.get(ek, np.nan)
                groups[g][t] = {
                    "pts": 0,
                    "gf": 0,
                    "ga": 0,
                    "w": 0,
                    "d": 0,
                    "l": 0,
                    "elo": float(elo) if pd.notna(elo) else get_stat(current_stats, t, "elo"),
                }

        p = predict_proba(model, ht, at, current_stats)
        probs = np.array([p["p_away"], p["p_draw"], p["p_home"]], dtype=float)
        probs = np.clip(probs, 0, None)
        s = probs.sum()
        probs = probs / s if s > 0 else np.array([1 / 3, 1 / 3, 1 / 3])
        outcome = rng.choice([0, 1, 2], p=probs)
        if outcome == 2:
            gh, ga = 2, 1
        elif outcome == 0:
            gh, ga = 0, 1
        else:
            gh, ga = 1, 1
        pth, pta = wu.group_play_result(gh, ga)
        groups[g][ht]["pts"] += pth
        groups[g][at]["pts"] += pta
        groups[g][ht]["gf"] += gh
        groups[g][ht]["ga"] += ga
        groups[g][at]["gf"] += ga
        groups[g][at]["ga"] += gh
        if pth == 3:
            groups[g][ht]["w"] += 1
            groups[g][at]["l"] += 1
        elif pta == 3:
            groups[g][at]["w"] += 1
            groups[g][ht]["l"] += 1
        else:
            groups[g][ht]["d"] += 1
            groups[g][at]["d"] += 1

        match_results.append(
            {
                "group": g,
                "home": ht,
                "away": at,
                "home_goals": gh,
                "away_goals": ga,
                **p,
            }
        )

    standings: dict[str, list[wu.Standing]] = {}
    for g, tdict in groups.items():
        lst = []
        for team, rec in tdict.items():
            lst.append(
                wu.Standing(
                    team=team,
                    grp=g,
                    pts=rec["pts"],
                    gd=rec["gf"] - rec["ga"],
                    gf=rec["gf"],
                    elo=rec["elo"],
                )
            )
        lst.sort(key=lambda x: x.rank_key, reverse=True)
        standings[g] = lst

    return standings, match_results, groups


def standings_to_json(standings: dict[str, list[wu.Standing]], groups_raw: dict) -> list:
    out = []
    for g in sorted(standings.keys()):
        rows = []
        for i, st in enumerate(standings[g]):
            rec = groups_raw[g][st.team]
            rows.append(
                {
                    "rank": i + 1,
                    "team": st.team,
                    "pts": st.pts,
                    "gd": st.gd,
                    "gf": st.gf,
                    "w": rec["w"],
                    "d": rec["d"],
                    "l": rec["l"],
                    "elo": st.elo,
                }
            )
        out.append({"group": g, "standings": rows})
    return out


def run_knockout_bracket(
    standings: dict[str, list[wu.Standing]],
    model,
    current_stats: dict,
    chalk: bool,
    rng: np.random.Generator,
) -> dict:
    """Return bracket tree with rounds and matches."""

    def sample_score(a, b, elo_a, elo_b, neutral):
        p = predict_proba(model, a, b, current_stats)
        pa, ph = knockout_probs(p)
        if chalk:
            return (2, 1) if ph >= pa else (0, 1)
        if rng.random() < ph:
            return (2, 1)
        return (0, 1)

    r32 = wu.build_r32_bracket(standings)
    winners: dict[int, tuple[str, float]] = {}
    matches_out: list[dict] = []

    def record(mid: int, ta: tuple, tb: tuple, w: str, elo_w: float, pa: float, ph: float):
        matches_out.append(
            {
                "id": mid,
                "team_a": ta[0],
                "team_b": tb[0],
                "winner": w,
                "p_win_a": round(ph, 4) if w == ta[0] else round(pa, 4),
                "p_win_b": round(ph, 4) if w == tb[0] else round(pa, 4),
            }
        )
        winners[mid] = (w, elo_w)

    for mid, ta, tb in r32:
        p = predict_proba(model, ta[0], tb[0], current_stats)
        pa, ph = knockout_probs(p)
        ga, gb = sample_score(ta[0], tb[0], ta[1], tb[1], True)
        if ga > gb:
            w, elo_w = ta[0], ta[1]
        else:
            w, elo_w = tb[0], tb[1]
        record(mid, ta, tb, w, elo_w, pa, ph)

    def play(id_a: int, id_b: int, mid: int):
        a, b = winners[id_a], winners[id_b]
        p = predict_proba(model, a[0], b[0], current_stats)
        pa, ph = knockout_probs(p)
        ga, gb = sample_score(a[0], b[0], a[1], b[1], True)
        if ga > gb:
            w, elo_w = a[0], a[1]
        else:
            w, elo_w = b[0], b[1]
        record(mid, a, b, w, elo_w, pa, ph)
        winners[mid] = (w, elo_w)

    play(73, 75, 90)
    play(74, 77, 89)
    play(76, 78, 91)
    play(79, 80, 92)
    play(83, 84, 93)
    play(81, 82, 94)
    play(86, 88, 95)
    play(85, 87, 96)
    play(89, 90, 97)
    play(93, 94, 98)
    play(91, 92, 99)
    play(95, 96, 100)
    play(97, 98, 101)
    play(99, 100, 102)
    play(101, 102, 103)

    champion = winners[103][0]
    round_map = {
        "R32": list(range(73, 89)),
        "R16": list(range(89, 97)),
        "QF": [97, 98, 99, 100],
        "SF": [101, 102],
        "Final": [103],
    }
    rounds = []
    for rname, ids in round_map.items():
        rounds.append(
            {
                "round": rname,
                "matches": [m for m in matches_out if m["id"] in ids],
            }
        )
    return {"rounds": rounds, "champion": champion}


def evaluate_capstone_temporal(train_df: pd.DataFrame) -> list[dict]:
    """Resume-grade evaluation: train on pre-2020, test on 2020+ (no random shuffle)."""
    tr = train_df[train_df["date"] < CAPSTONE_TEST_START]
    te = train_df[train_df["date"] >= CAPSTONE_TEST_START]
    X_tr, y_tr = tr[FEATURES], tr["match_outcome"]
    X_te, y_te = te[FEATURES], te["match_outcome"]

    rows = []
    for name, clf in [
        ("Logistic Regression", LogisticRegression(max_iter=2500, random_state=42)),
        ("Random Forest", RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)),
    ]:
        clf.fit(X_tr, y_tr)
        pred = clf.predict(X_te)
        rows.append(
            {
                "notebook": "wc_prediction",
                "model": name,
                "tier": "primary",
                "accuracy": round(float(accuracy_score(y_te, pred)), 4),
                "f1_macro": round(float(f1_score(y_te, pred, average="macro")), 4),
                "f1_draw": round(
                    float(f1_score(y_te, pred, labels=[1], average="macro", zero_division=0)), 4
                ),
                "split": "train < 2020, test ≥ 2020",
                "n_test": int(len(y_te)),
            }
        )

    xgb_model, xgb_name = train_xgboost(X_tr, y_tr)
    pred = xgb_model.predict(X_te)
    rows.append(
        {
            "notebook": "wc_prediction",
            "model": xgb_name,
            "tier": "primary",
            "accuracy": round(float(accuracy_score(y_te, pred)), 4),
            "f1_macro": round(float(f1_score(y_te, pred, average="macro")), 4),
            "f1_draw": round(
                float(f1_score(y_te, pred, labels=[1], average="macro", zero_division=0)), 4
            ),
            "split": "train < 2020, test ≥ 2020",
            "n_test": int(len(y_te)),
            "role": "Interactive site matchups & chalk bracket",
        }
    )
    return rows


def evaluate_capstone_random(train_df: pd.DataFrame) -> list[dict]:
    """Exploratory benchmark from notebook (optimistic; includes future info leakage risk)."""
    X = train_df[FEATURES]
    y = train_df["match_outcome"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model, model_name = train_xgboost(X_train, y_train)
    pred = model.predict(X_test)
    return [
        {
            "notebook": "wc_prediction",
            "model": model_name,
            "tier": "exploratory",
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "f1_macro": round(float(f1_score(y_test, pred, average="macro")), 4),
            "split": "80/20 random (notebook benchmark)",
            "note": "Not used for headline metrics — random split can inflate scores.",
        }
    ]


def save_plots(train_df, model, squad_quality, champ_odds, model_metrics) -> None:
    sns.set_theme(style="darkgrid")
    plt.figure(figsize=(8, 5))
    sns.countplot(data=train_df, x="match_outcome", palette="viridis")
    plt.title("Match outcomes (1998–2024)")
    plt.xticks([0, 1, 2], ["Away", "Draw", "Home"])
    plt.tight_layout()
    plt.savefig(OUT_ASSETS / "outcome_distribution.png", dpi=120)
    plt.close()

    if hasattr(model, "feature_importances_"):
        imp = pd.Series(model.feature_importances_, index=FEATURES).sort_values()
        imp.plot(kind="barh", figsize=(8, 4), color="#22c55e")
        plt.title("Feature importance (match outcome model)")
        plt.tight_layout()
        plt.savefig(OUT_ASSETS / "feature_importance.png", dpi=120)
        plt.close()

    top_sq = squad_quality.sort_values("squad_quality", ascending=False).head(10)
    plt.figure(figsize=(9, 5))
    sns.barplot(data=top_sq, y="team", x="squad_quality", palette="Blues_r")
    plt.title("Squad Quality Index (top 10)")
    plt.tight_layout()
    plt.savefig(OUT_ASSETS / "squad_quality_top10.png", dpi=120)
    plt.close()

    if champ_odds:
        top = champ_odds[:12]
        n = len(top)
        plt.figure(figsize=(11, max(5, n * 0.45)))
        teams = [x["team"] for x in top]
        ps = [x["p"] * 100 for x in top]
        plt.barh(teams[::-1], ps[::-1], color="#3b82f6")
        plt.xlabel("Title probability (%)")
        plt.title(f"Monte Carlo champion odds ({champ_odds[0].get('n_sims', '?')} sims)")
        plt.yticks(fontsize=10)
        plt.tight_layout()
        plt.savefig(OUT_ASSETS / "champion_odds.png", dpi=120)
        plt.close()


def main() -> None:
    ensure_dirs()
    print("Updating fixture teams (confirmed playoff winners)...")
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "scripts" / "update_fixture_teams.py")], check=True)
    print("Building training data...")
    squad_quality = load_squad_quality()
    train_df = build_train_df(squad_quality)
    current_stats = build_current_stats(train_df)

    tr = train_df[train_df["date"] < CAPSTONE_TEST_START]
    model, _ = train_xgboost(tr[FEATURES], tr["match_outcome"])
    joblib.dump({"model": model, "features": FEATURES, "current_stats": current_stats}, MODEL_DIR / "xgb_match.pkl")

    future = pd.read_csv(DATA / "future_match_probabilities_baseline.csv")
    tournament_teams = sorted(
        set(future["home_team"].map(wu.normalize_team_name))
        | set(future["away_team"].map(wu.normalize_team_name))
    )

    fixtures = []
    for _, row in future.iterrows():
        ht = wu.normalize_team_name(row["home_team"])
        at = wu.normalize_team_name(row["away_team"])
        mp = predict_proba(model, ht, at, current_stats)
        fixtures.append({
            "group": row["group"],
            "home": ht,
            "away": at,
            "p_home": round(mp["p_home"], 4),
            "p_draw": round(mp["p_draw"], 4),
            "p_away": round(mp["p_away"], 4),
            "baseline_p_home": float(row["p_home_win"]) if pd.notna(row.get("p_home_win")) else None,
            "baseline_p_draw": float(row["p_draw"]) if pd.notna(row.get("p_draw")) else None,
            "baseline_p_away": float(row["p_away_win"]) if pd.notna(row.get("p_away_win")) else None,
        })

    teams_json = []
    for t in tournament_teams:
        teams_json.append({
            "team": t,
            "elo": round(get_stat(current_stats, t, "elo"), 1),
            "form": round(get_stat(current_stats, t, "form"), 3),
            "gd": round(get_stat(current_stats, t, "gd"), 2),
            "squad": round(get_stat(current_stats, t, "squad"), 2),
            "slug": t.lower().replace(" ", "-").replace("'", ""),
        })

    matrix = []
    for i, h in enumerate(tournament_teams):
        for a in tournament_teams:
            if h == a or "Playoff" in h or "Playoff" in a:
                continue
            p = predict_proba(model, h, a, current_stats)
            matrix.append({"home": h, "away": a, **{k: round(v, 4) for k, v in p.items()}})

    matchups = []
    for h, a in CURATED_MATCHUPS:
        p = predict_proba(model, h, a, current_stats)
        matchups.append({
            "home": h,
            "away": a,
            "p_home": round(p["p_home"], 4),
            "p_draw": round(p["p_draw"], 4),
            "p_away": round(p["p_away"], 4),
        })

    print("Running Monte Carlo (full WC2026 pipeline)...")
    champ_odds, sim_test_metrics = run_monte_carlo(DATA, n_sims=1000, seed=42)

    rng = np.random.default_rng(7)
    standings, _, groups_raw = simulate_group_from_probs(future, model, current_stats, rng)
    chalk = run_knockout_bracket(standings, model, current_stats, chalk=True, rng=rng)

    squad_top10 = (
        squad_quality.sort_values("squad_quality", ascending=False)
        .head(10)
        .assign(squad_quality=lambda d: d["squad_quality"].round(2))
        .to_dict(orient="records")
    )

    findings = {
        "home_win_pct": round(100 * (train_df["match_outcome"] == 2).mean(), 1),
        "draw_pct": round(100 * (train_df["match_outcome"] == 1).mean(), 1),
        "away_win_pct": round(100 * (train_df["match_outcome"] == 0).mean(), 1),
        "squad_top10": squad_top10,
        "chalk_champion": chalk["champion"],
        "notes": [
            "Headline accuracy uses temporal holdout (test matches from 2020+), not random shuffle.",
            "Draw outcomes remain the hardest class (low F1 vs home/away wins).",
            "Squad Quality (FC26) is used for 2026 inference only — not merged into historical training rows.",
            "Title odds are scenario counts from 1,000 bracket simulations, not calibrated betting probabilities.",
        ],
    }

    model_metrics = evaluate_capstone_temporal(train_df) + evaluate_capstone_random(train_df)
    model_metrics.append(
        {
            "notebook": "WC2026_simulation",
            "model": sim_test_metrics["model"],
            "tier": "primary",
            "accuracy": round(sim_test_metrics["accuracy"], 4),
            "f1_macro": round(sim_test_metrics["f1_macro"], 4),
            "f1_draw": round(sim_test_metrics["f1_draw"], 4),
            "split": sim_test_metrics["split"],
            "n_test": sim_test_metrics["n_test"],
            "role": "Monte Carlo tournament (Poisson goals + FIFA bracket)",
        }
    )

    methodology = {
        "what_this_is": [
            "Supervised multiclass model (home / draw / away) on post-1998 competitive internationals.",
            "2026 tournament tool: group fixtures with confirmed qualifiers, interactive bracket, Monte Carlo title odds.",
        ],
        "limitations": [
            "No true holdout for World Cup 2026 — forecasts are forward-looking scenarios, not backtested predictions.",
            "Draw class is under-predicted; macro-F1 is a better headline metric than accuracy alone.",
            "FC26 squad ratings are contemporary; they are not applied to historical training rows to avoid roster anachronisms.",
            "Monte Carlo counts depend on simulation design (Poisson goals, FIFA bracket wiring, 1,000 runs).",
            "Third-place slot assignment uses combinatorial backtracking — close to FIFA rules but not every edge case.",
        ],
        "design_choices": [
            "Primary evaluation: chronological splits (train ≤ 2016, val ≤ 2019, test ≥ 2020 for simulation pipeline; train < 2020 / test ≥ 2020 for capstone features).",
            "Site matchups & chalk bracket: XGBoost with Elo, form, host advantage, squad quality.",
            "Title odds chart: temporal classifier + trained Poisson goal model + full knockout tree.",
        ],
    }

    def write(name: str, obj) -> None:
        path = OUT_DATA / name
        path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        print(f"  wrote {path}")

    write("fixtures.json", fixtures)
    write("teams.json", teams_json)
    write("matchup_matrix.json", matrix)
    write("matchups.json", matchups)
    write("champion_odds.json", champ_odds)
    write("chalk_bracket.json", chalk)
    write("model_metrics.json", model_metrics)
    write("findings.json", findings)
    write("methodology.json", methodology)
    write("default_groups.json", standings_to_json(standings, groups_raw))

    print("Saving plots...")
    save_plots(train_df, model, squad_quality, champ_odds, model_metrics)
    print("Done.")


if __name__ == "__main__":
    main()
