# Pipeline Architecture

## Overview

This is a four-script ETL pipeline that processes English Premier League match data from three sources into a single JSON file consumed by a static HTML dashboard. The current dataset is ~1,400 rows across 4 seasons (2022-23 through 2025-26, with 2025-26 as a live in-progress season). Small enough to fit entirely in memory, process in under 10 seconds, and deploy without a database. The tooling reflects this: Python + Pandas for ETL, a flat JSON file as the "database," and a zero-build-step frontend.

## Architecture

```
                           EXTRACT                    TRANSFORM                 LOAD
                    +------------------+        +------------------+     +----------------+
football-data.co.uk | 01_clean.py      |        |                  |     |                |
  CSVs (4 seasons)  | - download raw   |------->|                  |     |                |
                    | - strip BOM      |  csv   |                  |     |                |
                    | - drop betting   |        |                  |     |                |
                    | - standardize    |        |  02_transform.py |     |  index.html    |
                    +------------------+        |  - load required |---->|  - fetch JSON  |
                                                |  - load optional |json |  - render      |
FPL API (live)      +------------------+        |  - aggregate     |     |    Chart.js    |
                    | 03_fetch_fpl.py  |------->|  - merge         |     |  - Tailwind    |
                    | - player stats   |  csv   |  - regression    |     |  - conditional |
                    | - prices         |        |  - leaderboards  |     |    sections    |
                    | - fixtures       |        |  - export JSON   |     |                |
                    +------------------+        |                  |     |                |
                                                |                  |     |                |
Understat.com       +------------------+        |                  |     |                |
                    | 04_fetch_xg.py   |------->|                  |     |                |
                    | - match xG       |  csv   |                  |     |                |
                    | - team xG        |        +------------------+     +----------------+
                    | - player xG      |
                    +------------------+

                    [config.py] -- imported by all scripts
                                   seasons, team maps, URLs

                    [GitHub Actions] -- weekly cron runs full pipeline
```

## Scripts

### config.py
- **Reads:** Nothing (configuration only)
- **Produces:** Exports used by all scripts
- **Key decisions:** Single source of truth for season definitions, canonical team names, and all name maps. Adding a new season is 2 lines here, zero changes elsewhere. Controls live vs historical mode per season.

### 01_clean.py
- **Reads:** football-data.co.uk CSVs (downloaded on first run, cached locally in `data/raw/`)
- **Produces:** `data/cleaned/matches_clean.csv` (1,390 rows, 29 columns)
- **Runtime:** ~3 seconds (including download)
- **Key decisions:** Drops 96+ betting columns, standardizes dates to ISO 8601, maps team names to canonical form, adds 5 derived columns. Handles column count variation across seasons (107 to 133).

### 03_fetch_fpl.py
- **Reads:** FPL live API (`bootstrap-static` and `fixtures` endpoints)
- **Produces:** `data/cleaned/players.csv` (817 rows), `data/cleaned/fixtures_detailed.csv` (254 rows)
- **Runtime:** ~5 seconds (network-bound)
- **Key decisions:** Maps FPL team names to canonical form. Extracts player prices (used for money-vs-points regression). Supports both historical (GitHub CSV archive) and live (API JSON) modes, controlled by `fpl_mode` in config.py.

### 04_fetch_xg.py
- **Reads:** Understat.com via `understatapi` package (primary) or direct scraping (fallback)
- **Produces:** `data/cleaned/xg_matches.csv` (254 rows), `data/cleaned/xg_teams.csv` (20 rows), `data/cleaned/xg_players.csv` (511 rows)
- **Runtime:** ~5 seconds (network-bound)
- **Key decisions:** 24-hour cache to avoid unnecessary API calls. Dual fetch strategy: tries the understatapi package first, falls back to HTML scraping if unavailable.

### 02_transform.py
- **Reads:** `matches_clean.csv` (required), `players.csv`, `fixtures_detailed.csv`, `xg_teams.csv`, `xg_players.csv` (all optional)
- **Produces:** `data/dashboard_data.json` (14 data sections + 7 metadata fields)
- **Runtime:** ~1 second
- **Key decisions:** Loads enrichment CSVs with try/except. Builds 7 base sections unconditionally, then conditionally builds: xG analysis (4 sections), money-vs-points regression (1 section), player value chart (1 section), and player leaderboards with 6 sub-sections (1 section). Sanitizes all NaN/Infinity values before JSON serialization.

