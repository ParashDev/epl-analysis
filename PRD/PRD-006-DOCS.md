# PRD-006: Documentation & Reproducibility

## Feature Summary

Documentation is not an afterthought -- it is part of the deliverable. A hiring manager will read the README, cleaning log, and pipeline docs before they look at any code. These documents must demonstrate clear thinking, not just describe what files exist.

**Priority:** P0 (Must Have)
**Files:** `README.md`, `docs/cleaning-log.md`, `docs/pipeline.md`

---

## README.md

### Required Sections:

1. **Title + one-line description**
2. **Live demo link** (GitHub Pages URL placeholder)
3. **The Question** -- what this project is trying to answer, written in first person, 2-3 sentences
4. **Project Structure** -- full tree diagram of every file with one-line descriptions
5. **How to Run** -- step by step from clone to browser, including prerequisites
6. **Deploy to GitHub Pages** -- 3-step instructions
7. **What This Demonstrates** -- table mapping skills to how the project proves them:
   - Data Cleansing
   - ETL Pipeline
   - Multi-Source Integration
   - API Integration
   - xG / Advanced Analytics
   - Visualization
   - CI/CD Automation
   - Documentation
8. **Data Sources** -- table with source name, URL, format, what it provides
9. **Live Season Mode** -- how to switch to live tracking for the current season (reference config.py, explain 2-line change)
10. **Column Reference** -- quick lookup for the cryptic source abbreviations
11. **License** -- data attribution to football-data.co.uk

### Tone:
- Professional but not corporate
- First person where appropriate
- No filler phrases like "In this project we explore..."
- Direct and specific

---

## docs/cleaning-log.md

A decision journal. One entry per cleaning action, each with:

- **What** was done
- **Why** it was done (the reasoning, not just "to clean the data")
- **Impact** (rows affected, columns affected, data loss if any)

### Required Entries:

1. Drop betting columns (96 columns, why irrelevant)
2. BOM character handling (what it is, why it breaks things)
3. Date standardization (DD/MM/YYYY vs DD/MM/YY, why ISO 8601)
4. Team name mapping (which names, why proper names matter for merges)
5. Null handling strategy (what was checked, what would have been done if nulls existed)
6. Referee name cleanup (whitespace issue)
7. Column renaming (cryptic to readable)
8. Derived columns (what was added and why)
9. FPL team name mapping (differences from football-data names)
10. Understat team name normalization (underscore removal, name variants)
11. Handling missing xG data (matches without xG, how handled)
12. Player name deduplication across sources (FPL "Salah" vs Understat "Mohamed Salah")

### Format:
Each entry should have: Decision number, What, Why, Impact. Use a consistent template.

End with a summary table: input rows, output rows, rows dropped, columns dropped, columns added.

---

## docs/pipeline.md

### Required Content:

1. **Overview** -- one paragraph explaining the pipeline philosophy
2. **Architecture diagram** -- ASCII art showing all 4 scripts, their inputs/outputs, and the data flow. Include GitHub Actions.
3. **Script descriptions** -- for each of the 4 scripts: what it does, what it reads, what it produces, how long it takes
4. **Why not [Tool X]** -- explain why Airflow, dbt, a database, React, etc. were deliberately not used. This is not about ignorance -- it is about appropriate tool selection for the problem size.
5. **Rerunning the pipeline** -- exact commands to regenerate everything
6. **Extending to new seasons** -- step by step for adding 2025-26 data
7. **Merge strategy** -- how 02_transform.py handles combining 3 different data sources with different naming conventions
8. **Error handling philosophy** -- how the pipeline degrades gracefully when sources are unavailable

---

## Acceptance Criteria

- [ ] README allows someone to go from zero to running dashboard in under 5 minutes
- [ ] Cleaning log has an entry for every cleaning decision (minimum 10 entries)
- [ ] Pipeline doc has an architecture diagram
- [ ] Pipeline doc explains why heavier tools were not used
- [ ] All file paths referenced in docs actually exist in the project
- [ ] No dead links
- [ ] No emojis
- [ ] No AI-sounding filler phrases
