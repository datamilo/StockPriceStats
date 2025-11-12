#!/usr/bin/env python3
"""
Analyze "Fallen Angels" - Options with Historical High Probability

This script tests whether options that previously had 90%+ probability
but dropped to lower levels (60-80%) still expire worthless more often
than their current probability suggests.

Strategy Insight: If historical high probability provides additional signal,
we can write puts at better risk/reward when we catch "fallen angels."

Author: Claude Code
Date: November 12, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import json

# Configuration
DATA_FILE = Path(__file__).parent / 'probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv'
OUTPUT_DIR = Path(__file__).parent / 'fallen_angels_results'
OUTPUT_DIR.mkdir(exist_ok=True)

PROB_COLUMNS = {
    '1_2_3_ProbOfWorthless_Weighted': 'Weighted Average',
    'ProbWorthless_Bayesian_IsoCal': 'Bayesian Calibrated',
    '1_ProbOfWorthless_Original': 'Original Black-Scholes',
    '2_ProbOfWorthless_Calibrated': 'Bias Corrected',
    '3_ProbOfWorthless_Historical_IV': 'Historical IV'
}

# Analysis parameters
HISTORICAL_PEAK_THRESHOLD = 0.90  # Options must have hit 90%+ at some point
CURRENT_PROB_BINS = [(0.60, 0.70), (0.70, 0.80), (0.80, 0.90)]
DTE_BINS = [(0, 7), (8, 14), (15, 21), (22, 28), (29, 35), (36, 999)]

print("=" * 80)
print("FALLEN ANGELS ANALYSIS")
print("=" * 80)
print()
print(f"Testing if options that peaked at {HISTORICAL_PEAK_THRESHOLD:.0%}+ probability")
print("but dropped to lower levels still have better outcomes than current prob suggests")
print()

# =============================================================================
# LOAD AND PREPARE DATA
# =============================================================================
print("Loading probability history data...")
df = pd.read_csv(DATA_FILE, sep='|')
print(f"  Loaded {len(df):,} records")

# Convert dates
df['Update_date'] = pd.to_datetime(df['Update_date'], errors='coerce')
df['StrikeDate'] = pd.to_datetime(df['StrikeDate'], errors='coerce')

# Calculate days to expiry
df['DaysToExpiry'] = (df['StrikeDate'] - df['Update_date']).dt.days

# Filter to only expired options (have outcome data)
df_expired = df[df['StockPrice_AtExpiry'].notna()].copy()
print(f"  Filtered to {len(df_expired):,} records with expiry data")

# Calculate actual outcome (1 if expired worthless, 0 if exercised)
df_expired['ActualWorthless'] = (df_expired['StockPrice_AtExpiry'] > df_expired['StrikePrice']).astype(int)

print()

# =============================================================================
# IDENTIFY FALLEN ANGELS FOR EACH PROBABILITY METHOD
# =============================================================================
print("Identifying 'fallen angel' options...")

# Group by option to get each option's trajectory
option_groups = df_expired.groupby('OptionName')

fallen_angels_results = defaultdict(list)

for prob_col, prob_label in PROB_COLUMNS.items():
    print(f"\n  Analyzing {prob_label}...")

    # For each option, track if it ever hit 90%+
    for option_name, option_df in option_groups:
        # Sort by date to get chronological trajectory
        option_df = option_df.sort_values('Update_date')

        # Skip if probability column has no valid data
        if option_df[prob_col].isna().all():
            continue

        # Find peak probability for this option
        peak_prob = option_df[prob_col].max()

        # Check if this option ever hit the threshold
        is_fallen_angel = peak_prob >= HISTORICAL_PEAK_THRESHOLD

        # Process each daily update
        for idx, row in option_df.iterrows():
            current_prob = row[prob_col]

            if pd.isna(current_prob):
                continue

            # Assign to current probability bin
            for bin_min, bin_max in CURRENT_PROB_BINS:
                if bin_min <= current_prob < bin_max:
                    # Assign to DTE bin
                    dte = row['DaysToExpiry']
                    for dte_min, dte_max in DTE_BINS:
                        if dte_min <= dte <= dte_max:
                            fallen_angels_results[prob_col].append({
                                'OptionName': option_name,
                                'Stock': row['Name'],
                                'Update_date': row['Update_date'],
                                'DaysToExpiry': dte,
                                'DTE_Bin': f'{dte_min}-{dte_max}' if dte_max < 999 else f'{dte_min}+',
                                'CurrentProb': current_prob,
                                'CurrentProb_Bin': f'{int(bin_min*100)}-{int(bin_max*100)}%',
                                'PeakProb': peak_prob,
                                'IsFallenAngel': is_fallen_angel,
                                'ActualWorthless': row['ActualWorthless'],
                                'ProbMethod': prob_label
                            })
                            break
                    break

    print(f"    Processed {len(fallen_angels_results[prob_col]):,} option-date records")

print()
print("Combining results...")

# Combine all results into a single DataFrame
all_results = []
for prob_col, results in fallen_angels_results.items():
    all_results.extend(results)

df_results = pd.DataFrame(all_results)
print(f"  Total analysis records: {len(df_results):,}")

# =============================================================================
# CALCULATE STATISTICS
# =============================================================================
print("\nCalculating statistics...")

summary_stats = []

for prob_method in df_results['ProbMethod'].unique():
    df_method = df_results[df_results['ProbMethod'] == prob_method]

    for current_bin in df_results['CurrentProb_Bin'].unique():
        df_bin = df_method[df_method['CurrentProb_Bin'] == current_bin]

        for dte_bin in df_results['DTE_Bin'].unique():
            df_dte = df_bin[df_bin['DTE_Bin'] == dte_bin]

            if len(df_dte) == 0:
                continue

            # Calculate for fallen angels
            df_fallen = df_dte[df_dte['IsFallenAngel'] == True]
            fallen_n = len(df_fallen)
            fallen_worthless_rate = df_fallen['ActualWorthless'].mean() if fallen_n > 0 else np.nan
            fallen_avg_current_prob = df_fallen['CurrentProb'].mean() if fallen_n > 0 else np.nan
            fallen_avg_peak_prob = df_fallen['PeakProb'].mean() if fallen_n > 0 else np.nan

            # Calculate for baseline (never hit 90%)
            df_baseline = df_dte[df_dte['IsFallenAngel'] == False]
            baseline_n = len(df_baseline)
            baseline_worthless_rate = df_baseline['ActualWorthless'].mean() if baseline_n > 0 else np.nan
            baseline_avg_current_prob = df_baseline['CurrentProb'].mean() if baseline_n > 0 else np.nan
            baseline_avg_peak_prob = df_baseline['PeakProb'].mean() if baseline_n > 0 else np.nan

            # Calculate the "premium" - how much better fallen angels perform vs their current prob
            if not pd.isna(fallen_worthless_rate) and not pd.isna(fallen_avg_current_prob):
                fallen_premium = (fallen_worthless_rate - fallen_avg_current_prob) * 100  # percentage points
            else:
                fallen_premium = np.nan

            if not pd.isna(baseline_worthless_rate) and not pd.isna(baseline_avg_current_prob):
                baseline_premium = (baseline_worthless_rate - baseline_avg_current_prob) * 100
            else:
                baseline_premium = np.nan

            # Difference between fallen and baseline
            if not pd.isna(fallen_worthless_rate) and not pd.isna(baseline_worthless_rate):
                advantage = (fallen_worthless_rate - baseline_worthless_rate) * 100  # percentage points
            else:
                advantage = np.nan

            summary_stats.append({
                'ProbMethod': prob_method,
                'CurrentProb_Bin': current_bin,
                'DTE_Bin': dte_bin,
                'Fallen_N': fallen_n,
                'Fallen_WorthlessRate': fallen_worthless_rate,
                'Fallen_AvgCurrentProb': fallen_avg_current_prob,
                'Fallen_AvgPeakProb': fallen_avg_peak_prob,
                'Fallen_Premium_pp': fallen_premium,
                'Baseline_N': baseline_n,
                'Baseline_WorthlessRate': baseline_worthless_rate,
                'Baseline_AvgCurrentProb': baseline_avg_current_prob,
                'Baseline_AvgPeakProb': baseline_avg_peak_prob,
                'Baseline_Premium_pp': baseline_premium,
                'Advantage_pp': advantage
            })

df_summary = pd.DataFrame(summary_stats)

# =============================================================================
# CALCULATE PER-STOCK STATISTICS
# =============================================================================
print("Calculating per-stock statistics...")

stock_stats = []

for prob_method in df_results['ProbMethod'].unique():
    df_method = df_results[df_results['ProbMethod'] == prob_method]

    for stock in df_method['Stock'].unique():
        df_stock = df_method[df_method['Stock'] == stock]

        for current_bin in df_stock['CurrentProb_Bin'].unique():
            df_bin = df_stock[df_stock['CurrentProb_Bin'] == current_bin]

            # Calculate for fallen angels
            df_fallen = df_bin[df_bin['IsFallenAngel'] == True]
            fallen_n = len(df_fallen)
            fallen_worthless_rate = df_fallen['ActualWorthless'].mean() if fallen_n > 0 else np.nan

            # Calculate for baseline
            df_baseline = df_bin[df_bin['IsFallenAngel'] == False]
            baseline_n = len(df_baseline)
            baseline_worthless_rate = df_baseline['ActualWorthless'].mean() if baseline_n > 0 else np.nan

            # Advantage
            if not pd.isna(fallen_worthless_rate) and not pd.isna(baseline_worthless_rate):
                advantage = (fallen_worthless_rate - baseline_worthless_rate) * 100
            else:
                advantage = np.nan

            if fallen_n > 0 or baseline_n > 0:  # Only include if we have data
                stock_stats.append({
                    'Stock': stock,
                    'ProbMethod': prob_method,
                    'CurrentProb_Bin': current_bin,
                    'Fallen_N': fallen_n,
                    'Fallen_WorthlessRate': fallen_worthless_rate,
                    'Baseline_N': baseline_n,
                    'Baseline_WorthlessRate': baseline_worthless_rate,
                    'Advantage_pp': advantage
                })

df_stock_stats = pd.DataFrame(stock_stats)

# =============================================================================
# SAVE RESULTS
# =============================================================================
print("\nSaving results...")

# Save summary statistics
summary_file = OUTPUT_DIR / 'fallen_angels_summary.csv'
df_summary.to_csv(summary_file, index=False)
print(f"  Summary statistics: {summary_file}")

# Save stock-level statistics
stock_file = OUTPUT_DIR / 'fallen_angels_by_stock.csv'
df_stock_stats.to_csv(stock_file, index=False)
print(f"  Stock-level statistics: {stock_file}")

# Save detailed results
details_file = OUTPUT_DIR / 'fallen_angels_details.csv'
df_results.to_csv(details_file, index=False)
print(f"  Detailed results: {details_file}")

# =============================================================================
# PRINT KEY FINDINGS
# =============================================================================
print("\n" + "=" * 80)
print("KEY FINDINGS")
print("=" * 80)
print()

# Find best method with most significant advantage
best_results = df_summary[df_summary['Fallen_N'] >= 100].copy()  # Require 100+ samples
if len(best_results) > 0:
    best_results = best_results.nlargest(10, 'Advantage_pp')

    print("Top 10 scenarios where 'Fallen Angels' have the biggest advantage:")
    print()
    for idx, row in best_results.iterrows():
        print(f"  {row['ProbMethod']} | {row['CurrentProb_Bin']} | {row['DTE_Bin']} days")
        print(f"    Fallen Angels: {row['Fallen_WorthlessRate']:.1%} ({row['Fallen_N']:,} samples)")
        print(f"    Baseline:      {row['Baseline_WorthlessRate']:.1%} ({row['Baseline_N']:,} samples)")
        print(f"    Advantage:     +{row['Advantage_pp']:.2f} percentage points")
        print()

print("=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print()
print("Next steps:")
print("1. Review fallen_angels_summary.csv for overall statistics")
print("2. Open fallen_angels_report.html (to be generated) for interactive visualization")
print("3. Check fallen_angels_by_stock.csv for stock-specific patterns")
print()
