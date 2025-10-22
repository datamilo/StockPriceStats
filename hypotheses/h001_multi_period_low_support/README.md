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

---

## Streamlit App Guide

The Streamlit app has **two main tabs** for comprehensive analysis:

### 📈 Tab 1: Stock Analysis
**Single-stock deep dive with interactive visualization**

**Controls:**
- **Stock Selector:** Choose any of the 68 Nordic stocks
- **Rolling Period:** Select 1-Month, 3-Month, 6-Month, 9-Month, or 1-Year
- **Date Range Filter:** Analyze specific timeframes (defaults to 2024-present)

**Displays:**
1. **Price Chart** (Interactive Plotly)
   - Daily candlesticks showing open/high/low/close
   - Blue dashed line = rolling low support level
   - Red dots = dates when support broke (new lower low identified)

2. **Key Metrics**
   - Data points in date range
   - Latest closing price (kr)
   - Period low (kr)

3. **Support Level Performance Statistics**
   - Total support levels tested
   - Success rate % (with breakdown: ✓ successes / ✗ failures)
   - Average days until support breaks
   - Rolling low changes frequency
   - Detailed breakdown of successful vs failed supports

4. **Price Data Table** (Bottom)
   - Complete OHLC data for selected date range
   - Rolling low values for each day

---

### 🏆 Tab 2: Top Performers Analysis
**Comprehensive metrics across all 68 stocks with 5 sub-tabs**

**Master Control:**
- **Period Selector:** Choose 1-Month, 3-Month, 6-Month, 9-Month, or 1-Year to analyze

Each metric is calculated across all 68 stocks and displayed in the same time period.

#### **Sub-Tab 1: 📈 Success Metrics**
Identify high-performing stocks by success rate and opportunity frequency.

**Success Rate** (Left):
- Which stocks hold support most reliably?
- Shows: Stock name, success %, successful/total tests
- Top 5 performers highlighted
- Full table with all 68 stocks
- Summary: average success rate, best stock

**Support Frequency** (Right):
- Which stocks create new supports most often?
- Shows: Stock name, supports/year, total supports
- Top 5 performers highlighted
- Full table ranked by frequency
- Summary: average frequency, most active stock

---

#### **Sub-Tab 2: ⏱️ Resilience Metrics**
Analyze how long supports last and how predictable they are.

**Days to Break Support** (Left):
- How many days before support typically breaks?
- Shows: Stock name, avg days, number of breaks
- Top 5 most resilient highlighted
- Full table (higher days = more resilient)
- Summary: average days, most resilient stock

**Support Consistency** (Right):
- How predictable are the breaks (lower stddev = more predictable)?
- Shows: Stock name, stddev, mean days, breaks analyzed
- Top 5 most consistent highlighted
- Full table (lower stddev = easier to predict)
- Summary: average stddev, most consistent stock

---

#### **Sub-Tab 3: 🛡️ Risk Metrics**
Understand the downside when support eventually breaks.

**Downside Risk When Support Breaks:**
- Shows: Stock name, avg downside %, max downside %
- Top 5 lowest-risk stocks highlighted
- Full table (lower % = less risky)
- Summary: average downside, lowest/highest risk stocks
- **Interpretation:** Average % price drops below support when it breaks

---

#### **Sub-Tab 4: 🎯 Strategy Metrics**
Optimize your put option writing strategy.

**Best Option Expiry Period** (Left):
- Which expiry (7d, 14d, 21d, 30d, 45d) works best?
- Shows: Stock name, best expiry, success rate %
- Top 5 with highest success rates
- Full table with all expiry columns
- Summary: average best rate, most optimal stock

**Wait Time Effectiveness** (Right):
- Does waiting after support identification improve results?
- Shows: Stock name, immediate %, after wait %, improvement %
- Top 5 with biggest improvements
- Full table (positive % = waiting helps)
- Summary: average improvement, count of stocks improving with wait

---

#### **Sub-Tab 5: 🗓️ Temporal Patterns**
Identify seasonal trading opportunities.

**Seasonal Patterns - Best & Worst Months:**
- Which months are best for each stock?
- Shows: Stock name, best month, worst month, success rates
- Top 5 ranked by best month success rate
- Full table with best/worst months and rates
- Summary: average best rate, average worst rate, seasonal spread
- **Interpretation:** Useful for timing premium collection strategies

---

## Dataset

- **Stocks:** 68 Nordic blue-chip stocks with liquid options markets
- **Date Range:** 2000-2025 (25 years)
- **Total Records:** 359K price records (filtered for options-enabled stocks)
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
- **68 stocks** (Nordic options universe)
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

## Using the Streamlit App - Quick Start

**For Stock-Specific Analysis:**
1. Go to **📈 Stock Analysis** tab
2. Select a stock from the dropdown
3. Choose a rolling period (start with 1-Month for most opportunities)
4. Set your date range
5. Study the price chart and support levels
6. Review performance statistics at the bottom

**For Comparative Analysis:**
1. Go to **🏆 Top Performers** tab
2. Choose your time period
3. Navigate through the 5 sub-tabs to explore different metrics
4. Use sub-tabs to identify:
   - **Success Metrics** → Most reliable stocks
   - **Resilience Metrics** → Longest-lasting supports
   - **Risk Metrics** → Lowest assignment risk
   - **Strategy Metrics** → Best expiry & wait time strategies
   - **Temporal Patterns** → Best months for each stock

**Pro Tips:**
- Combine metrics: Look for stocks with high success rate AND low downside risk
- Check seasonal patterns before writing puts
- Use wait time effectiveness to decide when to enter positions
- Compare across different rolling periods to find the best opportunity/reliability balance

---

*Last Updated: 2025-10-22*
*Status: H001 complete with Streamlit web app*
*Data Current Through: 2025-10-22*
