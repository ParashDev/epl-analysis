# FRD-001: Data ETL Pipeline - Functional Specification

## Script: `scripts/01_clean.py`

---

## Input Specification

### Source files (auto-download if missing):

Defined in `scripts/config.py` as `ACTIVE_SEASONS`. Each entry has a `code` field used to construct the download URL. The script loops over all configured seasons.

| Season | Code | URL | Expected Rows | Expected Cols |
|---|---|---|---|---|
| 2024-25 | 2425 | https://www.football-data.co.uk/mmz4281/2425/E0.csv | 380 (complete) | 120 |
| 2023-24 | 2324 | https://www.football-data.co.uk/mmz4281/2324/E0.csv | 380 (complete) | 107 |
| 2022-23 | 2223 | https://www.football-data.co.uk/mmz4281/2223/E0.csv | 380 (complete) | 107 |
| 2025-26 | 2526 | https://www.football-data.co.uk/mmz4281/2526/E0.csv | 0-380 (live) | ~120 |

The 2025-26 row only appears when added to config.py. During a live season, the CSV grows as matches are played. Row count varies.

### Auto-download logic:

```python
from config import ACTIVE_SEASONS, FOOTBALL_DATA_URL, FOOTBALL_DATA_NAME_MAP
import os
import requests

def download_if_missing(filepath, url):
    if os.path.exists(filepath):
        print(f"  Using cached: {filepath}")
        return
    print(f"  Downloading: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(response.content)

# For live season: always re-download current season CSV to get latest matches
def download_current_season(filepath, url):
    """Always download (not cached) for the live/current season."""
    print(f"  Downloading latest: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        f.write(response.content)
```

For live seasons, the current season CSV must be re-downloaded every run (not cached) because it grows weekly. Historical season CSVs are cached and never re-downloaded.

---

## Processing Steps (in order)

### Step 1: Load CSVs
- Import `ACTIVE_SEASONS` and `CURRENT_SEASON` from config.py
- Loop over `ACTIVE_SEASONS` to download/load each season's CSV
- Read with `encoding='utf-8-sig'` to strip BOM
- Add a `Season` column to each dataframe before concatenating
- For the current season in live mode: re-download (not cache) to get latest matches
- For historical seasons: use cached files
- Concatenate all seasons into one dataframe

### Step 2: Column Selection
Retain only these 24 columns from the raw data:
```
Div, Date, Time, HomeTeam, AwayTeam, FTHG, FTAG, FTR,
HTHG, HTAG, HTR, Referee, HS, AS, HST, AST, HF, AF,
HC, AC, HY, AY, HR, AR
```
Drop everything else (all B365*, BW*, BF*, PS*, WH*, 1XB*, Max*, Avg*, BFE*, P*, AH* columns).

### Step 3: Date Parsing
```python
# Try DD/MM/YYYY first, fall back to DD/MM/YY
for fmt in ['%d/%m/%Y', '%d/%m/%y']:
    try:
        return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
    except ValueError:
        continue
return None  # track failures
```
Drop rows where date parsing fails. Log count.

### Step 4: Team Name Mapping
Import `FOOTBALL_DATA_NAME_MAP` from config.py. Apply to both HomeTeam and AwayTeam columns:

```python
TEAM_NAME_MAP = {
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Nott'm Forest": "Nottingham Forest",
    "Tottenham": "Tottenham Hotspur",
    "Newcastle": "Newcastle United",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton",
    "Luton": "Luton Town",
    "Leicester": "Leicester City",
    "Sheffield United": "Sheffield United",  # no change but explicit
}
```

### Step 5: Null Handling
- Check all 16 numeric stat columns for nulls
- If home_goals or away_goals are null: DROP the row (cannot impute)
- If other stats are null: fill with 0 (likely means "not recorded")
- Convert all stat columns to int after filling

### Step 6: Referee Cleanup
- Strip whitespace from all referee names
- Fill empty referee fields with "Unknown"

### Step 7: Column Rename

```python
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
    'Date': 'date', 'Time': 'time', 'Referee': 'referee', 'Season': 'season',
}
```

### Step 8: Derived Columns
```python
df['total_goals'] = df['home_goals'] + df['away_goals']
df['total_shots'] = df['home_shots'] + df['away_shots']
df['total_fouls'] = df['home_fouls'] + df['away_fouls']
df['total_cards'] = df['home_yellows'] + df['away_yellows'] + df['home_reds'] + df['away_reds']
df['match_id'] = range(1, len(df) + 1)
```

---

## Output Specification

**File:** `data/cleaned/matches_clean.csv`
**Encoding:** UTF-8 (no BOM)
**Delimiter:** Comma
**Header:** Yes (first row)
**Index:** No

Expected: 1,140 rows, 29 columns for 3 complete seasons. For a live 4th season with N matches played, expect 1,140 + N rows.

---

## Console Output Format

```
Loading raw match data...
  2024-25: 380 matches, 120 columns
  2023-24: 380 matches, 107 columns
  2022-23: 380 matches, 107 columns

Total raw records: 1140
Total raw columns: 133

Dropped 109 betting/odds columns
Keeping 24 match stat columns

All dates parsed successfully

Teams found across all seasons: 24
  - Arsenal
  - Aston Villa
  ...

Null check on match stats:
  No nulls found in stat columns

Unique referees: 33

Final cleaned dataset: 1140 matches, 29 columns

Saved: data/cleaned/matches_clean.csv
Cleaning complete.
```
