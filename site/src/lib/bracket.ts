import type { Fixture, MatrixEntry } from "../types";
import { compareStandings, type Standing } from "./standings";

type SideSpec = ["winner" | "runner" | "third", string | Set<string>];

export const R32_FIXTURES: [number, SideSpec, SideSpec][] = [
  [73, ["runner", "A"], ["runner", "B"]],
  [76, ["winner", "C"], ["runner", "F"]],
  [74, ["winner", "E"], ["third", "ABCDF"]],
  [75, ["winner", "F"], ["runner", "C"]],
  [78, ["runner", "E"], ["runner", "I"]],
  [77, ["winner", "I"], ["third", "CDFGH"]],
  [79, ["winner", "A"], ["third", "CEFHI"]],
  [80, ["winner", "L"], ["third", "EHIJK"]],
  [82, ["winner", "G"], ["third", "AEHIJ"]],
  [81, ["winner", "D"], ["third", "BEFIJ"]],
  [84, ["winner", "H"], ["runner", "J"]],
  [83, ["runner", "K"], ["runner", "L"]],
  [85, ["winner", "B"], ["third", "EFGIJ"]],
  [86, ["winner", "J"], ["runner", "H"]],
  [87, ["winner", "K"], ["third", "DEIJL"]],
  [88, ["runner", "D"], ["runner", "G"]],
];

function parseThirdLetters(s: string): Set<string> {
  return new Set(s.split(""));
}

function assignAllThirds(
  needs: [number, Set<string>][],
  thirds: Standing[]
): Map<number, Standing> {
  const sorted = [...thirds].sort(compareStandings);
  const assignment = new Map<number, Standing>();
  const reserved = new Set<string>();

  function backtrack(idx: number): boolean {
    if (idx >= needs.length) return true;
    const [mid, elig] = needs[idx];
    for (const t of sorted) {
      if (reserved.has(t.team)) continue;
      if (!elig.has(t.grp)) continue;
      assignment.set(mid, t);
      reserved.add(t.team);
      if (backtrack(idx + 1)) return true;
      assignment.delete(mid);
      reserved.delete(t.team);
    }
    return false;
  }

  if (!backtrack(0)) {
    for (const [mid, elig] of needs) {
      const t = sorted.find((c) => !reserved.has(c.team) && elig.has(c.grp));
      const pick = t ?? sorted.find((c) => !reserved.has(c.team));
      if (pick) {
        assignment.set(mid, pick);
        reserved.add(pick.team);
      }
    }
  }
  return assignment;
}

function resolveR32Team(
  spec: SideSpec,
  standings: Record<string, Standing[]>,
  thirdAssign: Map<number, Standing>,
  matchId: number
): [string, number] {
  const [kind, letter] = spec;
  if (kind === "winner") {
    const st = standings[letter as string][0];
    return [st.team, st.elo];
  }
  if (kind === "runner") {
    const st = standings[letter as string][1];
    return [st.team, st.elo];
  }
  const t = thirdAssign.get(matchId)!;
  return [t.team, t.elo];
}

export function buildR32Bracket(
  standings: Record<string, Standing[]>
): [number, [string, number], [string, number]][] {
  const allThirds = Object.keys(standings)
    .map((g) => standings[g][2])
    .filter(Boolean);
  allThirds.sort(compareStandings);
  const thirdsAdv = allThirds.slice(0, 8);

  const needs: [number, Set<string>][] = [];
  for (const [mid, a, b] of R32_FIXTURES) {
    if (a[0] === "third") needs.push([mid, parseThirdLetters(a[1] as string)]);
    else if (b[0] === "third") needs.push([mid, parseThirdLetters(b[1] as string)]);
  }
  const thirdAssign = assignAllThirds(needs, thirdsAdv);

  return R32_FIXTURES.map(([mid, sa, sb]) => {
    const ta = resolveR32Team(sa, standings, thirdAssign, mid);
    const tb = resolveR32Team(sb, standings, thirdAssign, mid);
    return [mid, ta, tb] as [number, [string, number], [string, number]];
  });
}

export function lookupProbs(
  matrix: MatrixEntry[],
  home: string,
  away: string
): { p_home: number; p_draw: number; p_away: number } {
  const hit = matrix.find((m) => m.home === home && m.away === away);
  if (hit) return { p_home: hit.p_home, p_draw: hit.p_draw, p_away: hit.p_away };
  return { p_home: 0.36, p_draw: 0.28, p_away: 0.36 };
}

export function knockoutWinProb(p: { p_home: number; p_away: number }): {
  pA: number;
  pB: number;
} {
  let pa = p.p_away;
  let ph = p.p_home;
  const s = pa + ph;
  if (s <= 0) return { pA: 0.5, pB: 0.5 };
  return { pA: pa / s, pB: ph / s };
}

export interface KnockoutMatch {
  id: number;
  team_a: string;
  team_b: string;
  winner: string;
  p_win_a: number;
  p_win_b: number;
}

