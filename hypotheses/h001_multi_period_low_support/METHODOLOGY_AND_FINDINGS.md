# Multi-Period Support Level Analysis: Comprehensive Methodology and Findings

> **📊 Interactive Dashboard:** For an interactive visual exploration, open `multi_period_dashboard.html` in your browser.

## Executive Summary

**Question:** How reliable are different rolling support levels (1-month, 3-month, 6-month, 9-month, 1-year lows) for identifying strike prices when writing put options?

**Methodology:** For each rolling time period and every trading day, we identify the support level (lowest price in that period) and test whether price remains above that level for different scenarios: waiting 0-180 days after support identification, then writing puts with 7-45 days to expiry.

## Understanding the Methodology

### Key Concepts

#### 1. Rolling Support Levels

For each time period (1-month, 3-month, etc.) and **for every single trading day**, we calculate:
- The lowest price over the past N days (30/90/180/270/365)
- This rolling low becomes the support level
- We generate a continuous stream of support observations (not rare events!)

**Example:** For a stock with 10,000 trading days of history:
- We calculate 10,000 different 1-month support levels (one per day)
- We calculate 10,000 different 1-year support levels (one per day)
- Each day's support level is a potential candidate for put option writing

#### 2. Wait Times After Support Identification

Once a support level is identified on a trading day:
- We can wait N days before writing the put (options: 0, 30, 60, 90, 120, 180)
- During this wait period, we verify the support hasn't been broken
- If support breaks during the wait, we skip that test
- If support holds, we proceed to write the put

