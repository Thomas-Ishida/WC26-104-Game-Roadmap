"""Full WC2026 Monte Carlo pipeline (matches WC2026_simulation.ipynb)."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.metrics import f1_score

import wc2026_simulation_utils as wu

FEATURE_COLS = [
    "elo_home",
    "elo_away",
    "elo_diff",
    "neutral_int",
    "form_pts_home",
    "form_gd_home",
    "form_pts_away",
    "form_gd_away",
    "h2h_home_points_avg",
    "home_injury",
    "away_injury",
]
TRAIN_END = pd.Timestamp("2016-12-31")
VAL_END = pd.Timestamp("2019-12-31")
ROLL_WINDOW = 10


def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = z * np.sqrt((p * (1 - p) / n) + z2 / (4 * n * n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def build_historical_feat(data_dir: str | Path):
    root = Path(data_dir)
    results_raw = pd.read_csv(root / "results.csv")
    elo_raw = pd.read_csv(root / "eloratings.csv")
    former = wu.load_former_name_map(str(root / "former_names.csv"))

    results_raw["date"] = pd.to_datetime(results_raw["date"])
    elo_raw["date"] = pd.to_datetime(elo_raw["date"], format="mixed", dayfirst=False)
    results_raw["home_team"] = results_raw["home_team"].map(lambda x: wu.to_elo_team(x, former))
    results_raw["away_team"] = results_raw["away_team"].map(lambda x: wu.to_elo_team(x, former))
    elo_raw["team"] = elo_raw["team"].map(lambda x: wu.to_elo_team(x, former))

    matches = results_raw[
        (results_raw["date"] >= pd.Timestamp("1998-01-01"))
        & (results_raw["tournament"] != "Friendly")
    ].copy()
    matches["target"] = np.select(
        [
            matches["home_score"] > matches["away_score"],
            matches["home_score"] == matches["away_score"],
        ],
        [2, 1],
        default=0,
    )
    matches["neutral_int"] = matches["neutral"].astype(str).str.upper().eq("TRUE").astype(int)
    matches = matches.sort_values("date").reset_index(drop=True)

    feat = wu.merge_asof_elo(matches, elo_raw)
    feat["elo_diff"] = feat["elo_home"] - feat["elo_away"]
    feat = wu.add_rolling_features_fast(feat, window=ROLL_WINDOW)
    feat["home_injury"] = 0
    feat["away_injury"] = 0
    feat = feat.dropna(subset=["elo_home", "elo_away"])
    feat[FEATURE_COLS] = feat[FEATURE_COLS].fillna(0.0)
    return feat, former, matches


def build_wc_features(future: pd.DataFrame, matches: pd.DataFrame, former: dict) -> pd.DataFrame:
    form_cutoff = matches["date"].max() + pd.Timedelta(seconds=1)
    hist = matches[matches["date"] < form_cutoff].copy()
    form_df = wu.latest_form_per_team(matches, form_cutoff, ROLL_WINDOW)
    form_lookup = form_df.set_index("team") if not form_df.empty else pd.DataFrame()

    def h2h_home_ppg(home_team: str, away_team: str, k: int = 5) -> float:
        sub = hist[
            ((hist["home_team"] == home_team) & (hist["away_team"] == away_team))
            | ((hist["home_team"] == away_team) & (hist["away_team"] == home_team))
        ].sort_values("date")
        if sub.empty:
            return 1.0
        pts = []
        for _, r in sub.tail(k).iterrows():
            if r["home_team"] == home_team:
                if r["home_score"] > r["away_score"]:
                    pts.append(3)
                elif r["home_score"] == r["away_score"]:
                    pts.append(1)
                else:
                    pts.append(0)
            else:
                if r["away_score"] > r["home_score"]:
                    pts.append(3)
                elif r["away_score"] == r["home_score"]:
                    pts.append(1)
                else:
                    pts.append(0)
        return float(np.mean(pts))

    def canon_team(x: str) -> str:
        return wu.to_elo_team(wu.normalize_team_name(x), former)

    rows = []
    for _, r in future.iterrows():
        ht = canon_team(str(r["home_team"]))
        at = canon_team(str(r["away_team"]))
        eh = float(r["home_elo"]) if pd.notna(r.get("home_elo")) else 1500.0
        ea = float(r["away_elo"]) if pd.notna(r.get("away_elo")) else 1500.0
        fh = form_lookup.loc[ht] if ht in form_lookup.index else None
        fa = form_lookup.loc[at] if at in form_lookup.index else None
        fph = float(fh["form_pts"]) if fh is not None else 1.0
        fgh = float(fh["form_gd"]) if fh is not None else 0.0
        fpa = float(fa["form_pts"]) if fa is not None else 1.0
        fga = float(fa["form_gd"]) if fa is not None else 0.0
        rows.append(
            {
                "group": r["group"],
                "home_team": ht,
                "away_team": at,
                "elo_home": eh,
                "elo_away": ea,
                "home_elo": eh,
                "away_elo": ea,
                "elo_diff": eh - ea,
                "neutral_int": 1,
                "form_pts_home": fph,
                "form_gd_home": fgh,
                "form_pts_away": fpa,
                "form_gd_away": fga,
                "h2h_home_points_avg": h2h_home_ppg(ht, at),
                "home_injury": int(r.get("home_injury_flag", 0) or 0),
                "away_injury": int(r.get("away_injury_flag", 0) or 0),
            }
        )
    return pd.DataFrame(rows)


def run_monte_carlo(data_dir: str | Path, n_sims: int = 1000, seed: int = 42) -> Tuple[List[dict], dict]:
    root = Path(data_dir)
    feat, former, matches = build_historical_feat(root)

    train_idx = feat["date"] <= TRAIN_END
    val_idx = (feat["date"] > TRAIN_END) & (feat["date"] <= VAL_END)
    test_idx = feat["date"] > VAL_END

    X_train = feat.loc[train_idx, FEATURE_COLS]
    y_train = feat.loc[train_idx, "target"]
    X_val = feat.loc[val_idx, FEATURE_COLS]
    y_val = feat.loc[val_idx, "target"]
    X_test = feat.loc[test_idx, FEATURE_COLS]
    y_test = feat.loc[test_idx, "target"]

    candidates = {
        "logreg": LogisticRegression(max_iter=2500, random_state=42),
        "rf": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
        "hgb": HistGradientBoostingClassifier(max_depth=6, random_state=42),
    }
    trained = {}
    val_f1 = {}
    for name, clf in candidates.items():
        clf.fit(X_train, y_train)
        trained[name] = clf
        val_f1[name] = f1_score(y_val, clf.predict(X_val), average="macro")

    best_name = max(val_f1, key=val_f1.get)

    train_goal = feat.loc[train_idx]
    Xg = train_goal[["elo_diff", "neutral_int"]].to_numpy()
    pr_home = PoissonRegressor(max_iter=300, alpha=1e-3)
    pr_away = PoissonRegressor(max_iter=300, alpha=1e-3)
    pr_home.fit(Xg, train_goal["home_score"])
    pr_away.fit(Xg, train_goal["away_score"])

    rng = np.random.default_rng(seed)

    def sample_goals_poisson(ht, at, elo_h, elo_a, neutral):
        diff = elo_h - elo_a
        z = np.array([[diff, float(neutral)]])
        lam_h = float(np.clip(pr_home.predict(z)[0], 0.15, 5.5))
        lam_a = float(np.clip(pr_away.predict(z)[0], 0.15, 5.5))
        return int(rng.poisson(lam_h)), int(rng.poisson(lam_a))

    future = pd.read_csv(root / "future_match_probabilities_baseline.csv")
    sim_fixtures = build_wc_features(future, matches, former)

    counts: Counter[str] = Counter()
    for _ in range(n_sims):
        standings = wu.simulate_group_stage_from_fixtures(
            sim_fixtures, sample_goals_poisson, neutral_site=True
        )
        champ = wu.run_full_knockout(standings, sample_goals_poisson)
        counts[champ] += 1

    rows = []
    for team, c in counts.most_common(20):
        lo, hi = wilson_ci(c, n_sims)
        rows.append(
            {
                "team": team,
                "p": c / n_sims,
                "ci_low": round(lo, 4),
                "ci_high": round(hi, 4),
                "wins": c,
                "source": "WC2026_simulation (temporal logreg + Poisson goals)",
                "n_sims": n_sims,
            }
        )

    test_metrics = {
        "model": best_name,
        "accuracy": float((trained[best_name].predict(X_test) == y_test).mean()),
        "f1_macro": float(f1_score(y_test, trained[best_name].predict(X_test), average="macro")),
        "f1_draw": float(
            f1_score(
                y_test,
                trained[best_name].predict(X_test),
                labels=[1],
                average="macro",
                zero_division=0,
            )
        ),
        "split": "test ≥ 2020",
        "n_test": int(len(y_test)),
        "val_f1_macro": {k: round(v, 4) for k, v in val_f1.items()},
    }

    return rows, test_metrics