export function runFullKnockout(
  standings: Record<string, Standing[]>,
  matrix: MatrixEntry[],
  chalk: boolean,
  rng: () => number = Math.random
): { rounds: { round: string; matches: KnockoutMatch[] }[]; champion: string } {
  const r32 = buildR32Bracket(standings);
  const matchesOut: KnockoutMatch[] = [];
  const winners = new Map<number, [string, number]>();

  function pickWinner(
    mid: number,
    ta: [string, number],
    tb: [string, number]
  ): [string, number] {
    const p = lookupProbs(matrix, ta[0], tb[0]);
    const { pA, pB } = knockoutWinProb({ p_home: p.p_home, p_away: p.p_away });
    const winA = chalk ? pB >= pA : rng() < pB;
    const w = winA ? ta[0] : tb[0];
    const elo = winA ? ta[1] : tb[1];
    matchesOut.push({
      id: mid,
      team_a: ta[0],
      team_b: tb[0],
      winner: w,
      p_win_a: Math.round(pB * 1000) / 1000,
      p_win_b: Math.round(pA * 1000) / 1000,
    });
    winners.set(mid, [w, elo]);
    return [w, elo];
  }

  for (const [mid, ta, tb] of r32) {
    pickWinner(mid, ta, tb);
  }

  const play = (ida: number, idb: number, mid: number) => {
    const a = winners.get(ida)!;
    const b = winners.get(idb)!;
    pickWinner(mid, a, b);
  };

  play(73, 75, 90);
  play(74, 77, 89);
  play(76, 78, 91);
  play(79, 80, 92);
  play(83, 84, 93);
  play(81, 82, 94);
  play(86, 88, 95);
  play(85, 87, 96);
  play(89, 90, 97);
  play(93, 94, 98);
  play(91, 92, 99);
  play(95, 96, 100);
  play(97, 98, 101);
  play(99, 100, 102);
  play(101, 102, 103);

  const champion = winners.get(103)![0];
  const roundMap: Record<string, number[]> = {
    R32: Array.from({ length: 16 }, (_, i) => 73 + i),
    R16: Array.from({ length: 8 }, (_, i) => 89 + i),
    QF: [97, 98, 99, 100],
    SF: [101, 102],
    Final: [103],
  };

  const rounds = Object.entries(roundMap).map(([round, ids]) => ({
    round,
    matches: matchesOut.filter((m) => ids.includes(m.id)),
  }));

  return { rounds, champion };
}

export interface SimMatchResult {
  group: string;
  home: string;
  away: string;
  home_goals: number;
  away_goals: number;
  p_home: number;
  p_draw: number;
  p_away: number;
}

export interface GroupTeamRec {
  pts: number;
  gf: number;
  ga: number;
  w: number;
  d: number;
  l: number;
  elo: number;
}

export function simulateGroupStage(
  fixtures: Fixture[],
  matrix: MatrixEntry[],
  rng: () => number = Math.random
): {
  standings: Record<string, Standing[]>;
  groupsRaw: Record<string, Record<string, GroupTeamRec>>;
  matchResults: SimMatchResult[];
} {
  const groups: Record<string, Record<string, GroupTeamRec>> = {};

  const initTeam = (g: string, t: string, elo = 1500) => {
    if (!groups[g][t]) {
      groups[g][t] = { pts: 0, gf: 0, ga: 0, w: 0, d: 0, l: 0, elo };
    }
  };

  const matchResults: SimMatchResult[] = [];

  for (const row of fixtures) {
    const g = row.group;
    const ht = row.home;
    const at = row.away;
    groups[g] ??= {};
    initTeam(g, ht, 1500);
    initTeam(g, at, 1500);

    const p = lookupProbs(matrix, ht, at);
    let probs = [p.p_away, p.p_draw, p.p_home];
    const sum = probs.reduce((a, b) => a + b, 0);
    probs = sum > 0 ? probs.map((x) => x / sum) : [1 / 3, 1 / 3, 1 / 3];
    const r = rng();
    let outcome = 1;
    if (r < probs[0]) outcome = 0;
    else if (r < probs[0] + probs[1]) outcome = 1;
    else outcome = 2;

    let gh: number, ga: number;
    if (outcome === 2) {
      gh = 2;
      ga = 1;
    } else if (outcome === 0) {
      gh = 0;
      ga = 1;
    } else {
      gh = 1;
      ga = 1;
    }

    const pth = gh > ga ? 3 : gh < ga ? 0 : 1;
    const pta = ga > gh ? 3 : ga < gh ? 0 : 1;
    groups[g][ht].pts += pth;
    groups[g][at].pts += pta;
    groups[g][ht].gf += gh;
    groups[g][ht].ga += ga;
    groups[g][at].gf += ga;
    groups[g][at].ga += gh;
    if (pth === 3) {
      groups[g][ht].w++;
      groups[g][at].l++;
    } else if (pta === 3) {
      groups[g][at].w++;
      groups[g][ht].l++;
    } else {
      groups[g][ht].d++;
      groups[g][at].d++;
    }

    matchResults.push({ group: g, home: ht, away: at, home_goals: gh, away_goals: ga, ...p });
  }

  const standings: Record<string, Standing[]> = {};
  for (const g of Object.keys(groups).sort()) {
    const lst: Standing[] = Object.entries(groups[g]).map(([team, rec]) => ({
      team,
      grp: g,
      pts: rec.pts,
      gd: rec.gf - rec.ga,
      gf: rec.gf,
      elo: rec.elo,
    }));
    lst.sort(compareStandings);
    standings[g] = lst;
  }

  return { standings, groupsRaw: groups, matchResults };
}

export function standingsToGroupBlocks(
  standings: Record<string, Standing[]>,
  groupsRaw: Record<string, Record<string, GroupTeamRec>>
) {
  return Object.keys(standings)
    .sort()
    .map((group) => ({
      group,
      standings: standings[group].map((st, i) => {
        const rec = groupsRaw[group][st.team];
        return {
          rank: i + 1,
          team: st.team,
          pts: st.pts,
          gd: st.gd,
          gf: st.gf,
          w: rec.w,
          d: rec.d,
          l: rec.l,
          elo: st.elo,
        };
      }),
    }));
}