**Time Window Constraints (can't wait longer than the period itself):**
- 1-month low (30d): valid wait times = [0, 30] days
- 3-month low (90d): valid wait times = [0, 30, 60, 90] days
- 6-month low (180d): valid wait times = [0, 30, 60, 90, 120, 180] days
- 9-month low (270d): valid wait times = [0, 30, 60, 90, 120, 180] days
- 1-year low (365d): valid wait times = [0, 30, 60, 90, 120, 180] days

#### 3. Option Testing

After the wait period, we write a put option with M days to expiry (7, 14, 21, 30, or 45 days):
- **Success:** Price stays **ABOVE** the support level for the entire option period
- **Success means:** Option expires worthless, we keep the premium
- **Failure:** Price touches or goes below the support level
- **Failure means:** Risk of assignment

#### 4. Test Matrix Organization

Results are organized as matrices:
- **Rows:** Wait times (0, 30, 60, 90, 120, 180 days - constrained by period)
- **Columns:** Expiry periods (7, 14, 21, 30, 45 days)
- **Values:**
  - Success rate (%) for that combination
  - Sample count (how many historical instances)

This allows queries like:
- "If I write a 30-day put on a 3-month low after waiting 60 days, what's the historical success rate?"
- "What's the best combination of wait time and expiry for 1-month lows?"

### Analysis Pipeline

```
For each time period (1/3/6/9/12 months):
  ├─ For each stock:
  │  └─ For each trading day (starting from day N of the period):
  │     ├─ Calculate rolling low (support level)
  │     ├─ For each valid wait time (0-180 days, constrained):
  │     │  ├─ Verify support holds during wait period
  │     │  └─ For each expiry period (7-45 days):
  │     │     ├─ Check if price stayed ≥ support during expiry
  │     │     └─ Record success/failure
  │     └─ Generate test results for this support
  └─ Create matrix: wait_time × expiry → success_rate & count
```

## Data and Statistics

### Dataset

- **Stocks:** 70 Nordic blue-chip stocks with liquid options markets
- **Date Range:** 2000-2025 (25 years of history)
- **Total Records:** 367K price records
- **Time Periods Tested:** 1-month, 3-month, 6-month, 9-month, 1-year
- **Wait Times:** 0, 30, 60, 90, 120, 180 days (constrained by period)
- **Expiry Periods:** 7, 14, 21, 30, 45 days

### Test Coverage

With 70 stocks, 25 years of data, 5 time periods, multiple wait times, and 5 expiry periods:
- **Hundreds of thousands** of individual test cases
- **Massive sample sizes** provide high statistical confidence
- Results show patterns across different market conditions

## Methodology Advantages

### 1. Every Support Level Tested

Unlike approaches that only test "rare" strong supports:
- We test **every rolling low** that occurs
- We don't pre-filter based on "proved support" criteria
- This captures the full distribution of support effectiveness

### 2. Realistic Time Window Constraints

- Wait times are limited by the period itself
- You can't wait 6 months on a 1-month low
- This ensures we test what's actually possible

### 3. Complete Scenario Testing

For each support level, we test:
- All possible wait periods
- All possible option expiry periods
- This reveals optimal strategy combinations

### 4. Historical Validation

Using 25 years of data:
- Captures multiple market cycles
- Tests across bull, bear, and sideways markets
- Shows strategy robustness

## How to Interpret Results

### Reading the Success Rate Matrices

**Example Matrix Row:**
```
wait_days=60, expiry_7d_rate=96.5%, expiry_30d_rate=89.2%, expiry_45d_rate=86.1%
```

**Interpretation:**
- If you identify a support level and wait 60 days
- Then write a 7-day put at that support price
- Historically, 96.5% of the time, price stayed above support
- If you write a 30-day put instead, success rate drops to 89.2%
- If you write a 45-day put, success rate is 86.1%

### Success Rate Trends

Typically you'll see:
1. **Higher success for shorter expiry periods** (7-14 days vs 45 days)
2. **Shorter wait times have lower success** (fresh support is weaker)
3. **Success increases with wait time** (aged support is stronger)
4. **All periods converge at high success** when well-aged (90+ days)

## Practical Application

### Finding Your Trading Setup

1. **Choose a time period** (1/3/6/9/12 month) based on your style
2. **Identify a support level** for your stock
3. **Calculate how long** it's been since the low (support age)
4. **Check the matrix** for your wait time + expiry combination
5. **Evaluate the success rate** and sample size
6. **Make your trading decision**

### Example Scenario

**Real Setup:**
- Stock XYZ has a 3-month low of 150 kr
- The low was set 90 days ago
- You want to write a 30-day put
- You're willing to wait 30 days before writing
- **Look up:** 3-month period, wait_60d (90-30=60), expiry_30d
- **Find:** 87% success rate on 500+ samples
- **Decision:** Good risk/reward for your edge

### Position Sizing

With historical success rates:
- 86% success → ~1.2:1 win/loss ratio for balanced sizing
- 89% success → ~1.5:1 win/loss ratio for more aggressive sizing
- 92% success → ~2.0:1 win/loss ratio for aggressive sizing

Use Kelly criterion or fixed fractional sizing based on your success rate and risk tolerance.

## Comparison: Different Low Periods

### 1-Month vs 3-Month vs 1-Year Lows

The analysis allows direct comparison:
- **Same wait time** (e.g., 60 days) → Compare across periods
- **Same expiry period** (e.g., 30 days) → Compare across periods
- **Identify which period** offers best risk/reward for your situation

### Key Questions Answered

1. **Are shorter periods reliable?** - Check the matrices
2. **Does waiting improve success?** - Compare row to row
3. **Which expiry is best?** - Compare column to column
4. **Where's the sweet spot?** - Look for high success + high sample count

## Limitations and Assumptions

### Assumptions

1. **Historical relationships hold** - Future success rates similar to past
2. **No structural breaks** - Market microstructure hasn't fundamentally changed
3. **Liquid options available** - We can actually write puts at these strikes
4. **No transaction costs** - In practice, commissions and bid/ask spreads matter
5. **Daily prices** - Using daily low (not intraday data)

### Limitations

1. **Survivorship bias** - Only includes stocks that survived to 2025
2. **Liquidity not modeled** - Success rates don't account for option liquidity at specific strikes
3. **Dividends not modeled** - Early assignment risk from dividends not considered
4. **Volatility impact** - IV changes affect option premiums but not support reliability
5. **Backtesting bias** - Past performance doesn't guarantee future results

## File Descriptions

### Analysis Output Files

- **`{period}_detailed_results.csv`** - Event-level data
  - Every support level identified
  - Every wait time tested
  - Every expiry period tested
  - Success/failure for each combination

- **`{period}_matrix.csv`** - Summary matrix
  - Rows: wait times
  - Columns: expiry periods + success rates
  - Useful for quick lookups

- **`multi_period_combined_matrix.csv`** - All periods combined
  - Compare across different time periods
  - Identify which period performs best

### Data Structure

Each detailed results file contains:
- `stock` - Stock symbol
- `support_date` - When the support level was set
- `support_level` - The price level (in kr)
- `wait_days` - Days waited before writing put
- `test_date` - When put was written
- `expiry_days` - Days until put expires
- `expiry_date` - When put expires
- `success` - True/False: did support hold?
- `min_during_option` - Lowest price during option period
- `days_to_break` - If failed, how many days until support broke
- `break_pct` - If failed, how far below support it went

## Interpretation Guide

### When Results Are Reliable

✅ **High confidence** when:
- Sample count > 1,000
- Success rate > 90%
- Consistent across multiple stocks

✅ **Moderate confidence** when:
- Sample count > 300
- Success rate 80-90%
- Reasonable consistency

⚠️ **Low confidence** when:
- Sample count < 100
- Success rate < 75%
- Highly variable across stocks

### Making Trading Decisions

**Conservative approach:**
- Only trade when success rate > 90% AND sample > 500
- Use tighter stops
- Smaller position sizes

**Moderate approach:**
- Trade when success rate > 85% AND sample > 200
- Normal risk management
- Normal position sizes

**Aggressive approach:**
- Trade when success rate > 80% AND sample > 100
- Wider stops
- Can size larger if conviction is high

## Next Steps

### Phase 1: Validation
1. Review results in dashboard
2. Spot-check against current market supports
3. Validate the methodology makes sense

### Phase 2: Implementation
1. Identify current 1-month or 3-month lows in your watchlist
2. Calculate support age
3. Check historical success rates for your desired setup
4. Paper trade a few setups

### Phase 3: Live Trading
1. Start with small positions
2. Track actual results vs historical predictions
3. Adjust position sizing based on actual performance
4. Refine stock/period selection over time

## Future Enhancements

**Planned Analyses:**
1. **Volatility regime** - High IV vs Low IV environments
2. **Volume confirmation** - Does low volume strengthen supports?
3. **Trend context** - Uptrend vs downtrend supports
4. **Multi-period signals** - Stock at multiple lows simultaneously
5. **Sector analysis** - Which sectors work best?

---

*Analysis Methodology: Rolling support testing with wait time constraints*
*Data Range: 2000-2025 (25 years)*
*Stocks: 70 Nordic blue-chip*
*Last Updated: 2025-10-21*
