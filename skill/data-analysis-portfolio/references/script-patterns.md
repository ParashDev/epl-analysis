# Script Patterns Reference

Templates and conventions for all Python scripts in a data analysis portfolio project.

## Global Standards

### Config Import Convention

ALL scripts import their configuration from `scripts/config.py`. No script contains hardcoded seasons, URLs, or team name maps.

```python
# Every script starts with this:
import os
import sys

# Add scripts directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    ACTIVE_SEASONS, CURRENT_SEASON,
    FOOTBALL_DATA_URL, FOOTBALL_DATA_NAME_MAP,  # for 01_clean.py
    # FPL_GITHUB_BASE, FPL_LIVE_API, FPL_NAME_MAP,  # for 03_fetch_fpl.py
    # UNDERSTAT_NAME_MAP,  # for 04_fetch_xg.py
)
```

### File Path Convention

All scripts use relative paths from project root. No hardcoded absolute paths.

```python
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)
```

### Error Handling Standard

```python
import sys

def main():
    try:
        # script logic
        pass
    except FileNotFoundError as e:
        print(f"ERROR: Required file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected failure: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

- Network errors = WARNINGS (don't crash, allow pipeline to continue)
- File system errors = ERRORS (crash with clear message)
- Missing dependencies = ERRORS (crash with install instructions)

### Dependency Check Pattern

```python
try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas is required. Run: pip install pandas")
    sys.exit(1)
```

### CSV Output Standard

- UTF-8 encoding (no BOM on output)
- Comma delimiter
- First row is header
- No index column (`index=False`)
- Floats rounded to 2 decimal places
- Dates in YYYY-MM-DD format

### JSON Output Standard

- UTF-8 encoding
- 2-space indentation
- Null for missing optional sections (do not omit the key)
- Integers where possible, floats to 2 decimal places

---

## 01_clean.py Template

```python
"""
01_clean.py - Data Cleansing Script
{Project Name}

Source: {URL}
Raw files have {N} columns. Most are {description of irrelevant columns}.
We keep {N} columns that describe {what matters}.

Run: python scripts/01_clean.py
"""

import pandas as pd
import os
import sys
import requests
from datetime import datetime

# ── CONFIGURATION ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)

# Sources to download if not cached locally
SOURCES = {
    'file_a.csv': 'https://example.com/data/file_a.csv',
}

# Canonical entity name mapping (source name -> proper name)
NAME_MAP = {
    "Abbrev Name": "Full Proper Name",
}

# Columns to keep from raw data (drop everything else)
KEEP_COLUMNS = ['Col1', 'Col2', 'Col3']

# Human-readable column renames
RENAME_MAP = {
    'Col1': 'readable_name_1',
    'Col2': 'readable_name_2',
}


def download_if_missing(filepath, url):
    """Download source file if not already cached locally."""
    if os.path.exists(filepath):
        print(f"  Using cached: {os.path.basename(filepath)}")
        return
    print(f"  Downloading: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        f.write(response.content)


def main():
    print("Loading raw data...")

    # ── STEP 1: Download + Load ────────────────
    # Comment: WHY we download (reproducibility, offline dev)
    frames = []
    for filename, url in SOURCES.items():
        filepath = os.path.join(RAW_DIR, filename)
        download_if_missing(filepath, url)
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        print(f"  {filename}: {len(df)} rows, {len(df.columns)} columns")
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    print(f"\nTotal raw: {len(df)} rows, {len(df.columns)} columns")

    # ── STEP 2: Drop Irrelevant Columns ────────
    # Comment: WHY these columns are irrelevant to the analysis
    df = df[KEEP_COLUMNS]
    print(f"Kept {len(df.columns)} columns")

    # ── STEP 3: Fix Date Formats ───────────────
    # Comment: WHY dates are inconsistent and what format we standardize to

    # ── STEP 4: Standardize Names ──────────────
    # Comment: WHY source uses abbreviations that break merges
    df['entity_column'] = df['entity_column'].replace(NAME_MAP)

    # ── STEP 5: Handle Nulls ──────────────────
    # Comment: WHY we drop vs impute for each column type

    # ── STEP 6: Rename Columns ─────────────────
    # Comment: WHY cryptic abbreviations hurt readability for portfolio reviewers
    df = df.rename(columns=RENAME_MAP)

    # ── STEP 7: Add Derived Columns ────────────
    # Comment: WHY these derived metrics add analytical value

    # ── SAVE ───────────────────────────────────
    output_path = os.path.join(CLEAN_DIR, 'data_clean.csv')
    df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path}")
    print(f"Final: {len(df)} rows, {len(df.columns)} columns")
    print("Cleaning complete.")


