# PROMPT.md -- Master Build Instruction

## What You Are Building

A complete, portfolio-grade EPL 2024-25 data analysis project. Built from scratch. No starter files provided.

## How to Use This

Read these documents in this exact order before writing any code:

### 1. Skill (Methodology)

The `skill/data-analysis-portfolio/` folder is a reusable Claude Skill that defines the project template, build process, design system, and script patterns.

- `skill/data-analysis-portfolio/SKILL.md` -- Start here. Defines project structure, build phases, principles, and constraints.
- `skill/data-analysis-portfolio/references/script-patterns.md` -- Python templates for 01_clean, 02_transform, and fetch scripts.
- `skill/data-analysis-portfolio/references/design-system.md` -- Dashboard colors, typography, Chart.js config, page layout.
- `skill/data-analysis-portfolio/references/doc-templates.md` -- README, cleaning-log, and pipeline doc templates.
- `skill/data-analysis-portfolio/references/live-season.md` -- Config-driven season selection, live vs historical mode, partial season handling.

### 2. PRDs (What to Build and Why)

- `PRD/PRD-MAIN.md` -- Product overview. Architecture, tech stack, constraints, development order.
- `PRD/PRD-001-DATA-ETL.md` -- Raw CSV cleaning: every known data quality issue.
- `PRD/PRD-002-FPL-API.md` -- FPL player stats: endpoints, fields, team mapping.
- `PRD/PRD-003-XG-DATA.md` -- Understat xG: what xG is, how to fetch, fallback strategy.
- `PRD/PRD-004-DASHBOARD.md` -- Frontend: all 10 chart specs, design system, conditional rendering.
- `PRD/PRD-005-AUTOMATION.md` -- GitHub Actions: workflow YAML, failure behavior.
- `PRD/PRD-006-DOCS.md` -- README, cleaning log, pipeline docs: what each must contain.

### 3. FRDs (How It Must Behave)

- `FRD/FRD-MAIN.md` -- Canonical team names, error handling standard, data flow diagram, validation rules.
- `FRD/FRD-001-DATA-ETL.md` -- Exact processing steps, column schemas, download logic.
- `FRD/FRD-002-FPL-API.md` -- API endpoints, output schemas, mode selection.
- `FRD/FRD-003-XG-DATA.md` -- understatapi code patterns, fallback scraping, caching.
- `FRD/FRD-004-DASHBOARD.md` -- Every chart config spec'd, conditional rendering JS.
- `FRD/FRD-005-AUTOMATION.md` -- Complete workflow YAML, failure behavior rules.

## Build Order

Execute in this exact sequence. Verify each phase works before moving to the next.

### Phase 1: Foundation
1. Create the project folder structure (see PRD-MAIN Section 5)
2. Build `scripts/config.py` per SKILL reference `references/live-season.md` -- season definitions, team maps, source URLs
3. Build `scripts/01_clean.py` per PRD-001 + FRD-001 + skill script patterns. Must import from config.py (no hardcoded seasons).
4. Run: `python scripts/01_clean.py`
5. Verify: 1,140 rows, 29 columns

### Phase 2: Base Transform + Dashboard
5. Build `scripts/02_transform.py` (match data aggregations only)
6. Run: `python scripts/02_transform.py`
7. Verify: dashboard_data.json is valid JSON
8. Build `index.html` per PRD-004 + FRD-004 + skill design system
9. Verify: `python -m http.server 8000` -- all 7 base charts render

### Phase 3: Enrichment
10. Build `scripts/03_fetch_fpl.py` per PRD-002 + FRD-002
11. Build `scripts/04_fetch_xg.py` per PRD-003 + FRD-003
12. Run both scripts
13. Update 02_transform.py to merge all sources
14. Update index.html for xG and player charts
15. Verify: all 10 charts render

### Phase 4: Documentation + Automation
16. Create docs/ files per PRD-006 + skill doc templates
17. Create requirements.txt, .gitignore, README.md
18. Create .github/workflows/update.yml per PRD-005 + FRD-005

### Phase 5: Verify
19. Delete all generated data files
20. Rerun full pipeline from scratch
21. Confirm all charts render
22. Delete enrichment CSVs only -- confirm graceful degradation

## Critical Reminders

- Read the skill FIRST. It defines the methodology.
- Read ALL PRDs before writing any code.
- Build config.py FIRST. All scripts import from it.
- Team names must be identical across all scripts (config.py is the single source of truth).
- No hardcoded seasons, URLs, or name maps in any script other than config.py.
- Comments explain WHY, not WHAT.
- Dashboard must work with ONLY match data (graceful degradation).
- Dashboard must work with partial season data (live mode).
- No emojis. No AI filler. No build steps.
- Test after every phase.
