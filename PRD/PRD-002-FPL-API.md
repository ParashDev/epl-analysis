# PRD-002: FPL API Player Data Integration

## Feature Summary

Fetch player-level statistics from the Fantasy Premier League ecosystem to enrich the match-level data with individual performance breakdowns. This answers the question: "Liverpool scored 2 goals, but who scored them?"

**Priority:** P1 (Should Have)
**Script:** `scripts/03_fetch_fpl.py`
**Input:** FPL API or vaastav GitHub repo
**Output:** `data/cleaned/players.csv`, `data/cleaned/fixtures_detailed.csv`

---

## Data Source Strategy

The FPL live API (`https://fantasy.premierleague.com/api/`) always reflects the CURRENT active season. The script reads `CURRENT_SEASON` and `fpl_mode` from `scripts/config.py` to determine which source to use:

- **Historical mode** (`fpl_mode: "historical"`): Fetch from the vaastav/Fantasy-Premier-League GitHub repo, which archives complete season data.
- **Live mode** (`fpl_mode: "live"`): Fetch from the live FPL API, which reflects the current gameweek and updates after each round of fixtures.

The script does NOT contain a hardcoded `SEASON` variable. It imports from config.py.

**Primary source (historical mode):**
GitHub repo: `https://github.com/vaastav/Fantasy-Premier-League/tree/master/data/2024-25`

Key files to download:
- `cleaned_players.csv` -- season totals for every player
- `gws/gw{1-38}.csv` -- per-gameweek stats for every player
- `teams.csv` -- team ID to name mapping

**Fallback source (current live season):**
If building for the current 2025-26 season, use the live API:
- `https://fantasy.premierleague.com/api/bootstrap-static/` -- players + teams + gameweeks
- `https://fantasy.premierleague.com/api/fixtures/` -- match events with player-level detail

The script should detect which mode to use based on a `SEASON` variable at the top of the file. Default to "2024-25" (historical mode).

---

## Data to Extract

### From players data (one row per player, season totals):

| Field | Source Field | Notes |
|---|---|---|
| player_name | web_name or first_name + second_name | Use web_name for display (e.g. "Salah") |
| full_name | first_name + " " + second_name | For matching with other sources |
| team | team (ID) | Map to team name using teams data |
| position | element_type | Map: 1=GK, 2=DEF, 3=MID, 4=FWD |
| goals | goals_scored | |
| assists | assists | |
| clean_sheets | clean_sheets | |
| minutes | minutes | |
| yellow_cards | yellow_cards | |
| red_cards | red_cards | |
| total_points | total_points | FPL fantasy points |
| price | now_cost / 10 | Stored as integer, divide by 10 for actual |
| ownership_pct | selected_by_percent | % of FPL managers who own this player |
| bonus | bonus | Bonus points awarded |
| influence | influence | FPL's influence metric |
| creativity | creativity | FPL's creativity metric |
| threat | threat | FPL's threat metric |

### From fixtures data (goal scorers per match):

For each completed fixture, extract which players scored and assisted. This creates a detailed match log showing individual contributions.

| Field | Notes |
|---|---|
| match_date | Date of the fixture |
| home_team | Mapped to standard team names |
| away_team | Mapped to standard team names |
| home_score | |
| away_score | |
| home_scorers | Comma-separated list of player names who scored for home team |
| away_scorers | Comma-separated list of player names who scored for away team |

---

## Team Name Mapping

Import `FPL_NAME_MAP` from `scripts/config.py`. The canonical mappings are:

```python
FPL_TEAM_MAP = {
    "Man Utd": "Manchester United",
    "Man City": "Manchester City",
    "Nott'm Forest": "Nottingham Forest",
    "Spurs": "Tottenham Hotspur",
    "Newcastle": "Newcastle United",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton",
    "Luton": "Luton Town",
    "Leicester": "Leicester City",
    # Others may need mapping too -- check the teams data and add as needed
}
```

---

## Error Handling

- If the GitHub raw file returns 404, print a warning and skip that file
- If the API is down (status != 200), print a warning and exit gracefully (do not crash)
- Add 1-second delay between HTTP requests
- Wrap all network calls in try/except
- If the script fails entirely, the rest of the pipeline (02_transform.py) must still work without FPL data

---

## Console Output

```
Fetching FPL data for season 2024-25 (historical mode)...
  Downloaded cleaned_players.csv: 562 players
  Downloaded teams.csv: 20 teams
  Processing gameweek files: 38/38 complete
  Team name mapping: 10 remapped, 10 unchanged

Saved: data/cleaned/players.csv (562 rows, 17 columns)
Saved: data/cleaned/fixtures_detailed.csv (380 rows, 7 columns)
FPL data fetch complete.
```

---

## Acceptance Criteria

- [ ] Script runs without errors: `python scripts/03_fetch_fpl.py`
- [ ] players.csv has one row per player who played in 2024-25
- [ ] All team names match canonical naming convention
- [ ] Price is in actual millions (e.g., 13.0 not 130)
- [ ] Position is readable text (GK/DEF/MID/FWD not 1/2/3/4)
- [ ] Script handles network failures gracefully (no crash)
- [ ] 02_transform.py works if this script was never run (files don't exist)
