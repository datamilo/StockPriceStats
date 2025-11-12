# Probability Prediction Validation Analysis

## Overview

This folder contains a complete pipeline for enriching option probability predictions with actual outcome data and validating the accuracy of 5 different probability prediction methods.

## Files and Purpose

### Data Files

| File | Size | Purpose |
|------|------|---------|
| `probability_history_FULL_HISTORICAL.csv` | 92 MB | Original probability predictions (1,073,731 options) |
| `probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv` | 140 MB | Enriched with strike info, dates, prices, and expiry outcomes |

**Columns in enriched file:**
- `StrikePrice` - Strike price of the option
- `StrikeDate` - Expiry date of the option
- `Name` - Stock name
- `StockPrice` - Stock closing price on update date
- `OptionName` - Option identifier
- `Update_date` - Date of the probability prediction
- `1_2_3_ProbOfWorthless_Weighted` - Weighted average probability
- `ProbWorthless_Bayesian_IsoCal` - Bayesian calibrated probability
- `1_ProbOfWorthless_Original` - Original Black-Scholes probability
- `2_ProbOfWorthless_Calibrated` - Bias-corrected probability
- `3_ProbOfWorthless_Historical_IV` - Historical IV probability
- `StockPrice_AtExpiry` - Stock closing price on expiry date (actual outcome)

### Python Scripts

| Script | Purpose | Execution |
|--------|---------|-----------|
| `probability_history_generator_FULL_HISTORICAL.py` | Generates initial probability predictions | Prerequisite (not included here) |
| `build_probability_history_complete.py` | Enriches probability history with strike info and prices | Run this to create enriched file |
| `validate_probability_predictions.py` | Validates predictions against actual outcomes and calculates metrics | Run after enrichment |
| `generate_validation_report.py` | Creates interactive HTML visualization report | Run after validation |

### Output Files

#### HTML Report
- **`probability_validation_report.html`** - Interactive dashboard with:
  - Executive summary with key findings
  - Performance metrics comparison (4-panel chart)
  - Calibration curves showing predicted vs actual rates
  - Calibration error analysis by probability bin
  - Sample distribution visualizations
  - Detailed metrics table
  - Recommendations

#### Validation Results (`validation_results/` folder)
- `metrics_summary.csv` - Performance metrics for all 5 methods
- `calibration_*.csv` - Binned calibration data for each method
- `calibration_curves.png` - Static calibration visualizations
- `reliability_diagrams.png` - Reliability analysis charts
- `metrics_comparison.png` - Metrics comparison bar charts

## Key Results

### Winner: Bayesian Calibrated Method

Based on empirical validation of 934,643 expired options:

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| **Brier Score** | 0.1397 | Best accuracy (lower is better) |
| **AUC-ROC** | 0.7764 | Excellent discrimination (higher is better) |
| **Expected Calibration Error** | 0.0032 | Only 0.32% error (exceptionally well-calibrated) |
| **Log Loss** | 0.3987 | Good probabilistic accuracy |

**Why this matters for put option writing:**
- The Bayesian Calibrated method provides reliable probability estimates
- 0.32% calibration error means predictions are trustworthy for strike selection
- Strong AUC-ROC (0.7764) indicates excellent ability to distinguish options likely to expire worthless

### Analysis Coverage

- **Options analyzed:** 934,643 expired options (87% of dataset)
- **Options not yet expiry:** 139,088 (13%) - these expire after latest price data
- **Actual expiry rate:** 78.8% of put options expired worthless
- **Methods compared:** 5 different probability prediction approaches
- **Time period:** 25 years of data (2000-2025)

## How to Use

### 1. Enrich Probability History

If you have new probability predictions in `probability_history_FULL_HISTORICAL.csv`:

```bash
cd /home/gustaf/StocksOptionsStats/Options
python3 build_probability_history_complete.py
```

**Output:** `probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv`

### 2. Validate Predictions

After enrichment, validate the predictions:

```bash
python3 validate_probability_predictions.py
```

**Outputs:**
- CSV files in `validation_results/` folder
- PNG charts for static visualization

### 3. Generate HTML Report

Create an interactive visualization report:

```bash
python3 generate_validation_report.py
```

