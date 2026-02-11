# Documentation Templates Reference

Templates for the three required documentation files in every portfolio case study.

## README.md Template

```markdown
# {Project Title}

{One-line description of the project and what it analyzes.}

[Live Demo]({github-pages-url}) | [Data Source]({source-url})

## The Question

{2-3 sentences in first person explaining what you wanted to find out and why.
Not "In this project we explore..." but "I wanted to know whether..."}

## Project Structure

{Full tree diagram with one-line description per file}

## How to Run

Prerequisites: Python 3.11+, pip

{Exact commands from clone to browser:}

git clone {url}
cd {project}
pip install -r requirements.txt
python scripts/01_clean.py
python scripts/02_transform.py
python -m http.server 8000
# Open http://localhost:8000

## Deploy to GitHub Pages

1. Push to GitHub
2. Settings > Pages > Source: main branch, / (root)
3. Site is live at https://{username}.github.io/{repo}

## What This Demonstrates

| Skill | How |
|---|---|
| Data Cleansing | {specific example from this project} |
| ETL Pipeline | {specific example} |
| Visualization | {specific example} |
| Documentation | {specific example} |

## Data Sources

| Source | URL | Format | What It Provides |
|---|---|---|---|

## License

Data provided by {source} under {terms}. Analysis and code are MIT.
```

Tone rules for README:
- Professional but not corporate
- First person where appropriate
- No filler phrases ("In this project we explore...")
- Direct and specific
- No emojis

---

## docs/cleaning-log.md Template

A decision journal. One entry per cleaning action.

```markdown
# Cleaning Decision Log

Every data cleaning choice documented with reasoning.

---

## Decision 01: {Short Title}

**What:** {What was done}
**Why:** {The reasoning -- not "to clean it" but the actual problem it solves}
**Impact:** {Rows affected, columns affected, data loss if any}

---

## Decision 02: {Short Title}

**What:** ...
**Why:** ...
**Impact:** ...

---

{Continue for all decisions, minimum 8-10 entries}

---

## Summary

| Metric | Value |
|---|---|
| Input rows | {N} |
| Output rows | {N} |
| Rows dropped | {N} |
| Input columns | {N} |
| Output columns | {N} |
| Columns dropped | {N} |
| Columns added (derived) | {N} |
```

Required decision categories (adapt to your dataset):
1. Column selection (what was dropped and why)
2. Encoding issues (BOM, UTF-8, etc.)
3. Date/time format standardization
4. Name/category standardization
5. Null handling strategy
6. Text cleanup (whitespace, casing)
7. Column renaming convention
8. Derived column rationale

If using enrichment sources, add entries for:
9. Source B name mapping differences
10. Source C normalization
11. Handling missing enrichment data
12. Cross-source entity matching

---

## docs/pipeline.md Template

```markdown
# Pipeline Architecture

## Overview

{One paragraph explaining the pipeline philosophy and why the chosen tools
are appropriate for this dataset size.}

## Architecture

{ASCII art diagram showing all scripts, inputs, outputs, data flow.
Include GitHub Actions if applicable.}

## Scripts

### 01_clean.py
- **Reads:** {input files}
- **Produces:** {output file}
- **Runtime:** ~{N} seconds
- **Key decisions:** {1-2 sentence summary}

### 02_transform.py
- **Reads:** {input files}
- **Produces:** {output file}
- **Runtime:** ~{N} seconds
- **Key decisions:** {1-2 sentence summary}

{Continue for all scripts}

## Why Not {Tool X}?

| Tool | Why Not |
|---|---|
| Airflow/Prefect | {reason -- usually: dataset fits in memory, 4 scripts don't need orchestration} |
| dbt | {reason -- usually: no database, CSV-to-JSON is simpler} |
| PostgreSQL | {reason -- usually: under 10K rows, JSON is the "database" for static frontend} |
| React/Next.js | {reason -- usually: single page, no routing, zero build step deploys instantly} |

This is not about ignorance of these tools. It is about appropriate tool
selection for the problem size.

## Rerunning the Pipeline

{Exact commands to regenerate everything from scratch}

## Extending to New Data

{Step-by-step for adding another season/year/dataset}

## Merge Strategy

{How 02_transform.py handles combining sources with different naming conventions}

## Error Handling

{How the pipeline degrades when sources are unavailable}
```
