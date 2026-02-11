"""
config.py - Project Configuration

Single source of truth for seasons, team name maps, and data source URLs.
All scripts import from this file. No other script has hardcoded seasons,
URLs, or team name maps.

To add a new season: add one entry to ACTIVE_SEASONS, update CURRENT_SEASON,
add the team list to CANONICAL_TEAMS, and add any new name mappings.
"""

# -- SEASON CONFIGURATION -------------------------------------------------
# Each season entry drives download URLs, API endpoints, and mode selection.
# code: used in football-data.co.uk URL path
# understat: year parameter for Understat API (season start year)
# fpl_mode: "historical" fetches from GitHub archive, "live" from FPL API
ACTIVE_SEASONS = {
    "2022-23": {"code": "2223", "understat": "2022", "fpl_mode": "historical"},
    "2023-24": {"code": "2324", "understat": "2023", "fpl_mode": "historical"},
    "2024-25": {"code": "2425", "understat": "2024", "fpl_mode": "historical"},
    "2025-26": {"code": "2526", "understat": "2025", "fpl_mode": "live"},
}

# The primary season shown in the dashboard hero and league table
CURRENT_SEASON = "2025-26"

# -- DATA SOURCE URLS ------------------------------------------------------
FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"

FPL_GITHUB_BASE = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}"
FPL_LIVE_API = "https://fantasy.premierleague.com/api"

# -- CANONICAL TEAM NAMES --------------------------------------------------
# Master lists per season. Every script normalizes to these exact strings.
# Merges across data sources depend on this being consistent.
CANONICAL_TEAMS = {
    "2022-23": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Chelsea", "Crystal Palace", "Everton", "Fulham",
        "Leeds United", "Leicester City", "Liverpool", "Manchester City",
        "Manchester United", "Newcastle United", "Nottingham Forest",
        "Southampton", "Tottenham Hotspur", "West Ham United", "Wolverhampton",
    ],
    "2023-24": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
        "Liverpool", "Luton Town", "Manchester City", "Manchester United",
        "Newcastle United", "Nottingham Forest", "Sheffield United",
        "Tottenham Hotspur", "West Ham United", "Wolverhampton",
    ],
    "2024-25": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich",
        "Leicester City", "Liverpool", "Manchester City", "Manchester United",
        "Newcastle United", "Nottingham Forest", "Southampton",
        "Tottenham Hotspur", "West Ham United", "Wolverhampton",
    ],
    "2025-26": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Burnley", "Chelsea", "Crystal Palace", "Everton", "Fulham",
        "Leeds United", "Liverpool", "Manchester City", "Manchester United",
        "Newcastle United", "Nottingham Forest", "Sunderland",
        "Tottenham Hotspur", "West Ham United", "Wolverhampton",
    ],
}

# -- NAME MAPPINGS (source-specific -> canonical) --------------------------
# football-data.co.uk uses short names and abbreviations
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
    "Leeds": "Leeds United",
    "Sunderland": "Sunderland",
}

# FPL uses its own short forms
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
    "Sheffield Utd": "Sheffield United",
    "Leeds": "Leeds United",
}

# Understat uses full names but with inconsistent spacing/suffixes
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
    "Leicester": "Leicester City",
    "Sheffield United": "Sheffield United",
    "Leeds United": "Leeds United",
    "Leeds": "Leeds United",
}
