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

## 🔄 GitHub Sync Workflow

**CRITICAL: Always sync changes to GitHub after completing any work**

### After Making Changes

```bash
# 1. Check what changed
git status
git diff [filename]  # Optional: review specific changes

# 2. Stage and commit changes
git add .
git commit -m "Description of changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 3. Push to GitHub
git push origin main
```

### Why This Is Important

- **Backup:** Protects work from local system failures
- **Collaboration:** Makes changes available to all team members
- **History:** Creates permanent record of what changed and why
- **Deployment:** Streamlit Cloud auto-deploys from GitHub main branch

### What to Commit

✅ **Always commit:**
- Code changes (Python scripts, analysis files)
- Documentation updates (README.md, CLAUDE.md, etc.)
- New results data (parquet files, CSV files)
- Configuration changes

❌ **Never commit:**
- Temporary files (.pyc, __pycache__)
- Personal notes or scratch files
- Large binary files not needed for analysis
- Sensitive credentials or API keys

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
- **Standalone HTML Dashboard:** `hypotheses/h001_multi_period_low_support/consecutive_breaks_dashboard.html`
  - No installation required - just double-click to open
  - Works offline with all data embedded
  - Master date range filter for flexible period analysis
  - Dynamic y-axis scaling for all time range buttons
  - Complete cluster metrics and break tables
  - Perfect for sharing and quick analysis
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

## Probability Validation Report

**Location:** `Options/probability_validation_report.html`

This interactive HTML report validates the accuracy of 5 different probability prediction methods by comparing predicted probabilities against actual outcomes for 934,643 expired options (2024-2025).

### Key Features

**📊 Interactive Calibration Analysis**
- Filter by individual stock or view all stocks combined
- See how well each prediction method performs for specific stocks
- Identify which stocks have models that are well-calibrated for put option writing

**📅 Days-to-Expiry (DTE) Analysis**
- Analyze how prediction accuracy varies based on time to expiration
- **IMPORTANT: Uses CALENDAR DAYS (not business days)** between prediction date and expiry
- 7 granular bins for detailed analysis:
  - 0-3 days (very short-term)
  - 4-7 days
  - 8-14 days
  - 15-21 days
  - 22-28 days
  - 29-35 days
  - 35+ days (longer-term predictions)
- Dual filtering: Select stock AND days-to-expiry range simultaneously

**🏆 Winner: Weighted Average Method**
- Best performance across Brier Score, AUC-ROC, and calibration error
- Exceptional calibration: Only 0.32% average error
- 934,643 validated predictions provide statistically significant results

### How to Use

1. **Open the Report:**
   - Double-click `Options/probability_validation_report.html` to open in browser
   - No installation required - fully self-contained

2. **Explore Overall Performance:**
   - View executive summary with key metrics
   - Compare performance metrics across all 5 methods
   - Review detailed calibration analysis

3. **Stock-Level Analysis:**
   - Use "Select Stock" dropdown in Calibration Analysis section
   - Choose from 75 unique stocks
   - See calibration curves specific to that stock

4. **Days-to-Expiry Analysis:**
   - Use stock AND DTE bin dropdowns in "Calibration by Days to Expiry" section
   - Examples:
     - "How accurate are predictions for Volvo with 0-3 days to expiry?"
     - "Do longer-term predictions (35+ days) work better for all stocks vs individual stocks?"
     - "Which stocks have better calibration for very short-term (0-3 days) options?"

### Technical Details

**5 Prediction Methods Evaluated:**
1. **Weighted Average** - Brier-score weighted combination of all methods
2. **Bayesian Calibrated** - Bayesian isotonic calibration with binning
3. **Original Black-Scholes** - Standard Black-Scholes probability (filtered to ≥50% prob)
4. **Bias Corrected** - Per-bin bias correction based on historical accuracy
5. **Historical IV** - Historical implied volatility accuracy tables

**Key Metrics Explained:**
- **Brier Score:** Measures accuracy (0=perfect, 1=worst). Lower is better.
- **AUC-ROC:** Ability to discriminate between outcomes (0.5=random, 1=perfect). Higher is better.
- **Log Loss:** Penalizes confident wrong predictions. Lower is better.
- **Expected Calibration Error (ECE):** Average difference between predicted and actual rates. Lower is better.

---

## "Fallen Angels" Analysis

**Location:** `Options/fallen_angels_report.html`

This groundbreaking analysis discovered that **options with historical high probability (90%+) that dropped to lower levels still expire worthless FAR more often** than their current probability suggests.