if __name__ == '__main__':
    main()
```

---

## 02_transform.py Template

```python
"""
02_transform.py - Data Transformation & Aggregation

Takes cleaned CSV(s) and produces aggregated JSON for the dashboard.
Optional enrichment sources are loaded if available, skipped if not.

Run: python scripts/02_transform.py
"""

import pandas as pd
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data')

# ── LOAD REQUIRED DATA ─────────────────────
df = pd.read_csv(os.path.join(CLEAN_DIR, 'data_clean.csv'))
print(f"Loaded primary data: {len(df)} rows")

# ── LOAD OPTIONAL ENRICHMENT DATA ──────────
has_source_b = False
source_b = None
try:
    source_b = pd.read_csv(os.path.join(CLEAN_DIR, 'source_b.csv'))
    has_source_b = True
    print(f"Loaded source B: {len(source_b)} rows")
except FileNotFoundError:
    print("Source B not available -- skipping enrichment")

# ── BASE AGGREGATIONS (always computed) ────
# Build each section as a list of dicts or a dict

# ── CONDITIONAL AGGREGATIONS ───────────────
optional_section = None
if has_source_b:
    optional_section = []  # build from source_b

# ── EXPORT ─────────────────────────────────
output = {
    'generated_at': pd.Timestamp.now().isoformat(),
    # required sections...
    # optional sections (null if not available)
    'optional_section': optional_section,
}

output_path = os.path.join(OUTPUT_DIR, 'dashboard_data.json')
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2, default=str)

print(f"\nSaved: {output_path}")
print("Transform complete.")
```

---

## 03_fetch_{source}.py Template

```python
"""
03_fetch_{source_name}.py - Fetch {Source Name} Data

Enriches the primary dataset with {what this source adds}.
If this script fails or is never run, the pipeline still works.

Run: python scripts/03_fetch_{source_name}.py
"""

import requests
import pandas as pd
import time
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
os.makedirs(CLEAN_DIR, exist_ok=True)

REQUEST_DELAY = 1.0  # seconds between API calls

# Canonical name mapping for this source
SOURCE_NAME_MAP = {
    "Source Form": "Canonical Form",
}


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


def normalize_name(name):
    """Convert source-specific name to canonical form."""
    return SOURCE_NAME_MAP.get(name, name)


def main():
    print(f"Fetching {source_name} data...")

    # Fetch, process, normalize names, save CSVs
    # Always add time.sleep(REQUEST_DELAY) between requests

    print("Fetch complete.")


if __name__ == '__main__':
    main()
```

---

## Console Output Best Practices

Scripts should print clear, structured output suitable for terminal screenshots:

```
Loading raw data...
  2024-25: 380 rows, 120 columns
  2023-24: 380 rows, 107 columns

Total raw: 1140 rows, 133 columns

Dropped 109 irrelevant columns
Keeping 24 match stat columns

Date parsing: 1140/1140 successful

Name standardization: 10 mappings applied

Null check:
  home_goals: 0 nulls
  away_goals: 0 nulls
  (all clear)

Final: 1140 rows, 29 columns
Saved: data/cleaned/matches_clean.csv
Cleaning complete.
```
