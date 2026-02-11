# Step-by-Step: From Zero to Live Dashboard

Everything you need to do, in order, with every command. Nothing skipped.

---

## Prerequisites (One-Time Setup)

### 1. Install Python

Check if you already have it:

```
python --version
```

You need 3.11 or higher. If not installed, download from https://www.python.org/downloads/

On Windows, during installation check "Add Python to PATH".

### 2. Install Git

Check if you already have it:

```
git --version
```

If not installed: https://git-scm.com/downloads

### 3. Install Claude Code

```
npm install -g @anthropic-ai/claude-code
```

If you don't have npm/Node.js: https://nodejs.org/ (install LTS version first, then run the command above)

### 4. Create a GitHub Account (if you don't have one)

Go to https://github.com/signup

### 5. Set Up GitHub Authentication

You need Git to be able to push to GitHub. The easiest way:

```
gh auth login
```

If you don't have the GitHub CLI (`gh`), install it: https://cli.github.com/

Alternatively, set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

## Phase 1: Create the GitHub Repo

### 6. Create a new repo on GitHub

Go to https://github.com/new

```
Repository name:  epl-analysis
Description:      EPL 2024-25 Season Data Analysis — ETL Pipeline + Interactive Dashboard
Public:           Yes (required for free GitHub Pages)
Initialize:       Do NOT check "Add a README" (we'll create our own)
```

Click "Create repository". You'll see an empty repo page. Leave this tab open.

### 7. Clone the empty repo to your machine

Open your terminal (Command Prompt, PowerShell, or Terminal):

