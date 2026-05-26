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

**Highlights:** time-based holdout (train &lt; 2020, test ≥ 2020), 1,000-tournament champion odds with Wilson CIs, interactive group-stage → knockout lab, matchup explorer, methodology & limitations section.

## Quick start (local)

**Python — regenerate site data**

```bash
python3 -m venv wc_env && source wc_env/bin/activate
pip install pandas numpy scikit-learn xgboost matplotlib seaborn joblib
# macOS: brew install libomp   # if XGBoost fails to import

python scripts/export_site_data.py
```

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

## Deploy to GitHub Pages

The site is a static build in the **`docs/`** folder at the repo root. Vite `base` is set to `/WC26-104-Game-Roadmap/` so assets load on a project site.

### One-time setup

1. **Push this repo** to GitHub ([Thomas-Ishida/WC26-104-Game-Roadmap](https://github.com/Thomas-Ishida/WC26-104-Game-Roadmap)).
2. On GitHub: **Settings → Pages**.
3. Under **Build and deployment**:
   - **Source:** Deploy from a branch
   - **Branch:** `main`
   - **Folder:** `/docs`
4. Click **Save**. The first deploy can take 1–3 minutes.
5. Open **https://thomas-ishida.github.io/WC26-104-Game-Roadmap/** (refresh after the Actions/Pages checkmark is green).

### When you change the site

```bash
# edit site/src/ … then:
cd site && npm run build
git add docs/ site/
git commit -m "Update site build"
git push
```

Pages rebuilds automatically on push to `main` when `docs/` changes.

### If assets 404

Confirm `site/vite.config.ts` has:

```ts
const base = "/WC26-104-Game-Roadmap/";
```

Rebuild `docs/` and push again. If you rename the repo, update `base` to match the new repo name.

## Data sources

- International match results (Kaggle)
- Historical Elo ratings
- WC 2026 fixture baseline probabilities (Zahran et al.)
- EA FC 26 ratings (squad quality index)

## Author

**Thomas Ishida** — portfolio / capstone project for LinkedIn and GitHub.
