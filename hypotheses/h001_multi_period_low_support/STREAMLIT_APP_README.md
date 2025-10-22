# H001 Stock Analysis Streamlit Dashboard

An interactive dashboard for visualizing per-stock support level success/failure patterns with dynamic filtering.

## Features

### 🎯 Dynamic Filtering
- **Low Period Selector:** Choose between 1-month, 3-month, 6-month, 9-month, or 1-year lows
- **Stock Selector:** Select any of the 70 stocks in the analysis
- **Wait Days Selector:** Filter by wait time before writing the put (0, 30, 60, 90, 120, 180 days)
- **Expiry Days Selector:** Filter by put option duration (7, 14, 21, 30, 45 days)

### 📊 Interactive Visualizations
- **Price Chart with Support Events:**
  - Shows actual stock price history with overlay of support events
  - Green diamonds (✅) = Support held successfully
  - Red X marks (❌) = Support broke and failed
  - Hover over markers for detailed information

### 📅 Date Range Control
- **Date Range Slider:** Zoom in on specific time periods
- **From/To Date Pickers:** Set exact date ranges
- Chart updates automatically as you adjust the range

### 📈 Key Metrics
- Total support events matching filters
- Success rate percentage and count
- Average support level
- Min/Max prices for the stock
- Success breakdown by wait days and expiry days

### 📋 Detailed Data Table
- View all support events in the selected date range
- Columns include: support date, support level, wait days, expiry days, test date, min price, result, days to break, decline percentage
- Sortable and filterable

## How to Run

### Prerequisites
First, install Streamlit if not already installed:
```bash
pip install streamlit plotly pandas numpy
```

### Starting the Dashboard

From the hypothesis directory:
```bash
cd hypotheses/h001_multi_period_low_support
streamlit run stock_analysis_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Command Line with Custom Port
```bash
streamlit run stock_analysis_app.py --server.port 8502
```

## Dashboard Layout

### Sidebar (Left)
- **📅 Low Period:** Select the support period to analyze
- **🏢 Stock:** Choose which stock to display
- **⏳ Wait Days:** Multi-select which wait periods to include
- **📈 Expiry Days:** Multi-select which option durations to include

### Main Panel (Center/Right)

#### 1. Header with Key Metrics
Shows at a glance:
- Total events matching filters
- Success rate
- Average support level
- Min/Max prices

#### 2. Date Range Selector
- **From:** Start date for the chart (defaults to last 2 years)
- **To:** End date for the chart
- Only events and prices in this range are displayed

#### 3. Interactive Price Chart
- Full price history with all support events marked
- Hover tooltips show:
  - Support date
  - Support level
  - Wait days and expiry days
  - Min price during the option period
  - Test end date
  - For failures: days to break and decline percentage

#### 4. Success Rate Breakdown
- **By Wait Days:** Success rate for each wait period
- **By Expiry Days:** Success rate for each option duration

#### 5. Detailed Event Data Table
- Complete record of each support event
- Sortable by any column
- Shows all relevant metrics

#### 6. Summary Statistics
- Support level statistics (mean, median, std dev)
- Failure analysis (average decline, minimum price)
- Data coverage (date range, number of events in view)

## Understanding the Data

### Support Events
Each row represents one **support event**:
1. A low was set on `support_date` at price `support_level`
2. You waited `wait_days` before writing a put
3. You wrote a `expiry_days` day put option
4. Over the next `expiry_days`, we checked if price stayed above support
5. `success` = True if it held, False if it broke

### Success/Failure Markers
- **Green Diamond (✅):** The support level held for the entire option period - put expired worthless
- **Red X (❌):** The price fell below the support level - assignment risk occurred
- **Days to Break:** If failed, how many days it took for price to touch support
- **Decline %:** If failed, how far below support the price went

### Hover Tooltip Information
When you hover over a marker, you see:
- **Support Date:** When the low was established
- **Support Level:** The price level in kr
- **Wait Days:** How long you waited before writing the put
- **Expiry Days:** The put option duration
- **Min Price During Option:** The lowest price while the put was active
- **Test End Date:** When the option would have expired
- **Days to Break (failures only):** How quickly it failed
- **Decline % (failures only):** How far below support it went

## Tips and Tricks

### Finding Reliable Setups
1. Select a low period (recommend 1-month or 3-month for most opportunities)
2. Filter to wait_days = 90 (aged supports are more reliable)
3. Filter to expiry_days = 30 (typical option duration)
4. Look for stocks with success rates > 90%

### Analyzing Specific Time Periods
1. Use the date range picker to zoom into a time period
2. Watch for patterns (seasonal, before earnings, etc.)
3. Check correlation with other events in price history

### Comparing Wait Times
1. Keep other filters constant
2. Toggle different wait_days values
3. Watch how success rate changes with support age

### Identifying Problem Periods
1. Sort the data table by "Decline %" in descending order
2. Identify which periods had the biggest breaks
3. Check if there were external events (news, earnings, etc.)

## Data Source

This dashboard uses the parquet files generated by the H001 analysis:
- `{period}_detailed_results.parquet` - Detailed event-level data
- `../../price_data_filtered.parquet` - Stock price history (70 Nordic stocks)

The analysis covers:
- **70 stocks:** Nordic blue-chip stocks with liquid options markets
- **25 years:** 2000-2025 historical data
- **5 low periods:** 1-month, 3-month, 6-month, 9-month, 1-year
- **5 wait times:** 0, 30, 60, 90, 120, 180 days
- **5 expiry periods:** 7, 14, 21, 30, 45 days

## Performance Notes

- **Data Loading:** The app caches data on startup, so subsequent interactions are instant
- **Chart Rendering:** Interactive Plotly charts render quickly even with thousands of data points
- **Date Range Filtering:** Adjusting date ranges is nearly instant

## Troubleshooting

### "File not found" error
- Make sure you're in the correct directory: `hypotheses/h001_multi_period_low_support/`
- Verify the parquet files exist in this directory
- Verify `price_data_filtered.parquet` exists in the parent directory

### Chart not showing any markers
- No support events match your filter combination
- Try adjusting the date range or filter selections
- Select a stock with more data points

### Slow performance
- The app caches data, so the first load takes a moment
- If you change the dataset (parquet files), restart the Streamlit app to reload
- Use Ctrl+C to stop and `streamlit run` to restart

## Future Enhancements

Potential improvements:
- Add volume data overlay
- Show volatility regime during success/failure periods
- Compare multiple stocks side-by-side
- Export filtered data to CSV
- Add statistical significance testing
- Sector analysis and comparison

---

**Last Updated:** 2025-10-22
**Status:** Active
**Hypothesis:** H001 - Multi-Period Low Support Analysis
