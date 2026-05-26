const links = [
  { href: "#pipeline", label: "Pipeline" },
  { href: "#findings", label: "Findings" },
  { href: "#methodology", label: "Methodology" },
  { href: "#matchups", label: "Matchups" },
  { href: "#brackets", label: "Brackets" },
  { href: "#lab", label: "Lab" },
];

export function Nav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="page-wrap h-14 flex items-center justify-between">
        <a href="#" className="font-display font-semibold text-white text-sm">
          WC 2026 ML
        </a>
        <div className="hidden md:flex gap-6 text-sm text-slate-400">
          {links.map((l) => (
            <a key={l.href} href={l.href} className="hover:text-emerald-400 transition-colors">
              {l.label}
            </a>
          ))}
        </div>
      </div>
    </nav>
  );
}
