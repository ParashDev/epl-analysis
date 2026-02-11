# PRD-MAIN: EPL Season Data Analysis Platform

## Document Control

| Field | Value |
|---|---|
| Version | 1.0 |
| Status | Ready for Development |
| Last Updated | 2026-02-10 |

---

## 1. Product Vision

A portfolio-grade data analysis project that takes raw English Premier League match data, enriches it with player stats and expected goals (xG) metrics from multiple sources, runs it through a documented ETL pipeline, and presents interactive visualizations in a single-page dashboard.

This is not a generic tutorial project. It is a case study designed to demonstrate real-world data engineering and analysis skills to hiring managers. Every file, comment, and design decision exists to prove competence in data cleansing, ETL processing, multi-source integration, and visualization.

---

## 2. Target Audience

Primary: Technical hiring managers and recruiters evaluating data analyst / product analyst / BI developer candidates.

Secondary: Anyone interested in EPL analytics.

What they are looking for when they land on this project:
- Can this person handle messy, real-world data?
- Do they have a repeatable process or did they just follow a tutorial?
- Can they explain their decisions, not just their code?
- Do they understand the full pipeline from source to visualization?

---

## 3. Architecture Overview

```
DATA SOURCES                    ETL PIPELINE                    OUTPUT
-----------                    ------------                    ------

football-data.co.uk -----> 01_clean.py --------\
(match CSVs, 120 cols)     (clean, standardize)  \
                                                   \
FPL API / GitHub repo ---> 03_fetch_fpl.py -------> 02_transform.py --> dashboard_data.json --> index.html
(player stats, prices)     (extract, normalize)   /                                             (Chart.js)
                                                 /
Understat.com -----------> 04_fetch_xg.py ------/
(xG match + player data)   (extract, normalize)

                                                    .github/workflows/update.yml
                                                    (weekly cron, auto-commit)
```

---

## 4. Feature Breakdown

Each feature has its own detailed PRD document:

| ID | Feature | PRD Document | Priority |
|---|---|---|---|
| F-001 | Raw Data Extraction & Cleansing | [PRD-001-DATA-ETL.md](./PRD-001-DATA-ETL.md) | P0 (Must Have) |
| F-002 | FPL API Player Data Integration | [PRD-002-FPL-API.md](./PRD-002-FPL-API.md) | P1 (Should Have) |
| F-003 | Understat xG Data Integration | [PRD-003-XG-DATA.md](./PRD-003-XG-DATA.md) | P1 (Should Have) |
| F-004 | Interactive Dashboard | [PRD-004-DASHBOARD.md](./PRD-004-DASHBOARD.md) | P0 (Must Have) |
| F-005 | GitHub Actions Automation | [PRD-005-AUTOMATION.md](./PRD-005-AUTOMATION.md) | P2 (Nice to Have) |
| F-006 | Documentation & Reproducibility | [PRD-006-DOCS.md](./PRD-006-DOCS.md) | P0 (Must Have) |

---

## 5. Project Structure (Target State)

```
epl-analysis/
  index.html                          # Single-file dashboard (HTML + CSS + JS)
  data/
    raw/
      matches_2425.csv                # Raw football-data.co.uk (2024-25)
      matches_2324.csv                # Raw football-data.co.uk (2023-24)
      matches_2223.csv                # Raw football-data.co.uk (2022-23)
    cleaned/
      matches_clean.csv               # Output of 01_clean.py
      players.csv                     # Output of 03_fetch_fpl.py
      fixtures_detailed.csv           # Output of 03_fetch_fpl.py
      xg_matches.csv                  # Output of 04_fetch_xg.py
      xg_players.csv                  # Output of 04_fetch_xg.py
      xg_teams.csv                    # Output of 04_fetch_xg.py
    dashboard_data.json               # Output of 02_transform.py (consumed by frontend)
  scripts/
    config.py                       # Season config, team maps, source URLs
    01_clean.py                       # Extract + Clean match data
    02_transform.py                   # Transform + Merge all sources into JSON
    03_fetch_fpl.py                   # Fetch FPL player data
    04_fetch_xg.py                    # Fetch Understat xG data
  docs/
    cleaning-log.md                   # Decision journal for every cleaning step
    pipeline.md                       # Pipeline architecture documentation
  .github/
    workflows/
      update.yml                      # Weekly auto-update cron
  requirements.txt
  .gitignore
  README.md
```