## JSON Output Sections

| Section | Source Required | Description |
|---|---|---|
| league_table | matches | Team standings with W/D/L, GF/GA, shots, clean sheets |
| cumulative_points | matches | Points race by matchday for all 20 teams |
| monthly_trends | matches | Goals per month time series |
| home_away | matches | Home vs away win rates and goal averages |
| referee_stats | matches | Card rates per referee |
| scoreline_frequency | matches | Most common scorelines |
| season_comparison | matches | Multi-season comparison (goals, home win %, cards) |
| xg_table | xG | Team xG for/against with PPDA |
| xg_vs_actual | xG | xG vs actual goals scatter data |
| top_scorers | xG + players | Top scorers with xG overlay |
| shot_quality | xG | xG per shot by team |
| player_value | FPL | Points vs price scatter |
| money_vs_points | FPL | Squad value regression, R-squared, residuals |
| player_leaderboards | FPL (+xG) | Goal scorers, assist leaders, iron men, best value, most booked, goals by position |

## Why Not {Tool X}?

| Tool | Why Not |
|---|---|
| Airflow / Prefect | 4 scripts with a linear dependency chain. Orchestration overhead is not justified for a pipeline that runs in 10 seconds. |
| dbt | No database to transform against. Source data is CSV, output is JSON. dbt adds complexity without benefit here. |
| PostgreSQL | Dataset is 1,390 rows. A flat JSON file is the "database" for a static frontend. Adding a database server would complicate deployment for zero analytical gain. |
| React / Next.js | Single page, no routing, no state management needed. A single HTML file with Tailwind CDN and Chart.js CDN deploys instantly to GitHub Pages with zero build step. |
| Jupyter Notebooks | Notebooks are for exploration, not production pipelines. Scripts are version-controllable, cron-schedulable, and produce reproducible output. |
| scikit-learn | The money-vs-points regression is a single-variable OLS. NumPy's polyfit handles it in one line. A full ML library would be overkill. |

This is not about ignorance of these tools. It is about appropriate tool selection for the problem size.

## Rerunning the Pipeline

Delete all generated files and regenerate from scratch:

```bash
# Clean slate
rm -rf data/raw/ data/cleaned/ data/dashboard_data.json

# Full pipeline (order matters: 01 first, then 03/04 in any order, then 02 last)
pip install -r requirements.txt
python scripts/01_clean.py
python scripts/03_fetch_fpl.py
python scripts/04_fetch_xg.py
python scripts/02_transform.py

# Preview
python -m http.server 8000
```

## Extending to a New Season

To add the 2026-27 season:

1. Open `scripts/config.py`
2. Add: `ACTIVE_SEASONS["2026-27"] = {"code": "2627", "understat": "2026", "fpl_mode": "live"}`
3. Update: `CURRENT_SEASON = "2026-27"`
4. Add the 20 teams for 2026-27 to `CANONICAL_TEAMS["2026-27"]` (account for promotion/relegation)
5. Add any new name mappings if source abbreviations differ
6. Rerun the pipeline

No script changes required. The config drives everything.

## Merge Strategy

02_transform.py combines three data sources that use different naming conventions:

- **football-data.co.uk:** `Man United`, `Wolves`, `Tottenham`, `Nott'm Forest`
- **FPL API:** `Spurs`, `Wolves`, `Man Utd`
- **Understat:** `Manchester_United`, `Wolverhampton_Wanderers`

Each fetch script applies its own name map (from config.py) to convert source-specific names to the canonical form used in `matches_clean.csv`. By the time 02_transform.py loads the CSVs, all team names are identical. Joins happen on these canonical names.

## Error Handling

The pipeline uses a "warn and continue" strategy for network-dependent scripts:

- **01_clean.py:** Network errors during CSV download are **hard failures** (no raw data = nothing to analyze).
- **03_fetch_fpl.py:** Network errors print a WARNING and exit cleanly. The pipeline continues without player data.
- **04_fetch_xg.py:** Tries `understatapi` package first. If it fails, tries direct scraping. If both fail, prints a WARNING and exits cleanly.
- **02_transform.py:** Loads optional CSVs with `try/except FileNotFoundError`. Missing enrichment data results in `null` JSON sections, not crashes.
- **index.html:** Checks for null sections before rendering. Missing data shows a "Data not available -- run the enrichment scripts" message instead of broken charts.

This ensures the dashboard always works with whatever data is available.