```bash
cd ~/Documents            # or wherever you keep projects
git clone https://github.com/YOUR_USERNAME/epl-analysis.git
cd epl-analysis
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Phase 2: Add the Documentation

### 8. Unzip the docs into the project

Copy the `epl-project-docs-v2.zip` file into the `epl-analysis` folder, then:

**Mac/Linux:**
```bash
unzip epl-project-docs-v2.zip
mv epl-project-docs-v2/* .
mv epl-project-docs-v2/.* . 2>/dev/null
rmdir epl-project-docs-v2
rm epl-project-docs-v2.zip
```

**Windows (PowerShell):**
```powershell
Expand-Archive epl-project-docs-v2.zip -DestinationPath .
Move-Item epl-project-docs-v2\* . -Force
Remove-Item epl-project-docs-v2 -Recurse
Remove-Item epl-project-docs-v2.zip
```

### 9. Verify the structure

```bash
ls -la
```

You should see:
```
PROMPT.md
PRD/
FRD/
skill/
```

These are the instruction files. Claude Code will read them and build the actual project.

---

## Phase 3: Build the Project with Claude Code

### 10. Install the skill (optional but recommended)

This lets Claude Code auto-discover the skill in future projects too:

**Mac/Linux:**
```bash
mkdir -p ~/.claude/skills
cp -r skill/data-analysis-portfolio ~/.claude/skills/
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"
Copy-Item -Recurse skill\data-analysis-portfolio "$env:USERPROFILE\.claude\skills\"
```

### 11. Start Claude Code

```bash
claude
```

This opens the Claude Code interactive session in your terminal.

### 12. Give Claude Code the build instruction

Type this (or paste it) into Claude Code:

```
Read PROMPT.md and execute all phases in order. Read the skill file at
skill/data-analysis-portfolio/SKILL.md first for methodology, then all PRD
files, then all FRD files before writing any code. Build config.py first.
After each phase, verify the output before moving to the next phase.
```

Then let Claude Code work. It will:

1. Read all your docs (takes ~30 seconds)
2. Create `scripts/config.py`
3. Create `scripts/01_clean.py` and run it
4. Create `scripts/02_transform.py` and run it
5. Create `index.html` (the dashboard)
6. Create `scripts/03_fetch_fpl.py` and run it
7. Create `scripts/04_fetch_xg.py` and run it
8. Update `02_transform.py` with enrichment data and rerun
9. Update `index.html` with xG and player charts
10. Create all documentation files
11. Create `.github/workflows/update.yml`
12. Create `requirements.txt` and `.gitignore`

This takes 10-20 minutes depending on API speed. Claude Code will ask for permission to run commands -- approve them.

### 13. If Claude Code stops mid-way or hits an error

Just tell it:

```
Continue from where you left off. We were on Phase X.
```

Or if a specific script has a bug:

```
The 04_fetch_xg.py script failed with [error message]. Fix it and continue.
```

---

## Phase 4: Test Locally

### 14. Run the full pipeline manually (to verify)

After Claude Code finishes, exit the Claude Code session and run:

```bash
pip install -r requirements.txt
python scripts/01_clean.py
python scripts/03_fetch_fpl.py
python scripts/04_fetch_xg.py
python scripts/02_transform.py
```

You should see output like:
```
Loading raw match data...
  2024-25: 380 matches, 120 columns
  2023-24: 380 matches, 107 columns
  2022-23: 380 matches, 107 columns
...
Saved: data/cleaned/matches_clean.csv
Cleaning complete.
```

### 15. Start a local web server

```bash
python -m http.server 8000
```

### 16. Open the dashboard in your browser

Go to: http://localhost:8000

You should see:
- Dark themed dashboard
- League table with Liverpool at the top
- Charts rendering (points race, monthly goals, home/away, referees, scorelines)
- If xG data loaded: scatter plot, xG justice table, top scorers chart

### 17. Test graceful degradation

Stop the server (Ctrl+C), delete the enrichment files, and verify the base dashboard still works:

**Mac/Linux:**
```bash
rm data/cleaned/players.csv data/cleaned/fixtures_detailed.csv
rm data/cleaned/xg_matches.csv data/cleaned/xg_players.csv data/cleaned/xg_teams.csv
python scripts/02_transform.py
python -m http.server 8000
```

Open http://localhost:8000 again. The base 7 charts should still render. The xG section should show a fallback message instead of broken charts.

Restore the data when done:
```bash
python scripts/03_fetch_fpl.py
python scripts/04_fetch_xg.py
python scripts/02_transform.py
```

---

## Phase 5: Push to GitHub

### 18. Stage all files

```bash
git add .
```

### 19. Check what's being committed

```bash
git status
```

You should see all your project files listed. Make sure you DON'T see:
- `__pycache__/` folders (should be in .gitignore)
- `.DS_Store` files (should be in .gitignore)
- The PRD/FRD/skill docs (you can choose to include these or not)

If you want to keep the docs out of the public repo (they're build instructions, not the portfolio piece itself):

```bash
echo "PRD/" >> .gitignore
echo "FRD/" >> .gitignore
echo "skill/" >> .gitignore
echo "PROMPT.md" >> .gitignore
git add .gitignore
```

### 20. Commit

```bash
git commit -m "initial commit: EPL 2024-25 data analysis dashboard"
```

### 21. Push to GitHub

```bash
git push origin main
```

If your default branch is `master` instead of `main`:
```bash
git push origin master
```

### 22. Verify on GitHub

Go to https://github.com/YOUR_USERNAME/epl-analysis

You should see all your files. Click around and verify:
- `index.html` exists at the root
- `data/dashboard_data.json` exists and is not empty
- `scripts/` folder has all 5 Python files
- `docs/` folder has cleaning-log.md and pipeline.md
- `README.md` looks good

---

## Phase 6: Enable GitHub Pages

### 23. Go to repo Settings

On your repo page, click **Settings** (top right, gear icon)

### 24. Navigate to Pages

In the left sidebar, click **Pages** (under "Code and automation")

### 25. Configure the source

```
Source:     Deploy from a branch
Branch:     main (or master)
Folder:     / (root)
```

Click **Save**.

### 26. Wait 60 seconds

GitHub builds your site. Refresh the Settings > Pages page.

### 27. Your site is live

You'll see a green box:

```
Your site is live at https://YOUR_USERNAME.github.io/epl-analysis/
```

Click that URL. Your full interactive dashboard is now live on the internet.

---

## Phase 7: Enable GitHub Actions (Auto-Update)

### 28. Verify the workflow file exists

Check that `.github/workflows/update.yml` was created by Claude Code. If not, create it:

```bash
mkdir -p .github/workflows
```

Then create the file (Claude Code should have done this already).

### 29. Push the workflow file (if you haven't already)

```bash
git add .github/workflows/update.yml
git commit -m "add weekly data update workflow"
git push
```

### 30. Verify the workflow appears in GitHub

Go to: https://github.com/YOUR_USERNAME/epl-analysis/actions

You should see "Update EPL Data" listed as a workflow.

### 31. Test with a manual run

On the Actions page:
1. Click "Update EPL Data" in the left sidebar
2. Click "Run workflow" button (right side)
3. Click the green "Run workflow" button in the dropdown

Watch it run. It should:
- Complete in about 2 minutes
- Show green checkmarks on all steps
- Probably NOT create a commit (because data hasn't changed since you just pushed)

### 32. Verify the cron will work

The cron is set to `0 8 * * 1` which means every Monday at 8am UTC. You don't need to do anything else. GitHub will run it automatically.

To check upcoming runs or past runs: https://github.com/YOUR_USERNAME/epl-analysis/actions

---

## Phase 8: Link to Your Portfolio

### 33. Option A: Direct link

On your portfolio website, add a project card that links to:

```
https://YOUR_USERNAME.github.io/epl-analysis/
```

### 34. Option B: Embed as iframe

If your portfolio supports HTML:

```html
<iframe
  src="https://YOUR_USERNAME.github.io/epl-analysis/"
  width="100%"
  height="800px"
  style="border: none; border-radius: 8px;"
  title="EPL 2024-25 Data Analysis Dashboard">
</iframe>
```

### 35. Option C: Custom domain

If your portfolio is at `yourdomain.com` and you want the dashboard at `yourdomain.com/epl-analysis/`:

This requires your portfolio site to be hosted on GitHub Pages too, with the dashboard as a subdirectory. Otherwise, link directly.

For a standalone custom domain on the dashboard repo:

1. In repo Settings > Pages > Custom domain, enter: `epl.yourdomain.com`
2. In your DNS provider, add a CNAME record: `epl` pointing to `YOUR_USERNAME.github.io`
3. Wait for DNS propagation (5 mins to 24 hours)
4. Check "Enforce HTTPS" once the certificate is issued

---

## Phase 9: Switch to Live Season (When 2025-26 Starts)

When the new EPL season kicks off in August 2025:

### 36. Edit config.py (2 lines)

```bash
cd epl-analysis
```

Open `scripts/config.py` in any editor and make these changes:

```python
# ADD this line to ACTIVE_SEASONS:
ACTIVE_SEASONS["2025-26"] = {"code": "2526", "understat": "2025", "fpl_mode": "live"}

# CHANGE this line:
CURRENT_SEASON = "2025-26"   # was "2024-25"
```

### 37. Add the new season's teams

Still in `scripts/config.py`, add:

```python
CANONICAL_TEAMS["2025-26"] = [
    # Copy from 2024-25, remove 3 relegated teams, add 3 promoted teams
    # Check the actual promoted teams when the Championship ends in May 2025
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
    "Chelsea", "Crystal Palace", "Everton", "Fulham",
    "Liverpool", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest",
    "Tottenham Hotspur", "West Ham United", "Wolverhampton",
    # Replace these 3 with actual promoted teams:
    "Promoted Team 1", "Promoted Team 2", "Promoted Team 3",
]
```

### 38. Check if new teams need name mappings

If a promoted team has a different name in football-data.co.uk, FPL, or Understat, add mappings to the relevant `*_NAME_MAP` dicts in config.py.

### 39. Test locally

```bash
python scripts/01_clean.py
python scripts/03_fetch_fpl.py
python scripts/04_fetch_xg.py
python scripts/02_transform.py
python -m http.server 8000
```

Open http://localhost:8000 and verify:
- LIVE badge appears in nav
- "Matchday X of 38" shows
- "Data as of [date]" shows
- League table shows current standings
- Points race chart stops at current matchday (not empty space to 38)

### 40. Push and let automation take over

```bash
git add .
git commit -m "switch to 2025-26 live season"
git push
```

From now on, every Monday at 8am UTC:
1. GitHub Actions runs your pipeline
2. Downloads the latest match data (new weekend results)
3. Fetches updated FPL and xG data
4. Rebuilds dashboard_data.json
5. Commits the new JSON to your repo
6. GitHub Pages serves the updated dashboard

Your dashboard updates automatically. You never touch it again until the season ends.

### 41. When the season ends (May 2026)

Change `fpl_mode` from `"live"` to `"historical"` in config.py:

```python
ACTIVE_SEASONS["2025-26"] = {"code": "2526", "understat": "2025", "fpl_mode": "historical"}
```

Push. The dashboard drops the LIVE badge, shows "Final Standings", and uses past tense in the takeaway. The cron still runs but detects no changes and creates no commits.

---

## Troubleshooting

### "Page not found" on GitHub Pages

- Check Settings > Pages is configured (Step 24-25)
- Make sure `index.html` is at the ROOT of the repo, not in a subfolder
- Wait 2-3 minutes after pushing for GitHub Pages to build

### Dashboard shows "Failed to load data"

- `data/dashboard_data.json` must exist in your repo
- Open browser dev tools (F12) > Console tab to see the actual error
- Common cause: the JSON file path in index.html doesn't match where the file actually is

### GitHub Actions workflow not running

- Go to Actions tab and check if the workflow is listed
- Make sure the file is at exactly `.github/workflows/update.yml` (spelling matters)
- For cron: it only runs on the default branch (main or master)
- Try a manual run first (Step 31)

### GitHub Actions runs but doesn't commit

This is normal when data hasn't changed. The `git diff --cached --quiet` check prevents empty commits. For a completed season, data won't change, so no commits are expected.

### Charts not rendering

- Open browser dev tools (F12) > Console tab
- Common errors: Chart.js CDN blocked (try a different network), JSON has unexpected nulls
- Test with `python -m http.server 8000` locally first before debugging GitHub Pages

### "Permission denied" on git push

Run `git remote -v` to check your remote URL. If it starts with `https://`, you need to authenticate:
```bash
gh auth login
```
Or switch to SSH:
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/epl-analysis.git
```

---

## Summary: What You End Up With

```
LIVE URL:     https://YOUR_USERNAME.github.io/epl-analysis/
REPO:         https://github.com/YOUR_USERNAME/epl-analysis
AUTO-UPDATE:  Every Monday 8am UTC (GitHub Actions)
COST:         $0 (GitHub Free tier)
```

Your portfolio now links to a live, interactive, auto-updating data analysis dashboard that:
- Runs on real EPL data (not a toy dataset)
- Shows you built the full pipeline (clean, transform, visualize)
- Documents every decision (cleaning log, pipeline architecture)
- Auto-updates during live seasons
- Degrades gracefully when data sources are down
- Costs nothing to host or run
