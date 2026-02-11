# Live Season Mode Reference

How to run a data analysis portfolio project against a live, in-progress season where data updates weekly.

## The Core Concept

Every project has two modes:

| Mode | When | Data Source Behavior |
|---|---|---|
| **Historical** | Season is complete (e.g., 2024-25 analyzed in Feb 2026) | Download archived CSVs, fetch from GitHub repos, data is static |
| **Live** | Season is in progress (e.g., 2025-26 during Oct 2025) | Download updating CSVs, fetch from live APIs, data changes weekly |

The SAME codebase handles both modes. A single config file controls which mode is active.

## Config-Driven Season Selection

Create `scripts/config.py` as the single source of truth:

```python
"""
config.py - Project Configuration

Change ACTIVE_SEASONS and CURRENT_SEASON to switch between
historical analysis and live tracking.

Everything flows from this file. No other script has hardcoded seasons.
"""

# ── SEASON CONFIGURATION ──────────────────────
# Which seasons to include in the analysis
ACTIVE_SEASONS = {
    "2022-23": {"code": "2223", "understat": "2022", "fpl_mode": "historical"},
    "2023-24": {"code": "2324", "understat": "2023", "fpl_mode": "historical"},
    "2024-25": {"code": "2425", "understat": "2024", "fpl_mode": "historical"},
}

# To add 2025-26 live season, uncomment:
# ACTIVE_SEASONS["2025-26"] = {"code": "2526", "understat": "2025", "fpl_mode": "live"}

# The "primary" season for the dashboard hero section and league table
CURRENT_SEASON = "2024-25"

# ── DATA SOURCE URLS ──────────────────────────
FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"

FPL_GITHUB_BASE = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}"
FPL_LIVE_API = "https://fantasy.premierleague.com/api"

# ── CANONICAL TEAM NAMES ──────────────────────
# Master list. All scripts import this instead of maintaining their own.
CANONICAL_TEAMS = {
    "2024-25": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich",
        "Leicester City", "Liverpool", "Manchester City", "Manchester United",
        "Newcastle United", "Nottingham Forest", "Southampton",
        "Tottenham Hotspur", "West Ham United", "Wolverhampton",
    ],
    # Add 2025-26 teams when the season starts (3 promoted, 3 relegated)
}

# ── NAME MAPPINGS (source-specific → canonical) ──
FOOTBALL_DATA_NAME_MAP = {
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Nott'm Forest": "Nottingham Forest",
    "Tottenham": "Tottenham Hotspur",
    "Newcastle": "Newcastle United",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton",
    "Luton": "Luton Town",
    "Leicester": "Leicester City",
    "Sheffield United": "Sheffield United",
}

FPL_NAME_MAP = {
    "Man Utd": "Manchester United",
    "Man City": "Manchester City",
    "Nott'm Forest": "Nottingham Forest",
    "Spurs": "Tottenham Hotspur",
    "Newcastle": "Newcastle United",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton",
    "Luton": "Luton Town",
    "Leicester": "Leicester City",
}

UNDERSTAT_NAME_MAP = {
    "Manchester United": "Manchester United",
    "Manchester City": "Manchester City",
    "Nottingham Forest": "Nottingham Forest",
    "Tottenham": "Tottenham Hotspur",
    "Newcastle United": "Newcastle United",
    "West Ham": "West Ham United",
    "Wolverhampton Wanderers": "Wolverhampton",
    "Luton Town": "Luton Town",
    "Leicester City": "Leicester City",
    "Sheffield United": "Sheffield United",
}
```

## How Each Script Uses Config

### 01_clean.py

```python
from config import ACTIVE_SEASONS, FOOTBALL_DATA_URL, FOOTBALL_DATA_NAME_MAP

# Loop over configured seasons instead of hardcoded list
for season_label, season_info in ACTIVE_SEASONS.items():
    url = FOOTBALL_DATA_URL.format(code=season_info["code"])
    filepath = os.path.join(RAW_DIR, f'matches_{season_info["code"]}.csv')
    download_if_missing(filepath, url)
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    df['Season'] = season_label
    frames.append(df)
```

Adding a new season = one line in config.py. No script changes.

### 03_fetch_fpl.py

```python
from config import ACTIVE_SEASONS, CURRENT_SEASON, FPL_GITHUB_BASE, FPL_LIVE_API, FPL_NAME_MAP

season_info = ACTIVE_SEASONS[CURRENT_SEASON]

if season_info["fpl_mode"] == "historical":
    # Fetch from vaastav GitHub repo (archived, complete)
    base_url = FPL_GITHUB_BASE.format(season=CURRENT_SEASON)
    # ...
elif season_info["fpl_mode"] == "live":
    # Fetch from live FPL API (current, updating weekly)
    # bootstrap-static endpoint reflects current gameweek
    response = requests.get(f"{FPL_LIVE_API}/bootstrap-static/")
    # ...
```

