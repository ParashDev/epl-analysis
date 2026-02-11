# Dashboard Design System Reference

Specification for the single-file HTML dashboard used in data analysis portfolio projects.

## Tech Stack

- Single HTML file. All CSS and JS inline.
- Tailwind CSS via CDN: `https://cdn.tailwindcss.com`
- Chart.js via CDN: `https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js`
- Google Fonts: Pick TWO -- one serif for headings, one sans-serif for body.
- Recommended pair: DM Sans (body) + Source Serif 4 (headings).
- No React, Vue, npm, Webpack, or any build step.

## Color System (Dark Editorial Theme)

"Bloomberg Terminal meets The Athletic" -- data-dense but readable.

| Token | Hex | Usage |
|---|---|---|
| bg-base | #0f0f1a | Page background |
| bg-surface | #1a1a2e | Cards, chart containers |
| bg-surface-hover | #252540 | Hover states |
| text-primary | #f0ede6 | Headings, body text (warm off-white) |
| text-secondary | #6b7280 | Labels, axis text |
| text-muted | #4b5563 | Tertiary text |
| accent | #52b788 | Positive, primary action, highlights |
| warn | #e76f51 | Negative, alerts, red cards |
| gold | #d4a843 | Neutral highlight, secondary data |
| blue | #4895ef | Tertiary data series |

Define as Tailwind config extensions in a `<script>` tag:

```html
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          base: '#0f0f1a',
          surface: '#1a1a2e',
          'surface-hover': '#252540',
          chalk: '#f0ede6',
          accent: '#52b788',
          warn: '#e76f51',
          gold: '#d4a843',
        }
      }
    }
  }
</script>
```

## Typography

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Source+Serif+4:wght@400;600;700&display=swap');
```

| Element | Font | Weight | Size |
|---|---|---|---|
| Body text | DM Sans | 400 | 14-16px |
| Section labels | DM Sans | 700 | 0.65rem, uppercase, letter-spacing 0.08em |
| Headings | Source Serif 4 | 600/700 | 1.5-2.5rem |
| Data values | DM Sans | 500 | varies |

## Page Structure (5 Sections)

### Section 0: Fixed Navigation
- Sticky top bar with backdrop blur
- Logo text in serif font
- Nav links with bottom border on hover/active
- Smooth scroll on click, active state tracks scroll position

### Section 1: "The Brief" (Hero)
- Tag label: "Case Study 001" (uppercase, accent color, micro text)
- Large serif heading describing the project
- 2-3 sentence scope paragraph
- Tech stack pills/tags

### Section 2: "The Raw Data"
- Tag label: "Section 01"
- Three stat cards: raw columns, total rows, columns dropped
- Faux terminal window showing actual raw data lines
- Numbered data quality flags with explanations

### Section 3: "The Pipeline"
- Tag label: "Section 02"
- Flow diagram: Extract -> Clean -> Transform -> Serve
- Code snippet showing a key cleaning decision

### Section 4: "The Dashboard" (Main Charts)
- Tag label: "Section 03"
- KPI summary row (3-4 big numbers)
- Base charts always visible
- Enrichment charts conditional (hidden with fallback message if data missing)

### Section 5: "The Takeaway"
- Tag label: "Section 04"
- Auto-generated narrative using JS (not hardcoded)
- "What I would do differently" subsection
- Tools used grid, source attribution

## Chart.js Global Configuration

```javascript
Chart.defaults.color = '#6b7280';
Chart.defaults.borderColor = 'rgba(255,255,255,0.04)';
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.boxWidth = 12;
Chart.defaults.plugins.legend.labels.padding = 16;
```

All tooltips: dark background (#1a1a2e), subtle border, rounded corners.

## Conditional Rendering Pattern

```javascript
if (data.optional_section && data.optional_section.length > 0) {
  document.getElementById('optional-section').classList.remove('hidden');
  renderOptionalChart(data);
} else {
  document.getElementById('optional-fallback').classList.remove('hidden');
  // Shows: "Data not loaded. Run scripts/0X_fetch.py to enable."
}
```

Never show empty charts or broken layouts. Always show a subtle note.

## Component Patterns

- `.stat-card`: gradient bg, subtle border, rounded-lg, p-5
- `.chart-container`: bg-surface, 1px border rgba(255,255,255,0.06), rounded-lg
- `.tag`: uppercase, micro text, accent color, letter-spacing
- `.position-badge`: 28x28 rounded square, color-coded

## Responsive

| Breakpoint | Behavior |
|---|---|
| Desktop (md+) | 2-column grid for paired charts, full table columns |
| Mobile (<md) | Single column, hide auxiliary table columns, reduce chart heights |

## Animations

- Fade-in on dashboard content load
- Hover states on table rows (subtle bg change)
- Smooth scroll navigation
- No excessive motion

## Live Season UI States

When `data.season_status.is_complete === false`, the dashboard enters "live mode":

### LIVE Badge (Nav Bar)
- Small pulsing green dot (CSS animation) + "LIVE" text in uppercase accent color
- Positioned next to the season label in the nav bar
- CSS: `@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`

### Last Updated Footer
- Text: "Data as of {last_match_date}" in text-muted
- Positioned below the nav bar or in the footer
- Hidden when season is complete

### Matchday Counter (KPI Card)
- Instead of "380 Matches", show "240 / 380" with a subtle progress bar underneath
- Progress bar: bg-surface with accent fill at `matches_played / matches_total * 100`%

### League Table Header
- Complete: "2024-25 Final Standings"
- Live: "2025-26 Standings (Matchday 24)"
- If teams have different games played (postponements), the "P" column becomes prominent

### Takeaway Tense
- Complete season: "Liverpool won the league with 84 points"
- Live season: "Liverpool lead the table with 56 points after 24 matchdays"
- JS logic: `const verb = isLive ? 'lead' : 'won';`

### Chart Axis Limits
- Points Race: X-axis max = `matchdays_played` (not hardcoded 38)
- Monthly Goals: only show months with data (no empty December-May bars mid-season)
- Season Comparison: current live season bar gets a subtle dashed border to indicate "in progress"
