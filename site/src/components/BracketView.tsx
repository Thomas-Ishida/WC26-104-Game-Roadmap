import { motion } from "framer-motion";
import type { BracketRound } from "../types";
import { TeamName } from "./TeamName";

interface Props {
  rounds: BracketRound[];
  champion: string;
  compact?: boolean;
}

export function BracketView({ rounds, champion, compact }: Props) {
  return (
    <div className={compact ? "space-y-6" : "space-y-10"}>
      <p className="text-center text-lg">
        Champion:{" "}
        <span className="text-amber-400 font-display font-semibold">
          <TeamName name={champion} />
        </span>
      </p>
      <div className="overflow-x-auto pb-4">
        <div className="flex gap-6 min-w-max px-2">
          {rounds.map((round) => (
            <motion.div
              key={round.round}
              initial={{ opacity: 0, x: 12 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="w-56 shrink-0"
            >
              <h4 className="text-xs font-semibold text-emerald-500 uppercase tracking-wider mb-3 text-center">
                {round.round}
              </h4>
              <div className="space-y-3">
                {round.matches.map((m) => (
                  <div
                    key={m.id}
                    className="rounded-lg border border-slate-800 bg-slate-900/80 p-3 text-sm"
                    title={`P(${m.team_a})=${(m.p_win_a * 100).toFixed(0)}%`}
                  >
                    <div
                      className={
                        m.winner === m.team_a
                          ? "text-amber-300 font-medium"
                          : "text-slate-400"
                      }
                    >
                      <TeamName name={m.team_a} />
                      <span className="float-right text-xs text-slate-600">
                        {(m.p_win_a * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div
                      className={
                        m.winner === m.team_b
                          ? "text-amber-300 font-medium mt-1"
                          : "text-slate-400 mt-1"
                      }
                    >
                      <TeamName name={m.team_b} />
                      <span className="float-right text-xs text-slate-600">
                        {(m.p_win_b * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
