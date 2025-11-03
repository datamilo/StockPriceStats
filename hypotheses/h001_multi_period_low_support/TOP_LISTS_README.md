# Top Lists - Pre-Calculated Statistics

## Overview

The Top Lists feature in the Streamlit app shows rankings of stocks based on historical support level behavior. To ensure fast loading times, these statistics are **pre-calculated** and stored in parquet files.

## How It Works

### 1. Pre-Calculation Script

**File:** `calculate_top_lists.py`

This script processes all 68 stocks for all 5 rolling low periods (1-Month, 3-Month, 6-Month, 9-Month, 1-Year) and calculates:

- **First Date / Last Date / Years of Data** - Data range for fair comparisons
- **Total breaks** - Number of times support was broken
- **Avg Days Between** - Average calendar days between breaks (useful metric)
- **Median Days Between** - Median spacing (calculated but hidden - not useful for ranking)
- **Trading Days per Break** - Break frequency normalized to trading days
- **Stability %** - Percentage of days without breaks
- **Avg/Max Break %** - Magnitude of support breaks
- **Days Since Last** - Recency of last break

**Runtime:** ~30-40 minutes for all stocks and periods

**Auto-Commit:** Script automatically commits and pushes to GitHub when complete

### 2. Output Files

**Directory:** `top_lists/`

Generated files:
- `1_month_top_lists.parquet` (~12KB)
- `3_month_top_lists.parquet` (~12KB)
- `6_month_top_lists.parquet` (~12KB)
- `9_month_top_lists.parquet` (~12KB)
- `1_year_top_lists.parquet` (~12KB)

### 3. Streamlit App

The app loads these pre-calculated files instantly (< 1 second) instead of calculating in real-time.

**Data Quality Filter:** The app includes a sidebar filter for minimum years of historical data (default: 5 years). This prevents stocks with limited data (e.g., Autoliv with 1.8 years) from dominating rankings unfairly.

## When to Regenerate

Run the pre-calculation script whenever:

1. **Price data is updated** - New daily prices added to `price_data_filtered.parquet`
2. **First time setup** - Initial installation of the dashboard
3. **After code changes** - If calculation logic in `calculate_rolling_low()` or `analyze_support_breaks()` is modified

## How to Regenerate

```bash
cd /path/to/StockPriceStats
python hypotheses/h001_multi_period_low_support/calculate_top_lists.py
```

**Output:**
```
================================================================================
TOP LISTS CALCULATION
================================================================================
Loading price data...
Loaded 350,657 rows for 68 stocks

Calculating statistics for 1-Month (30 days)...
  [68/68] Processing Volvo, AB ser. B...  Completed! 68 stocks with statistics
  Saved to: .../top_lists/1_month_top_lists.parquet

Calculating statistics for 3-Month (90 days)...
  [68/68] Processing Volvo, AB ser. B...  Completed! 68 stocks with statistics
  Saved to: .../top_lists/3_month_top_lists.parquet

... (continues for all periods)

================================================================================
✓ All calculations complete!
✓ Files saved to: .../top_lists
================================================================================

Committing and pushing to GitHub...
✓ Changes committed and pushed successfully!
```

## Integration with Update Workflow

**RECOMMENDED:** Use the master update script to update all Streamlit data at once:

```bash
python update_streamlit_data.py
```

This single command:
1. Filters price data to relevant stocks (~1 min)
2. Runs incremental H001 analysis (~5-10 min)
3. Regenerates top lists (~30-40 min)
4. Commits and pushes everything to GitHub automatically

**Total time:** ~35-50 minutes

See `STREAMLIT_UPDATE_GUIDE.txt` for full documentation.

## Benefits

✅ **Instant Loading** - App loads in < 1 second (vs 30-60 seconds before)
✅ **Better UX** - No waiting for calculations
✅ **Scalable** - Can handle much larger datasets
✅ **Consistent** - Same statistics every time until explicitly regenerated
✅ **Efficient** - Only calculates when data actually changes

## File Sizes

The parquet files are small (~12KB each, 60KB total) because they only store:
- 66-68 rows (one per stock)
- 12 columns (statistics including data range tracking)
- Highly compressed format

## Maintenance

**Monthly:** Regenerate after price data updates using `update_streamlit_data.py`
**On-demand:** Regenerate if calculation logic changes
**Git:** Files are automatically committed and pushed to repo for easy deployment
