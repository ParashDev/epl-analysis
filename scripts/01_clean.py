"""
01_clean.py - EPL Match Data Cleansing

Source: football-data.co.uk
Raw files have 107-120 columns per season. ~96 are betting odds from
bookmakers (B365, BW, BF, PS, WH, etc.) irrelevant to match analysis.
We keep 24 columns describing actual match events and derive 5 more.

Run: python scripts/01_clean.py
"""

import os
import sys
from datetime import datetime

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
    FOOTBALL_DATA_URL, FOOTBALL_DATA_NAME_MAP,
)

# -- PATHS -----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)

# -- COLUMNS TO KEEP -------------------------------------------------------
# These 24 columns capture everything about the match itself.
# Div is dropped after load (always "E0" for EPL), but we keep it
# briefly to verify we have the right league.
KEEP_COLUMNS = [
    'Date', 'Time', 'HomeTeam', 'AwayTeam',
    'FTHG', 'FTAG', 'FTR',
    'HTHG', 'HTAG', 'HTR',
    'Referee',
    'HS', 'AS', 'HST', 'AST',
    'HF', 'AF', 'HC', 'AC',
    'HY', 'AY', 'HR', 'AR',
]

# -- HUMAN-READABLE RENAMES ------------------------------------------------
# Cryptic abbreviations hurt readability for anyone reviewing the portfolio.
RENAME_MAP = {
    'FTHG': 'home_goals', 'FTAG': 'away_goals', 'FTR': 'result',
    'HTHG': 'ht_home_goals', 'HTAG': 'ht_away_goals', 'HTR': 'ht_result',
    'HS': 'home_shots', 'AS': 'away_shots',
    'HST': 'home_shots_on_target', 'AST': 'away_shots_on_target',
    'HF': 'home_fouls', 'AF': 'away_fouls',
    'HC': 'home_corners', 'AC': 'away_corners',
    'HY': 'home_yellows', 'AY': 'away_yellows',
    'HR': 'home_reds', 'AR': 'away_reds',
    'HomeTeam': 'home_team', 'AwayTeam': 'away_team',
    'Date': 'date', 'Time': 'time', 'Referee': 'referee',
}

# -- STAT COLUMNS (for null checks) ----------------------------------------
STAT_COLS = [
    'FTHG', 'FTAG', 'HTHG', 'HTAG',
    'HS', 'AS', 'HST', 'AST',
    'HF', 'AF', 'HC', 'AC',
    'HY', 'AY', 'HR', 'AR',
]

GOAL_COLS = ['FTHG', 'FTAG']


