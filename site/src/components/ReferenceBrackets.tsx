import { useState } from "react";
import type { BracketTree } from "../types";
import { BracketView } from "./BracketView";

interface Props {
  chalk: BracketTree;
}

export function ReferenceBrackets({ chalk }: Props) {
  const [tab, setTab] = useState<"chalk">("chalk");

  return (
    <section id="brackets" className="py-20 page-wrap">
      <h2 className="section-title mb-3">Reference brackets</h2>
      <p className="text-slate-400 mb-8">
        Deterministic chalk path from the capstone notebook — every knockout match goes
        to the higher model win probability.
      </p>

      <div className="flex gap-2 mb-6">
        <button
          type="button"
          onClick={() => setTab("chalk")}
          className={`px-4 py-2 rounded-full text-sm font-medium ${
            tab === "chalk"
              ? "bg-emerald-600 text-white"
              : "bg-slate-800 text-slate-400"
          }`}
        >
          Chalk bracket (exported)
        </button>
      </div>

      <div className="card">
        <BracketView rounds={chalk.rounds} champion={chalk.champion} />
      </div>
    </section>
  );
}
