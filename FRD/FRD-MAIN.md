# FRD-MAIN: Functional Requirements Document

## Document Control

| Field | Value |
|---|---|
| Version | 1.0 |
| Companion PRD | PRD-MAIN.md |
| Last Updated | 2026-02-10 |

---

## 1. Purpose

This document defines the technical functional requirements for the EPL Data Analysis Platform. Where the PRDs describe WHAT to build and WHY, this document describes HOW it must behave at a technical level: data contracts, interfaces, error handling, validation rules, and acceptance tests.

---

## 2. Feature FRD Index

| ID | Feature | FRD Document |
|---|---|---|
| F-001 | Data ETL Pipeline | [FRD-001-DATA-ETL.md](./FRD-001-DATA-ETL.md) |
| F-002 | FPL API Integration | [FRD-002-FPL-API.md](./FRD-002-FPL-API.md) |
| F-003 | Understat xG Integration | [FRD-003-XG-DATA.md](./FRD-003-XG-DATA.md) |
| F-004 | Dashboard Frontend | [FRD-004-DASHBOARD.md](./FRD-004-DASHBOARD.md) |
| F-005 | GitHub Actions CI/CD | [FRD-005-AUTOMATION.md](./FRD-005-AUTOMATION.md) |

---

## 3. Global Functional Requirements

These apply across ALL features.

### 3.1 Config File (scripts/config.py)

ALL scripts import their season definitions, team name maps, and source URLs from `scripts/config.py`. No script contains hardcoded seasons, URLs, or name maps.

The config file defines:
- `ACTIVE_SEASONS` -- dict of season labels to metadata (code, understat year, fpl_mode)
- `CURRENT_SEASON` -- which season is the "primary" for the dashboard
- `FOOTBALL_DATA_URL` -- URL template with `{code}` placeholder
- `FPL_GITHUB_BASE` -- URL template with `{season}` placeholder
- `FPL_LIVE_API` -- base URL for live FPL API
- `CANONICAL_TEAMS` -- dict of season to list of 20 team names
- `FOOTBALL_DATA_NAME_MAP`, `FPL_NAME_MAP`, `UNDERSTAT_NAME_MAP` -- source-specific to canonical mappings

See the SKILL reference `references/live-season.md` for the complete config.py template.

To add a new season: add one entry to `ACTIVE_SEASONS`, update `CURRENT_SEASON`, add the team list to `CANONICAL_TEAMS`, and add any new name mappings. Zero script changes.

### 3.2 Team Name Canonical Map

ALL scripts must output team names using this exact canonical form. This is the single source of truth for team identity across the entire project. These are defined in `scripts/config.py` and imported by all scripts.

```python
CANONICAL_TEAMS_2024_25 = [
    "Arsenal",
    "Aston Villa",
    "Bournemouth",
    "Brentford",
    "Brighton",
    "Chelsea",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Ipswich",
    "Leicester City",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Newcastle United",
    "Nottingham Forest",
    "Southampton",
    "Tottenham Hotspur",
    "West Ham United",
    "Wolverhampton",
]
```

Every data source uses different names. Each script must include a mapping dictionary that converts source-specific names to the canonical form above.

### 3.3 Error Handling Standard

All scripts must follow this pattern:

```python
import sys

def main():
    try:
        # script logic
        pass
    except FileNotFoundError as e:
        print(f"ERROR: Required file not found: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"WARNING: Network request failed: {e}")
        print("Skipping this data source. Pipeline will continue without it.")
        # Do NOT sys.exit -- allow pipeline to continue
    except Exception as e:
        print(f"ERROR: Unexpected failure: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

Rules:
- Network errors are WARNINGS (don't crash)
- File system errors are ERRORS (crash)
- Missing dependencies are ERRORS (crash with install instructions)
- Always print what went wrong and what the user should do

### 3.4 File Path Convention

All scripts use relative paths from the project root. No hardcoded absolute paths.

```python
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data')
```

### 3.5 CSV Output Standard

All CSV files use:
- UTF-8 encoding (no BOM)
- Comma delimiter
- First row is header
- No index column (`index=False` in pandas)
- Floats rounded to 2 decimal places for xG values
- Dates in YYYY-MM-DD format

### 3.6 JSON Output Standard

The dashboard_data.json file:
- UTF-8 encoding
- 2-space indentation for readability
- No trailing commas
- Null for missing optional sections (not omitted keys)
- Numbers: integers where possible, floats to 2 decimal places

### 3.7 Dependency Management

requirements.txt must list exact minimum versions:

```
pandas>=2.0.0
requests>=2.28.0
understatapi>=0.7.0
```

Scripts must check for missing packages and print install instructions:

```python
try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas is required. Run: pip install pandas")
    sys.exit(1)
```

---

## 4. Data Flow Diagram

```
                    ┌─────────────────────────────────────────────┐
                    │              DATA SOURCES                    │
                    ├──────────┬──────────────┬───────────────────┤
                    │ football │  FPL API /   │   Understat.com   │
                    │ -data.co │  GitHub Repo │   (understatapi)  │
                    │ .uk CSVs │              │                   │
                    └────┬─────┴──────┬───────┴─────────┬─────────┘
                         │            │                 │
                         v            v                 v
                    ┌─────────┐ ┌──────────┐    ┌──────────┐
                    │01_clean │ │03_fetch  │    │04_fetch  │
                    │  .py    │ │ _fpl.py  │    │ _xg.py   │
                    └────┬────┘ └────┬─────┘    └────┬─────┘
                         │           │               │
                         v           v               v
                    matches_   players.csv      xg_matches.csv
                    clean.csv  fixtures_        xg_players.csv
                               detailed.csv    xg_teams.csv
                         │           │               │
                         └─────┬─────┴───────────────┘
                               │
                               v
                        ┌─────────────┐
                        │02_transform │
                        │    .py      │
                        └──────┬──────┘
                               │
                               v
                        dashboard_data.json
                               │
                               v
                        ┌─────────────┐
                        │ index.html  │  (Chart.js + Tailwind)
                        └─────────────┘
```

---

## 5. Validation Rules

After the full pipeline runs, these conditions must be true:

| Check | Expected (Complete Season) | Expected (Live Season) |
|---|---|---|
| matches_clean.csv row count | 1,140 (380 x 3 seasons) | (380 x completed seasons) + N current |
| matches_clean.csv column count | 29 | 29 |
| Unique teams in current season | 20 | 20 |
| All team names in canonical list | True | True |
| dashboard_data.json is valid JSON | True | True |
| dashboard_data.json league_table length | 20 | 20 |
| dashboard_data.json total_matches | 380 | N (current matchday x 10) |
| dashboard_data.json season_status exists | True | True |
| dashboard_data.json season_status.is_complete | True | False |
| index.html loads without JS console errors | True | True |
| All Chart.js canvases render | True (for available data) | True (axes adapt to data) |
| LIVE indicator hidden | True | False (visible) |

---

## 6. Performance Requirements

| Metric | Target |
|---|---|
| 01_clean.py execution time | Under 5 seconds |
| 03_fetch_fpl.py execution time | Under 60 seconds (network dependent) |
| 04_fetch_xg.py execution time | Under 60 seconds (network dependent) |
| 02_transform.py execution time | Under 10 seconds |
| index.html initial load time | Under 3 seconds on broadband |
| dashboard_data.json file size | Under 200 KB |
