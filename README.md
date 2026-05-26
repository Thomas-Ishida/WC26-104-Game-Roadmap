# WC26: The 104-Game Roadmap

Machine-learning project for the **2026 FIFA World Cup** (48 teams, 104 matches). Trains match-outcome and goal models on international results, runs Monte Carlo tournament simulations, and ships an interactive **React** portfolio on GitHub Pages.

**Live site:** [thomas-ishida.github.io/WC26-104-Game-Roadmap](https://thomas-ishida.github.io/WC26-104-Game-Roadmap/)

## What’s in the repo

| Piece | Description |
|-------|-------------|
| [`wc_prediction.ipynb`](wc_prediction.ipynb) | Capstone story: XGBoost match outcomes, squad quality, curated matchups |
| [`WC2026_simulation.ipynb`](WC2026_simulation.ipynb) | Temporal evaluation, Poisson goals, full-bracket Monte Carlo |
| [`scripts/export_site_data.py`](scripts/export_site_data.py) | Trains models, exports JSON + charts into `site/public/` |
| [`site/`](site/) | Vite + React + Tailwind UI (build output → [`docs/`](docs/)) |

## Quick start (local)

**Node — run the dev site**

```bash
cd site
npm install
npm run dev
```

**Production build** (writes to `docs/` for GitHub Pages):

```bash
cd site
npm run build
```

## Data sources

- International match results (Kaggle)
- Historical Elo ratings
- WC 2026 fixture baseline probabilities (Zahran et al.)
- EA FC 26 ratings (squad quality index)

## Author

**Thomas Ishida** 