### Key Discovery: +43 Percentage Point Advantage!

**The Finding:** Options currently at 60-70% probability that previously peaked at 90%+ expire worthless **84.8%** of the time, while baseline options at the same 60-70% probability only expire worthless **41.8%** of the time.

**This is a massive +43pp advantage** - the historical high probability is a powerful additional signal!

### What Are "Fallen Angels"?

Options that:
1. ✅ Previously reached 90%+ probability of expiring worthless at some point during their life
2. ✅ Subsequently dropped to lower probabilities (60-90%) as the stock price moved
3. ✅ Still retain the fundamental strength indicated by their historical peak

### Strategy Implications for Put Writing

**Traditional Approach:** Write puts at 70% probability → expect 70% success rate

**Fallen Angels Approach:** Write puts at 70% probability that were previously 90%+ → expect **85-90% success rate!**

This means:
- **Much safer positions** for the same premium
- **Lower assignment risk** than current probability suggests
- **Better risk-adjusted returns** by selecting the right options

### When the Effect is Strongest

**Best Scenarios (by advantage):**
1. **36+ days to expiry:** +28pp to +43pp advantage
2. **Current probability 60-70%:** Largest absolute advantage
3. **Bayesian Calibrated method:** Clearest signal (+43pp)
4. **Current probability 70-80%:** Still strong at +16pp to +34pp

### How to Use

1. **Open the Report:**
   - Open `Options/fallen_angels_report.html` in your browser
   - Interactive filtering by method, current probability, stock, and DTE

2. **Identify Opportunities:**
   - Filter to your preferred probability method (recommend Bayesian Calibrated)
   - Select current probability range (60-70% or 70-80% show strongest effects)
   - Review advantage by days to expiry

3. **Apply in Practice:**
   - Track options over time to identify when they peak at 90%+
   - When they drop to 60-80%, prioritize these for put writing
   - Focus on longer-dated options (36+ days) for maximum advantage

### Analysis Details

**Data Analyzed:**
- 2,958,138 option-date records across 934,643 expired options
- All 5 probability prediction methods compared
- Full breakdown by: current probability (60-70%, 70-80%, 80-90%), days to expiry (7 bins), and stock (75 stocks)

**Top 3 Scenarios:**
1. Bayesian Calibrated | 60-70% | 36+ days: **+43.03pp** (33,333 fallen angels)
2. Original Black-Scholes | 60-70% | 36+ days: **+39.61pp** (32,984 fallen angels)
3. Bias Corrected | 60-70% | 36+ days: **+38.15pp** (30,848 fallen angels)

### Files Generated

- `Options/fallen_angels_report.html` - Interactive visualization (203 KB)
- `Options/fallen_angels_results/fallen_angels_summary.csv` - 90 scenarios analyzed
- `Options/fallen_angels_results/fallen_angels_by_stock.csv` - 1,097 stock-specific results
- `Options/fallen_angels_results/fallen_angels_details.csv` - Full dataset (2.96M records)

### Important Caveats

⚠️ **Risk Warnings:**
- Historical patterns don't guarantee future performance
- Market conditions can change rapidly
- Always use appropriate position sizing
- This is backtesting on historical data
- Never rely solely on any single indicator

✅ **Best Practices:**
- Use as **one factor** in put writing decisions
- Combine with fundamental analysis
- Monitor positions actively
- Maintain proper risk management
- Start with small position sizes when testing the strategy

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
| **Fallen Angels Analysis** | `Options/fallen_angels_report.html` | **⭐ NEW!** Historical probability advantage (+43pp) |
| **Probability Validation** | `Options/probability_validation_report.html` | Interactive report with stock & DTE filtering |
| **H001 Dashboard** | `hypotheses/h001_multi_period_low_support/multi_period_dashboard.html` | Interactive results viewer |
| **H001 Details** | `hypotheses/h001_multi_period_low_support/METHODOLOGY_AND_FINDINGS.md` | Comprehensive analysis |
| **Data Filtering** | `filter_relevant_stocks.py` | Script to filter dataset |
| **Example Analysis** | `example_analysis.py` | Technical analysis example |

---

*Last Updated: 2025-11-12*
*Active Components: H001 hypothesis + Probability Validation + Fallen Angels Analysis*
*Status: H001 complete; Validation & Fallen Angels analysis active with interactive reports*
*Data Workflow: Fully automated with incremental updates*
