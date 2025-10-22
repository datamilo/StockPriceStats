# Streamlined Data Update Workflow

## Quick Start (TL;DR)

After you get new stock price data:

1. **Place** `price_data_all.parquet` in the main `StockPriceStats/` folder
2. **Run** `python update_analysis_data.py`
3. **Done!** The Streamlit app will use the updated data automatically

That's it. Takes about 5-10 minutes total.

---

## What Gets Updated?

When you run `python update_analysis_data.py`, the following automatically happens:

### 1. Data Filtering
- **Input:** `price_data_all.parquet` (all 2,100+ stocks)
- **Process:** Filters to only the 70 Nordic stocks with liquid options
- **Output:** `price_data_filtered.parquet` (367K+ records)

### 2. Incremental H001 Analysis
- **Input:** `price_data_filtered.parquet` (newly filtered)
- **Process:** Analyzes ONLY the new dates (since last update)
  - Detects max date in existing results (e.g., 2025-10-17)
  - Only processes new dates (e.g., 2025-10-18 onwards)
  - Uses multiprocessing for speed
- **Output:** Appends to 5 parquet files:
  - `1_month_detailed_results.parquet`
  - `3_month_detailed_results.parquet`
  - `6_month_detailed_results.parquet`
  - `9_month_detailed_results.parquet`
  - `1_year_detailed_results.parquet`

### 3. Streamlit App Update
- Automatically uses new data on next refresh
- No configuration needed
- Works locally and on Streamlit Cloud

---

## Performance

### Old Way (Still Available)
```bash
# Full re-analysis from scratch
cd hypotheses/h001_multi_period_low_support
python multi_period_low_analysis.py
```
- **Time:** 2-3 hours
- **Use case:** First-time analysis or if you want to regenerate everything

### New Way (Recommended)
```bash
# Incremental update - only process new data
python update_analysis_data.py
```
- **Time:** 5-10 minutes (for a few days of new data)
- **Use case:** Regular updates after new price data arrives

**Speed Difference:** ~15-30x faster for incremental updates!

---

## File Structure

### Main Folder (`StockPriceStats/`)
```
price_data_all.parquet              ← Your NEW/UPDATED price data (put here)
price_data_filtered.parquet         ← Auto-updated by the script (70 stocks)
update_analysis_data.py             ← THE SCRIPT TO RUN (this one!)
filter_relevant_stocks.py           ← Called automatically
example_analysis.py                 ← For reference
```

### H001 Folder (`hypotheses/h001_multi_period_low_support/`)
```
streamlit_app_lite.py               ← The Streamlit web app
multi_period_low_analysis.py        ← Full re-analysis (if needed)
multi_period_low_analysis_incremental.py  ← Incremental updates (called automatically)
1_month_detailed_results.parquet    ← Auto-updated results
3_month_detailed_results.parquet    ← Auto-updated results
6_month_detailed_results.parquet    ← Auto-updated results
9_month_detailed_results.parquet    ← Auto-updated results
1_year_detailed_results.parquet     ← Auto-updated results
```

---

## Step-by-Step Example

### Scenario: You have new stock data for Oct 18-22, 2025

**Step 1:** Place the updated price file
```bash
# Copy your updated data to the main folder
cp /path/to/your/price_data_all.parquet ~/StockPriceStats/
```

**Step 2:** Run the update script
```bash
cd ~/StockPriceStats
python update_analysis_data.py
```

**Step 3:** Watch the magic happen
```
================================================================================
        STOCKPRICESTATS - MASTER DATA UPDATE SCRIPT
        (Updates H001 analysis with one command)
================================================================================

STEP: PRE-FLIGHT CHECKS
✓ Found price_data_all.parquet (17.1 MB)
✓ Found filter script
✓ Found incremental analysis script

STEP: Filter price data to relevant stocks
2025-10-22 12:30:52 - INFO - ✓ Found 70 stocks with options
2025-10-22 12:30:52 - INFO - ✓ Loaded 678,713 records from price_data_all.parquet
2025-10-22 12:30:53 - INFO - ✓ Filtering complete: 678,713 → 367,588 records
✓ Filter script completed successfully!

STEP: Analyze new data and append to H001 results
================================================================================
1-Month: Last analyzed date: 2025-10-17
Will analyze dates AFTER: 2025-10-17
✓ Generated 1,945 new test cases
✓ Updated 1_month_detailed_results.parquet
  - Old size: 3,009,145 rows
  - New size: 3,011,090 rows
  - Added: 1,945 rows

3-Month: ... (similar for other periods)

✓ INCREMENTAL ANALYSIS COMPLETE!
✓ ALL UPDATES COMPLETE!
```

