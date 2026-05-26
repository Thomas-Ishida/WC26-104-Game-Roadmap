"""
Helpers for WC2026_simulation.ipynb: Elo merge, features, bracket, simulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

import unicodedata

import numpy as np
import pandas as pd

TEAM_ALIASES = {
    "cote d'ivoire": "Ivory Coast",
    "cape verde": "Cape Verde",
    "usa": "United States",
    "korea republic": "South Korea",
    "korea, republic of": "South Korea",
    "curacao": "Curaçao",
    "china pr": "China",
    "dr congo": "Democratic Republic of the Congo",
    "congo dr": "Democratic Republic of the Congo",
    "türkiye": "Turkey",
    "turkiye": "Turkey",
}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("\u2019", "'").replace("`", "'")


def normalize_team_name(name: str) -> str:
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return name
    raw = str(name).strip()
    s = _fold(raw)
    if "_" in s and " " not in s:
        s = s.replace("_", " ")
    key = s.lower()
    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key]
    return s


def load_former_name_map(path: str) -> Dict[str, str]:
    fn = pd.read_csv(path)
    return {str(r["former"]): str(r["current"]) for _, r in fn.iterrows()}


def to_elo_team(name: str, former_map: Dict[str, str]) -> str:
    n = normalize_team_name(name)
    return former_map.get(n, n)


def merge_asof_elo(matches: pd.DataFrame, elo_long: pd.DataFrame) -> pd.DataFrame:
    m = matches.copy()
    m["date"] = pd.to_datetime(m["date"])
    elo = elo_long.copy()
    elo["date"] = pd.to_datetime(elo["date"])

    left_home = m[["date", "home_team"]].rename(columns={"home_team": "team"})
    left_away = m[["date", "away_team"]].rename(columns={"away_team": "team"})
    elo_h = elo.rename(columns={"rating": "elo_home"})
    elo_a = elo.rename(columns={"rating": "elo_away"})

    mh = pd.merge_asof(
        left_home.sort_values("date"),
        elo_h.sort_values("date"),
        on="date",
        by="team",
        direction="backward",
    )
    ma = pd.merge_asof(
        left_away.sort_values("date"),
        elo_a.sort_values("date"),
        on="date",
        by="team",
        direction="backward",
    )
    m = m.sort_values("date").reset_index(drop=True)
    mh = mh.sort_values("date").reset_index(drop=True)
    ma = ma.sort_values("date").reset_index(drop=True)
    m["elo_home"] = mh["elo_home"].values
    m["elo_away"] = ma["elo_away"].values
    return m


def add_rolling_features_fast(matches: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    m = matches.sort_values("date").reset_index(drop=True)
    long_rows = []
    for _, r in m.iterrows():
        d, hs, asos = r["date"], r["home_score"], r["away_score"]
        long_rows.append(
            {"date": d, "team": r["home_team"], "gf": hs, "ga": asos, "is_home": 1}
        )
        long_rows.append(
            {"date": d, "team": r["away_team"], "gf": asos, "ga": hs, "is_home": 0}
        )
    L = pd.DataFrame(long_rows).sort_values(["team", "date"])
    L["pts"] = np.where(L["gf"] > L["ga"], 3, np.where(L["gf"] == L["ga"], 1, 0))
    L["gd"] = L["gf"] - L["ga"]

    gobj = L.groupby("team", sort=False, group_keys=False)
    L["form_pts"] = gobj["pts"].transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    L["form_gd"] = gobj["gd"].transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    L["form_n"] = gobj["pts"].transform(lambda s: s.shift(1).rolling(window, min_periods=1).count())
    home_part = L[L["is_home"] == 1][["date", "team", "form_pts", "form_gd", "form_n"]].rename(
        columns={
            "team": "home_team",
            "form_pts": "form_pts_home",
            "form_gd": "form_gd_home",
            "form_n": "form_n_home",
        }
    )
    away_part = L[L["is_home"] == 0][["date", "team", "form_pts", "form_gd", "form_n"]].rename(
        columns={
            "team": "away_team",
            "form_pts": "form_pts_away",
            "form_gd": "form_gd_away",
            "form_n": "form_n_away",
        }
    )
    out = m.merge(home_part, on=["date", "home_team"], how="left")
    out = out.merge(away_part, on=["date", "away_team"], how="left")
    for c in [
        "form_pts_home",
        "form_gd_home",
        "form_n_home",
        "form_pts_away",
        "form_gd_away",
        "form_n_away",
    ]:
        out[c] = out[c].fillna(0.0)

    h2h_home: List[float] = []
    hist: Dict[Tuple[str, str], List[int]] = {}
    for _, r in out.iterrows():
        ht, at = r["home_team"], r["away_team"]
        xs = hist.get((ht, at), [])
        h2h_home.append(float(np.mean(xs[-5:])) if xs else 1.0)
        if r["home_score"] > r["away_score"]:
            hp, ap = 3, 0
        elif r["home_score"] < r["away_score"]:
            hp, ap = 0, 3
        else:
            hp, ap = 1, 1
        hist.setdefault((ht, at), []).append(hp)
        hist.setdefault((at, ht), []).append(ap)
    out["h2h_home_points_avg"] = h2h_home
    return out


@dataclass
class Standing:
    team: str
    grp: str
    pts: int
    gd: int
    gf: int
    elo: float

    @property
    def rank_key(self) -> Tuple[int, int, int, float]:
        return (self.pts, self.gd, self.gf, self.elo)


def group_play_result(gh: int, ga: int) -> Tuple[int, int]:
    if gh > ga:
        return 3, 0
    if gh < ga:
        return 0, 3
    return 1, 1


def simulate_group_stage_from_fixtures(
    fixture_rows: pd.DataFrame,
    sample_score: Callable[[str, str, float, float, bool], Tuple[int, int]],
    neutral_site: bool = True,
) -> Dict[str, List[Standing]]:
    fixtures = fixture_rows.copy()
    groups: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for _, row in fixtures.iterrows():
        g = row["group"]
        ht = normalize_team_name(row["home_team"])
        at = normalize_team_name(row["away_team"])
        groups.setdefault(g, {})
        for t, elo_key in [(ht, "home_elo"), (at, "away_elo")]:
            if t not in groups[g]:
                elo = row.get(elo_key, np.nan)
                groups[g][t] = {"pts": 0, "gf": 0, "ga": 0, "elo": float(elo) if pd.notna(elo) else 1500.0}

    seen = set()
    for _, row in fixtures.iterrows():
        g = row["group"]
        ht = normalize_team_name(row["home_team"])
        at = normalize_team_name(row["away_team"])
        key = (g, tuple(sorted([ht, at])))
        if key in seen:
            continue
        seen.add(key)
        he = float(row["home_elo"]) if pd.notna(row.get("home_elo")) else groups[g][ht]["elo"]
        ae = float(row["away_elo"]) if pd.notna(row.get("away_elo")) else groups[g][at]["elo"]
        groups[g][ht]["elo"] = he
        groups[g][at]["elo"] = ae
        gh, ga = sample_score(ht, at, he, ae, neutral_site)
        pth, pta = group_play_result(gh, ga)
        groups[g][ht]["pts"] += pth
        groups[g][at]["pts"] += pta
        groups[g][ht]["gf"] += gh
        groups[g][ht]["ga"] += ga
        groups[g][at]["gf"] += ga
        groups[g][at]["ga"] += gh

    out: Dict[str, List[Standing]] = {}
    for g, tdict in groups.items():
        lst = []
        for team, rec in tdict.items():
            lst.append(
                Standing(
                    team=team,
                    grp=g,
                    pts=rec["pts"],
                    gd=rec["gf"] - rec["ga"],
                    gf=rec["gf"],
                    elo=rec["elo"],
                )
            )
        lst.sort(key=lambda x: x.rank_key, reverse=True)
        out[g] = lst
    return out


# R32 slot definitions: (match_code, side_a, side_b) where side is ('winner', letter) | ('runner', letter) | ('third', frozenset letters)
R32_FIXTURES: List[Tuple[int, Any, Any]] = [
    (73, ("runner", "A"), ("runner", "B")),
    (76, ("winner", "C"), ("runner", "F")),
    (74, ("winner", "E"), ("third", frozenset("ABCDF"))),
    (75, ("winner", "F"), ("runner", "C")),
    (78, ("runner", "E"), ("runner", "I")),
    (77, ("winner", "I"), ("third", frozenset("CDFGH"))),
    (79, ("winner", "A"), ("third", frozenset("CEFHI"))),
    (80, ("winner", "L"), ("third", frozenset("EHIJK"))),
    (82, ("winner", "G"), ("third", frozenset("AEHIJ"))),
    (81, ("winner", "D"), ("third", frozenset("BEFIJ"))),
    (84, ("winner", "H"), ("runner", "J")),
    (83, ("runner", "K"), ("runner", "L")),
    (85, ("winner", "B"), ("third", frozenset("EFGIJ"))),
    (86, ("winner", "J"), ("runner", "H")),
    (87, ("winner", "K"), ("third", frozenset("DEIJL"))),
    (88, ("runner", "D"), ("runner", "G")),
]


def pick_third_for_slot(
    eligible_groups: frozenset,
    thirds_pool: List[Standing],
    reserved: set,
) -> Standing | None:
    for t in thirds_pool:
        if t.grp in eligible_groups and t.team not in reserved:
            return t
    return None


def assign_all_thirds(r32_needs_third: List[Tuple[int, frozenset]], thirds_advancing: List[Standing]) -> Dict[int, Standing]:
    sorted_thirds = sorted(thirds_advancing, key=lambda x: x.rank_key, reverse=True)
    assignment: Dict[int, Standing] = {}
    reserved_teams = set()

    def backtrack(idx: int) -> bool:
        if idx >= len(r32_needs_third):
            return True
        mid, elig = r32_needs_third[idx]
        for t in sorted_thirds:
            if t.team in reserved_teams:
                continue
            if t.grp not in elig:
                continue
            assignment[mid] = t
            reserved_teams.add(t.team)
            if backtrack(idx + 1):
                return True
            del assignment[mid]
            reserved_teams.remove(t.team)
        return False

    if not backtrack(0):
        for mid, elig in r32_needs_third:
            t = pick_third_for_slot(elig, sorted_thirds, reserved_teams)
            if t is None:
                for cand in sorted_thirds:
                    if cand.team not in reserved_teams:
                        t = cand
                        break
            if t is not None:
                assignment[mid] = t
                reserved_teams.add(t.team)
    return assignment


def resolve_r32_team(
    spec: Tuple[str, Any],
    standings: Dict[str, List[Standing]],
    third_assign: Dict[int, Standing],
    match_id: int,
) -> Tuple[str, float]:
    kind, letter = spec[0], spec[1]
    if kind == "winner":
        st = standings[letter][0]
        return st.team, st.elo
    if kind == "runner":
        st = standings[letter][1]
        return st.team, st.elo
    assert kind == "third"
    t = third_assign[match_id]
    return t.team, t.elo


def build_r32_bracket(
    standings: Dict[str, List[Standing]],
) -> List[Tuple[int, Tuple[str, float], Tuple[str, float]]]:
    all_thirds = [s[2] for s in standings.values()]
    all_thirds_sorted = sorted(all_thirds, key=lambda x: x.rank_key, reverse=True)
    thirds_adv = all_thirds_sorted[:8]

    r32_third_list: List[Tuple[int, frozenset]] = []
    for mid, a, b in R32_FIXTURES:
        if a[0] == "third":
            r32_third_list.append((mid, a[1]))
        elif b[0] == "third":
            r32_third_list.append((mid, b[1]))

    third_assign = assign_all_thirds(r32_third_list, thirds_adv)

    matches = []
    for mid, sa, sb in R32_FIXTURES:
        ta = resolve_r32_team(sa, standings, third_assign, mid)
        tb = resolve_r32_team(sb, standings, third_assign, mid)
        matches.append((mid, ta, tb))
    return matches


def knockout_winner(
    team_a: str,
    elo_a: float,
    team_b: str,
    elo_b: float,
    sample_score: Callable[[str, str, float, float, bool], Tuple[int, int]],
    neutral: bool = True,
) -> Tuple[str, float]:
    ga, gb = sample_score(team_a, team_b, elo_a, elo_b, neutral)
    if ga > gb:
        return team_a, elo_a
    if ga < gb:
        return team_b, elo_b
    p_a = 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))
    if np.random.rand() < p_a:
        return team_a, elo_a
    return team_b, elo_b


def latest_form_per_team(
    matches: pd.DataFrame, cutoff: pd.Timestamp, window: int = 10
) -> pd.DataFrame:
    """Rolling form (pts/gd) from each team's last pre-cutoff match."""
    sub = matches[matches["date"] < cutoff].copy()
    if sub.empty:
        return pd.DataFrame(columns=["team", "form_pts", "form_gd"])
    sub = add_rolling_features_fast(sub, window)
    teams = pd.unique(pd.concat([sub["home_team"], sub["away_team"]], ignore_index=True))
    rows = []
    for team in teams:
        hm = sub[(sub["home_team"] == team) | (sub["away_team"] == team)].sort_values("date")
        if hm.empty:
            continue
        r = hm.iloc[-1]
        if r["home_team"] == team:
            rows.append(
                {
                    "team": team,
                    "form_pts": float(r["form_pts_home"]),
                    "form_gd": float(r["form_gd_home"]),
                }
            )
        else:
            rows.append(
                {
                    "team": team,
                    "form_pts": float(r["form_pts_away"]),
                    "form_gd": float(r["form_gd_away"]),
                }
            )
    return pd.DataFrame(rows)


