# FRD-005: GitHub Actions CI/CD - Functional Specification

## File: `.github/workflows/update.yml`

---

## Workflow Specification

```yaml
name: Update EPL Data

on:
  schedule:
    - cron: '0 8 * * 1'    # Monday 8am UTC
  workflow_dispatch:         # Manual trigger

jobs:
  update-data:
    runs-on: ubuntu-latest
    permissions:
      contents: write        # Needed to push commits

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Clean raw data
        run: python scripts/01_clean.py

      - name: Fetch FPL player data
        run: python scripts/03_fetch_fpl.py
        continue-on-error: true

      - name: Fetch xG data
        run: python scripts/04_fetch_xg.py
        continue-on-error: true

      - name: Transform and merge
        run: python scripts/02_transform.py

      - name: Commit updated data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --cached --quiet || git commit -m "data: auto-update $(date +%Y-%m-%d)"
          git push
```

---

## Behavior Rules

| Scenario | Expected Behavior |
|---|---|
| All scripts succeed | Data committed, dashboard updated |
| FPL fetch fails | Pipeline continues, base data still updated |
| Understat fetch fails | Pipeline continues, base data still updated |
| No data changed | No commit created (clean git history) |
| Clean script fails | Job fails (this is a critical error) |
| Transform script fails | Job fails (this is a critical error) |

---

## Verification

After enabling, check:
- Actions tab shows workflow listed
- Manual trigger button works
- Commit appears with bot identity
- No commit when data unchanged
