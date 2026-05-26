#!/usr/bin/env python3
"""Replace playoff placeholders with confirmed 2026 World Cup qualifiers."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "future_match_probabilities_baseline.csv"
ELO = ROOT / "data" / "eloratings.csv"

# Path → winner (March 2026 playoffs, UEFA + intercontinental)
PLAYOFF_WINNERS = {
    "UEFA_Playoff_A": "Bosnia and Herzegovina",
    "UEFA_Playoff_B": "Sweden",
    "UEFA_Playoff_C": "Turkey",
    "UEFA_Playoff_D": "Czechia",
    "Interconf_Playoff_1": "DR Congo",
    "Interconf_Playoff_2": "Iraq",
}

ELO_LOOKUP = {
    "Bosnia and Herzegovina": "Bosnia and Herzegovina",
    "DR Congo": "Democratic Republic of the Congo",
}


def latest_elo() -> dict[str, float]:
    elo = pd.read_csv(ELO)
    elo["date"] = pd.to_datetime(elo["date"], format="mixed")
    elo = elo.sort_values("date")
    out: dict[str, float] = {}
    for team, grp in elo.groupby("team"):
        out[str(team)] = float(grp.iloc[-1]["rating"])
    return out


def _norm(s: str) -> str:
    return s.replace("\u00a0", " ").strip().lower()


def resolve_elo(team: str, ratings: dict[str, float]) -> float | None:
    key = ELO_LOOKUP.get(team, team)
    if key in ratings:
        return ratings[key]
    nk = _norm(key)
    for k, v in ratings.items():
        if _norm(k) == nk:
            return v
    if team == "DR Congo":
        for k, v in ratings.items():
            if "democratic" in _norm(k) and "congo" in _norm(k):
                return v
    return None


def main() -> None:
    df = pd.read_csv(FIXTURES)
    ratings = latest_elo()

    for col in ("home_team", "away_team"):
        df[col] = df[col].replace(PLAYOFF_WINNERS)

    for i, row in df.iterrows():
        for side, elo_col in (("home_team", "home_elo"), ("away_team", "away_elo")):
            t = row[side]
            e = resolve_elo(t, ratings)
            if e is not None:
                df.at[i, elo_col] = e
        he, ae = row.get("home_elo"), row.get("away_elo")
        if pd.notna(df.at[i, "home_elo"]) and pd.notna(df.at[i, "away_elo"]):
            df.at[i, "elo_diff"] = float(df.at[i, "home_elo"]) - float(df.at[i, "away_elo"])

    df.to_csv(FIXTURES, index=False)
    print(f"Updated {FIXTURES}")
    for k, v in PLAYOFF_WINNERS.items():
        print(f"  {k} → {v}")


if __name__ == "__main__":
    main()
