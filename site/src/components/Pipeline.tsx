const steps = [
  {
    title: "Data",
    items: [
      "Historical international results (Kaggle)",
      "Elo ratings merged as-of match date",
      "2026 group fixtures + baseline probabilities (Zahran et al.)",
      "EA FC 26 player ratings for squad quality",
    ],
  },
  {
    title: "Features",
    items: [
      "Elo difference & host advantage (USA, Mexico, Canada)",
      "5-match rolling form and goal differential",
      "Squad Quality Index — top 23 players per nation",
    ],
  },
  {
    title: "Models",
    items: [
      "Primary metrics: train < 2020, test ≥ 2020 (macro-F1)",
      "Site matchups: XGBoost + squad quality; MC: temporal classifier + Poisson goals",
    ],
  },
  {
    title: "Simulation",
    items: [
      "1,000 Monte Carlo bracket runs (Wilson CIs on title shares)",
      "Interactive groups → overrides → knockout (chalk or upset mode)",
    ],
  },
];

export function Pipeline() {
  return (
    <section id="pipeline" className="py-20 page-wrap">
      <h2 className="section-title mb-3">How it works</h2>
      <p className="text-slate-400 mb-12 max-w-2xl">
        From raw match history to a full tournament bracket in four steps — designed
        for clarity on a portfolio page.
      </p>
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {steps.map((s, i) => (
          <div key={s.title} className="card relative">
            <span className="text-emerald-500/80 text-xs font-bold">0{i + 1}</span>
            <h3 className="font-display text-xl font-semibold text-white mt-2 mb-4">
              {s.title}
            </h3>
            <ul className="space-y-2 text-sm text-slate-400">
              {s.items.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-emerald-600 shrink-0">·</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