def download_if_missing(filepath, url):
    """Download source file if not already cached locally."""
    if os.path.exists(filepath):
        print(f"  Using cached: {os.path.basename(filepath)}")
        return
    print(f"  Downloading: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"  WARNING: Could not download {url} -- {e}")
        raise


def download_current(filepath, url):
    """Always re-download for live season (CSV grows weekly)."""
    print(f"  Downloading latest: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"  WARNING: Could not download {url} -- {e}")
        raise


def parse_date(date_str):
    """Standardize DD/MM/YYYY and DD/MM/YY to ISO 8601 (YYYY-MM-DD)."""
    if pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    for fmt in ['%d/%m/%Y', '%d/%m/%y']:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def main():
    print("Loading raw match data...")

    # -- STEP 1: Download + Load -------------------------------------------
    # Each season is a separate CSV on football-data.co.uk. We download
    # once and cache locally so development works offline.
    frames = []
    for season_label, season_info in ACTIVE_SEASONS.items():
        code = season_info["code"]
        url = FOOTBALL_DATA_URL.format(code=code)
        filepath = os.path.join(RAW_DIR, f'matches_{code}.csv')

        # Live season needs fresh data each run; historical seasons are static
        is_current = (season_label == CURRENT_SEASON
                      and season_info.get("fpl_mode") == "live")
        if is_current:
            download_current(filepath, url)
        else:
            download_if_missing(filepath, url)

        # utf-8-sig strips the BOM that football-data.co.uk prepends
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        df = df.assign(Season=season_label)
        print(f"  {season_label}: {len(df)} matches, {len(df.columns)} columns")
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    total_raw_cols = len(df.columns)
    print(f"\nTotal raw records: {len(df)}")
    print(f"Total raw columns: {total_raw_cols}")

    # -- STEP 2: Drop Irrelevant Columns -----------------------------------
    # ~96 columns are betting odds from various bookmakers. They add noise
    # and are irrelevant to match performance analysis.
    available = [c for c in KEEP_COLUMNS if c in df.columns]
    missing = [c for c in KEEP_COLUMNS if c not in df.columns]
    if missing:
        print(f"  Note: columns not in all files (filled later): {missing}")

    df = df[available + ['Season']]
    dropped = total_raw_cols - len(df.columns)
    print(f"\nDropped {dropped} betting/odds columns")
    print(f"Keeping {len(df.columns)} columns")

    # -- STEP 3: Fix Date Formats ------------------------------------------
    # Some files use DD/MM/YYYY, others DD/MM/YY. Standardize to ISO 8601
    # so sorting and grouping by date work correctly.
    df['Date'] = df['Date'].apply(parse_date)
    date_nulls = df['Date'].isna().sum()
    if date_nulls > 0:
        print(f"\n  WARNING: {date_nulls} dates could not be parsed -- dropping those rows")
        df = df.dropna(subset=['Date'])
    else:
        print(f"\nAll dates parsed successfully")

    # -- STEP 4: Standardize Team Names ------------------------------------
    # football-data.co.uk uses abbreviations ("Man United", "Wolves") that
    # break merges with FPL and Understat. Map to canonical full names.
    df['HomeTeam'] = df['HomeTeam'].replace(FOOTBALL_DATA_NAME_MAP)
    df['AwayTeam'] = df['AwayTeam'].replace(FOOTBALL_DATA_NAME_MAP)

    all_teams = sorted(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique()))
    print(f"\nTeams found across all seasons: {len(all_teams)}")
    for t in all_teams:
        print(f"  - {t}")

    # -- STEP 5: Handle Nulls in Stat Columns ------------------------------
    # Goals cannot be imputed -- a null goal column means bad data.
    # Peripheral stats (corners, cards) null likely means "not recorded".
    for col in GOAL_COLS:
        if col in df.columns:
            nulls = df[col].isna().sum()
            if nulls > 0:
                print(f"\n  Dropping {nulls} rows with null {col}")
                df = df.dropna(subset=[col])

    peripheral = [c for c in STAT_COLS if c not in GOAL_COLS and c in df.columns]
    null_counts = {}
    for col in peripheral:
        n = df[col].isna().sum()
        if n > 0:
            null_counts[col] = n
            df[col] = df[col].fillna(0)

    print(f"\nNull check on match stats:")
    if null_counts:
        for col, n in null_counts.items():
            print(f"  {col}: {n} nulls (filled with 0)")
    else:
        print("  No nulls found in stat columns")

    # Convert stat columns to int after filling
    for col in STAT_COLS:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # -- STEP 6: Referee Cleanup -------------------------------------------
    # Trailing whitespace creates duplicate entries in aggregations
    if 'Referee' in df.columns:
        df['Referee'] = df['Referee'].fillna('Unknown').str.strip()
        unique_refs = df['Referee'].nunique()
        print(f"\nUnique referees: {unique_refs}")

    # Fill missing Time values
    if 'Time' in df.columns:
        df['Time'] = df['Time'].fillna('').str.strip()

    # -- STEP 7: Rename Columns --------------------------------------------
    # Cryptic abbreviations hurt readability for portfolio reviewers.
    df = df.rename(columns=RENAME_MAP)
    df = df.rename(columns={'Season': 'season'})

    # -- STEP 8: Add Derived Columns ---------------------------------------
    # These aggregations save repeated computation in the transform script
    # and are the most commonly queried metrics in match analysis.
    df['total_goals'] = df['home_goals'] + df['away_goals']
    df['total_shots'] = df['home_shots'] + df['away_shots']
    df['total_fouls'] = df['home_fouls'] + df['away_fouls']
    df['total_cards'] = (df['home_yellows'] + df['away_yellows']
                         + df['home_reds'] + df['away_reds'])
    df['match_id'] = range(1, len(df) + 1)

    # Reorder so match_id and season come first
    col_order = ['match_id', 'season', 'date', 'time',
                 'home_team', 'away_team',
                 'home_goals', 'away_goals', 'result',
                 'ht_home_goals', 'ht_away_goals', 'ht_result',
                 'referee',
                 'home_shots', 'away_shots',
                 'home_shots_on_target', 'away_shots_on_target',
                 'home_fouls', 'away_fouls',
                 'home_corners', 'away_corners',
                 'home_yellows', 'away_yellows',
                 'home_reds', 'away_reds',
                 'total_goals', 'total_shots', 'total_fouls', 'total_cards']
    df = df[[c for c in col_order if c in df.columns]]

    # -- SAVE --------------------------------------------------------------
    output_path = os.path.join(CLEAN_DIR, 'matches_clean.csv')
    df.to_csv(output_path, index=False)

    print(f"\nFinal cleaned dataset: {len(df)} matches, {len(df.columns)} columns")
    print(f"\nSaved: {output_path}")
    print("Cleaning complete.")


if __name__ == '__main__':
    main()
