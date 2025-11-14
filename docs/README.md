# Documentation Index

All project documentation is organized here for easy reference.

## Start Here

- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Complete project overview, strategy explanation, and active hypotheses
  - Project purpose and goals
  - Dataset information
  - Hypothesis testing framework
  - Key project guidelines and rules

## Workflows

- **[OPTIONS_WORKFLOW.md](OPTIONS_WORKFLOW.md)** - Complete guide to the Options analysis workflows
  - Workflow 1: Generate enriched probability data
  - Workflow 2: Generate analysis reports (weekly)
  - Input/output specifications
  - Configuration options

- **[DATA_UPDATE_WORKFLOW.md](DATA_UPDATE_WORKFLOW.md)** - How to update analysis with new data
  - Quick update process
  - Automated workflow
  - Performance improvements

## Quick References

- **[OPTIONS_QUICK_REFERENCE.md](OPTIONS_QUICK_REFERENCE.md)** - Quick reference for Options folder operations
- **[ANALYSIS_RESULTS.md](ANALYSIS_RESULTS.md)** - Detailed analysis results and findings

## Deployment & Infrastructure

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment configuration and setup instructions

---

## Key Scripts

### Data Generation
```bash
python Options/generate_probability_history_complete.py
```
Generates enriched probability history file with all strike and price data.

### Report Generation
```bash
python Options/generate_reports.py
```
Generates interactive HTML reports for probability validation and recovery analysis.

---

## Repository Structure

```
StocksOptionsStats/
├── docs/                           ← You are here
├── Options/
│   ├── generate_probability_history_complete.py
│   ├── generate_reports.py
│   └── Archive/                    (superseded scripts)
├── hypotheses/
│   └── h001_multi_period_low_support/
├── price_data_all.parquet
├── price_data_filtered.parquet
└── .gitignore
```

---

**Last Updated:** November 14, 2025
**Maintained By:** Claude Code
