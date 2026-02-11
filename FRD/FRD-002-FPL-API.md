# FRD-002: FPL API Integration - Functional Specification

## Script: `scripts/03_fetch_fpl.py`

---

## Mode Selection

```python
from config import ACTIVE_SEASONS, CURRENT_SEASON, FPL_GITHUB_BASE, FPL_LIVE_API, FPL_NAME_MAP

season_info = ACTIVE_SEASONS[CURRENT_SEASON]
MODE = season_info["fpl_mode"]  # "historical" or "live"
```

No hardcoded `SEASON` variable in the script. Config.py controls everything.

---

## Historical Mode (2024-25)

### Source URLs:

```python
# Historical mode: URLs built from config
GITHUB_BASE = FPL_GITHUB_BASE.format(season=CURRENT_SEASON)
# e.g., https://raw.githubusercontent.com/.../data/2024-25

URLS = {
    "players": f"{GITHUB_BASE}/cleaned_players.csv",
    "teams": f"{GITHUB_BASE}/teams.csv",
    # Gameweek files: gws/gw1.csv through gws/gw38.csv
    "gw_template": f"{GITHUB_BASE}/gws/gw{{gw}}.csv",
}
```

### Processing:
1. Download `cleaned_players.csv` -- contains season totals per player
2. Download `teams.csv` -- maps team IDs to team names
3. Merge player data with team names
4. Apply team name mapping to canonical form
5. Map element_type to position string
6. Calculate derived fields (price = now_cost / 10)

---

## Live Mode (Current Season)

### Endpoints:

```python
# Live mode: base URL from config
ENDPOINTS = {
    "bootstrap": f"{FPL_LIVE_API}/bootstrap-static/",  # 1.4 MB JSON
    "fixtures": f"{FPL_LIVE_API}/fixtures/",
}
```

### Processing:
1. Fetch bootstrap-static
2. Extract `elements` array (players) and `teams` array
3. Build team lookup: `{team_id: team_name}`
4. For each player, join with team name
5. Fetch fixtures, extract goal scorer events from completed matches
6. Build fixtures_detailed.csv with scorer names

---

## Team Name Mapping

```python
# Import from config -- single source of truth
from config import FPL_NAME_MAP
# Apply after getting team names. For any name not in map, use as-is.
```

---

## Output Schema: players.csv

| Column | Type | Example |
|---|---|---|
| player_name | string | "Salah" |
| full_name | string | "Mohamed Salah" |
| team | string | "Liverpool" |
| position | string | "MID" |
| goals | int | 23 |
| assists | int | 12 |
| clean_sheets | int | 0 |
| minutes | int | 3200 |
| yellow_cards | int | 2 |
| red_cards | int | 0 |
| total_points | int | 265 |
| price | float | 13.0 |
| ownership_pct | float | 45.2 |
| bonus | int | 32 |

## Output Schema: fixtures_detailed.csv

| Column | Type | Example |
|---|---|---|
| match_date | string | "2024-08-17" |
| home_team | string | "Manchester United" |
| away_team | string | "Fulham" |
| home_score | int | 1 |
| away_score | int | 0 |
| home_scorers | string | "Zirkzee" |
| away_scorers | string | "" |

---

## Error Handling

```python
def fetch_url(url, description=""):
    """Fetch URL with retry and error handling."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        print(f"  TIMEOUT: {description} ({url})")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP ERROR {e.response.status_code}: {description}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  NETWORK ERROR: {description} -- {e}")
        return None
```

- All network calls use this wrapper
- 1 second delay between requests: `time.sleep(1)`
- If critical data fails (players file), exit with warning
- If supplementary data fails (individual gameweeks), continue with what we have

---

## Validation

After processing, verify:
- players.csv has 400+ rows (20 teams, ~25 players each)
- All team names exist in CANONICAL_TEAMS list
- No negative values in goals, assists, minutes
- Price values are between 3.5 and 20.0 (sanity range for EPL)
- No duplicate player entries (same full_name + team)
