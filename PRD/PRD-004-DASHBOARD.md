# PRD-004: Interactive Dashboard

## Feature Summary

A single-page interactive dashboard that presents the analysis as a narrative case study. Not a generic chart gallery -- a story with five chapters: Brief, Raw Data, Pipeline, Dashboard, Takeaway.

**Priority:** P0 (Must Have)
**File:** `index.html` (single file, no build step)
**Input:** `data/dashboard_data.json`
**Hosting:** GitHub Pages (static)

---

## Tech Constraints

- Single HTML file containing all CSS and JS inline
- Tailwind CSS via CDN (`https://cdn.tailwindcss.com`)
- Chart.js via CDN (`https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js`)
- Google Fonts: DM Sans (body) + Source Serif 4 (headings)
- No React, Vue, or any framework
- No npm, no build step, no bundler
- Must work when served from GitHub Pages or `python -m http.server`
- No emojis anywhere in the UI

---

## Design System

### Theme: Dark Editorial

Think "Bloomberg Terminal meets The Athletic" -- data-dense but readable.

**Colors (define as Tailwind config extensions):**
- Background: `#0f0f1a` (near-black with slight blue)
- Surface: `#1a1a2e` (cards, chart backgrounds)
- Surface hover: `#252540`
- Text primary: `#f0ede6` (chalk -- warm off-white)
- Text secondary: `#6b7280` (gray-500)
- Text muted: `#4b5563` (gray-600)
- Accent: `#52b788` (green -- positive, primary action)
- Warning: `#e76f51` (red-orange -- negative, alerts)
- Gold: `#d4a843` (neutral highlight)
- Blue: `#4895ef` (secondary data)

**Typography:**
- Body: DM Sans 400/500/700
- Headings: Source Serif 4 400/600/700
- Code: system monospace
- Section labels: DM Sans 700, 0.65rem, uppercase, letter-spacing 0.08em, accent color

**Components:**
- `.stat-card` -- gradient background, subtle border, rounded-lg, p-5
- `.chart-container` -- bg-slate, 1px border, rounded-lg
- `.tag` -- uppercase micro label in accent green
- `.section-divider` -- 1px top border at rgba(255,255,255,0.06)
- `.nav-link` -- bottom border transition, accent on hover/active
- `.position-badge` -- 28x28 rounded square with color coding (green for top 4, blue for 5-6, red for bottom 3)

---

## Page Structure (5 Sections)

### Section 0: Fixed Navigation
- Sticky top bar, blurred background
- Logo text: "EPL 24/25" in serif font
- Nav links: Brief, Raw Data, Pipeline, Dashboard, xG Analysis, Players, Takeaway
- Smooth scroll on click
- Active state tracks scroll position

### Section 1: "The Brief" (Hero)
- Tag: "Case Study 001"
- Large serif heading: "The Numbers Behind the 2024-25 Premier League"
- Paragraph explaining the project scope (380 matches, 120 columns, what was done)
- Tech stack pills: Python / Pandas, Data Cleansing, ETL Pipeline, Chart.js, Tailwind CSS

### Section 2: "The Raw Data"
- Tag: "Section 01"
- Three stat cards: raw column count (120), total rows (1,140), columns dropped (96)
- Faux terminal window showing actual raw CSV lines with betting columns highlighted in warn color
- "Data quality issues found" list with FLAG 01 through FLAG 05, each explaining a real problem found and how it was resolved

### Section 3: "The Pipeline"
- Tag: "Section 02"
- Four-column flow diagram: Extract -> Clean -> Transform -> Serve
- Each column shows: script name, what it does, output file
- Code snippet window showing key decisions from 01_clean.py (BOM handling, team name map)

### Section 4: "The Dashboard" (Main Visualization Area)
- Tag: "Section 03"
- Loading state shown while JSON fetches
- KPI row: Matches Played, Total Goals, Goals Per Match, Champions

**Base charts (always visible):**
- League table with position badges, color-coded GD, shot accuracy, clean sheets
- Points race: cumulative line chart for top 6 + bottom 3
- Monthly goals: bar chart, avg goals per match by month
- Home vs Away: doughnut chart with stat callouts
- Referee card rates: horizontal bar chart, avg cards + avg fouls
- Common scorelines: bar chart, top 10 frequencies
- Season comparison: grouped bar chart across 3 seasons

**xG charts (conditional -- only show if data.xg_table exists):**
- xG vs Actual Goals scatter plot
  - X-axis: total xG, Y-axis: actual goals
  - Diagonal reference line (y=x) showing "fair" performance
  - Teams above the line = clinical/overperforming
  - Teams below = wasteful/underperforming
  - Each dot labeled with team name
  - Color: accent for overperformers, warn for underperformers

- xG Justice Table
  - Ranked by expected points (xPoints)
  - Columns: position, team, xG for, xG against, xPoints, actual points, difference
  - Difference column: green positive = overperforming, red negative = underperforming

**Player charts (conditional -- only show if data.top_scorers exists):**
- Top 10 scorers: grouped bar chart (goals bar + xG bar side by side)
  - Gap between bars visually shows over/underperformance
- Shot quality by team: horizontal bar chart, xG per shot

**If xG/player data is missing:**
- Show a subtle note: "xG data not loaded. Run scripts/04_fetch_xg.py to enable advanced analytics."
- Do NOT show empty charts or broken layouts

### Section 5: "The Takeaway"
- Tag: "Section 04"
- Auto-generated narrative text using the data (built in JS, not hardcoded)
- Cover: champion, top scorer, best defense, home advantage stats, relegation
- If xG data present: add xG overperformers/underperformers narrative
- "What I would do differently" subsection (hardcoded text about future improvements)
- "Tools Used" grid
- "Source & Reproducibility" with links and commands

