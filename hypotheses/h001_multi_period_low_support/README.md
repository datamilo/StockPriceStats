# H001: Multi-Period Support Level Analysis for Put Option Writing

> **📊 START HERE:** Run the Streamlit app to interactively analyze any stock!
>
> ```bash
> streamlit run streamlit_app_lite.py
> ```
> Then open your browser to `http://localhost:8501`

## Hypothesis & Conclusion

**Question:** Do shorter-term support levels (1-month, 3-month) work just as well as longer-term ones (1-year) for identifying reliable strike prices when writing put options?

**Conclusion:** ✅ **YES** - Shorter-term rolling lows are actually SUPERIOR because they provide equal success rates (89-90%) with 6-7x more trading opportunities.

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

### Interactive Web App
- **`streamlit_app_lite.py`** - Main Streamlit application
  - Real-time analysis of any stock
  - Period selection (1/3/6/9/12 months)
  - Interactive price charts with rolling low visualization
  - Date range filtering
  - Support level markers (red dots when support breaks)
  - Performance statistics

### Analysis Scripts
- **`multi_period_low_analysis.py`** - Full re-analysis (for first-time setup)
  - Regenerates all results from scratch
  - Takes 2-3 hours (only needed for methodology changes)
- **`multi_period_low_analysis_incremental.py`** - Incremental updates
  - Processes only new data (much faster)
  - Called automatically by `../update_analysis_data.py`
  - Takes 5-10 minutes for new data

### Result Data Files
- **`{period}_detailed_results.parquet`** - Detailed test results for each period
  - Columns: stock, support_date, support_level, wait_days, success, days_to_break
  - Used by the Streamlit app for visualization

### Documentation
- **`README.md`** - This file (quick reference)
- **`METHODOLOGY_AND_FINDINGS.md`** - Detailed methodology and findings

## How to Run the Streamlit App

### Locally on Your Computer
```bash
cd StockPriceStats
streamlit run hypotheses/h001_multi_period_low_support/streamlit_app_lite.py
```
Then open `http://localhost:8501` in your browser.

### On Streamlit Cloud
If deployed, access the live app at the provided URL (no installation needed).

## Dataset

- **Stocks:** 70 Nordic blue-chip stocks with liquid options markets
- **Date Range:** 2000-2025 (25 years)
- **Total Records:** 367K price records
- **Source:** `../../price_data_filtered.parquet`

## Example: How the Analysis Works

**Scenario:** Stock at 150 kr in January

1. **January 10:** 1-month rolling low = 150 kr (lowest price in past 30 days)
2. **Wait 30 days** → February 9 (price stays above 150 kr during the wait)
3. **February 9:** Write 30-day put with strike at 150 kr
4. **March 11:** Check if price stayed ≥ 150 kr the entire option period
   - If YES: ✓ Success (option expired worthless, premium kept)
   - If NO: ✗ Failure (price went below 150 kr, assignment risk)

The analysis tested this exact scenario across:
- **70 stocks** (Nordic options universe)
- **25 years** of historical data (2000-2025)
- **All 5 rolling periods** (1, 3, 6, 9, 12 months)
- **All wait times** (0-180 days, constrained by period)
- **All option expiries** (7-45 days)
- **Total:** ~30 million historical test cases

## What the Results Show

Success rates show the historical probability that a put option would expire worthless:

| Period | Success Rate | Opportunities |
|--------|-------------|----------------|
| 1-Month | 89.7% | Highest (daily) |
| 3-Month | 89.0% | Very high (6-7x vs 1-year) |
| 6-Month | ~88% | Moderate |
| 9-Month | ~88% | Moderate |
| 1-Year | 87.8% | Lowest |

**Key Insight:** Shorter periods give equal or better success rates with far more trading opportunities.

## Using the Streamlit App

1. **Launch the app** (see instructions above)
2. **Select a stock** from the dropdown (any of the 70)
3. **Choose a rolling period** (1-month, 3-month, etc.)
4. **Set your date range** to analyze a specific timeframe
5. **View the chart** showing:
   - Daily price candlesticks
   - Rolling low line (blue dashed)
   - Support breaks (red dots)
6. **Scroll down** for detailed performance statistics

The app lets you explore the data interactively and understand why shorter-term rolling lows are better for put option writing.

---

*Last Updated: 2025-10-22*
*Status: H001 complete with Streamlit web app*
*Data Current Through: 2025-10-22*
