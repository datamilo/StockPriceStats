# H001: Multi-Period Support Level Analysis for Put Option Writing

> **📊 START HERE:** Open `multi_period_dashboard.html` in your browser for interactive analysis!

## Hypothesis Statement

**Question:** Do shorter-term support levels (1-month, 3-month) work just as well as longer-term ones (1-year) for identifying reliable strike prices when writing put options?

**Methodology:** For each rolling time period, we identify the support level (lowest price) and test whether price remains above that level when we write puts at various wait times after the support is set, with different option expiry periods.

## Understanding the Analysis

### Key Concepts

**1. Rolling Support Levels**
- For EVERY trading day, we calculate the lowest price over the past N days (30/90/180/270/365)
- Each day produces a new support level
- This creates a rolling stream of support observations (not rare events!)

**2. Wait Times After Support**
- Once a support level is identified on a trading day, we can wait N days (0/30/60/90/120/180) before writing the put
- Wait times are constrained by the period: 1-month lows can't be waited more than 30 days
- During the wait period, we verify the support hasn't already been broken

**3. Option Testing**
- After the wait period, we write a put option with M days to expiry (7/14/21/30/45)
- Success = Price stays ABOVE the support during the entire option period
- Success = Option expires worthless, we keep the premium

**4. Time Window Constraints**
- 1-month low: wait times can be [0, 30] days only
- 3-month low: wait times can be [0, 30, 60, 90] days only
- 6-month low: wait times can be [0, 30, 60, 90, 120, 180] days
- 9-month low: wait times can be [0, 30, 60, 90, 120, 180] days
- 1-year low: wait times can be [0, 30, 60, 90, 120, 180] days

## Methodology

1. **Calculate Rolling Lows:** For each period and each trading day, find the lowest price in that period
2. **Identify Support Date:** Each trading day produces a support level
3. **Verify Wait Period:** Check that support hasn't been broken during the wait time
4. **Test Option Period:** Check if price stayed above support for the full option duration
5. **Record Success:** Support held = Put expired worthless

## Files in This Hypothesis

### Interactive Dashboard
- **`multi_period_dashboard.html`** - Main interactive dashboard (START HERE!)
  - Period comparison tables showing success rates
  - Interactive price charts with support visualization
  - Filters for:
    - Time period (1/3/6/9/12 months)
    - Stock selection
    - Date range
    - Wait time (constrained by period)
    - Option expiry period
  - Success rate matrices
  - Swedish market focus (all prices in kr)

### Data Files
- **`multi_period_dashboard_data.json`** - Dashboard data
- **`multi_period_combined_matrix.csv`** - Combined success rate matrix
- **`{period}_detailed_results.csv`** - Detailed results for each period
- **`{period}_matrix.csv`** - Success rate matrix for each period

### Analysis Scripts
- **`multi_period_low_analysis.py`** - Main analysis (generates all results)
- **`add_price_data_to_dashboard.py`** - Adds price chart data to dashboard
- **`build_clean_dashboard.py`** - Builds HTML dashboard

### Documentation
- **`README.md`** - This file (quick reference)
- **`METHODOLOGY_AND_FINDINGS.md`** - Comprehensive analysis

## How to Run the Analysis

```bash
cd hypotheses/h001_multi_period_low_support

# 1. Run the multi-period analysis
python multi_period_low_analysis.py

# 2. Add price data to dashboard
python add_price_data_to_dashboard.py

# 3. Build the interactive dashboard
python build_clean_dashboard.py

# 4. Open the dashboard
open multi_period_dashboard.html
```

## Dataset

- **Stocks:** 70 Nordic blue-chip stocks with liquid options markets
- **Date Range:** 2000-2025 (25 years)
- **Total Records:** 367K price records
- **Source:** `../../price_data_filtered.parquet`

## Example: How the Analysis Works

**Scenario:** Stock ABC in January 2023

1. **January 10:** 1-month low is 150 kr
2. **Wait 30 days** → February 9 (support holds above 150 kr during wait)
3. **February 9:** Write 30-day put at 150 kr strike
4. **March 11:** Check if price stayed ≥ 150 kr during the option period
   - If YES: Success ✓ (option expired worthless, premium kept)
   - If NO: Failure ✗ (price touched support, assignment risk)

The analysis tests this scenario for:
- All 70 stocks
- All time periods (1/3/6/9/12 months)
- All valid wait times for each period
- All expiry periods (7/14/21/30/45 days)
- Over 25 years of historical data

## Results

Results are organized in matrices with:
- **Rows:** Wait times (0, 30, 60, 90, 120, 180 days - constrained by period)
- **Columns:** Expiry periods (7, 14, 21, 30, 45 days)
- **Values:** Success rates (%) and sample counts

This allows you to look up: "If I write a 30-day put on a 3-month low after waiting 60 days, what's the historical success rate?"

## Next Steps

1. **Open multi_period_dashboard.html** to explore results interactively
2. **Use the filters** to:
   - Select a time period (1/3/6/9/12 months)
   - Pick a stock
   - View the success rate matrix
3. **Notice the time window constraints** - wait times available depend on the period
4. **Compare strategies** - see which combinations offer the best probability

---

*Last Updated: 2025-10-21*
*Status: Methodology corrected - no more "Proven Support" filtering*
*All rolling support levels tested - complete historical validation*
