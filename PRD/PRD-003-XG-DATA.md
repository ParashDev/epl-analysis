# PRD-003: Understat xG Data Integration

## Feature Summary

Fetch expected goals (xG) data from Understat to add an advanced analytics layer. This transforms the project from "basic match stats" to "this person understands modern football analytics." xG is the single most important advanced metric in football analysis today.

**Priority:** P1 (Should Have)
**Script:** `scripts/04_fetch_xg.py`
**Input:** Understat.com via understatapi Python package
**Output:** `data/cleaned/xg_matches.csv`, `data/cleaned/xg_players.csv`, `data/cleaned/xg_teams.csv`

---

## What is xG (for context)

Expected Goals (xG) assigns a probability (0 to 1) to every shot based on: distance from goal, angle, body part, game situation (open play vs set piece), and other factors. A penalty has ~0.76 xG. A shot from the halfway line has ~0.01 xG.

If a team has 2.5 xG but scored 1 goal, they were wasteful.
If a team has 0.8 xG but scored 2 goals, they were clinical (or lucky).

Over a season, the gap between xG and actual goals reveals which teams are overperforming (likely to regress) and which are underperforming (likely to improve).

---

## Data Source

**Package:** `understatapi` (pip install understatapi)
**Website:** https://understat.com/
**Season parameter:** Imported from `scripts/config.py`. The `understat` field in `ACTIVE_SEASONS[CURRENT_SEASON]` provides the year value. For 2024-25, this is `"2024"`. For 2025-26 live season, this is `"2025"`.

The script does NOT contain a hardcoded season year. It imports from config.py.

---

## Data to Extract

### 1. Match-level xG (xg_matches.csv)

```python
from understatapi import UnderstatClient
understat = UnderstatClient()
matches = understat.league(league="EPL").get_match_data(season="2024")
```

| Field | Source | Notes |
|---|---|---|
| match_id | id | Understat's internal match ID |
| date | datetime | Match date |
| home_team | h.title | Map to standard names |
| away_team | a.title | Map to standard names |
| home_goals | goals.h | Actual goals scored |
| away_goals | goals.a | Actual goals scored |
| home_xg | xG.h | Expected goals for home team |
| away_xg | xG.a | Expected goals for away team |

### 2. Team-level season xG (xg_teams.csv)

```python
team_data = understat.league(league="EPL").get_team_data(season="2024")
```

Aggregate from team history data for each team:

| Field | Notes |
|---|---|
| team | Standard team name |
| matches_played | Count of matches |
| xg_for | Sum of xG generated |
| xg_against | Sum of xG conceded |
| actual_goals_for | Sum of actual goals scored |
| actual_goals_against | Sum of actual goals conceded |
| xg_difference | xg_for - xg_against |
| npxg_for | Non-penalty xG (more accurate measure of open play quality) |
| npxg_against | Non-penalty xG conceded |
| ppda | Passes per defensive action (pressing metric) |
| deep_completions | Passes completed within 20 yards of goal |

### 3. Player-level xG (xg_players.csv)

```python
player_data = understat.league(league="EPL").get_player_data(season="2024")
```

| Field | Source | Notes |
|---|---|---|
| player_name | player_name | |
| team | team_title | Map to standard names |
| games | games | Matches played |
| minutes | time | Minutes played |
| goals | goals | Actual goals |
| xg | xG | Expected goals |
| assists | assists | |
| xa | xA | Expected assists |
| shots | shots | Total shots taken |
| key_passes | key_passes | Passes leading to a shot |
| npg | npg | Non-penalty goals |
| npxg | npxG | Non-penalty xG |
| xg_chain | xGChain | xG involvement in buildup |
| xg_buildup | xGBuildup | xG contribution to buildup play |
| position | position | Position(s) played |

---

## Team Name Mapping

Import `UNDERSTAT_NAME_MAP` from `scripts/config.py`. Understat uses names with underscores and sometimes different forms:

```python
UNDERSTAT_TEAM_MAP = {
    "Manchester_United": "Manchester United",
    "Manchester_City": "Manchester City",
    "Nottingham_Forest": "Nottingham Forest",
    "Tottenham": "Tottenham Hotspur",
    "Newcastle_United": "Newcastle United",
    "West_Ham": "West Ham United",
    "Wolverhampton_Wanderers": "Wolverhampton",
    "Luton_Town": "Luton Town",
    "Leicester_City": "Leicester City",
    "Sheffield_United": "Sheffield United",
    "Aston_Villa": "Aston Villa",
    "Crystal_Palace": "Crystal Palace",
    "West_Bromwich_Albion": "West Bromwich Albion",
}
# For any team not in the map, replace underscores with spaces
```

---

## Rate Limiting

Understat is a free resource maintained by a small team. Be respectful:
- Add 0.5 second delay between requests
- Cache responses locally -- don't re-fetch if the CSV files already exist and are less than 24 hours old
- Print a message when fetching vs using cache

---

## Fallback Strategy

If the `understatapi` package fails (it depends on the site structure not changing), implement a direct scraping fallback:

```python
# Fallback: direct scraping from understat.com
# The data is embedded in <script> tags as JavaScript variables
# Parse with requests + json
import requests
import json
import re

url = "https://understat.com/league/EPL/2024"
response = requests.get(url)
# Extract JSON from script tags using regex
# This is fragile but well-documented in the football analytics community
```

If both methods fail, print a warning and exit gracefully. The pipeline must continue without xG data.

---

## Error Handling

- Wrap all Understat calls in try/except
- If the package is not installed, print: "understatapi not installed. Run: pip install understatapi"
- If the site is down, print a warning and skip
- If data looks incomplete (fewer than 300 matches for a full season), print a warning
- Never crash the pipeline

---

## Acceptance Criteria

- [ ] Script runs without errors: `python scripts/04_fetch_xg.py`
- [ ] xg_matches.csv has ~380 rows (one per EPL match)
- [ ] xg_teams.csv has 20 rows (one per team)
- [ ] xg_players.csv has 400+ rows (all players who appeared)
- [ ] All team names match canonical naming convention
- [ ] xG values are floats between 0 and ~5 per match (sanity check)
- [ ] Rate limiting is in place (script takes at least 5 seconds to run)
- [ ] 02_transform.py works if this script was never run
