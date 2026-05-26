import { useEffect, useState } from "react";
import type {
  BracketTree,
  ChampionOdds,
  Findings,
  Fixture,
  GroupBlock,
  MatrixEntry,
  ModelMetric,
  MatchupProb,
  MethodologyData,
  SiteData,
  Team,
} from "../types";

const base = import.meta.env.BASE_URL;

async function loadJson<T>(path: string): Promise<T> {
  const res = await fetch(`${base}data/${path}`);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return res.json() as Promise<T>;
}

export function useSiteData() {
  const [data, setData] = useState<SiteData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      loadJson<Team[]>("teams.json"),
      loadJson<Fixture[]>("fixtures.json"),
      loadJson<MatchupProb[]>("matchups.json"),
      loadJson<MatrixEntry[]>("matchup_matrix.json"),
      loadJson<ChampionOdds[]>("champion_odds.json"),
      loadJson<BracketTree>("chalk_bracket.json"),
      loadJson<ModelMetric[]>("model_metrics.json"),
      loadJson<Findings>("findings.json"),
      loadJson<GroupBlock[]>("default_groups.json"),
      loadJson<MethodologyData>("methodology.json"),
    ])
      .then(
        ([
          teams,
          fixtures,
          matchups,
          matchupMatrix,
          championOdds,
          chalkBracket,
          modelMetrics,
          findings,
          defaultGroups,
          methodology,
        ]) => {
          setData({
            teams,
            fixtures,
            matchups,
            matchupMatrix,
            championOdds,
            chalkBracket,
            modelMetrics,
            findings,
            defaultGroups,
            methodology,
          });
        }
      )
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, []);

  return { data, error, asset: (name: string) => `${base}assets/${name}` };
}
