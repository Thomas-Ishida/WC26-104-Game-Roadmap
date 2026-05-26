export interface Standing {
  team: string;
  grp: string;
  pts: number;
  gd: number;
  gf: number;
  elo: number;
}

export function rankKey(s: Standing): [number, number, number, number] {
  return [s.pts, s.gd, s.gf, s.elo];
}

export function compareStandings(a: Standing, b: Standing): number {
  const ka = rankKey(a);
  const kb = rankKey(b);
  for (let i = 0; i < ka.length; i++) {
    if (ka[i] !== kb[i]) return kb[i] - ka[i];
  }
  return 0;
}

export function sortStandings(list: Standing[]): Standing[] {
  return [...list].sort(compareStandings);
}

export function groupStandingsFromRows(
  groups: { group: string; standings: { team: string; pts: number; gd: number; gf: number; elo: number }[] }[]
): Record<string, Standing[]> {
  const out: Record<string, Standing[]> = {};
  for (const g of groups) {
    out[g.group] = g.standings.map((r) => ({
      team: r.team,
      grp: g.group,
      pts: r.pts,
      gd: r.gd,
      gf: r.gf,
      elo: r.elo,
    }));
  }
  return out;
}
