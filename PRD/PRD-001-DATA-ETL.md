# PRD-001: Raw Data Extraction & Cleansing

## Feature Summary

Download raw EPL match CSV files from football-data.co.uk, clean them, standardize formats, and produce a consistent cleaned dataset. This is the foundation of the entire pipeline.

**Priority:** P0 (Must Have)
**Script:** `scripts/01_clean.py`
**Input:** `data/raw/matches_2425.csv`, `data/raw/matches_2324.csv`, `data/raw/matches_2223.csv`
**Output:** `data/cleaned/matches_clean.csv`

---

## Data Source

URL pattern: `https://www.football-data.co.uk/mmz4281/{code}/E0.csv` (replace `{code}` with season code from config.py)

The script imports `ACTIVE_SEASONS` from `scripts/config.py` and loops over all configured seasons. It does NOT have a hardcoded list of files. To add a new season (e.g., 2025-26), add one entry to config.py -- this script handles it automatically.

The script should download these files programmatically if they don't exist in `data/raw/`. If they already exist, skip the download and use the local copies. This allows offline development and avoids hammering the source site.

During a live season, the current season's CSV updates twice weekly on football-data.co.uk. Running the script again re-downloads the latest version, which now contains new matches since last run. Previous season CSVs are static and won't change.

---

## Raw Data Characteristics (Known Issues to Handle)

1. **BOM character.** Files start with a UTF-8 Byte Order Mark that prepends to the first column name. Use `encoding='utf-8-sig'` when reading.

2. **120 columns per file.** Only 24 contain actual match statistics. The other 96 are betting odds from B365, BW, BF, PS, WH, 1XB and their derivatives (closing odds, Asian handicap, over/under). Drop all betting columns.

3. **Column headers are cryptic abbreviations:**
   - FTHG = Full Time Home Goals
   - FTAG = Full Time Away Goals
   - FTR = Full Time Result (H/D/A)
   - HTHG/HTAG = Half Time Home/Away Goals
   - HTR = Half Time Result
   - HS/AS = Home/Away Shots
   - HST/AST = Home/Away Shots on Target
   - HF/AF = Home/Away Fouls
   - HC/AC = Home/Away Corners
   - HY/AY = Home/Away Yellow Cards
   - HR/AR = Home/Away Red Cards
   Rename ALL of these to human-readable names.

4. **Date format inconsistency.** Some files use DD/MM/YYYY, others use DD/MM/YY. Standardize to YYYY-MM-DD (ISO 8601).

5. **Team name abbreviations.** Source uses shortened names. Import `FOOTBALL_DATA_NAME_MAP` from config.py and apply to both HomeTeam and AwayTeam columns. The canonical mappings are:
   - "Man United" -> "Manchester United"
   - "Man City" -> "Manchester City"
   - "Nott'm Forest" -> "Nottingham Forest"
   - "Tottenham" -> "Tottenham Hotspur"
   - "Newcastle" -> "Newcastle United"
   - "West Ham" -> "West Ham United"
   - "Wolves" -> "Wolverhampton"
   - "Luton" -> "Luton Town"
   - "Leicester" -> "Leicester City"

6. **Potential nulls in stat columns.** Check all numeric columns. If goals columns are null, drop the row (can't impute goals). If peripheral stats (corners, cards) are null, fill with 0.

7. **Referee name whitespace.** Some entries have trailing spaces causing duplicate entries in aggregations. Strip all whitespace.

8. **Inconsistent column counts across seasons.** 2024-25 has 120 columns, older files have 107. The 13 extra columns are additional betting exchange data. Since we drop all betting columns, this inconsistency is handled automatically.

---

## Output Schema (matches_clean.csv)

| Column | Type | Description |
|---|---|---|
| match_id | int | Sequential ID (1 to N) |
| season | string | "2024-25", "2023-24", "2022-23" |
| date | string | YYYY-MM-DD |
| time | string | HH:MM |
| home_team | string | Full team name |
| away_team | string | Full team name |
| home_goals | int | Full time home goals |
| away_goals | int | Full time away goals |
| result | string | H, D, or A |
| ht_home_goals | int | Half time home goals |
| ht_away_goals | int | Half time away goals |
| ht_result | string | H, D, or A |
| referee | string | Referee name |
| home_shots | int | |
| away_shots | int | |
| home_shots_on_target | int | |
| away_shots_on_target | int | |
| home_fouls | int | |
| away_fouls | int | |
| home_corners | int | |
| away_corners | int | |
| home_yellows | int | |
| away_yellows | int | |
| home_reds | int | |
| away_reds | int | |
| total_goals | int | Derived: home_goals + away_goals |
| total_shots | int | Derived: home_shots + away_shots |
| total_fouls | int | Derived: home_fouls + away_fouls |
| total_cards | int | Derived: sum of all yellows + reds |

---

## Console Output Requirements

The script must print a clear log of every action taken:
- How many rows and columns loaded per file
- How many columns dropped
- How many dates parsed/failed
- How many team names remapped
- Null check results per column
- Final row/column count
- File saved confirmation

This output serves as a verification step and looks professional in a terminal screenshot for the portfolio.

---

## Acceptance Criteria

- [ ] Script runs without errors: `python scripts/01_clean.py`
- [ ] Script imports seasons and name maps from config.py (no hardcoded seasons in the script)
- [ ] Output file has exactly 1,140 rows for 3 complete seasons (380 per season x 3). For a live season with N matches, output has (380 x completed_seasons) + N rows.
- [ ] Output file has 29 columns
- [ ] All dates are in YYYY-MM-DD format
- [ ] All team names are proper full names (no abbreviations)
- [ ] No null values in goal columns
- [ ] Column names are human-readable English (no abbreviations)
- [ ] Script works if raw files already exist (no re-download)
- [ ] Script downloads raw files if they don't exist in data/raw/
- [ ] Adding a new season to config.py causes the script to download and process it without any code changes
