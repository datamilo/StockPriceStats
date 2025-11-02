# Stock Price Statistics - Put Option Writing Strategy

> **📋 Note:** This file serves as a **high-level index and overview** of the project.
> Detailed documentation, methodologies, and findings are located in subdirectories.
> Refer to the links below to access comprehensive documentation for each component.

---

## 🚨 CRITICAL DOCUMENTATION RULE

**ALL DOCUMENTATION MUST REFLECT CURRENT STATE ONLY**

- ✅ **DO:** Document what exists NOW and how it works TODAY
- ❌ **DON'T:** Keep historical notes, old troubleshooting, previous fixes, deprecated approaches
- ❌ **DON'T:** Keep obsolete files, backup files, old versions in hypotheses folders
- ✅ **DO:** Clean up and remove outdated content when updating documentation

**Why:** Documentation should guide users on the current system, not confuse them with historical context.

**When updating:**
1. Remove all references to old/deprecated approaches
2. Delete obsolete files from hypotheses folders (OLD/, backup files, etc.)
3. Update docs to reflect only the current working state
4. Keep it clean and focused on NOW

---

## Project Purpose

This project analyzes stock price data to determine optimal put option writing strategies. The goal is to collect premium by writing put options while minimizing the risk of assignment.

## Strategy Overview

**Put Option Writing for Premium Collection:**
- Write (sell) put options on selected stocks
- Collect premium upfront
- Objective: Options expire worthless (never get assigned)
- Focus: Identifying optimal strike prices that maximize premium while minimizing assignment risk

## Dataset

**Scope:**
- **All Data:** 678K records, 2,100 stocks (2000-2025)
- **Filtered Data:** 359K records, 68 Nordic stocks with liquid options markets
- **Geographic Focus:** Swedish, Norwegian, Danish, and Finnish blue-chip stocks

**Data Files:**
- `price_data_all.parquet` - Complete historical data
- `price_data_filtered.parquet` - Filtered data (options-enabled stocks only)
- `nasdaq_options_available.csv` - List of 68 stocks with available options

**Filtering Rationale:** Only stocks with liquid options markets can be used for this strategy, reducing the universe to 68 actionable candidates. (Note: Fortnox AB and Kindred Group plc were delisted and removed from analysis)

---

## ⚠️ IMPORTANT: Time Estimates

**CRITICAL RULE: NEVER give time estimates unless you are 100% certain they are correct.**

- ❌ **WRONG:** "This will take about 30 minutes", "Should be done in an hour", "Approximately 15 minutes"
- ✅ **CORRECT:** "The analysis is currently running. Check progress by looking at file timestamps or process status"

**Why:**
- Complex tasks depend on too many variables (data size, CPU cores, I/O, memory contention, system load)
- Estimates are almost always wrong
- False time estimates create false expectations and frustration
- It's better to provide NO estimate than an incorrect one

**Instead of estimates:**
- Check actual progress indicators (process CPU/memory, file modification times, console output)
- Report what you observe: "70/70 stocks processed for 1-Month LOW, currently processing 6-Month LOW"
- Invite the user to check back when they want updates: "Check in whenever you like for progress updates"
- Never use words like "should", "should take", "approximately", "about", "estimated"

---

## ⚠️ IMPORTANT: Currency Convention

**This is a Swedish market analysis. ALL currency references MUST use Swedish Krona (kr), NEVER USD ($).**

- ✅ **Correct:** "50 kr", "100 kr", "price of 250 kr"
- ❌ **Wrong:** "$50", "$100", "price of $250", "SEK"

**Rules:**
- Use "kr" for Swedish Krona (not "SEK")
- Never use "$" or "USD" in any documentation, examples, code comments, or dashboards
- All price examples should reflect realistic Swedish stock prices (typically 50-500 kr range)
- When creating examples or documentation, always use "kr" as the currency symbol

---

## Project Structure

```
StockPriceStats/
├── CLAUDE.md (this file - index)
├── price_data_all.parquet
├── price_data_filtered.parquet
├── nasdaq_options_available.csv
├── filter_relevant_stocks.py
├── example_analysis.py
└── hypotheses/
    └── h{NNN}_{name}/
        ├── README.md
        ├── METHODOLOGY_AND_FINDINGS.md
        ├── dashboard.html
        └── [analysis scripts and results]
```

---

## Hypotheses Testing Framework

This project uses a **structured hypothesis testing approach** to systematically evaluate put option writing strategies.

### Directory Structure

**Location:** `hypotheses/`

**Naming Convention:** `h{NNN}_{short_description}/`
- `NNN` = 3-digit hypothesis number (001, 002, 003, ...)
- `short_description` = Brief snake_case name

### Standard Files in Each Hypothesis

Every hypothesis folder contains:

| File | Purpose |
|------|---------|
| `README.md` | Quick reference, overview, and navigation |
| `METHODOLOGY_AND_FINDINGS.md` | Comprehensive detailed analysis |
| `*dashboard.html` | Interactive visualization dashboard (recommended starting point) |
| `*.py` | Analysis scripts |
| `*.csv` | Results data |
| `*.png` | Static visualization charts |

**Dashboard Features (H001 example):**
- Self-contained with comprehensive explanations
- Interactive charts with date range sliders
- Visual event markers
- All examples use kr (Swedish Krona)

---

## Active Hypotheses

### H001: Multi-Period Low Support Analysis

**Location:** `hypotheses/h001_multi_period_low_support/`

**Question:** Do we need to wait for a full 1-year low, or are shorter-term lows (1, 3, 6, 9 months) just as reliable for put option writing?

**Result:** ✅ **VALIDATED** - Shorter-term lows work equally well as longer-term lows, with 6-7x more trading opportunities!

