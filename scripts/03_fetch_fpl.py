"""
03_fetch_fpl.py - Fetch Fantasy Premier League Player Data

Enriches the match-level data with individual player statistics.
Supports two modes controlled by config.py:
  - historical: fetches from vaastav/Fantasy-Premier-League GitHub archive
  - live: fetches from the live FPL API (current season only)

If this script fails or is never run, the pipeline still works.
02_transform.py loads players.csv with try/except.

Run: python scripts/03_fetch_fpl.py
"""

import os
import sys
import time

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

from config import (
    ACTIVE_SEASONS, CURRENT_SEASON,
    FPL_GITHUB_BASE, FPL_LIVE_API, FPL_NAME_MAP,
)

# -- PATHS -----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
os.makedirs(CLEAN_DIR, exist_ok=True)

REQUEST_DELAY = 1.0

POSITION_MAP = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}


def fetch_url(url, description=""):
    """Fetch URL with error handling. Returns response or None."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        print(f"  TIMEOUT: {description}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP ERROR {e.response.status_code}: {description}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  NETWORK ERROR: {description} -- {e}")
        return None


def normalize_team(name):
    """Convert FPL team name to canonical form."""
    return FPL_NAME_MAP.get(name, name)


def fetch_historical():
    """Fetch from vaastav GitHub archive for completed seasons."""
    season = CURRENT_SEASON
    base = FPL_GITHUB_BASE.format(season=season)
    print(f"Fetching FPL data for season {season} (historical mode)...")

    # Players
    resp = fetch_url(f"{base}/cleaned_players.csv", "cleaned_players.csv")
    if resp is None:
        print("WARNING: Could not fetch player data. Skipping FPL enrichment.")
        return
    time.sleep(REQUEST_DELAY)

    players_df = pd.read_csv(pd.io.common.StringIO(resp.text))
    print(f"  Downloaded cleaned_players.csv: {len(players_df)} players")

    # Teams
    resp = fetch_url(f"{base}/teams.csv", "teams.csv")
    if resp is None:
        print("WARNING: Could not fetch teams data. Skipping FPL enrichment.")
        return
    time.sleep(REQUEST_DELAY)

    teams_df = pd.read_csv(pd.io.common.StringIO(resp.text))
    print(f"  Downloaded teams.csv: {len(teams_df)} teams")

    # Build team lookup
    team_lookup = dict(zip(teams_df['id'], teams_df['name']))

    # Process players
    result = []
    for _, row in players_df.iterrows():
        team_id = row.get('team', 0)
        team_name = team_lookup.get(team_id, str(team_id))
        team_name = normalize_team(team_name)

        pos_id = row.get('element_type', 0)
        position = POSITION_MAP.get(pos_id, 'UNK')

        price = row.get('now_cost', 0)
        if price > 100:
            price = price / 10.0

        result.append({
            'player_name': row.get('web_name', ''),
            'full_name': f"{row.get('first_name', '')} {row.get('second_name', '')}".strip(),
            'team': team_name,
            'position': position,
            'goals': int(row.get('goals_scored', 0)),
            'assists': int(row.get('assists', 0)),
            'clean_sheets': int(row.get('clean_sheets', 0)),
            'minutes': int(row.get('minutes', 0)),
            'yellow_cards': int(row.get('yellow_cards', 0)),
            'red_cards': int(row.get('red_cards', 0)),
            'total_points': int(row.get('total_points', 0)),
            'price': round(float(price), 1),
            'bonus': int(row.get('bonus', 0)),
        })

    output_df = pd.DataFrame(result)

    # Team name mapping summary
    mapped = sum(1 for t in output_df['team'].unique() if t in FPL_NAME_MAP.values())
    print(f"  Team name mapping: {mapped} canonical names applied")

    output_path = os.path.join(CLEAN_DIR, 'players.csv')
    output_df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path} ({len(output_df)} rows, {len(output_df.columns)} columns)")

    # Fixtures detailed (simplified -- not all seasons have granular event data)
    build_fixtures_from_github(base, team_lookup)

    print("FPL data fetch complete.")


def build_fixtures_from_github(base, team_lookup):
    """Build fixtures_detailed.csv from gameweek files if available."""
    # The vaastav repo structure varies. Try to build a basic fixture list.
    resp = fetch_url(f"{base}/fixtures.csv", "fixtures.csv")
    if resp is None:
        print("  Fixtures file not available -- skipping fixtures_detailed.csv")
        return
    time.sleep(REQUEST_DELAY)

    fixtures_df = pd.read_csv(pd.io.common.StringIO(resp.text))
    print(f"  Downloaded fixtures.csv: {len(fixtures_df)} rows")

    # Filter to finished matches
    if 'finished' in fixtures_df.columns:
        fixtures_df = fixtures_df[fixtures_df['finished'] == True]

    rows = []
    for _, row in fixtures_df.iterrows():
        home_id = row.get('team_h', 0)
        away_id = row.get('team_a', 0)
        home_team = normalize_team(team_lookup.get(home_id, str(home_id)))
        away_team = normalize_team(team_lookup.get(away_id, str(away_id)))

        rows.append({
            'match_date': str(row.get('kickoff_time', ''))[:10],
            'home_team': home_team,
            'away_team': away_team,
            'home_score': int(row.get('team_h_score', 0)) if pd.notna(row.get('team_h_score')) else 0,
            'away_score': int(row.get('team_a_score', 0)) if pd.notna(row.get('team_a_score')) else 0,
        })

    if rows:
        output_df = pd.DataFrame(rows)
        output_path = os.path.join(CLEAN_DIR, 'fixtures_detailed.csv')
        output_df.to_csv(output_path, index=False)
        print(f"  Saved: {output_path} ({len(output_df)} rows)")


def fetch_live():
    """Fetch from the live FPL API for the current season."""
    print(f"Fetching FPL data for season {CURRENT_SEASON} (live mode)...")

    resp = fetch_url(f"{FPL_LIVE_API}/bootstrap-static/", "bootstrap-static")
    if resp is None:
        print("WARNING: FPL API unavailable. Skipping FPL enrichment.")
        return
    time.sleep(REQUEST_DELAY)

    data = resp.json()
    elements = data.get('elements', [])
    teams = data.get('teams', [])

    team_lookup = {t['id']: t['name'] for t in teams}

    result = []
    for p in elements:
        team_name = normalize_team(team_lookup.get(p.get('team', 0), 'Unknown'))
        pos = POSITION_MAP.get(p.get('element_type', 0), 'UNK')
        price = p.get('now_cost', 0) / 10.0

        result.append({
            'player_name': p.get('web_name', ''),
            'full_name': f"{p.get('first_name', '')} {p.get('second_name', '')}".strip(),
            'team': team_name,
            'position': pos,
            'goals': int(p.get('goals_scored', 0)),
            'assists': int(p.get('assists', 0)),
            'clean_sheets': int(p.get('clean_sheets', 0)),
            'minutes': int(p.get('minutes', 0)),
            'yellow_cards': int(p.get('yellow_cards', 0)),
            'red_cards': int(p.get('red_cards', 0)),
            'total_points': int(p.get('total_points', 0)),
            'price': round(price, 1),
            'bonus': int(p.get('bonus', 0)),
        })

    output_df = pd.DataFrame(result)
    output_path = os.path.join(CLEAN_DIR, 'players.csv')
    output_df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path} ({len(output_df)} rows, {len(output_df.columns)} columns)")

    # Fixtures
    resp = fetch_url(f"{FPL_LIVE_API}/fixtures/", "fixtures")
    if resp:
        time.sleep(REQUEST_DELAY)
        fixtures = resp.json()
        finished = [f for f in fixtures if f.get('finished')]
        rows = []
        for f in finished:
            rows.append({
                'match_date': str(f.get('kickoff_time', ''))[:10],
                'home_team': normalize_team(team_lookup.get(f.get('team_h', 0), 'Unknown')),
                'away_team': normalize_team(team_lookup.get(f.get('team_a', 0), 'Unknown')),
                'home_score': int(f.get('team_h_score', 0) or 0),
                'away_score': int(f.get('team_a_score', 0) or 0),
            })
        if rows:
            fx_df = pd.DataFrame(rows)
            fx_path = os.path.join(CLEAN_DIR, 'fixtures_detailed.csv')
            fx_df.to_csv(fx_path, index=False)
            print(f"  Saved: {fx_path} ({len(fx_df)} rows)")

    print("FPL data fetch complete.")


def main():
    try:
        season_info = ACTIVE_SEASONS[CURRENT_SEASON]
        mode = season_info.get("fpl_mode", "historical")

        if mode == "live":
            fetch_live()
        else:
            fetch_historical()

    except requests.exceptions.RequestException as e:
        print(f"WARNING: Network request failed: {e}")
        print("Skipping FPL data. Pipeline will continue without it.")
    except Exception as e:
        print(f"WARNING: FPL fetch failed: {e}")
        print("Skipping FPL data. Pipeline will continue without it.")


if __name__ == '__main__':
    main()