### Footer
- Single line: project description, data source credit, disclaimer

---

## Interactivity

- Chart.js tooltips on all charts (dark background, border, custom callbacks showing context)
- Hover state on table rows (subtle background change)
- Smooth scroll navigation
- Fade-in animation when dashboard content loads
- Responsive: works on mobile (stack columns, hide some table columns on small screens)

---

## Data Contract (dashboard_data.json)

The HTML expects this JSON structure. The 02_transform.py script must produce exactly this:

```json
{
  "generated_at": "ISO timestamp",
  "season": "2024-25",
  "source": "football-data.co.uk",
  "total_matches": 380,
  "season_status": {
    "matches_played": 380,
    "matches_total": 380,
    "matchdays_played": 38,
    "matchdays_total": 38,
    "is_complete": true,
    "last_match_date": "2025-05-25"
  },
  "league_table": [
    { "position": 1, "team": "Liverpool", "played": 38, "won": 25, "drawn": 9, "lost": 4, "goals_for": 83, "goals_against": 38, "goal_difference": 45, "points": 84, "home_won": 14, "away_won": 11, "clean_sheets": 15, "total_shots": 600, "total_shots_on_target": 220, "shot_accuracy": 36.7, "goals_per_game": 2.18, ... }
  ],
  "monthly_trends": [
    { "month": "2024-08", "matches": 30, "total_goals": 85, "avg_goals": 2.83, "home_wins": 12, "draws": 8, "away_wins": 10 }
  ],
  "home_away": { "home_wins": 155, "draws": 93, "away_wins": 132, "home_goals_avg": 1.51, "away_goals_avg": 1.42, "total_matches": 380, "home_win_pct": 40.8, "away_win_pct": 34.7 },
  "referee_stats": [
    { "referee": "M Oliver", "matches": 25, "avg_goals": 2.8, "avg_fouls": 21.3, "avg_cards": 4.5, "total_reds": 2 }
  ],
  "season_comparison": [ ... ],
  "scoreline_frequency": [ { "score": "1-1", "count": 45 } ],
  "cumulative_points": { "Liverpool": [{ "matchday": 1, "points": 3 }, ...] },

  // --- OPTIONAL (null if not available) ---
  "xg_table": [ { "team": "Liverpool", "xg_for": 75.2, "xg_against": 35.1, "x_points": 80.5, "actual_points": 84, "over_under": 3.5 } ],
  "top_scorers": [ { "player_name": "Salah", "team": "Liverpool", "goals": 23, "assists": 12, "xg": 19.5, "xa": 8.2, "minutes": 3200, "goals_minus_xg": 3.5, "position": "MID" } ],
  "xg_vs_actual": [ { "team": "Liverpool", "total_xg": 75.2, "actual_goals": 83, "difference": 7.8 } ],
  "shot_quality": [ { "team": "Liverpool", "total_shots": 600, "xg_per_shot": 0.125 } ],
  "player_value": [ { "player_name": "Salah", "team": "Liverpool", "price": 13.0, "goals": 23, "goals_per_million": 1.77 } ]
}
```

### Partial Season Handling (season_status)

The `season_status` object drives all live-season UI behavior. When `is_complete` is false:

| UI Element | Complete Season | Live Season (Partial Data) |
|---|---|---|
| Hero subtitle | "380 matches across 38 matchdays" | "240 of 380 matches -- Matchday 24 of 38" |
| KPI: matches | "380" | "240 / 380" with subtle progress indicator |
| League table header | "2024-25 Final Standings" | "2025-26 Standings (Matchday 24)" |
| Played column | All show 38 | Some show 23, some 24 (postponements) |
| Points race X-axis | Matchday 1-38 | Matchday 1 to matchdays_played (dynamic) |
| Takeaway tense | Past: "Liverpool won the league" | Present: "Liverpool lead the table" |
| Nav bar | No indicator | Pulsing green dot + "LIVE" badge |
| Last updated | Not shown | "Data as of {last_match_date}" in footer |

```javascript
// In index.html after loading data:
const status = data.season_status;
const isLive = !status.is_complete;

if (isLive) {
  document.getElementById('live-badge').classList.remove('hidden');
  document.getElementById('last-updated').textContent =
    `Data as of ${status.last_match_date}`;
  document.getElementById('matches-kpi').textContent =
    `${status.matches_played} / ${status.matches_total}`;
  document.getElementById('table-heading').textContent =
    `${data.season} Standings (Matchday ${status.matchdays_played})`;
}

// Points race: dynamic X-axis max
const maxMatchday = isLive ? status.matchdays_played : 38;
```

---

## Acceptance Criteria

- [ ] Page loads and renders all base charts with only match data
- [ ] Page loads and renders xG/player charts when that data is present
- [ ] Page shows graceful fallback message when xG data is absent
- [ ] All charts are interactive (tooltips, hover)
- [ ] Navigation smooth-scrolls to correct sections
- [ ] Active nav link updates on scroll
- [ ] Responsive on mobile (no horizontal scroll, tables overflow properly)
- [ ] No console errors in browser dev tools
- [ ] No emojis anywhere in the rendered page
- [ ] Passes basic accessibility check (alt text not needed for charts, but nav is keyboard accessible)
- [ ] Dashboard renders correctly with partial season data (e.g., 200 of 380 matches)
- [ ] "LIVE" indicator shows when season_status.is_complete is false
- [ ] "Last updated" date shows when season is in progress
- [ ] Cumulative points chart X-axis stops at matchdays_played (no empty matchdays)
- [ ] League table handles teams with different games played (postponements)
- [ ] Takeaway text uses present tense for live season, past tense for complete season
