# H001 Support Level Analyzer - Lite Version

A lightweight Streamlit app for investigating support levels on a single stock at a time. Designed to be fast and stable without crashing.

## Features

✅ **Lightweight Data Loading** - Only loads the stock and date range you select
✅ **Interactive Charts** - Zoom, pan, hover for details
✅ **Multiple Time Periods** - Test 1M, 3M, 6M, 9M, 1Y rolling lows
✅ **Visual Support Markers** - Green for successful supports, red for failures
✅ **Data Table** - View all prices and rolling lows
✅ **No Crashes** - Handles large datasets gracefully

## How to Run

### Option 1: Run from the hypothesis directory

```bash
cd /home/gustaf/StockPriceStats/hypotheses/h001_multi_period_low_support/
streamlit run streamlit_app_lite.py
```

Then open your browser to: `http://localhost:8501`

### Option 2: Run from project root

```bash
cd /home/gustaf/StockPriceStats/
streamlit run hypotheses/h001_multi_period_low_support/streamlit_app_lite.py
```

## How to Use

1. **Select a Stock** - Use the dropdown in the sidebar to pick any of the 70 stocks
2. **Set Date Range** - Use the date pickers to zoom in on a specific period
3. **Choose Rolling Low Period** - Select which rolling low to analyze (1-Month, 3-Month, etc.)
4. **View the Chart** - The chart shows:
   - **Candlestick**: Daily OHLC prices
   - **Blue dashed line**: The rolling low for your selected period
   - **Green circles**: Support levels that held (price didn't breach)
   - **Red circles**: Support levels that failed (price went below)
5. **Explore the Table** - Scroll down to see all daily prices and rolling lows

## What You're Looking For

When investigating why there are "so many low points":

- **Observe:** The rolling low (blue dashed line) does NOT change every day
- **Expected:** It stays flat for stretches, then jumps to new lows when:
  - A new lower price enters the rolling window, OR
  - An older low price exits the rolling window
- **Support Markers:** Each time the rolling low is identified, it becomes a test case for whether it will hold as support

## Example: AAK AB from 2006-2007

You'll notice:
- The rolling low stays at 26.50 kr for about 16 consecutive days
- Then stays at 26.50 kr for another 17 consecutive days
- This is normal - it only changes when prices change

The high number of "low points" is actually correct because:
1. You have 5,000+ trading days per stock
2. Many of those days create new rolling lows
3. But they're not random - they follow the price history exactly

## Troubleshooting

### App is still slow
- Try a shorter date range (e.g., just one year instead of all data)
- Close any other memory-intensive apps
- The app caches data after first load, so it should be faster on second run

### No data showing
- Make sure the date range includes data for that stock
- Some stocks might not have data for the entire period

### Support markers not showing
- The H001 analysis for that stock might not be computed yet
- The app will still show the price and rolling low even without analysis results

## Files Used

- `../../price_data_filtered.parquet` - Price data for all 70 stocks
- `*_detailed_results.parquet` - H001 analysis results (if available)

## Performance Notes

This lite version:
- ✅ Loads only the selected stock (not all stocks at once)
- ✅ Filters by date range before processing
- ✅ Caches data after first load
- ✅ Uses lightweight Plotly charts (not heavy dashboards)
- ✅ Should handle your data easily without crashes

Compared to the full app which loads all data for all stocks at once.
