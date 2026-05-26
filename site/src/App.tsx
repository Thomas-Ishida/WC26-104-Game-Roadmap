import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { Pipeline } from "./components/Pipeline";
import { Findings } from "./components/Findings";
import { MatchupExplorer } from "./components/MatchupExplorer";
import { ReferenceBrackets } from "./components/ReferenceBrackets";
import { InteractiveLab } from "./components/InteractiveLab";
import { Footer } from "./components/Footer";
import { Methodology } from "./components/Methodology";
import { useSiteData } from "./hooks/useSiteData";

export default function App() {
  const { data, error, asset } = useSiteData();

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center text-red-400">
        Failed to load site data: {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-400">
        Loading tournament data…
      </div>
    );
  }

  return (
    <>
      <Nav />
      <main className="pt-14">
        <Hero />
        <Pipeline />
        <Findings
          findings={data.findings}
          championOdds={data.championOdds}
          modelMetrics={data.modelMetrics}
          asset={asset}
        />
        <MatchupExplorer
          teams={data.teams}
          presets={data.matchups}
          matrix={data.matchupMatrix}
        />
        <Methodology data={data.methodology} />
        <ReferenceBrackets chalk={data.chalkBracket} />
        <InteractiveLab
          fixtures={data.fixtures}
          matrix={data.matchupMatrix}
          initialGroups={data.defaultGroups}
        />
        <Footer />
      </main>
    </>
  );
}