**Key Findings:**
- **1-Month Lows:** 89.7% success rate with continuous daily opportunities
- **3-Month Lows:** 89.0% success rate with 6-7x more opportunities than 1-year lows
- **1-Year Lows:** 87.8% success rate but fewer opportunities
- **Conclusion:** Shorter-term rolling lows are superior for put option writing because they provide equal reliability with significantly more trading opportunities

**📊 View & Analyze:**
- **Interactive Streamlit App:** `hypotheses/h001_multi_period_low_support/streamlit_app_lite.py` ⭐ **START HERE**
  - Run locally: `streamlit run hypotheses/h001_multi_period_low_support/streamlit_app_lite.py`
  - Or deployed on Streamlit Cloud (if available)
  - Real-time analysis of any stock
  - Visual support level markers
  - Interactive price charts with rolling low overlay
  - All prices in Swedish Krona (kr)
- **Quick Reference:** `hypotheses/h001_multi_period_low_support/README.md`
- **Detailed Methodology:** `hypotheses/h001_multi_period_low_support/METHODOLOGY_AND_FINDINGS.md`

**What We Tested:**
- 70 Nordic stocks with liquid options markets
- 25 years of historical data (2000-2025)
- 5 rolling low periods: 1-month, 3-month, 6-month, 9-month, 1-year
- 6 wait times after support identification: 0-180 days
- 5 option expiry periods: 7-45 days
- Results: ~30 million test cases across all stocks and time periods

---

## Future Hypotheses (Planned)

### H002: Multi-Year Lows
- Test 2-year and 3-year lows as support levels
- Hypothesis: Longer-term lows may be more significant

### H003: Volume-Confirmed Supports
- Require low volume during support testing period
- Hypothesis: Low volume = less selling pressure = stronger support

### H004: Trend Context Analysis
- Separate uptrend vs downtrend support levels
- Hypothesis: Uptrend lows are more reliable

### H005: Volatility Regime Analysis
- High IV vs Low IV environment comparison
- Hypothesis: Support reliability varies by volatility regime

---

## Data Update Workflow

When you have new stock price data, updating the analysis is now streamlined and automated:

### Quick Update Process
```bash
# 1. Place your new price data file
cp /path/to/new/price_data_all.parquet ~/StockPriceStats/

# 2. Run the master update script
cd ~/StockPriceStats
python update_analysis_data.py

# 3. Sync to GitHub (optional)
git add .
git commit -m "Update: New price data"
git push origin main
```

**Time:** ~5-10 minutes (fully automated)

### What Happens Automatically
1. **Data Filtering:** Converts `price_data_all.parquet` → `price_data_filtered.parquet` (70 stocks only)
2. **Incremental Analysis:** Updates H001 analysis with ONLY new data (not entire dataset)
3. **File Updates:** All parquet files updated with latest analysis through current date

### Performance
- **Old Way:** Full re-analysis took 2-3 hours
- **New Way:** Incremental updates take 5-10 minutes
- **Speed Improvement:** 15-30x faster! 🚀

### Documentation
- **Quick Reference:** `QUICK_UPDATE_REFERENCE.txt` - One-page cheat sheet
- **Complete Guide:** `UPDATE_WORKFLOW.md` - Detailed instructions with examples
- **Script Code:** `update_analysis_data.py` - Automated master update script

---

## Adding New Hypotheses

**Workflow:**

1. **Create Directory:**
   ```bash
   mkdir hypotheses/h{NNN}_{name}
   ```

2. **Create Core Files:**
   - `README.md` - Quick reference and overview
   - `METHODOLOGY_AND_FINDINGS.md` - Detailed analysis
   - Analysis scripts (Python)

3. **Required Content:**
   - Clear hypothesis statement
   - Methodology description
   - Results and findings
   - Risk implications for put writing
   - Recommendation (supported/rejected)

4. **Update This File:**
   - Add hypothesis to "Active Hypotheses" section
   - Include brief summary and result
   - Link to detailed documentation

5. **Optional but Recommended:**
   - Create `dashboard.html` for interactive visualization
   - Generate charts and summary statistics
   - Export detailed results to CSV

---

## Documentation Philosophy

**This CLAUDE.md file:**
- ✅ Provides high-level project overview
- ✅ Acts as an index to detailed documentation
- ✅ Lists active hypotheses with quick summaries
- ✅ Shows project structure
- ❌ Does NOT contain detailed methodologies
- ❌ Does NOT contain full results
- ❌ Does NOT contain comprehensive findings

**For detailed information:**
- Navigate to the specific hypothesis folder
- Start with the interactive `dashboard.html` (if available)
- Read `README.md` for quick reference
- Consult `METHODOLOGY_AND_FINDINGS.md` for comprehensive analysis

**Goal:** Keep this file clean, scannable, and easy to navigate while maintaining comprehensive documentation in appropriate subdirectories.

---

## Quick Navigation

| Component | Location | Description |
|-----------|----------|-------------|
| **Project Overview** | This file | High-level summary |
| **H001 Dashboard** | `hypotheses/h001_multi_period_low_support/multi_period_dashboard.html` | Interactive results viewer |
| **H001 Details** | `hypotheses/h001_multi_period_low_support/METHODOLOGY_AND_FINDINGS.md` | Comprehensive analysis |
| **Data Filtering** | `filter_relevant_stocks.py` | Script to filter dataset |
| **Example Analysis** | `example_analysis.py` | Technical analysis example |

---

*Last Updated: 2025-10-22*
*Active Hypotheses: 1*
*Status: H001 complete and validated with Streamlit app*
*Data Workflow: Fully automated with incremental updates*
