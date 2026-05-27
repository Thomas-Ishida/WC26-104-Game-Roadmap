import {
  Bar,
  BarChart,
  Cell,
  ErrorBar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type {
  ChampionOdds,
  Findings as FindingsT,
  ModelMetric,
} from "../types";
import { formatTeam } from "../lib/flags";

interface Props {
  findings: FindingsT;
  championOdds: ChampionOdds[];
  modelMetrics: ModelMetric[];
  asset: (n: string) => string;
}

export function Findings({ findings, championOdds, modelMetrics, asset }: Props) {
  const chartData = championOdds.slice(0, 12).map((c) => ({
    team: c.team,
    teamLabel: formatTeam(c.team),
    pct: Math.round(c.p * 1000) / 10,
    err: c.ci_low != null && c.ci_high != null ? [(c.p - c.ci_low) * 100, (c.ci_high - c.p) * 100] : undefined,
  }));

  const primary = modelMetrics.filter((m) => m.tier === "primary");
  const exploratory = modelMetrics.filter((m) => m.tier === "exploratory");

  const outcomeData = [
    { name: "Home win", value: findings.home_win_pct },
    { name: "Draw", value: findings.draw_pct },
    { name: "Away win", value: findings.away_win_pct },
  ];

  return (
    <section id="findings" className="py-20 page-wrap">
      <h2 className="section-title mb-3">Key findings</h2>
      <p className="text-slate-400 mb-12 max-w-3xl">
        Headline metrics use <strong className="text-slate-200">time-based holdouts</strong> (matches
        from 2020 onward). Random 80/20 splits from the notebook are shown separately as
        exploratory only.
      </p>

      <div className="grid lg:grid-cols-2 gap-8 mb-10">
        <div className="card">
          <h3 className="font-display text-lg font-semibold text-white mb-1">
            Primary evaluation (temporal)
          </h3>
          <p className="text-slate-500 text-xs mb-4">Macro-F1 preferred over accuracy for 3-way soccer outcomes</p>
          <div className="space-y-3">
            {primary.map((m) => (
              <MetricRow key={`${m.notebook}-${m.model}`} m={m} />
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="font-display text-lg font-semibold text-white mb-4">
            Outcome distribution (training set)
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={outcomeData} layout="vertical" margin={{ left: 8 }}>
                <XAxis type="number" domain={[0, 60]} tick={{ fill: "#94a3b8" }} />
                <YAxis type="category" dataKey="name" width={72} tick={{ fill: "#94a3b8" }} />
                <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
                <Bar dataKey="value" fill="#22c55e" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {exploratory.length > 0 && (
            <>
              <h4 className="text-slate-500 text-xs uppercase tracking-wider mt-8 mb-3">
                Exploratory (notebook random split)
              </h4>
              {exploratory.map((m) => (
                <MetricRow key={`${m.notebook}-${m.model}-exp`} m={m} muted />
              ))}
            </>
          )}
        </div>
      </div>

      <div className="card mb-10">
        <h3 className="font-display text-lg font-semibold text-white mb-4">
          Monte Carlo champion odds
        </h3>
        <p className="text-slate-500 text-sm mb-4 max-w-3xl">
          {championOdds[0]?.n_sims ?? "?"} independent tournament simulations ·{" "}
          {championOdds[0]?.source}. Bars show empirical win rate with approximate 95% Wilson
          intervals. These are <em className="text-slate-400">scenario frequencies</em>, not
          market odds.
        </p>
        <div className="h-[440px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ left: 8, right: 24, top: 8, bottom: 8 }}
            >
              <XAxis type="number" tick={{ fill: "#94a3b8" }} unit="%" />
              <YAxis
                type="category"
                dataKey="teamLabel"
                width={220}
                interval={0}
                tick={{ fill: "#e2e8f0", fontSize: 13 }}
              />
              <Tooltip
                formatter={(v) => [`${Number(v)}%`, "Title share"]}
                contentStyle={{ background: "#1e293b", border: "1px solid #334155" }}
              />
              <Bar dataKey="pct" fill="#3b82f6" radius={4}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill="#3b82f6" />
                ))}
                <ErrorBar dataKey="err" direction="x" width={2} stroke="#93c5fd" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="card">
          <h3 className="font-display text-lg font-semibold text-white mb-4">
            Squad Quality Index (top 10)
          </h3>
          <img src={asset("squad_quality_top10.png")} alt="Squad quality top 10" className="rounded-lg w-full" />
        </div>
        <div className="card">
          <h3 className="font-display text-lg font-semibold text-white mb-4">
            Feature importance (XGBoost)
          </h3>
          <img src={asset("feature_importance.png")} alt="Feature importance" className="rounded-lg w-full" />
          <ul className="mt-4 space-y-2 text-sm text-slate-400">
            {findings.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

function MetricRow({ m, muted }: { m: ModelMetric; muted?: boolean }) {
  return (
    <div
      className={`flex justify-between items-start text-sm border-b border-slate-800 pb-2 ${
        muted ? "opacity-70" : ""
      }`}
    >
      <div>
        <span className="text-white font-medium">{m.model}</span>
        {m.role && <span className="block text-slate-500 text-xs mt-0.5">{m.role}</span>}
        <span className="text-slate-500 ml-0 block text-xs">{m.split}</span>
        {m.note && <span className="block text-amber-600/80 text-xs mt-1">{m.note}</span>}
      </div>
      <div className="text-right font-mono text-sm shrink-0 ml-4">
        {m.f1_macro != null && (
          <div className={muted ? "text-slate-400" : "text-emerald-400"}>
            F1 {m.f1_macro.toFixed(3)}
          </div>
        )}
        <div className="text-slate-500">Acc {(m.accuracy * 100).toFixed(1)}%</div>
        {m.f1_draw != null && (
          <div className="text-slate-600 text-xs">Draw F1 {m.f1_draw.toFixed(3)}</div>
        )}
      </div>
    </div>
  );
}
