export function Footer() {
  return (
    <footer className="border-t border-slate-800 py-12 px-6 text-center text-sm text-slate-500">
      <p className="mb-2">
        Thomas Ishida — World Cup 2026 ML Prediction Project
      </p>
      <p>
        Data: Kaggle results, Elo ratings, Zahran WC2026 fixtures, EA FC 26. Reproduce
        with <code className="text-slate-400">wc_prediction.ipynb</code>,{" "}
        <code className="text-slate-400">WC2026_simulation.ipynb</code>, and{" "}
        <code className="text-slate-400">scripts/export_site_data.py</code>.
      </p>
    </footer>
  );
}
