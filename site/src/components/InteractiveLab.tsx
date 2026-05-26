import { useCallback, useState } from "react";
import type { Fixture, GroupBlock, MatrixEntry } from "../types";
import {
  groupStandingsFromRows,
  sortStandings,
  type Standing,
} from "../lib/standings";
import {
  runFullKnockout,
  simulateGroupStage,
  standingsToGroupBlocks,
} from "../lib/bracket";
import { BracketView } from "./BracketView";

interface Props {
  fixtures: Fixture[];
  matrix: MatrixEntry[];
  initialGroups: GroupBlock[];
}

function blocksToStandings(groups: GroupBlock[]): Record<string, Standing[]> {
  return groupStandingsFromRows(
    groups.map((g) => ({
      group: g.group,
      standings: g.standings.map((r) => ({
        team: r.team,
        pts: r.pts,
        gd: r.gd,
        gf: r.gf,
        elo: r.elo,
      })),
    }))
  );
}

export function InteractiveLab({ fixtures, matrix, initialGroups }: Props) {
  const [groups, setGroups] = useState<GroupBlock[]>(initialGroups);
  const [knockout, setKnockout] = useState<ReturnType<typeof runFullKnockout> | null>(null);
  const [mode, setMode] = useState<"chalk" | "simulate">("simulate");
  const [selectedThird, setSelectedThird] = useState<Set<string>>(() => {
    const thirds = initialGroups
      .map((g) => g.standings[2]?.team)
      .filter(Boolean) as string[];
    return new Set(thirds.slice(0, 8));
  });

  const simulateGroups = useCallback(() => {
    const { standings: st, groupsRaw, matchResults: _mr } = simulateGroupStage(
      fixtures,
      matrix,
      Math.random
    );
    const blocks = standingsToGroupBlocks(st, groupsRaw);
    setGroups(blocks);
    const thirds = Object.keys(st)
      .map((g) => st[g][2]?.team)
      .filter(Boolean) as string[];
    thirds.sort((a, b) => {
      const sa = st[Object.keys(st).find((k) => st[k].some((x) => x.team === a))!].find(
        (x) => x.team === a
      )!;
      const sb = st[Object.keys(st).find((k) => st[k].some((x) => x.team === b))!].find(
        (x) => x.team === b
      )!;
      return (
        sb.pts - sa.pts ||
        sb.gd - sa.gd ||
        sb.gf - sa.gf ||
        sb.elo - sa.elo
      );
    });
    setSelectedThird(new Set(thirds.slice(0, 8)));
    setKnockout(null);
  }, [fixtures, matrix]);

  const swapRank = (group: string, team: string) => {
    setGroups((prev) => {
      const g = prev.find((x) => x.group === group);
      if (!g) return prev;
      const idx = g.standings.findIndex((r) => r.team === team);
      if (idx < 0 || idx >= 2) return prev;
      const next = [...g.standings];
      [next[idx], next[idx + 1]] = [next[idx + 1], next[idx]];
      return prev.map((x) =>
        x.group === group
          ? {
              ...x,
              standings: next.map((r, i) => ({ ...r, rank: i + 1 })),
            }
          : x
      );
    });
    setKnockout(null);
  };

  const toggleThird = (team: string) => {
    setSelectedThird((prev) => {
      const n = new Set(prev);
      if (n.has(team)) n.delete(team);
      else if (n.size < 8) n.add(team);
      return n;
    });
    setKnockout(null);
  };

  const runKnockout = () => {
    const st = blocksToStandings(groups);
    for (const g of Object.keys(st)) {
      const third = st[g][2];
      if (third && !selectedThird.has(third.team)) {
        const promoted = [...st[g]]
          .filter((s) => selectedThird.has(s.team) && s.team !== st[g][0].team && s.team !== st[g][1].team)
          .sort((a, b) => b.pts - a.pts || b.gd - a.gd)[0];
        if (promoted) {
          const reordered = [st[g][0], st[g][1], promoted, ...st[g].slice(3).filter((x) => x.team !== promoted.team)];
          st[g] = sortStandings(reordered);
        }
      }
    }
    const result = runFullKnockout(st, matrix, mode === "chalk", Math.random);
    setKnockout(result);
  };

  const allThirds = groups
    .map((g) => g.standings[2])
    .filter(Boolean) as GroupBlock["standings"];

  return (
    <section id="lab" className="py-20 page-wrap">
      <h2 className="section-title mb-3">Interactive bracket lab</h2>
      <p className="text-slate-400 mb-8 max-w-2xl">
        Step 1: simulate the group stage from model probabilities. Step 2: click teams
        to swap 1st/2nd or pick which third-place teams advance. Step 3: run the FIFA
        knockout bracket.
      </p>

      <div className="flex flex-wrap gap-3 mb-8">
        <button
          type="button"
          onClick={simulateGroups}
          className="px-5 py-2.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm"
        >
          Simulate group stage
        </button>
        <button
          type="button"
          onClick={runKnockout}
          className="px-5 py-2.5 rounded-full bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm"
        >
          Run knockout
        </button>
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          <div className="flex rounded-full border border-slate-700 overflow-hidden text-sm shrink-0">
            <button
              type="button"
              onClick={() => setMode("simulate")}
              className={`px-4 py-2 ${mode === "simulate" ? "bg-slate-700 text-white" : "text-slate-500"}`}
              title="Random knockout winners weighted by model win probability"
            >
              Simulate upsets
            </button>
            <button
              type="button"
              onClick={() => setMode("chalk")}
              className={`px-4 py-2 ${mode === "chalk" ? "bg-slate-700 text-white" : "text-slate-500"}`}
              title="Always advance the team with higher win probability"
            >
              Chalk path
            </button>
          </div>
          <p className="text-slate-500 text-xs sm:max-w-xl">
            {mode === "chalk"
              ? "Chalk: no randomness in knockouts — the favorite always wins each tie."
              : "Simulate: weighted coin flips — upsets happen when the underdog’s win % beats the draw."}
          </p>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-10">
        {groups.map((g) => (
          <div key={g.group} className="card p-4">
            <h4 className="font-display font-semibold text-emerald-400 mb-3">
              Group {g.group}
            </h4>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-slate-500 text-left">
                  <th className="pb-1">#</th>
                  <th>Team</th>
                  <th>Pts</th>
                  <th>GD</th>
                </tr>
              </thead>
              <tbody>
                {g.standings.map((r, i) => (
                  <tr key={r.team} className="border-t border-slate-800/80">
                    <td className="py-1.5 text-slate-500">{i + 1}</td>
                    <td className="py-1.5">
                      <button
                        type="button"
                        onClick={() => i < 2 && swapRank(g.group, r.team)}
                        className={`text-left hover:text-emerald-400 transition-colors ${
                          i < 2 ? "cursor-pointer" : ""
                        } ${i === 2 && selectedThird.has(r.team) ? "text-amber-400" : "text-slate-200"}`}
                        title={i < 2 ? "Click to swap with team below" : "Third place — toggle qualifier"}
                        onDoubleClick={() => i === 2 && toggleThird(r.team)}
                      >
                        {r.team}
                      </button>
                    </td>
                    <td>{r.pts}</td>
                    <td>{r.gd > 0 ? `+${r.gd}` : r.gd}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      <div className="card mb-10">
        <h4 className="font-display font-semibold text-white mb-3">
          Third-place qualifiers ({selectedThird.size}/8)
        </h4>
        <p className="text-slate-500 text-xs mb-4">
          Click a 3rd-place team in the tables above to toggle. Top 8 by default after simulation.
        </p>
        <div className="flex flex-wrap gap-2">
          {allThirds.map((r) => (
            <button
              key={r.team}
              type="button"
              onClick={() => toggleThird(r.team)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                selectedThird.has(r.team)
                  ? "border-amber-500 text-amber-300 bg-amber-500/10"
                  : "border-slate-700 text-slate-500"
              }`}
            >
              {r.team} ({groups.find((g) => g.standings.some((s) => s.team === r.team))?.group})
            </button>
          ))}
        </div>
      </div>

      {knockout && (
        <div className="card">
          <BracketView rounds={knockout.rounds} champion={knockout.champion} />
        </div>
      )}
    </section>
  );
}
