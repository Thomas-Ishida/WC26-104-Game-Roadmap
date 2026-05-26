import { motion } from "framer-motion";

export function Hero() {
  return (
    <section className="relative min-h-[88vh] flex items-center overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/40" />
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 50%, #16a34a 0%, transparent 40%), radial-gradient(circle at 80% 20%, #3b82f6 0%, transparent 35%)",
        }}
      />
      <div className="relative z-10 page-wrap py-24 text-center">
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-emerald-400 text-sm font-medium tracking-widest uppercase mb-4"
        >
          Thomas Ishida
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="font-display text-4xl md:text-6xl font-bold text-white leading-tight mb-6"
        >
          The 104-Game Roadmap
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto mb-10"
        >
          Machine learning for international soccer — temporal validation, squad-aware
          matchups, and bracket simulations for World Cup 2026 (scenario analysis, not betting tips).
        </motion.p>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.35 }}
          className="flex flex-wrap gap-4 justify-center"
        >
          <a
            href="#lab"
            className="px-6 py-3 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors"
          >
            Try the bracket lab
          </a>
          <a
            href="#findings"
            className="px-6 py-3 rounded-full border border-slate-600 hover:border-slate-400 text-slate-200 font-medium transition-colors"
          >
            View findings
          </a>
        </motion.div>
      </div>
    </section>
  );
}
