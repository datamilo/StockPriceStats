# Stock Price Statistics - Put Option Writing Strategy

This project analyzes stock price data to determine optimal put option writing strategies.

## Quick Start

👉 **[View Complete Documentation](docs/README.md)** - All project documentation is in the `docs/` folder

## Two Essential Commands

```bash
# Generate enriched probability data (one-time or when you have new data)
python Options/generate_probability_history_complete.py

# Generate analysis reports (weekly)
python Options/generate_reports.py
```

## Key Documentation

- **[Project Overview](docs/PROJECT_OVERVIEW.md)** - Full project description, strategy, and hypotheses
- **[Options Workflow](docs/OPTIONS_WORKFLOW.md)** - Detailed guide to the analysis workflows
- **[Data Update Workflow](docs/DATA_UPDATE_WORKFLOW.md)** - How to update with new data

## Repository Structure

```
├── docs/                           ← All documentation
├── Options/                        ← Analysis scripts
│   ├── generate_probability_history_complete.py
│   └── generate_reports.py
├── hypotheses/                     ← Research hypotheses
└── price_data_*.parquet            ← Data files
```

## Strategy Overview

This project uses a **structured hypothesis testing approach** to systematically evaluate put option writing strategies. We analyze Nordic stocks with liquid options markets to identify optimal strike prices that maximize premium while minimizing assignment risk.

### Key Findings

- **H001: Multi-Period Low Support Analysis** - Shorter-term rolling lows (1, 3, 6 months) work as well as longer-term lows, with 6-7x more trading opportunities
- **Probability Validation** - Validated 5 probability prediction methods against 934,643 expired options
- **Historical Probability Recovery** - Options with historical high probability peaks still expire worthless far more often than current probability suggests (+43pp advantage)

---

**Last Updated:** November 14, 2025
**Maintained By:** Claude Code
