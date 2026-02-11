---
name: data-analysis-portfolio
description: Build portfolio-grade data analysis case study projects from scratch. Use when creating data engineering portfolios, ETL pipeline projects, interactive dashboards, or data cleansing showcases meant to impress hiring managers. Generates complete project structures with Python ETL scripts, single-file HTML dashboards (Chart.js + Tailwind), cleaning decision logs, pipeline documentation, and optional GitHub Actions automation. Supports multi-source data integration with graceful degradation.
---

# Data Analysis Portfolio Case Study Builder

Build complete, portfolio-ready data analysis projects that demonstrate real-world data engineering skills. Each project follows a "Case File" narrative structure: Brief, Raw Data, Pipeline, Dashboard, Takeaway.

## Core Principles

1. **Question-first.** Every project starts with a genuine question, not a dataset.
2. **Show the mess.** Include raw data with real quality issues. Document every cleaning decision with WHY, not just WHAT.
3. **Graceful degradation.** Dashboard works with only the primary data source. Enrichment sources are additive.
4. **No AI smell.** First-person writing, opinions in takeaways, imperfect-but-intentional design. No emojis anywhere.
5. **Single-file frontend.** HTML + CSS (Tailwind CDN) + JS (Chart.js CDN). No build step. Deploys to GitHub Pages.
6. **Config-driven.** One config file controls which seasons/datasets are active. Adding a new season or switching from historical to live mode = changing one file, zero script changes.

## Project Structure

Every case study uses this exact folder layout:

```
{project-name}/
  index.html                    # Single-file dashboard
  data/
    raw/                        # Untouched source files
    cleaned/                    # Output of cleaning scripts
    dashboard_data.json         # Aggregated JSON for frontend
  scripts/
    config.py                   # Season config, team maps, source URLs (imported by all scripts)
    01_clean.py                 # Always first: clean raw data
    02_transform.py             # Always second: aggregate + merge into JSON
    03_fetch_{source_b}.py      # Optional: API source B
    04_fetch_{source_c}.py      # Optional: API source C
  docs/
    cleaning-log.md             # Decision journal
    pipeline.md                 # Architecture docs
  .github/workflows/update.yml  # Optional: cron automation
  requirements.txt
  .gitignore
  README.md
```

Rules:
- Scripts numbered in execution order. 01 and 02 always present.
- All scripts write to `data/cleaned/`. Only 02 writes `dashboard_data.json`.
- `index.html` reads ONLY from `dashboard_data.json`.

## Step-by-Step Build Process

### Phase 1: Foundation

1. Create folder structure.
2. Build `scripts/config.py` -- season definitions, team name maps, source URLs. See `references/live-season.md` for the full config pattern.
3. Build `scripts/01_clean.py` following the pattern in `references/script-patterns.md`.
   - Import seasons and name maps from config.py (no hardcoded seasons in scripts).
   - Download raw data if not present locally.
   - Handle encoding (BOM), drop irrelevant columns, fix dates, standardize names, handle nulls, rename columns, add derived columns.
   - Print a clear log of every action for terminal screenshot value.
4. Run and verify output CSV.

### Phase 2: Base Transform + Dashboard

4. Build `scripts/02_transform.py` -- aggregate cleaned data into JSON sections.
   - Import CURRENT_SEASON from config.py.
   - Load required data. Attempt to load optional enrichment CSVs with `try/except FileNotFoundError`.
   - Set `has_source_b = True/False` flags for conditional aggregations.
   - Detect season completeness (partial vs full) and include `season_status` in JSON output.
   - Output JSON with null for missing optional sections.
5. Build `index.html` following the design system in `references/design-system.md`.
   - 5-section narrative: Brief, Raw Data, Pipeline, Dashboard, Takeaway.
   - Base charts always visible. Enrichment charts conditional with fallback messages.
   - Handle partial season: dynamic axis limits, "LIVE" indicator, matchday counter, "last updated" timestamp. See `references/live-season.md` for UI states.
6. Verify: start local server, confirm all base charts render.

### Phase 3: Enrichment (if applicable)

7. Build fetch scripts for additional API sources.
   - Rate limit requests. Handle network errors gracefully (warn, don't crash).
   - Map all entity names to canonical form matching 01_clean.py output.
8. Update 02_transform.py to merge new sources into JSON.
9. Update index.html to render enrichment charts conditionally.

### Phase 4: Documentation

10. Create `docs/cleaning-log.md` -- one entry per cleaning decision with What/Why/Impact.
11. Create `docs/pipeline.md` -- ASCII architecture diagram, "Why not [Tool X]" section, rerun instructions.
12. Create `README.md` -- the question, project tree, run instructions, skills demonstrated table.
13. Create `requirements.txt`, `.gitignore`.
14. Optionally create `.github/workflows/update.yml` for cron automation.

### Phase 5: Verify

15. Delete all generated files. Rerun full pipeline from scratch. Confirm dashboard renders.
16. Delete enrichment CSVs only. Confirm dashboard still works (graceful degradation).

## Script Patterns

See `references/script-patterns.md` for complete Python templates for cleaning, transform, and fetch scripts including:
- Step-separated comment blocks explaining WHY
- Console output formatting
- Error handling standards
- File path conventions using relative paths from project root

## Dashboard Design

See `references/design-system.md` for the frontend specification including:
- Dark editorial theme colors and typography
- Chart.js configuration defaults
- Conditional rendering patterns
- Responsive breakpoints
- 5-section narrative structure
- Partial season UI states (live indicator, matchday counter, last updated)

## Live Season Mode

See `references/live-season.md` for the complete guide to running against a live, in-progress season:
- Config-driven season selection (scripts/config.py)
- Historical vs live mode switching
- Partial season data handling in transform and dashboard
- UI states for incomplete data (progress bars, dynamic axis limits, tense switching)
- How to add a new season (2 lines in config.py, zero script changes)

## Documentation Templates

See `references/doc-templates.md` for README, cleaning-log, and pipeline doc templates with required sections and tone guidance.

## Anti-Patterns

- Iris, Titanic, or any Kaggle starter dataset
- Dashboards with no narrative (charts floating on a page)
- Comments that say "clean the data" instead of explaining why
- Over-engineering with Airflow/dbt for datasets under 10K rows
- Light theme with purple gradients
- Hardcoded analysis text instead of data-driven JS generation
- Missing error handling on API calls
- No fallback when optional data sources are unavailable
- Hardcoded season/year values scattered across scripts (use config.py)
- Dashboard that assumes complete data (breaks mid-season)

## Non-Negotiable Constraints

- No build step. Single HTML file.
- Comments explain WHY, not WHAT.
- No emojis. Anywhere.
- Dark theme. No light mode.
- Reproducible: clone, run scripts, start server, see dashboard.
- Team/entity name consistency across ALL scripts (use a canonical map).
