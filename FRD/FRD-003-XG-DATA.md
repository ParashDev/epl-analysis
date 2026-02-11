# FRD-003: Understat xG Integration - Functional Specification

## Script: `scripts/04_fetch_xg.py`

---

## Primary Method: understatapi package

```python
from understatapi import UnderstatClient
from config import ACTIVE_SEASONS, CURRENT_SEASON, UNDERSTAT_NAME_MAP
import time

season_info = ACTIVE_SEASONS[CURRENT_SEASON]
understat_year = season_info["understat"]  # e.g., "2024" for 2024-25 season

understat = UnderstatClient()

# Match-level xG
matches = understat.league(league="EPL").get_match_data(season=understat_year)
time.sleep(0.5)

# Team-level aggregated xG
teams = understat.league(league="EPL").get_team_data(season=understat_year)
time.sleep(0.5)

# Player-level xG
players = understat.league(league="EPL").get_player_data(season=understat_year)
```

No hardcoded season year in the script. Config.py controls which season is fetched.

---

## Fallback Method: Direct Scraping

If understatapi fails (import error or runtime error), fall back to:

```python
import requests
import json
import re
from bs4 import BeautifulSoup

def scrape_understat_league(league="EPL", season=None):
    """Fallback if understatapi package fails. Season param from config."""
    if season is None:
        from config import ACTIVE_SEASONS, CURRENT_SEASON
        season = ACTIVE_SEASONS[CURRENT_SEASON]["understat"]
    url = f"https://understat.com/league/{league}/{season}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    # Data is embedded in <script> tags as JS variables
    scripts = soup.find_all("script")
    for script in scripts:
        text = script.string or ""
        if "teamsData" in text:
            # Extract JSON between quotes after "JSON.parse("
            match = re.search(r"JSON\.parse\('(.+?)'\)", text)
            if match:
                raw = match.group(1).encode().decode('unicode_escape')
                return json.loads(raw)
    return None
```

---

## Team Name Mapping

```python
from config import UNDERSTAT_NAME_MAP

def normalize_understat_team(name):
    """Convert Understat team name to canonical form."""
    clean = name.replace("_", " ")
    return UNDERSTAT_NAME_MAP.get(clean, clean)
```

---

## Output Schemas

### xg_matches.csv

| Column | Type | Example |
|---|---|---|
| match_id | int | 22345 |
| date | string | "2024-08-17" |
| home_team | string | "Manchester United" |
| away_team | string | "Fulham" |
| home_goals | int | 1 |
| away_goals | int | 0 |
| home_xg | float | 1.45 |
| away_xg | float | 0.82 |

### xg_teams.csv

| Column | Type | Example |
|---|---|---|
| team | string | "Liverpool" |
| matches | int | 38 |
| xg_for | float | 75.23 |
| xg_against | float | 35.12 |
| goals_for | int | 83 |
| goals_against | int | 38 |
| npxg_for | float | 68.50 |
| npxg_against | float | 32.80 |
| xg_difference | float | 40.11 |
| ppda | float | 9.8 |
| deep_completions | int | 245 |

### xg_players.csv

| Column | Type | Example |
|---|---|---|
| player_name | string | "Mohamed Salah" |
| team | string | "Liverpool" |
| position | string | "F M S" |
| games | int | 36 |
| minutes | int | 3050 |
| goals | int | 23 |
| xg | float | 19.52 |
| assists | int | 12 |
| xa | float | 8.23 |
| shots | int | 126 |
| key_passes | int | 55 |
| npg | int | 21 |
| npxg | float | 17.20 |

---

## Rate Limiting

```python
REQUEST_DELAY = 0.5  # seconds between requests

# After each API call:
time.sleep(REQUEST_DELAY)
```

---

## Caching

```python
import os
from datetime import datetime, timedelta

def is_cache_fresh(filepath, max_age_hours=24):
    """Check if cached file is recent enough to skip re-fetching."""
    if not os.path.exists(filepath):
        return False
    modified = datetime.fromtimestamp(os.path.getmtime(filepath))
    return datetime.now() - modified < timedelta(hours=max_age_hours)
```

If all 3 output files exist and are less than 24 hours old, skip fetching and print "Using cached xG data."

---

## Validation

- xg_matches.csv should have ~380 rows for a complete season (fewer for live season, proportional to matchdays played)
- xg_teams.csv should have 20 rows
- xg_players.csv should have 400+ rows (complete season) or proportionally fewer (live season)
- All xG values should be between 0.0 and 120.0 (season total range)
- All team names must be in the canonical list
- If fewer than 300 matches returned for a season expected to be complete, print warning about incomplete data
- For a live season, fewer matches is expected -- do not warn if matches < 380