**Step 4:** Verify results
- Check that all parquet files were updated
- Run the Streamlit app locally: `streamlit run hypotheses/h001_multi_period_low_support/streamlit_app_lite.py`
- If deployed on Streamlit Cloud, it will auto-redeploy within seconds (data was automatically pushed to GitHub)

**Note:** The script automatically commits and pushes changes to GitHub, so no manual git operations are needed!

---

## Troubleshooting

### Error: "price_data_all.parquet not found"
- Make sure you placed the file in the main `StockPriceStats/` folder (not in a subfolder)
- File name must be exactly `price_data_all.parquet`

### Error: "Filter script failed"
- Make sure `filter_relevant_stocks.py` exists in the main folder
- Check that `nasdaq_options_available.csv` exists (list of 70 stocks with options)

### Error: "Incremental analysis failed"
- Make sure `multi_period_low_analysis_incremental.py` exists in `hypotheses/h001_multi_period_low_support/`
- Make sure existing parquet files are readable

### Script runs but takes hours
- You may have accidentally run `multi_period_low_analysis.py` instead of the master script
- Run `python update_analysis_data.py` instead

### Streamlit app shows old data
- Click "Rerun" in the app (upper right corner)
- Or restart the Streamlit server locally

---

## Under the Hood: How Incremental Updates Work

### The Smart Detection
```python
1. Load existing analysis results (e.g., 1_month_detailed_results.parquet)
2. Find the max support_date (e.g., 2025-10-17)
3. Load new price data
4. Filter price data to only dates AFTER 2025-10-17
5. Analyze only the new data (2025-10-18 onwards)
6. Append new results to existing file
```

### Why It's Fast
- Old way: Re-analyze ALL 25 years of data for ALL 70 stocks
- New way: Analyze only 5 days of new data for ALL 70 stocks
- Result: ~98% less work = 15-30x faster

### Data Integrity
- Duplicates removed automatically (if any)
- DateTime columns preserved correctly
- Original data never overwritten (safe append)
- Can re-run safely without issues

---

## When to Use Full Re-analysis

Sometimes you may want to run the full analysis from scratch:

```bash
cd hypotheses/h001_multi_period_low_support
python multi_period_low_analysis.py  # Takes 2-3 hours
```

**Use cases:**
- First time setting up the project
- You changed the analysis methodology
- You want to verify results from scratch
- Data was corrupted and you want to rebuild

For regular updates (new price data), always use `python update_analysis_data.py`

---

## Deployment Notes

### Local Usage
```bash
python update_analysis_data.py    # Updates all data
cd hypotheses/h001_multi_period_low_support
streamlit run streamlit_app_lite.py  # View in browser
```

### Streamlit Cloud
1. Push updated files to GitHub
2. Streamlit Cloud auto-detects changes
3. Automatically redeploys within 10 seconds
4. New data available globally within minutes

### Git Workflow
The `update_analysis_data.py` script now handles git operations automatically:
```bash
# Just run the script - it does everything!
python update_analysis_data.py
# ✓ Updates all data
# ✓ Automatically commits with descriptive message
# ✓ Automatically pushes to GitHub
# ✓ Streamlit Cloud redeploys automatically!
```

---

## Summary

| Task | Command | Time |
|------|---------|------|
| Regular updates (recommended) | `python update_analysis_data.py` | 5-10 min |
| Full re-analysis | `python multi_period_low_analysis.py` | 2-3 hours |
| View app locally | `streamlit run hypotheses/h001_multi_period_low_support/streamlit_app_lite.py` | - |
| Deploy to cloud | `git push` | 10 sec |

**Bottom Line:** Place your data file, run one script, done. ✓

---

*Last Updated: 2025-10-22*
*Workflow: Streamlined and automated*
