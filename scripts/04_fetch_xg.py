"""
04_fetch_xg.py - Fetch Understat Expected Goals (xG) Data

Adds an advanced analytics layer: expected goals per match, per team,
and per player. xG is the single most important advanced metric in
modern football analysis.

If this script fails or is never run, the pipeline still works.
02_transform.py loads xG CSVs with try/except.

Run: python scripts/04_fetch_xg.py
"""

import os
import sys
import time
import json
import re
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas is required. Run: pip install pandas")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests is required. Run: pip install requests")
    sys.exit(1)

from config import ACTIVE_SEASONS, CURRENT_SEASON, UNDERSTAT_NAME_MAP

# -- PATHS -----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
os.makedirs(CLEAN_DIR, exist_ok=True)

REQUEST_DELAY = 0.5


def normalize_team(name):
    """Convert Understat team name to canonical form."""
    clean = name.replace("_", " ")
    return UNDERSTAT_NAME_MAP.get(clean, clean)


def is_cache_fresh(filepath, max_age_hours=24):
    """Check if cached file is recent enough to skip re-fetching."""
    if not os.path.exists(filepath):
        return False
    modified = datetime.fromtimestamp(os.path.getmtime(filepath))
    return datetime.now() - modified < timedelta(hours=max_age_hours)


def fetch_with_understatapi(understat_year):
    """Primary method: use the understatapi package."""
    from understatapi import UnderstatClient
    understat = UnderstatClient()

    print("  Fetching match data...")
    matches = understat.league(league="EPL").get_match_data(season=understat_year)
    time.sleep(REQUEST_DELAY)

    print("  Fetching team data...")
    teams_data = understat.league(league="EPL").get_team_data(season=understat_year)
    time.sleep(REQUEST_DELAY)

    print("  Fetching player data...")
    players = understat.league(league="EPL").get_player_data(season=understat_year)
    time.sleep(REQUEST_DELAY)

    return matches, teams_data, players


