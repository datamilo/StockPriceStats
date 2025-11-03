# H001: Multi-Period Support Level Analysis for Put Option Writing

> **📊 START HERE:** Choose your preferred analysis tool:
>
> **Option 1: Streamlit App (Recommended for comprehensive analysis)**
> ```bash
> streamlit run streamlit_app_lite.py
> ```
> Then open your browser to `http://localhost:8501`
>
> **Option 2: Standalone HTML Dashboard (Recommended for quick browsing)**
> ```bash
> # Self-contained version (no dependencies needed)
> open consecutive_breaks_dashboard.html
> # or just double-click the file in your file explorer
> ```
> Works offline, no installation required!

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

### Interactive Analysis Tools

#### **Streamlit Application** (Recommended)
- **`streamlit_app_lite.py`** - Main Streamlit application
  - Real-time analysis of any stock
  - Period selection (1/3/6/9/12 months)
  - Interactive price charts with rolling low visualization
  - Date range filtering
  - Support level markers (red dots when support breaks)
  - Performance statistics
  - Consecutive break clustering analysis

#### **Standalone HTML Dashboard** (Alternative)

- **`consecutive_breaks_dashboard.html`** (14.2 MB)
  - ✅ Fully self-contained, no dependencies
  - ✅ All data embedded in one HTML file
  - ✅ Just open in browser (works offline)
  - ✅ Perfect for sharing/archiving
  - ✅ No setup required - double-click to use
  - Interactive features: time range buttons, zoom, pan, dynamic y-axis scaling
  - Same data as Streamlit app but lighter experience

### Analysis Scripts
- **`multi_period_low_analysis.py`** - Full re-analysis (for first-time setup)
  - Regenerates all results from scratch
  - Takes 2-3 hours (only needed for methodology changes)
- **`multi_period_low_analysis_incremental.py`** - Incremental updates
  - Processes only new data (much faster)
  - Called automatically by `../update_analysis_data.py`
  - Takes 5-10 minutes for new data
- **`analyze_consecutive_breaks.py`** ⭐ NEW - Consecutive break pattern analysis
  - Identifies clusters of consecutive support breaks
  - Analyzes all stocks across all 5 periods
  - Generates parquet files with cluster data
  - Provides summary statistics and comparisons
- **`test_consecutive_breaks.py`** - Quick test/demo script
  - Demonstrates consecutive break analysis on a sample stock
  - Useful for understanding the clustering concept

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

## HTML Dashboard Guide

The standalone **`consecutive_breaks_dashboard.html`** provides a lightweight, offline-capable interface with the same analysis as the Streamlit app.

### How to Use

**Opening the Dashboard:**
1. Simply double-click `consecutive_breaks_dashboard.html` in your file explorer, OR
2. Right-click → Open with → Your web browser

**No installation or setup required!**

### Dashboard Features

**Top Controls:**
- **Stock Selector:** Choose from 68 Nordic stocks
- **Rolling Low Period:** Select 30d (1M), 90d (3M), 180d (6M), 270d (9M), or 365d (1Y)
- **Max Days Between Breaks:** Adjust clustering sensitivity (default: 30 days)

**Main Chart - Support Breaks Timeline**
- **Candlestick chart:** Daily price action (Open, High, Low, Close)
- **Blue dotted line:** Rolling low support level for selected period
- **Red dots:** Dates when support broke (new lower low identified)
- **Dynamic Y-axis:** Automatically scales to fit visible data when using time buttons
- **Interactive controls:**
  - **Time Range Buttons:** Quick navigation (All Data, 1Y, 6M, 3M, 1M)
  - **Box Zoom:** Click and drag on chart to zoom into specific area
  - **Pan:** Click and drag to move around the chart
  - **Hover:** See detailed values when hovering over prices

**Break Cluster Distribution Chart**
- Shows how many clusters have 1 break, 2 breaks, 3 breaks, etc.
- Colored bars indicate cluster intensity (yellow=1 break, orange=2-3, red=4+)
- Helps understand volatility patterns

**Key Metrics Cards**
- Total support breaks identified
- Total clusters found
- Number of multi-break clusters (volatility events)
- Maximum consecutive breaks in a cluster

**Cluster Statistics**
- Average duration of multi-break clusters
- Average gap between breaks in clusters
- Shortest gap observed (tightest clustering)

**Support Break Statistics**
- Total breaks and stability percentage
- Days since last break
- Average days until support breaks
- Downside risk when breaks occur
- Break patterns and frequency

**All Break Clusters Details**
- Expandable list of every cluster found
- Duration, gaps, and total price drop
- Individual break dates with drop magnitudes
- Cluster severity indicators (🔴 = multi-break, 🟡 = single)

### Interaction Tips

**For Fast Browsing:**
1. Click time range buttons (1M, 3M, 6M, 1Y) to jump to periods of interest
2. Look at the cluster distribution chart for volatility hot spots
3. Expand specific clusters to see exact break patterns

**For Detailed Analysis:**
1. Use box zoom (click-drag on chart) to examine specific periods closely
2. Watch how the y-axis rescales when you click time buttons
3. Compare cluster statistics across different rolling periods
4. Study individual break magnitudes in the cluster details

