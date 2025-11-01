# Top Lists - Pre-Calculated Statistics

## Overview

The Top Lists feature in the Streamlit app shows rankings of stocks based on historical support level behavior. To ensure fast loading times, these statistics are **pre-calculated** and stored in parquet files.

## How It Works

### 1. Pre-Calculation Script

**File:** `calculate_top_lists.py`

This script processes all 68 stocks for all 5 rolling low periods (1-Month, 3-Month, 6-Month, 9-Month, 1-Year) and calculates:

- Total breaks
- Average/median days between breaks
- Trading days per break
- Stability %
- Average/max break magnitude
- Days since last break

**Runtime:** ~45 minutes for all stocks and periods

### 2. Output Files

**Directory:** `top_lists/`

Generated files:
- `1_month_top_lists.parquet` (~9KB)
- `3_month_top_lists.parquet` (~9KB)
- `6_month_top_lists.parquet` (~9KB)
- `9_month_top_lists.parquet` (~9KB)
- `1_year_top_lists.parquet` (~9KB)

### 3. Streamlit App

The app loads these pre-calculated files instantly (< 1 second) instead of calculating in real-time.

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
```

## Integration with Update Workflow

You can integrate this into your existing data update workflow by adding it to `update_analysis_data.py`:

```python
# After updating price_data_filtered.parquet
import subprocess

print("Regenerating top lists...")
subprocess.run([
    'python',
    'hypotheses/h001_multi_period_low_support/calculate_top_lists.py'
])
```

## Benefits

✅ **Instant Loading** - App loads in < 1 second (vs 30-60 seconds before)
✅ **Better UX** - No waiting for calculations
✅ **Scalable** - Can handle much larger datasets
✅ **Consistent** - Same statistics every time until explicitly regenerated
✅ **Efficient** - Only calculates when data actually changes

## File Sizes

The parquet files are small (~9KB each, 45KB total) because they only store:
- 66-68 rows (one per stock)
- 9 columns (statistics)
- Highly compressed format

## Maintenance

**Monthly:** Regenerate after price data updates
**On-demand:** Regenerate if calculation logic changes
**Git:** Files are committed to repo for easy deployment
