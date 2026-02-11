# Does Money Buy Points in the Premier League?

Four seasons of English Premier League match data cleaned, enriched with player prices and expected goals, and visualized as an interactive dashboard to answer a simple question: does spending predict success?

[Live Demo](https://parashdev.github.io/epl-analysis) | [Data Sources](https://www.football-data.co.uk/)

## The Question

Every summer, Premier League clubs pour hundreds of millions into squad building. The conventional wisdom says the biggest spenders win titles. I wanted to test that. Using FPL player prices as a proxy for squad market value, I ran a linear regression against league points for the 2025-26 season. The answer: spending explains just 5.5% of the variance (R-squared = 0.055). Arsenal are 21 points above what their budget predicts. Wolverhampton are 26 points below.

Along the way, I built a full ETL pipeline that handles 4 seasons of match data, player statistics, and expected goals -- robust enough to run against a live, in-progress season without breaking.

## Project Structure

```
EPL-Analysis/
  index.html                          # Single-file dashboard (Chart.js + Tailwind)
  data/
    raw/                              # Downloaded CSVs (auto-fetched by 01_clean.py)
    cleaned/                          # Script outputs
      matches_clean.csv               #   1,390 rows, 29 columns (4 seasons)
      players.csv                     #   817 FPL player records
      fixtures_detailed.csv           #   254 fixtures with scores (live season)
      xg_matches.csv                  #   254 matches with xG
      xg_teams.csv                    #   20 teams with season xG totals
      xg_players.csv                  #   511 players with xG/xA
    dashboard_data.json               # Aggregated JSON consumed by index.html
  scripts/
    config.py                         # Season config, team maps, URLs (build first)
    01_clean.py                       # Clean raw match data from football-data.co.uk
    02_transform.py                   # Merge all sources, aggregate into JSON
    03_fetch_fpl.py                   # FPL player stats and prices (live API)
    04_fetch_xg.py                    # Understat xG data
  docs/
    cleaning-log.md                   # Decision journal (12 entries)
    pipeline.md                       # Architecture, "why not X", rerun instructions
  .github/workflows/update.yml       # Weekly cron automation
  requirements.txt
  .gitignore
```

## How to Run

Prerequisites: Python 3.11+, pip

```bash
git clone https://github.com/ParashDev/epl-analysis.git
cd epl-analysis
pip install -r requirements.txt

# Full pipeline (order matters: 01 first, then 03/04 in any order, then 02 last)
python scripts/01_clean.py
python scripts/03_fetch_fpl.py
python scripts/04_fetch_xg.py
python scripts/02_transform.py

# Preview
python -m http.server 8000
# Open http://localhost:8000
```

The dashboard works with only match data. If FPL or xG scripts fail (network issues, API changes), skip them -- the base dashboard still renders 7 charts with fallback messages for enrichment sections.

## Deploy to GitHub Pages

1. Push to GitHub
2. Settings > Pages > Source: main branch, / (root)
3. Site is live at `https://parashdev.github.io/epl-analysis`

## What This Demonstrates

| Skill | How |
|---|---|
| Data Cleansing | Stripped BOM encoding, dropped 96+ betting columns from 133, standardized dates across 4 formats, unified team names across 3 sources with different abbreviation conventions |
| ETL Pipeline | 4-script pipeline with config-driven seasons, graceful degradation when enrichment sources fail, NaN sanitization for JSON serialization, live season support |
| Statistical Analysis | Linear regression of squad value vs league points, R-squared calculation, over/underperformance residuals, per-90-minute rate statistics |
| API Integration | FPL live API for player stats and prices, Understat via package + scraping fallback, rate limiting, 24-hour cache |
| Data Visualization | 14+ interactive charts and tables (league standings, points race, xG scatter, money scatter, player leaderboards, scoreline heatmap), responsive dark theme, conditional rendering |
| Documentation | Cleaning decision log with WHY not WHAT, ASCII architecture diagrams, "Why Not Tool X" justifications |

## Dashboard Sections

1. **The Brief** -- Money thesis narrative with key findings
2. **The Raw Data** -- Data source cards, the name problem, before/after cleaning, quality issues found
3. **The Pipeline** -- 5-step pipeline visualization with code preview
4. **The Dashboard** -- League table, KPI cards, cumulative points race, monthly goals, home/away splits, referee cards, common scorelines, season comparison
5. **Money vs Points** -- Squad value scatter plot with regression line, over/underperformance bar chart, R-squared KPI
6. **xG Analysis** -- Expected vs actual goals, top scorers vs xG, shot quality by team
7. **Player Leaderboards** -- Top scorers, assist leaders, best value (G+A per million), most booked, iron men (most minutes per team), goals by position breakdown
8. **The Takeaway** -- Summary, "What I Would Do Differently", tools used

## Data Sources

| Source | URL | Format | What It Provides |
|---|---|---|---|
| football-data.co.uk | https://www.football-data.co.uk/englandm.php | CSV | Match results, shots, fouls, cards, corners, referees (4 seasons) |
| Fantasy Premier League | https://fantasy.premierleague.com/api/ | JSON API | Player stats, prices, positions, minutes, goals, assists (817 players) |
| Understat | https://understat.com/league/EPL | JSON (embedded) | Expected goals (xG), expected assists (xA), shot quality, PPDA (511 players) |

## License

Data provided by football-data.co.uk, the Premier League, and Understat. Analysis and code are MIT.
