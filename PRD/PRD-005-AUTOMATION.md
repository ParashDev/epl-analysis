# PRD-005: GitHub Actions Automation

## Feature Summary

Automate the data pipeline to run weekly using GitHub Actions. During a live season, this keeps the dashboard up to date without manual intervention. For a completed season, it serves as proof that the author thinks about production deployment, not just one-off analysis.

**How it works with live season mode:** When `scripts/config.py` has `CURRENT_SEASON` set to a live season (e.g., 2025-26 with `fpl_mode: "live"`), the weekly cron triggers the full pipeline. The 01_clean.py script re-downloads the current season CSV from football-data.co.uk (which now has new matches since last week). The FPL and xG fetch scripts pull fresh data from live APIs. The transform script rebuilds dashboard_data.json with updated stats. The workflow commits the new JSON back to the repo. GitHub Pages serves the updated dashboard automatically.

**For a completed season** (e.g., 2024-25 with `fpl_mode: "historical"`), the cron still runs but produces identical output. The `git diff --cached --quiet` check detects no changes and skips the commit. No wasted commits, clean history.

**Priority:** P2 (Nice to Have)
**File:** `.github/workflows/update.yml`

---

## Trigger Conditions

1. **Scheduled:** Every Monday at 8:00 AM UTC (`cron: '0 8 * * 1'`)
   - Monday because all weekend EPL matches will be complete
   - 8 AM UTC gives time for football-data.co.uk and Understat to update

2. **Manual:** `workflow_dispatch` -- allows triggering from the GitHub Actions UI with a button click

---

## Workflow Steps

```yaml
name: Update EPL Data

on:
  schedule:
    - cron: '0 8 * * 1'
  workflow_dispatch:

jobs:
  update-data:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run cleaning pipeline
        run: python scripts/01_clean.py

      - name: Fetch FPL data
        run: python scripts/03_fetch_fpl.py
        continue-on-error: true

      - name: Fetch xG data
        run: python scripts/04_fetch_xg.py
        continue-on-error: true

      - name: Run transformation
        run: python scripts/02_transform.py

      - name: Commit and push if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --cached --quiet || git commit -m "data: auto-update $(date +%Y-%m-%d)"
          git push
```

---

## Key Design Decisions

1. **`continue-on-error: true`** on fetch scripts. If FPL API or Understat is down, the pipeline should still complete with existing/cached data. The transform script handles missing files gracefully.

2. **Only commit data/ directory.** Scripts and HTML don't change during auto-updates. Only data files get committed.

3. **Conditional commit.** `git diff --cached --quiet || git commit` means: if nothing changed, don't create an empty commit. This keeps the git history clean.

4. **Bot identity for commits.** Uses the standard GitHub Actions bot identity so it is clear these commits are automated.

---

## Acceptance Criteria

- [ ] Workflow file is valid YAML and passes GitHub Actions syntax check
- [ ] Manual trigger works from GitHub Actions UI
- [ ] Pipeline completes even if FPL or Understat fetch fails
- [ ] Only data/ files are committed
- [ ] No empty commits when data hasn't changed
- [ ] Commit message includes the date
