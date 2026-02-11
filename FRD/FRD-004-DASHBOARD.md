# FRD-004: Dashboard Frontend - Functional Specification

## File: `index.html`

---

## Data Loading

```javascript
async function loadData() {
  const response = await fetch('data/dashboard_data.json');
  if (!response.ok) throw new Error('Failed to load');
  return await response.json();
}
```

- Show loading state while fetching
- Show error message if fetch fails (with hint to use local server)
- On success, hide loading, show dashboard with fade-in animation
- Read `data.season_status` to determine live vs complete mode
- Set global `isLive = !data.season_status.is_complete` flag used by all chart renderers

---

## Chart Specifications

### Chart 1: League Table (HTML table, not Chart.js)

| Feature | Spec |
|---|---|
| Rows | 20 (one per team) |
| Columns | Position, Team, P, W, D, L, GF, GA, GD, Shots, Acc%, CS, Pts |
| Position badge colors | 1-4: accent green, 5-6: blue, 18-20: warn red |
| GD coloring | Positive: accent, Negative: warn, Zero: default |
| Hover | Subtle background change |
| Responsive | Hide Shots, Acc%, CS columns on mobile |

### Chart 2: Points Race (Chart.js Line)

| Feature | Spec |
|---|---|
| Type | line |
| Series | Top 6 teams + Bottom 3 teams |
| X-axis | Matchday (1 to `season_status.matchdays_played` for live, 1-38 for complete) |
| Y-axis | Cumulative points |
| Line colors | Use team-specific colors from TEAM_COLORS map |
| Bottom 3 style | Thinner lines (1.5px), dashed |
| Top 6 style | Thicker lines (2.5px), solid |
| Points | Hidden (pointRadius: 0), show on hover (pointHoverRadius: 4) |
| Tension | 0.2 (slight curve) |
| Live mode | X-axis max = matchdays_played (no empty matchdays beyond current) |

### Chart 3: Monthly Goals (Chart.js Bar)

| Feature | Spec |
|---|---|
| Type | bar |
| X-axis | Month labels (Aug 24, Sep 24, ..., May 25) |
| Y-axis | Average goals per match |
| Bar color | Accent green, brighter for months with avg >= 3.0 |
| Tooltip | Shows match count and total goals for that month |

### Chart 4: Home vs Away (Chart.js Doughnut)

| Feature | Spec |
|---|---|
| Type | doughnut |
| Segments | Home Wins (accent), Draws (gold), Away Wins (warn) |
| Cutout | 60% |
| Below chart | Three stat callouts: home goals/match, draw count, away goals/match |

### Chart 5: Referee Card Rates (Chart.js Horizontal Bar)

| Feature | Spec |
|---|---|
| Type | bar (indexAxis: 'y') |
| Filter | Only referees with 5+ matches |
| Datasets | Avg Cards/Match (warn), Avg Fouls/Match (gold dimmed) |
| Sort | By avg cards descending |
| Max refs shown | 15 |

### Chart 6: Common Scorelines (Chart.js Bar)

| Feature | Spec |
|---|---|
| Type | bar |
| Data | Top 10 most frequent scorelines |
| Highlight | Most common scoreline gets full accent, others dimmed |

### Chart 7: Season Comparison (Chart.js Grouped Bar)

| Feature | Spec |
|---|---|
| Type | bar (grouped) |
| X-axis | Season labels (2022-23, 2023-24, 2024-25) |
| Datasets | Avg Goals (accent), Avg Cards (warn), Home Win % scaled (gold) |
| Tooltip | Shows actual values including unscaled home win % |

### Chart 8: xG vs Actual Goals Scatter (CONDITIONAL)

| Feature | Spec |
|---|---|
| Render condition | `data.xg_vs_actual !== null` |
| Type | scatter |
| X-axis | Total xG for the season |
| Y-axis | Actual goals scored |
| Reference line | Diagonal y=x line (use a line dataset or annotation) |
| Dot labels | Team names next to each dot |
| Dot colors | Above diagonal (clinical): accent, Below (wasteful): warn |

### Chart 9: Top Scorers with xG (CONDITIONAL)

| Feature | Spec |
|---|---|
| Render condition | `data.top_scorers !== null` |
| Type | bar (grouped) |
| Data | Top 10 scorers |
| Datasets | Actual Goals (accent), xG (gold dimmed) |
| Sort | By actual goals descending |
| Gap visualization | Space between bars shows over/underperformance |

### Chart 10: Shot Quality by Team (CONDITIONAL)

| Feature | Spec |
|---|---|
| Render condition | `data.shot_quality !== null` |
| Type | bar (indexAxis: 'y') |
| Data | All 20 teams |
| Metric | xG per shot |
| Sort | Descending |
| Color | Gradient from accent (high quality) to warn (low quality) |

---

## Conditional Rendering Logic

```javascript
// After loading data:
if (data.xg_table && data.xg_table.length > 0) {
  document.getElementById('xg-section').classList.remove('hidden');
  renderXgScatter(data);
  renderXgTable(data);
} else {
  document.getElementById('xg-fallback').classList.remove('hidden');
  // Shows: "xG data not loaded. Run scripts/04_fetch_xg.py to enable."
}

if (data.top_scorers && data.top_scorers.length > 0) {
  document.getElementById('players-section').classList.remove('hidden');
  renderTopScorers(data);
  renderShotQuality(data);
}
```

---

## Responsive Breakpoints

| Breakpoint | Behavior |
|---|---|
| Desktop (md+) | 2-column grid for paired charts, full table columns |
| Mobile (<md) | Single column, hide auxiliary table columns (shots, accuracy, clean sheets), reduce chart heights |

---

## Chart.js Global Defaults

```javascript
Chart.defaults.color = '#6b7280';
Chart.defaults.borderColor = 'rgba(255,255,255,0.04)';
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.boxWidth = 12;
Chart.defaults.plugins.legend.labels.padding = 16;
```

All tooltips: dark background (#1a1a2e), subtle border, custom callbacks.