def run_full_knockout(
    standings: Dict[str, List[Standing]],
    sample_score: Callable[[str, str, float, float, bool], Tuple[int, int]],
) -> str:
    r32 = build_r32_bracket(standings)
    winners: Dict[int, Tuple[str, float]] = {}
    for mid, ta, tb in r32:
        w, elo = knockout_winner(ta[0], ta[1], tb[0], tb[1], sample_score, neutral=True)
        winners[mid] = (w, elo)

    def play(id_a: int, id_b: int) -> Tuple[str, float]:
        a, b = winners[id_a], winners[id_b]
        w, elo = knockout_winner(a[0], a[1], b[0], b[1], sample_score, neutral=True)
        return w, elo

    # Round of 16 (FIFA match numbers from Wikipedia)
    winners[90] = play(73, 75)
    winners[89] = play(74, 77)
    winners[91] = play(76, 78)
    winners[92] = play(79, 80)
    winners[93] = play(83, 84)
    winners[94] = play(81, 82)
    winners[95] = play(86, 88)
    winners[96] = play(85, 87)

    # Quarter-finals
    winners[97] = knockout_winner(
        winners[89][0], winners[89][1], winners[90][0], winners[90][1], sample_score, neutral=True
    )
    winners[98] = knockout_winner(
        winners[93][0], winners[93][1], winners[94][0], winners[94][1], sample_score, neutral=True
    )
    winners[99] = knockout_winner(
        winners[91][0], winners[91][1], winners[92][0], winners[92][1], sample_score, neutral=True
    )
    winners[100] = knockout_winner(
        winners[95][0], winners[95][1], winners[96][0], winners[96][1], sample_score, neutral=True
    )

    # Semi-finals
    winners[101] = knockout_winner(
        winners[97][0], winners[97][1], winners[98][0], winners[98][1], sample_score, neutral=True
    )
    winners[102] = knockout_winner(
        winners[99][0], winners[99][1], winners[100][0], winners[100][1], sample_score, neutral=True
    )

    # Final
    champion = knockout_winner(
        winners[101][0], winners[101][1], winners[102][0], winners[102][1], sample_score, neutral=True
    )[0]
    return champion
