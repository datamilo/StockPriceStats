# Options Analysis - Consolidated Workflow

This folder contains consolidated scripts for probability data generation, validation, and analysis.

## Two Simple Workflows

### Workflow 1: Generate Complete Probability History (Data Setup)

When you have new probability data or need to regenerate the enriched dataset:

```bash
python generate_probability_history_complete.py
```

This consolidates TWO steps into ONE command:
- ✅ Generates base probability predictions (Step 1)
- ✅ Enriches with strike & price data (Step 2)
- ✅ Outputs: `probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv`

**Run when:** You have new raw probability data from OneDrive and need to enrich it

---

### Workflow 2: Generate Analysis Reports (Weekly)

Once you have the enriched CSV file:

```bash
python generate_reports.py
```

This single command:
- ✅ Validates probability predictions against actual outcomes
- ✅ Analyzes historical probability recovery patterns
- ✅ Generates both interactive HTML reports

**Run when:** You want to update analysis reports with current data

**Output:** Two self-contained HTML reports ready to share or analyze

---

## The Two Reports

### 1. Probability Validation Report
**File:** `probability_validation_report.html`

Validates the accuracy of 5 different probability prediction methods by comparing predicted probabilities against 934,643 actual option outcomes.

**What it shows:**
- Performance comparison (Brier Score, AUC-ROC, Log Loss, Calibration Error)
- Calibration curves for each method
- Stock-level performance filtering
- Days-to-expiry (DTE) analysis

**Winner:** Bayesian Calibrated method (0.32% calibration error)

### 2. Historical Probability Recovery Analysis Report
**File:** `probability_recovery_analysis_report.html`

Examines options that previously peaked at high probability levels (80%+) but have since declined.

**Key Finding:** Options currently at 60-70% probability that previously peaked at 90%+ expire worthless **85-90%** of the time, vs. only **42%** for baseline options.

**What it shows:**
- Interactive filtering by threshold, method, probability, and stock
- Comparison of recovery candidates vs. baseline options
- Days-to-expiry breakdown
- 43 percentage point advantage in optimal scenarios

---

## Complete Workflow

### Prerequisites

**For Report Generation:**
- Python 3.7+ with: pandas, numpy, plotly, scikit-learn
- Data file: `probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv` (use Workflow 1 to generate)

**For Data Generation:**
- Python 3.7+ with: pandas, numpy, scipy, joblib, requests, beautifulsoup4, tqdm
- OneDrive data files: `All_Options_Data.parquet`, `price_data_all.parquet`, `Implied_Volatility_Historical_ALL.parquet`
- Weekly maintenance calibration files in: `OneDrive/OptionsData/WeeklyMaintenance/`

### Running Workflow 1: Data Generation

```bash
cd ~/StocksOptionsStats/Options
python generate_probability_history_complete.py
```

**What it does:**
- Step 1: Generates base probability predictions (all 5 methods)
- Step 2: Enriches with strike prices and stock prices at update/expiry
- Output: `probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv`

**Processing time:** Variable (depends on data size; Step 1 is computationally intensive)

### Running Workflow 2: Report Generation

```bash
cd ~/StocksOptionsStats/Options
python generate_reports.py
```

**What it does:**
- Validates probability predictions against actual outcomes
- Analyzes historical probability recovery patterns
- Generates both interactive HTML reports

**Processing time:** A few minutes (depending on data size)

### Output Files

**HTML Reports (Open in Browser):**
- `probability_validation_report.html` - Probability prediction validation
- `probability_recovery_analysis_report.html` - Historical recovery patterns

**CSV Analysis Results:**
```
validation_results/
├── metrics_summary.csv          # Performance metrics for all methods
└── calibration_[method].csv     # Calibration data per method

probability_recovery_results/
├── probability_recovery_summary.csv      # Summary statistics
├── probability_recovery_by_stock.csv     # Per-stock analysis
└── probability_recovery_details.csv      # Full detailed dataset
```

---

## Input Data Format

The script expects: `probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv`

**Required columns:**
| Column | Type | Purpose |
|--------|------|---------|
| `Name` | String | Stock ticker |
| `OptionName` | String | Unique option ID |
| `Update_date` | DateTime | Probability update date |
| `StrikeDate` | DateTime | Option expiration date |
| `StrikePrice` | Float | Put strike price |
| `StockPrice_AtExpiry` | Float | Actual stock price at expiry (for validation) |
| `1_2_3_ProbOfWorthless_Weighted` | Float | Weighted average method (0-1) |
| `ProbWorthless_Bayesian_IsoCal` | Float | Bayesian calibrated method (0-1) |
| `1_ProbOfWorthless_Original` | Float | Original Black-Scholes (0-1) |
| `2_ProbOfWorthless_Calibrated` | Float | Bias corrected method (0-1) |
| `3_ProbOfWorthless_Historical_IV` | Float | Historical IV method (0-1) |

**Calendar Days Convention:** All DTE calculations use calendar days, not business days.