---

## 6. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| ETL | Python 3.11+, Pandas | Industry standard for data work. Pandas handles CSV/JSON natively. |
| APIs | requests, understatapi | requests for FPL API. understatapi wraps Understat scraping. |
| Frontend | HTML, Tailwind CDN, Chart.js | Single file, zero build step, deploys to GitHub Pages instantly. |
| Automation | GitHub Actions | Free for public repos. No server to maintain. |
| Hosting | GitHub Pages | Free, automatic, tied to the repo. |

---

## 7. Non-Negotiable Constraints

1. **No build step.** The dashboard is a single HTML file. No React, no Webpack, no npm install.
2. **Graceful degradation.** Dashboard must work with ONLY match data. FPL and xG are additive. If those scripts fail or haven't run, the dashboard still renders the base charts.
3. **Team name consistency.** All scripts must produce identical team names. The canonical form is full proper names: "Manchester United", "Nottingham Forest", "Tottenham Hotspur", etc.
4. **Comments explain WHY, not WHAT.** Every Python script must have inline comments explaining the reasoning behind decisions, not just describing what the code does.
5. **No emojis.** Anywhere. Code, comments, HTML, docs. This is a professional portfolio piece.
6. **Dark theme.** The dashboard uses a dark editorial aesthetic. No light mode needed.
7. **Reproducible.** Anyone should be able to clone the repo, run 4 Python scripts, start a local server, and see the full dashboard.
8. **Config-driven seasons.** No script contains hardcoded season years, source URLs, or team name maps. All of these live in `scripts/config.py`. Adding a new season or switching from historical to live mode requires changing only config.py.
9. **Partial season safe.** The dashboard must render correctly whether the current season has 100 matches or 380. Charts must not assume 38 matchdays. The league table must handle teams with different games played.

---

## 8. Data Sources

| Source | URL | Format | Auth | Update Frequency |
|---|---|---|---|---|
| football-data.co.uk | https://www.football-data.co.uk/englandm.php | CSV | None | Twice weekly during season |
| FPL API (live season) | https://fantasy.premierleague.com/api/ | JSON | None | After each gameweek |
| FPL GitHub (historical) | https://github.com/vaastav/Fantasy-Premier-League | CSV | None | End of season archive |
| Understat | https://understat.com/ | Scraped JSON | None | After each match |

Note: The FPL live API reflects the CURRENT season (2025-26 as of Feb 2026). For 2024-25 historical data, use the vaastav/Fantasy-Premier-League GitHub repo. The 03_fetch_fpl.py script supports both modes, controlled by `fpl_mode` in config.py.

### Live Season vs Historical Mode

All data source behavior is controlled by `scripts/config.py`. See the SKILL reference `references/live-season.md` for the full config pattern.

- **Historical mode** (default for completed seasons): Scripts download archived CSVs and fetch from GitHub repos. Data does not change between runs.
- **Live mode** (for in-progress season): Scripts download updating CSVs from football-data.co.uk, fetch from the live FPL API, and scrape current Understat data. Data changes weekly. GitHub Actions cron keeps the dashboard current.

Switching modes = changing `CURRENT_SEASON` and `fpl_mode` in config.py. No script changes needed.

---

## 9. Success Criteria

A hiring manager lands on the GitHub Pages site. Within 60 seconds they can:
- See the project is about real EPL data, not a toy dataset
- Click through a clear narrative: raw data, cleaning process, pipeline, dashboard, takeaway
- Interact with at least 7 different chart types
- Read the code and understand the author's decision-making
- Reproduce the entire project locally in under 5 minutes

---

## 10. Development Order

Build in this exact sequence. Each phase must work independently before moving to the next.

**Phase 1 (Core):** F-001 + F-004 + F-006 -- Raw data pipeline + base dashboard + docs
**Phase 2 (Enrichment):** F-002 + F-003 -- FPL and xG integrations + dashboard updates
**Phase 3 (Polish):** F-005 -- GitHub Actions automation + final README updates
