import { useMemo, useState, type ReactNode } from "react";
import type { MatrixEntry, MatchupProb, Team } from "../types";
import { lookupProbs } from "../lib/bracket";
import { formatTeam } from "../lib/flags";
import { TeamName } from "./TeamName";

interface Props {
  teams: Team[];
  presets: MatchupProb[];
  matrix: MatrixEntry[];
}

export function MatchupExplorer({ teams, presets, matrix }: Props) {
  const names = useMemo(
    () => teams.map((t) => t.team).sort(),
    [teams]
  );
  const [home, setHome] = useState(presets[0]?.home ?? names[0] ?? "");
  const [away, setAway] = useState(presets[0]?.away ?? names[1] ?? "");

  const p = lookupProbs(matrix, home, away);
  const pct = {
    home: (p.p_home * 100).toFixed(1),
    draw: (p.p_draw * 100).toFixed(1),
    away: (p.p_away * 100).toFixed(1),
  };

  const hTeam = teams.find((t) => t.team === home);
  const aTeam = teams.find((t) => t.team === away);

  return (
    <section id="matchups" className="py-20 page-wrap">
      <h2 className="section-title mb-3">Matchup explorer</h2>
      <p className="text-slate-400 mb-8">
        XGBoost + squad quality model — home / draw / away probabilities for any pair.
      </p>

      <div className="card">
        <div className="flex flex-wrap gap-4 mb-6">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Home</span>
            <select
              value={home}
              onChange={(e) => setHome(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 min-w-[180px]"
            >
              {names.map((n) => (
                <option key={n} value={n}>
                  {formatTeam(n)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-slate-500">Away</span>
            <select
              value={away}
              onChange={(e) => setAway(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 min-w-[180px]"
            >
              {names.map((n) => (
                <option key={n} value={n}>
                  {formatTeam(n)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8 text-center">
          <ProbCard label={<TeamName name={home} />} pct={pct.home} />
          <ProbCard label="Draw" pct={pct.draw} />
          <ProbCard label={<TeamName name={away} />} pct={pct.away} />
        </div>

        {hTeam && aTeam && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <StatCompare label="Elo" a={hTeam.elo} b={aTeam.elo} />
            <StatCompare label="Squad" a={hTeam.squad} b={aTeam.squad} />
            <StatCompare label="Form" a={hTeam.form} b={aTeam.form} />
          </div>
        )}

        <div className="mt-8 flex flex-wrap gap-2">
          {presets.map((m) => (
            <button
              key={`${m.home}-${m.away}`}
              type="button"
              onClick={() => {
                setHome(m.home);
                setAway(m.away);
              }}
              className="text-xs px-3 py-1.5 rounded-full border border-slate-700 hover:border-emerald-600 text-slate-400 hover:text-white transition-colors"
            >
              <TeamName name={m.home} /> vs <TeamName name={m.away} />
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function ProbCard({
  label,
  pct,
}: {
  label: ReactNode;
  pct: string;
}) {
  return (
    <div className="rounded-xl bg-slate-800/80 py-4 px-2">
      <div className="text-2xl font-bold text-white">{pct}%</div>
      <div className="text-xs text-slate-400 mt-1 leading-snug">{label}</div>
    </div>
  );
}

function StatCompare({
  label,
  a,
  b,
}: {
  label: string;
  a: number;
  b: number;
}) {
  const max = Math.max(a, b, 1);
  return (
    <div>
      <div className="text-slate-500 mb-2 text-center">{label}</div>
      <div className="space-y-1">
        <div className="h-2 bg-slate-800 rounded overflow-hidden">
          <div className="h-full bg-blue-500" style={{ width: `${(a / max) * 100}%` }} />
        </div>
        <div className="h-2 bg-slate-800 rounded overflow-hidden">
          <div className="h-full bg-orange-500" style={{ width: `${(b / max) * 100}%` }} />
        </div>
      </div>
    </div>
  );
}
