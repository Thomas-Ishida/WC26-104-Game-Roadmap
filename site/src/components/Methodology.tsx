export interface MethodologyData {
  what_this_is: string[];
  limitations: string[];
  design_choices: string[];
}

export function Methodology({ data }: { data: MethodologyData }) {
  return (
    <section id="methodology" className="py-20 page-wrap">
      <h2 className="section-title mb-3">Methodology & limitations</h2>
      <p className="text-slate-400 mb-10 max-w-3xl">
        A strict reviewer should see what is validated, what is exploratory, and what is
        scenario simulation — not overstated prediction claims.
      </p>
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="font-display text-lg font-semibold text-white mb-4">What this is</h3>
          <ul className="space-y-2 text-sm text-slate-400">
            {data.what_this_is.map((t) => (
              <li key={t} className="flex gap-2">
                <span className="text-emerald-500 shrink-0">·</span>
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card border-amber-900/40">
          <h3 className="font-display text-lg font-semibold text-amber-200 mb-4">Limitations</h3>
          <ul className="space-y-2 text-sm text-slate-400">
            {data.limitations.map((t) => (
              <li key={t} className="flex gap-2">
                <span className="text-amber-500 shrink-0">·</span>
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3 className="font-display text-lg font-semibold text-white mb-4">Design choices</h3>
          <ul className="space-y-2 text-sm text-slate-400">
            {data.design_choices.map((t) => (
              <li key={t} className="flex gap-2">
                <span className="text-blue-400 shrink-0">·</span>
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
