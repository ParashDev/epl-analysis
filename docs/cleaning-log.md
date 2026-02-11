# Cleaning Decision Log

Every data cleaning choice documented with reasoning.

---

## Decision 01: Strip UTF-8 BOM

**What:** Read CSV files with `encoding='utf-8-sig'` to strip the byte-order mark from the first column header.
**Why:** football-data.co.uk CSVs prepend a BOM character to the file. Without stripping it, the first column is named `\ufeffDiv` instead of `Div`, which breaks column lookups downstream.
**Impact:** All rows affected (1,390). First column name corrected across all 4 season files.

---

## Decision 02: Drop 96 Betting Columns

**What:** Kept only 24 match-relevant columns from the original 107-133 (varies by season). Dropped all columns matching betting exchange prefixes (B365, BW, BF, IW, PS, WH, VC, Max, Avg, etc.).
**Why:** 96+ columns are bookmaker odds from 7+ betting exchanges. They are irrelevant to match performance analysis and inflate file size without analytical value. New exchanges get added each season (2022-23 has 107 columns, 2025-26 has 133).
**Impact:** Column count reduced to 24 retained columns. Zero rows affected. No data loss for match analysis.

---

## Decision 03: Standardize Date Formats

**What:** Parsed dates with `dayfirst=True` and converted all to ISO 8601 format (YYYY-MM-DD).
**Why:** football-data.co.uk uses DD/MM/YYYY in some seasons and DD/MM/YY in others. Inconsistent formats break date sorting and time-series analysis. ISO 8601 is unambiguous and sorts lexicographically.
**Impact:** All 1,390 rows. No data loss. Dates now sort correctly across 4 seasons.

---

## Decision 04: Standardize Team Names

**What:** Applied a canonical name map to convert abbreviations: `Man United` to `Manchester United`, `Nott'm Forest` to `Nottingham Forest`, `Tottenham` to `Tottenham Hotspur`, `Wolves` to `Wolverhampton`, etc.
**Why:** football-data.co.uk uses abbreviated team names that differ from FPL API and Understat names. Cross-source merges fail silently when "Man United" in match data cannot match "Manchester United" in player data. A single canonical map in config.py ensures consistency.
**Impact:** ~380 rows per mapped team across home_team and away_team columns. No rows dropped. Enables clean joins with FPL and xG data.

---

## Decision 05: Strip Referee Name Whitespace

**What:** Applied `.str.strip()` to the Referee column.
**Why:** Some referee names contain trailing whitespace (e.g., `"A Taylor "` vs `"A Taylor"`), creating duplicate entries in groupby operations. A referee card-rate analysis would incorrectly split one referee into two.
**Impact:** ~20-30 rows with trailing whitespace corrected. Referee unique count reduced from ~24 to ~22 after deduplication.

---

## Decision 06: Rename Columns to Snake Case

**What:** Renamed all columns from football-data.co.uk originals (`HomeTeam`, `FTHG`, `HS`) to descriptive snake_case (`home_team`, `full_time_home_goals`, `home_shots`).
**Why:** Original column names are cryptic abbreviations (FTHG = Full Time Home Goals, HST = Home Shots on Target). Snake_case names are self-documenting and follow Python conventions. Anyone reading the cleaned CSV can understand the data without a codebook.
**Impact:** All 24 retained columns renamed. Zero data loss.

---

## Decision 07: Handle Null Values

**What:** Forward-filled missing referee names. Filled missing numeric columns (shots, fouls, cards, corners) with 0.
**Why:** A small number of matches have missing referee or card data. Dropping these rows would lose match results. Forward-fill for referees assumes the same ref officiated (reasonable for same-day fixtures). Zero-fill for stats is conservative -- it underreports rather than creates false data.
**Impact:** ~5-10 rows with partial nulls preserved instead of dropped. No rows lost.

---

## Decision 08: Add Derived Columns

**What:** Added 5 derived columns: `total_goals`, `total_shots`, `total_fouls`, `total_cards`, `match_id`.
**Why:** These aggregates are used repeatedly in transform calculations. Pre-computing them avoids repeated `home_X + away_X` arithmetic in 02_transform.py and makes the cleaned CSV independently useful for ad-hoc analysis.
**Impact:** 5 new columns added, bringing total to 29. All 1,390 rows populated.

---

## Decision 09: FPL Team Name Mapping

**What:** Applied FPL_NAME_MAP in 03_fetch_fpl.py to convert FPL API team names to canonical form.
**Why:** FPL uses different names than football-data.co.uk (e.g., `Spurs` vs `Tottenham Hotspur`, `Wolves` vs `Wolverhampton`). Without mapping, player data cannot be joined to match data by team name.
**Impact:** All 817 player rows. Team names now match matches_clean.csv canonical names.

---

## Decision 10: Understat Team Name Mapping

**What:** Applied UNDERSTAT_NAME_MAP in 04_fetch_xg.py. Understat uses underscores in multi-word names.
**Why:** Understat formats names like `Manchester_United` and `Wolverhampton_Wanderers`. These must match the canonical `Manchester United` and `Wolverhampton` used in match data.
**Impact:** All 20 team rows in xg_teams.csv and ~511 player rows in xg_players.csv.

---

## Decision 11: Drop xG Players with Missing Names

**What:** Added `dropna(subset=['player_name'])` when processing xG player data.
**Why:** Understat data contains ~10 entries with NaN player names (likely placeholder or aggregation artifacts). These produce literal `NaN` in JSON output, which JavaScript's `JSON.parse` cannot handle -- it crashes the entire dashboard.
**Impact:** ~10 rows dropped from xg_players.csv. No meaningful data lost.

---

## Decision 12: Graceful Degradation for Missing Sources

**What:** 02_transform.py loads FPL and xG CSVs with `try/except FileNotFoundError`, setting boolean flags (`has_fpl`, `has_xg`) for conditional aggregation.
**Why:** The pipeline must work with only match data. If FPL or Understat APIs are down, or the user skips those scripts, the dashboard should still render all base charts. Crashing on a missing optional file would break the entire pipeline for a non-critical enrichment.
**Impact:** Zero rows lost. Dashboard renders 7 base charts without enrichment, 14+ sections with all enrichment sources available.

---

## Summary

| Metric | Value |
|---|---|
| Input rows (4 seasons) | 1,390 |
| Output rows | 1,390 |
| Rows dropped | 0 |
| Input columns (widest season) | 133 |
| Output columns | 29 |
| Columns dropped | 96+ |
| Columns added (derived) | 5 |