**For Offline Use:**
- Works without internet connection (all data embedded)
- Perfect for analysis on the go
- Share the file via email - recipient can open it without any software

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

4. **Consecutive Break Analysis** ⭐ NEW
   - Identifies clusters of consecutive support breaks
   - Shows when breaks happen in rapid succession (e.g., within days)
   - Interactive slider to adjust clustering definition (1-90 days)
   - Distribution chart of cluster sizes
   - Expandable cluster details showing:
     - Duration of each cluster
     - Average gap between breaks
     - Total price drop during cluster
     - Individual break dates and magnitudes
   - Summary statistics on clustering patterns
   - Critical for understanding risk during volatile periods

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

## Understanding Consecutive Break Patterns ⭐ NEW

### What Are Consecutive Breaks?

When support breaks, it often doesn't happen in isolation. Instead, breaks tend to **cluster together** during volatile periods. Understanding these patterns is critical for put option risk management.

**Example - AAK AB (3-month rolling low):**
- **2008 Financial Crisis Cluster:** 25 consecutive breaks over 126 days
  - Some breaks just 1 day apart
  - Total drop: -65.59%
  - Average gap: 11 days between breaks

- **Recent 2025 Cluster:** 16 consecutive breaks over 65 days
  - Total drop: -19.16%
  - Rapid succession of small breaks

### Why This Matters for Put Writing

**Risk Assessment:**
- If one support breaks, there's an 81.6% chance more breaks will follow soon (based on AAK AB example)
- During volatile periods, breaks cluster together with short gaps (1-14 days typical)
- Single isolated breaks are actually the minority (18.4% of cases)

**Strategy Implications:**
- Don't immediately write new puts after a support break
- Wait for the cluster to complete (volatility to settle)
- Use the "max gap" slider to identify when a cluster has likely ended
- Larger clusters often signal major trend changes (e.g., 2008 crisis)

### How to Use the Feature

1. **Select a stock** in the Streamlit app
2. **Scroll to "Consecutive Break Analysis"** section
3. **Adjust the gap slider** (default: 30 days)
   - Lower values (5-15 days): Identifies tight volatility clusters
   - Higher values (30-60 days): Broader trend identification
4. **Review the distribution chart** to see clustering patterns
5. **Expand cluster details** to see individual breaks

The analysis automatically identifies and groups breaks based on your gap definition, showing you exactly when and how breaks cluster together.

---

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

## Updating Data with New Stock Prices

When you have new stock price data and want to update the analysis:

### Quick Update Process (5-10 minutes)
```bash
# Simply run the automated update script
cd ~/StockPriceStats
python update_analysis_data.py

# That's it! The script automatically:
#   ✓ Fetches latest data from OneDrive (C:\Users\Gustaf\OneDrive\OptionsData)
#   ✓ Filters data to 70 options-enabled stocks
#   ✓ Analyzes only NEW dates (incremental)
#   ✓ Updates all 5 period result files
#   ✓ Commits changes to git
#   ✓ Pushes to GitHub
```

**Note:** The script automatically checks for the latest `price_data_all.parquet` in your OneDrive folder and copies it if it's newer than the local version. No manual copying needed!

### What Gets Updated
- `price_data_filtered.parquet` - Filtered stock data (70 stocks)
- `1_month_detailed_results.parquet` - Rolling low analysis results
- `3_month_detailed_results.parquet` - Rolling low analysis results
- `6_month_detailed_results.parquet` - Rolling low analysis results
- `9_month_detailed_results.parquet` - Rolling low analysis results
- `1_year_detailed_results.parquet` - Rolling low analysis results

### Performance
- **Incremental updates:** 5-10 minutes (recommended for regular updates)
- **Full re-analysis:** 2-3 hours (only needed for methodology changes)

### Viewing Updated Data
- **Local:** Refresh the Streamlit app (click "Rerun" in upper-right corner)
- **Streamlit Cloud:** Auto-redeploys within 10 seconds after GitHub push

### Detailed Documentation
For comprehensive update instructions, troubleshooting, and examples:
- **Quick Reference:** `../../QUICK_UPDATE_REFERENCE.txt`
- **Complete Guide:** `../../UPDATE_WORKFLOW.md`
- **Update Script:** `../../update_analysis_data.py`

---

*Last Updated: 2025-11-03*
*Status: H001 complete with Streamlit app + interactive HTML dashboard*
*Data Current Through: 2025-10-22*

## Recent Updates (2025-11-03)

### HTML Dashboard Enhancements
- ✅ Added rolling low blue dotted line visualization to match Streamlit app
- ✅ Added time range preset buttons (All Data, 1Y, 6M, 3M, 1M) for quick navigation
- ✅ Implemented dynamic y-axis scaling that adjusts to visible data
- ✅ Increased chart interactivity with box zoom and pan controls
- ✅ Removed rangeslider for cleaner interface
- ✅ Improved chart responsiveness and visibility (600px height)

### Dashboard is Now Feature-Complete
- Same data and analysis as Streamlit app
- No dependencies or installation required
- Works completely offline
- Perfect for sharing and quick analysis
