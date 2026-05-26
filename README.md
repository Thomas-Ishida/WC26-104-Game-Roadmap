# The 104-Game Roadmap — FIFA World Cup 2026 ML Portfolio

Machine learning bracket simulator for the 2026 FIFA World Cup (48-team format). Interactive portfolio site + reproducible notebooks.

## Live site

After enabling GitHub Pages (Settings → Pages → branch `main`, folder `/docs`), the site is at:

`https://<your-username>.github.io/<repo-name>/`

If your repo is not `username.github.io`, set `base` in `site/vite.config.ts` to `/<repo-name>/`.

## Project structure

| Path | Description |
|------|-------------|
| `wc_prediction.ipynb` | Capstone narrative: XGBoost + Squad Quality, matchups, chalk bracket |
| `WC2026_simulation.ipynb` | Leakage-safe splits, Poisson goals, FIFA bracket Monte Carlo |
| `wc2026_simulation_utils.py` | Bracket / group-stage simulation helpers |
| `scripts/export_site_data.py` | Export JSON + charts for the website |
| `site/` | Vite + React portfolio (build output → `docs/`) |

## Reproduce the site data

```bash
source wc_env/bin/activate   # or your Python 3.10+ env
pip install pandas numpy scikit-learn xgboost matplotlib seaborn joblib
# macOS XGBoost: brew install libomp  (if import fails)

python scripts/export_site_data.py
```

## Build & deploy

```bash
cd site
npm install
npm run build    # writes to ../docs/
```

Commit `docs/` and push. Enable GitHub Pages from `/docs` on `main`.

## Data credits

- International match results (Kaggle)
- Elo ratings history
- [Zahran et al.](https://github.com/) WC 2026 baseline fixture probabilities
- EA FC 26 player ratings (squad quality index)

## Resume / LinkedIn framing (honest)

- Built a **3-way match-outcome classifier** (home / draw / away) on 10k+ competitive internationals with **time-based holdout** evaluation (test ≥ 2020).
- Engineered **leakage-aware** features: as-of Elo, rolling form, head-to-head; added **FC26 squad quality** for 2026 inference only.
- Ran **1,000-tournament Monte Carlo** simulations with Poisson goals, FIFA-style knockout wiring, and **Wilson confidence intervals** on title shares.
- Shipped an interactive **React** portfolio (GitHub Pages) with bracket lab, matchup explorer, and documented limitations.

## Author

Thomas Ishida