---

## Configuration & Parameters

Edit the top of `generate_reports.py` to adjust analysis parameters:

```python
# Historical recovery analysis thresholds
HISTORICAL_PEAK_THRESHOLDS = [0.80, 0.85, 0.90, 0.95]

# Current probability ranges
CURRENT_PROB_BINS = [(0.60, 0.70), (0.70, 0.80), (0.80, 0.90)]

# Days to expiry bins
DTE_BINS = [(0, 7), (8, 14), (15, 21), (22, 28), (29, 35), (36, 999)]
```

---

## Key Metrics Explained

### Probability Validation Metrics

| Metric | Range | Interpretation |
|--------|-------|-----------------|
| **Brier Score** | 0-1 | Accuracy; lower is better; 0.14 = very accurate |
| **AUC-ROC** | 0-1 | Discrimination ability; 0.78 = strong |
| **Expected Calibration Error** | 0-1 | Prediction reliability; 0.0032 (0.32%) = exceptional |
| **Log Loss** | 0-∞ | Probabilistic accuracy; lower is better |

### Recovery Analysis Metrics

| Metric | Meaning |
|--------|---------|
| **Recovery_WorthlessRate** | % of recovery candidates that expire worthless |
| **Baseline_WorthlessRate** | % of baseline options that expire worthless |
| **Advantage_pp** | Percentage point difference (recovery - baseline) |

---

## The 5 Probability Methods Compared

| Method | Source | Best For |
|--------|--------|----------|
| **Weighted Average** | Brier-score weighted blend | Overall accuracy |
| **Bayesian Calibrated** | Bayesian isotonic calibration | Well-calibrated predictions |
| **Original Black-Scholes** | Standard B-S formula | Theoretical baseline |
| **Bias Corrected** | Per-bin historical correction | Reducing systematic error |
| **Historical IV** | Historical volatility tables | Empirical patterns |

---

## Historical Probability Recovery Analysis

### What It Measures

For each option-date record, the analysis tracks:
1. **Historical Peak Probability** - Highest probability this option ever reached
2. **Current Probability** - Probability on this specific date
3. **Actual Outcome** - Whether it expired worthless or was assigned

### Why It Matters

Options that previously peaked at 90%+ probability provide a strong signal, even if current probability has declined to 60-70%. This suggests:
- Fundamental strength (stock stays above strike)
- Stable underlying characteristics
- Lower assignment risk than current probability alone suggests

### Optimal Scenarios

**Best conditions for recovery advantage:**
- **Historical Peak:** 90%+ (strongest signal)
- **Current Probability:** 60-70% (largest advantage)
- **Days to Expiry:** 36+ calendar days (strongest effect)
- **Method:** Bayesian Calibrated (+43pp advantage)

---

## File Organization

```
Options/
├── MAIN SCRIPTS (Run these!)
├── generate_probability_history_complete.py  ⭐ Workflow 1: Generate enriched data
├── generate_reports.py                        ⭐ Workflow 2: Generate reports (weekly)
├── README.md                                  (this file)
│
├── DATA FILE
├── probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv
│
├── GENERATED OUTPUT (Reports)
├── probability_validation_report.html
└── probability_recovery_analysis_report.html
│
├── GENERATED OUTPUT (Analysis Data)
├── validation_results/
│   ├── metrics_summary.csv
│   └── calibration_[method].csv
└── probability_recovery_results/
    ├── probability_recovery_summary.csv
    ├── probability_recovery_by_stock.csv
    └── probability_recovery_details.csv
│
├── SUPPORT MODULES
├── constants.py
├── config_utils.py
├── data_loader.py
│
└── Archive/                          (Superseded/historical scripts)
    ├── probability_history_generator_FULL_HISTORICAL.py
    ├── build_probability_history_complete.py
    ├── validate_probability_predictions.py
    ├── generate_validation_report.py
    ├── analyze_probability_drops.py
    └── generate_fallen_angels_report.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "File not found" | Ensure `probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv` exists in this directory |
| Missing results | Check CSV has required columns; only expired options (with `StockPrice_AtExpiry`) are analyzed |
| Blank HTML reports | Verify CSV files created in validation_results/ and probability_recovery_results/; check column names |
| Script errors | Ensure pandas, numpy, plotly, scikit-learn are installed: `pip install pandas numpy plotly scikit-learn` |

---

## Complete Workflows

### One-Time: Generate Enriched Data

When you have new raw probability data:

```bash
# Generate enriched CSV (combines 2 steps into 1)
python generate_probability_history_complete.py

# This outputs: probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv
```

### Weekly: Update Analysis Reports

Every week when you want to refresh the analysis:

```bash
# Update both reports with current data
python generate_reports.py

# Open the generated reports
open probability_validation_report.html
open probability_recovery_analysis_report.html
```

That's it! Each script handles everything needed for its workflow.

---

**Last Updated:** November 14, 2025
**Workflow:** Consolidated weekly report generation
**Maintained By:** Claude Code