def fetch_with_scraping(understat_year):
    """Fallback: scrape data directly from understat.com."""
    print("  Using fallback scraping method...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    url = f"https://understat.com/league/EPL/{understat_year}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY)

    # Extract datesData (match data)
    matches = extract_json_var(resp.text, "datesData")
    # Extract teamsData
    teams_raw = extract_json_var(resp.text, "teamsData")
    # Extract playersData
    players = extract_json_var(resp.text, "playersData")

    # Convert teamsData dict to list format similar to understatapi
    teams_data = teams_raw if isinstance(teams_raw, dict) else {}

    return matches, teams_data, players


def extract_json_var(html, var_name):
    """Extract JSON data embedded in script tags as JS variables."""
    pattern = rf"var\s+{var_name}\s*=\s*JSON\.parse\('(.+?)'\)"
    match = re.search(pattern, html)
    if match:
        raw = match.group(1).encode('utf-8').decode('unicode_escape')
        return json.loads(raw)
    return None


def process_matches(matches):
    """Process match data into xg_matches.csv format."""
    rows = []
    for m in matches:
        if not m.get('isResult', True):
            continue

        home_team = normalize_team(m.get('h', {}).get('title', '') if isinstance(m.get('h'), dict) else str(m.get('h', '')))
        away_team = normalize_team(m.get('a', {}).get('title', '') if isinstance(m.get('a'), dict) else str(m.get('a', '')))

        home_xg = m.get('xG', {}).get('h', 0) if isinstance(m.get('xG'), dict) else 0
        away_xg = m.get('xG', {}).get('a', 0) if isinstance(m.get('xG'), dict) else 0
        home_goals = m.get('goals', {}).get('h', 0) if isinstance(m.get('goals'), dict) else 0
        away_goals = m.get('goals', {}).get('a', 0) if isinstance(m.get('goals'), dict) else 0

        date_str = m.get('datetime', '')[:10] if m.get('datetime') else ''

        rows.append({
            'match_id': m.get('id', 0),
            'date': date_str,
            'home_team': home_team,
            'away_team': away_team,
            'home_goals': int(home_goals),
            'away_goals': int(away_goals),
            'home_xg': round(float(home_xg), 2),
            'away_xg': round(float(away_xg), 2),
        })

    return pd.DataFrame(rows)


def process_teams(teams_data):
    """Process team data into xg_teams.csv format."""
    rows = []

    if isinstance(teams_data, dict):
        # understatapi returns dict of {team_id: {title, history}}
        for team_id, team_info in teams_data.items():
            title = team_info.get('title', '') if isinstance(team_info, dict) else ''
            history = team_info.get('history', []) if isinstance(team_info, dict) else []

            if not history:
                continue

            team_name = normalize_team(title)
            matches_count = len(history)
            xg_for = sum(float(h.get('xG', 0)) for h in history)
            xg_against = sum(float(h.get('xGA', 0)) for h in history)
            goals_for = sum(int(h.get('scored', 0)) for h in history)
            goals_against = sum(int(h.get('missed', 0)) for h in history)
            npxg_for = sum(float(h.get('npxG', 0)) for h in history)
            npxg_against = sum(float(h.get('npxGA', 0)) for h in history)
            ppda_sum = sum(float(h.get('ppda', {}).get('att', 0)) / max(float(h.get('ppda', {}).get('def', 1)), 1) for h in history if isinstance(h.get('ppda'), dict))
            deep = sum(int(h.get('deep', 0)) for h in history)

            rows.append({
                'team': team_name,
                'matches': matches_count,
                'xg_for': round(xg_for, 2),
                'xg_against': round(xg_against, 2),
                'goals_for': goals_for,
                'goals_against': goals_against,
                'npxg_for': round(npxg_for, 2),
                'npxg_against': round(npxg_against, 2),
                'xg_difference': round(xg_for - xg_against, 2),
                'ppda': round(ppda_sum / matches_count, 2) if matches_count > 0 else 0,
                'deep_completions': deep,
            })
    elif isinstance(teams_data, list):
        # Fallback format might be a list
        for team_info in teams_data:
            team_name = normalize_team(team_info.get('title', team_info.get('team_name', '')))
            rows.append({
                'team': team_name,
                'matches': int(team_info.get('matches', 0)),
                'xg_for': round(float(team_info.get('xG', 0)), 2),
                'xg_against': round(float(team_info.get('xGA', 0)), 2),
                'goals_for': int(team_info.get('scored', team_info.get('goals_for', 0))),
                'goals_against': int(team_info.get('missed', team_info.get('goals_against', 0))),
                'npxg_for': round(float(team_info.get('npxG', 0)), 2),
                'npxg_against': round(float(team_info.get('npxGA', 0)), 2),
                'xg_difference': round(float(team_info.get('xG', 0)) - float(team_info.get('xGA', 0)), 2),
                'ppda': round(float(team_info.get('ppda', 0)), 2),
                'deep_completions': int(team_info.get('deep', 0)),
            })

    return pd.DataFrame(rows)


def process_players(players):
    """Process player data into xg_players.csv format."""
    rows = []
    if not players:
        return pd.DataFrame(rows)

    for p in players:
        team_name = normalize_team(p.get('team_title', p.get('team_name', '')))
        rows.append({
            'player_name': p.get('player_name', ''),
            'team': team_name,
            'position': p.get('position', ''),
            'games': int(p.get('games', 0)),
            'minutes': int(p.get('time', p.get('minutes', 0))),
            'goals': int(p.get('goals', 0)),
            'xg': round(float(p.get('xG', 0)), 2),
            'assists': int(p.get('assists', 0)),
            'xa': round(float(p.get('xA', 0)), 2),
            'shots': int(p.get('shots', 0)),
            'key_passes': int(p.get('key_passes', 0)),
            'npg': int(p.get('npg', 0)),
            'npxg': round(float(p.get('npxG', 0)), 2),
        })

    return pd.DataFrame(rows)


def main():
    season_info = ACTIVE_SEASONS[CURRENT_SEASON]
    understat_year = season_info["understat"]

    # Check cache
    cache_files = [
        os.path.join(CLEAN_DIR, 'xg_matches.csv'),
        os.path.join(CLEAN_DIR, 'xg_teams.csv'),
        os.path.join(CLEAN_DIR, 'xg_players.csv'),
    ]
    if all(is_cache_fresh(f) for f in cache_files):
        print("Using cached xG data (less than 24 hours old).")
        return

    print(f"Fetching xG data for season {CURRENT_SEASON} (Understat year: {understat_year})...")

    matches = None
    teams_data = None
    players = None

    # Try understatapi first
    try:
        matches, teams_data, players = fetch_with_understatapi(understat_year)
        print("  Fetched via understatapi")
    except ImportError:
        print("  understatapi not installed -- trying fallback scraping")
        try:
            matches, teams_data, players = fetch_with_scraping(understat_year)
            print("  Fetched via scraping fallback")
        except Exception as e:
            print(f"WARNING: Scraping fallback failed: {e}")
            print("Skipping xG data. Pipeline will continue without it.")
            return
    except Exception as e:
        print(f"  understatapi failed ({e}) -- trying fallback scraping")
        try:
            matches, teams_data, players = fetch_with_scraping(understat_year)
            print("  Fetched via scraping fallback")
        except Exception as e2:
            print(f"WARNING: Both methods failed: {e2}")
            print("Skipping xG data. Pipeline will continue without it.")
            return

    # Process and save
    if matches:
        matches_df = process_matches(matches)
        matches_path = os.path.join(CLEAN_DIR, 'xg_matches.csv')
        matches_df.to_csv(matches_path, index=False)
        print(f"\n  Saved: xg_matches.csv ({len(matches_df)} rows)")

        # Warn if data looks incomplete for a finished season
        if len(matches_df) < 300 and season_info.get("fpl_mode") == "historical":
            print(f"  WARNING: Only {len(matches_df)} matches found -- expected ~380 for complete season")
    else:
        print("  No match data returned")

    if teams_data:
        teams_df = process_teams(teams_data)
        teams_path = os.path.join(CLEAN_DIR, 'xg_teams.csv')
        teams_df.to_csv(teams_path, index=False)
        print(f"  Saved: xg_teams.csv ({len(teams_df)} rows)")
    else:
        print("  No team data returned")

    if players:
        players_df = process_players(players)
        players_path = os.path.join(CLEAN_DIR, 'xg_players.csv')
        players_df.to_csv(players_path, index=False)
        print(f"  Saved: xg_players.csv ({len(players_df)} rows)")
    else:
        print("  No player data returned")

    print("\nxG data fetch complete.")


if __name__ == '__main__':
    main()