**Output:** `probability_validation_report.html`

### 4. View Results

Open the HTML report in your browser:

```bash
# On Linux/WSL
xdg-open probability_validation_report.html

# Or just double-click the file in file explorer
```

## Understanding the Metrics

### Brier Score
- **Formula:** Mean squared error between predicted probability and actual outcome
- **Range:** 0 to 1 (0 = perfect, 1 = worst)
- **Interpretation:** 0.1397 means average squared error of 14%, very accurate

### AUC-ROC (Area Under Receiver Operating Characteristic Curve)
- **Range:** 0 to 1 (0.5 = random guessing, 1 = perfect discrimination)
- **Interpretation:** 0.7764 indicates strong ability to rank options by likelihood of expiring worthless

### Expected Calibration Error (ECE)
- **Formula:** Weighted average of |predicted probability - actual rate| across bins
- **Range:** 0 to 1 (0 = perfectly calibrated)
- **Interpretation:** 0.0032 (0.32%) means predictions match reality exceptionally well

### Log Loss
- **Formula:** -[y·log(p) + (1-y)·log(1-p)]
- **Range:** 0 to ∞ (0 = perfect)
- **Interpretation:** Penalizes confident wrong predictions more heavily; 0.3987 is good

## Calibration Analysis

The validation includes a binning analysis that divides predictions into 10 bins (0-10%, 10-20%, ..., 90-100%) and compares:
- **Predicted Probability:** Mean of all predictions in each bin
- **Actual Rate:** Percentage of options that actually expired worthless in that bin
- **Calibration Error:** Difference between predicted and actual

Perfect calibration means the actual rate matches the predicted probability in each bin. Our Bayesian Calibrated method achieves this exceptionally well (0.32% error).

## Recommendations for Put Option Writing

Based on this validation analysis:

1. **Use Bayesian Calibrated probabilities** for strike selection decisions
2. **Trust the predictions** - the calibration error is only 0.32%, extremely reliable
3. **Use probabilities as-is** - no adjustment needed, they match reality
4. **Consider the 78.8% baseline** - out of all put options, this percentage expire worthless naturally
5. **Focus on risk management** - use these probabilities as input to position sizing and portfolio management

## Data Quality Notes

### Missing Expiry Prices (139,088 records, 12.95%)
These are options expiring after November 11, 2025 (latest available price data). They cannot be validated yet but will have outcomes when prices are updated.

### Data Preservation
All 1,073,731 original records are preserved in the enriched file. Missing values only occur for:
- `StockPrice_AtExpiry` - for future options
- `StockPrice` - rare cases where price data is unavailable

## File Organization

```
Options/
├── README.md (this file)
├── ANALYSIS_RESULTS.md (detailed findings)
│
├── Data files
├── probability_history_FULL_HISTORICAL.csv
├── probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv
│
├── Scripts
├── probability_history_generator_FULL_HISTORICAL.py
├── build_probability_history_complete.py
├── validate_probability_predictions.py
├── generate_validation_report.py
│
├── Reports and Results
├── probability_validation_report.html ⭐ START HERE
├── validation_results/
│   ├── metrics_summary.csv
│   ├── calibration_*.csv
│   ├── calibration_curves.png
│   ├── reliability_diagrams.png
│   └── metrics_comparison.png
│
└── Supporting modules
    ├── config_utils.py
    ├── constants.py
    └── data_loader.py
```

## Quick Start

```bash
# 1. If you have new probability data, enrich it
python3 build_probability_history_complete.py

# 2. Validate predictions
python3 validate_probability_predictions.py

# 3. Generate HTML report
python3 generate_validation_report.py

# 4. Open the report
xdg-open probability_validation_report.html
```

## Next Steps

To use these validated probabilities for your put option writing strategy:

1. Review the HTML report to understand model performance
2. Use the Bayesian Calibrated probabilities for strike selection
3. Combine with your risk management rules (position sizing, portfolio allocation)
4. Monitor outcomes and recalibrate if market conditions change significantly
5. Update the analysis when new price data becomes available

---

**Last Updated:** November 12, 2025
**Data Currency:** Through November 11, 2025
**Status:** Validation complete and validated