### 04_fetch_xg.py

```python
from config import ACTIVE_SEASONS, CURRENT_SEASON, UNDERSTAT_NAME_MAP

season_info = ACTIVE_SEASONS[CURRENT_SEASON]
understat_year = season_info["understat"]

matches = understat.league(league="EPL").get_match_data(season=understat_year)
```

### 02_transform.py

```python
from config import CURRENT_SEASON

# Filter for current season when building league table
current = df[df['season'] == CURRENT_SEASON]
total_matches_played = len(current)  # Could be 380 (complete) or 200 (in progress)

# Calculate matchdays completed
max_matchday = current.groupby('home_team').size().max()
```

## Handling Partial Season Data

A complete EPL season has 380 matches (20 teams x 19 home matches x 2). During a live season, you might have 100, 200, or 300 matches depending on the gameweek.

### In 02_transform.py

```python
# Detect season completeness
FULL_SEASON_MATCHES = 380
matches_played = len(current_season_df)
season_complete = matches_played >= FULL_SEASON_MATCHES
matchdays_played = current_season_df.groupby('home_team').size().max()

# Add to JSON output
output["season_status"] = {
    "matches_played": matches_played,
    "matches_total": FULL_SEASON_MATCHES,
    "matchdays_played": int(matchdays_played),
    "matchdays_total": 38,
    "is_complete": season_complete,
    "last_match_date": current_season_df['date'].max(),
}
```

### In dashboard_data.json

```json
{
  "season_status": {
    "matches_played": 240,
    "matches_total": 380,
    "matchdays_played": 24,
    "matchdays_total": 38,
    "is_complete": false,
    "last_match_date": "2026-02-08"
  }
}
```

### In index.html

```javascript
// Show "live" indicator if season is in progress
if (!data.season_status.is_complete) {
  const liveTag = document.getElementById('live-indicator');
  liveTag.classList.remove('hidden');
  liveTag.textContent = `Live — Matchday ${data.season_status.matchdays_played} of 38`;

  const updatedTag = document.getElementById('last-updated');
  updatedTag.classList.remove('hidden');
  updatedTag.textContent = `Last updated: ${data.season_status.last_match_date}`;
}

// Cumulative points chart: X-axis only goes to matchdays played
const maxMatchday = data.season_status.matchdays_played;
// Don't draw empty matchdays 25-38 if only 24 played

// League table: show "P" (played) column prominently
// Teams may have different games played due to postponements

// KPI cards: show "240 of 380 matches" instead of just "380 matches"
```

### UI States for Partial Season

| Element | Complete Season | Live Season |
|---|---|---|
| Hero subtitle | "380 matches across 38 matchdays" | "240 of 380 matches -- Matchday 24 of 38" |
| KPI card: matches | "380" | "240 / 380" with progress bar |
| League table header | "2024-25 Final Standings" | "2025-26 Standings (Matchday 24)" |
| Played column | All show 38 | Some show 23, some 24 (postponements) |
| Cumulative points chart | X-axis: 1 to 38 | X-axis: 1 to 24 (stops at current matchday) |
| Takeaway section | Past tense: "Liverpool won the league" | Present tense: "Liverpool lead the table" |
| Nav bar | No indicator | Pulsing green dot + "LIVE" tag |
| Last updated | Not shown | "Data as of 2026-02-08" |

## Switching to Live Season

When the 2025-26 season starts (August 2025), make these changes:

### Step 1: Update config.py (one file, 2 lines)

```python
ACTIVE_SEASONS["2025-26"] = {
    "code": "2526",
    "understat": "2025",
    "fpl_mode": "live"
}
CURRENT_SEASON = "2025-26"
```

### Step 2: Add 2025-26 teams to canonical list

```python
CANONICAL_TEAMS["2025-26"] = [
    # Copy from 2024-25, swap relegated for promoted
    # e.g., remove Southampton, Leicester, Ipswich
    # add promoted teams from Championship
]
```

### Step 3: Add name mappings for any new teams

Check if promoted teams have different names in football-data.co.uk, FPL, or Understat.

### Step 4: Push and let GitHub Actions handle the rest

The weekly cron now fetches live data every Monday. Dashboard updates automatically.

That's it. No script changes. No HTML changes. Config drives everything.

## Reverting to Historical Mode

When the season ends, change `fpl_mode` from `"live"` to `"historical"` and push. The FPL script switches from live API to the archived GitHub repo. The dashboard detects `is_complete: true` and drops the "LIVE" indicator.
