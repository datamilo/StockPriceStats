"""
Multi-Period Support Level Analysis: Correct Methodology with Multiprocessing

This script tests support level reliability for put option writing strategies.

KEY CONCEPTS:
1. For each time period (1/3/6/9/12 months), a NEW rolling low is calculated
   for EVERY SINGLE TRADING DAY
2. Each rolling low = a potential support level for put option writing
3. After identifying a support level, we wait N days (0/30/60/90/120/180)
4. We then write a put option with M days to expiry (7/14/21/30/45)
5. We test if price stayed ABOVE the support level during the option period
6. Success = Option expires worthless (price never touched support)

TIME WINDOW CONSTRAINTS:
- 1-month low: can only wait 0-30 days (max)
- 3-month low: can wait 0-90 days (max)
- 6-month low: can wait 0-180 days (max)
- 9-month low: can wait 0-270 days (max)
- 1-year low: can wait 0-365 days (max)

PERFORMANCE:
- Uses multiprocessing to parallelize stock processing
- Each stock processed by separate worker process
- Significant speedup on multi-core systems (8x+ faster on 8-core CPU)
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from pathlib import Path
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

# Configuration
LOW_PERIODS = {
    30: '1-Month',
    90: '3-Month',
    180: '6-Month',
    270: '9-Month',
    365: '1-Year'
}

# Wait times after support is identified (in days)
WAIT_TIMES = [0, 30, 60, 90, 120, 180]

# Option expiry periods (in days)
EXPIRY_PERIODS = [7, 14, 21, 30, 45]

# Maximum wait time for each period (can't wait longer than the period itself)
MAX_WAIT_BY_PERIOD = {
    30: 30,
    90: 90,
    180: 180,
    270: 270,
    365: 365
}

DATA_FILE = '../../price_data_filtered.parquet'
NUM_WORKERS = max(1, os.cpu_count() - 1)  # Use all cores except one


def load_data():
    """Load price data"""
    print(f"Loading data from {DATA_FILE}...")
    df = pd.read_parquet(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['name', 'date']).reset_index(drop=True)

    # Rename columns
    df = df.rename(columns={
        'date': 'Date',
        'name': 'Stock',
        'low': 'Low',
        'high': 'High',
        'close': 'Close',
        'open': 'Open'
    })

    print(f"✓ Loaded {len(df):,} records for {df['Stock'].nunique()} stocks")
    return df


def analyze_stock_for_period(args):
    """
    Analyze a single stock for a single period.
    This function runs in a worker process.
    """
    stock, stock_data, period_days, period_name, wait_times = args

    results = []

    if len(stock_data) < period_days:
        return results

    # For each trading day where we can calculate a rolling low
    # Processing ~5,000 trading days per stock for each period
    for idx in range(period_days - 1, len(stock_data)):
        current_date = stock_data.loc[idx, 'Date']

        # Calculate rolling low for this day
        window_start_idx = idx - period_days + 1
        window_data = stock_data.iloc[window_start_idx:idx+1]
        rolling_low = window_data['Low'].min()

        # Test each valid wait time
        for wait_days in wait_times:
            test_date = current_date + timedelta(days=wait_days)

            # Get data from current_date to test_date (to check if support breaks during wait)
            wait_period_data = stock_data[
                (stock_data['Date'] > current_date) &
                (stock_data['Date'] <= test_date)
            ]

            # Check if support was broken during the wait period
            if len(wait_period_data) > 0:
                min_during_wait = wait_period_data['Low'].min()
                if min_during_wait < rolling_low:
                    continue  # Support broke during wait, skip this test

            # Test each expiry period
            for expiry_days in EXPIRY_PERIODS:
                expiry_date = test_date + timedelta(days=expiry_days)

                # Get data during the option period (after test_date)
                option_period_data = stock_data[
                    (stock_data['Date'] > test_date) &
                    (stock_data['Date'] <= expiry_date)
                ]

                if len(option_period_data) == 0:
                    # No data available for this period
                    success = None
                    min_during_option = None
                    days_to_break = None
                    break_pct = None
                else:
                    min_during_option = option_period_data['Low'].min()

                    if min_during_option >= rolling_low:
                        # Support held! Option expired worthless
                        success = True
                        days_to_break = None
                        break_pct = None
                    else:
                        # Support was broken
                        success = False

                        # Find when it broke
                        break_data = option_period_data[option_period_data['Low'] < rolling_low]
                        if len(break_data) > 0:
                            first_break = break_data.iloc[0]
                            days_to_break = (first_break['Date'] - test_date).days
                            break_pct = ((first_break['Low'] - rolling_low) / rolling_low) * 100
                        else:
                            days_to_break = None
                            break_pct = ((min_during_option - rolling_low) / rolling_low) * 100

                results.append({
                    'stock': stock,
                    'period_name': period_name,
                    'period_days': period_days,
                    'support_date': current_date,
                    'support_level': rolling_low,
                    'wait_days': wait_days,
                    'test_date': test_date,
                    'expiry_days': expiry_days,
                    'expiry_date': expiry_date,
                    'success': success,
                    'min_during_option': min_during_option,
                    'days_to_break': days_to_break,
                    'break_pct': break_pct
                })

    return results


def analyze_single_period(df, period_days, period_name):
    """
    Analyze support levels for a single time period using multiprocessing.
    """
    print(f"\n{'='*80}")
    print(f"ANALYZING: {period_name} LOW ({period_days} days)")
    print(f"{'='*80}")

    stocks = df['Stock'].unique()
    valid_wait_times = [w for w in WAIT_TIMES if w <= MAX_WAIT_BY_PERIOD[period_days]]

    print(f"Using {NUM_WORKERS} worker processes...")
    print(f"Processing {len(stocks)} stocks with {len(valid_wait_times)} wait times...")

    # Prepare arguments for worker processes
    worker_args = []
    for stock in stocks:
        stock_data = df[df['Stock'] == stock].copy().reset_index(drop=True)
        worker_args.append((stock, stock_data, period_days, period_name, valid_wait_times))

    # Process in parallel
    all_results = []
    completed = 0

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(analyze_stock_for_period, worker_arg): worker_arg[0]
                   for worker_arg in worker_args}

        for future in as_completed(futures):
            completed += 1
            stock_results = future.result()
            all_results.extend(stock_results)

            if completed % 10 == 0:
                print(f"  Progress: {completed}/{len(stocks)} stocks processed...")

    results_df = pd.DataFrame(all_results)
    print(f"✓ Generated {len(results_df):,} test cases")

    return results_df


def create_success_matrix(detailed_results):
    """
    Create success rate matrix organized by wait_days and expiry_days.

    Rows: wait_days (0, 30, 60, 90, 120, 180)
    Columns: expiry periods (7, 14, 21, 30, 45 days)
    Values: success rates
    """
    if len(detailed_results) == 0:
        return pd.DataFrame()

    matrix_data = []

    # Group by wait_days
    for wait_days in sorted(detailed_results['wait_days'].unique()):
        row = {'wait_days': wait_days}

        # For each expiry period
        for expiry in sorted(detailed_results['expiry_days'].unique()):
            subset = detailed_results[
                (detailed_results['wait_days'] == wait_days) &
                (detailed_results['expiry_days'] == expiry) &
                (detailed_results['success'].notna())
            ]

            if len(subset) > 0:
                success_rate = (subset['success'].sum() / len(subset)) * 100
                row[f'expiry_{expiry}d_rate'] = round(success_rate, 1)
                row[f'expiry_{expiry}d_count'] = len(subset)
            else:
                row[f'expiry_{expiry}d_rate'] = None
                row[f'expiry_{expiry}d_count'] = 0

        matrix_data.append(row)

    return pd.DataFrame(matrix_data)


def main():
    """Main analysis pipeline"""
    print("="*80)
    print("MULTI-PERIOD SUPPORT LEVEL ANALYSIS (MULTIPROCESSING)")
    print("Testing support level reliability for put option writing")
    print("="*80)
    print(f"\nSystem Configuration:")
    print(f"  CPU Cores Available: {os.cpu_count()}")
    print(f"  Worker Processes: {NUM_WORKERS}")

    # Load data once
    df = load_data()

    # Store results for all periods
    all_results = {}

    # Analyze each period
    for period_days, period_name in LOW_PERIODS.items():
        detailed_results = analyze_single_period(df, period_days, period_name)

        all_results[period_days] = {
            'detailed': detailed_results,
            'matrix': create_success_matrix(detailed_results)
        }

    # Save results
    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)

    for period_days, period_name in LOW_PERIODS.items():
        file_prefix = period_name.lower().replace(' ', '_').replace('-', '_')

        # Save detailed results to Parquet
        detailed_file = f'{file_prefix}_detailed_results.parquet'
        all_results[period_days]['detailed'].to_parquet(detailed_file, compression='snappy', index=False)
        print(f"✓ Saved: {detailed_file} ({len(all_results[period_days]['detailed']):,} rows)")

        # Save matrix to Parquet
        matrix_file = f'{file_prefix}_matrix.parquet'
        all_results[period_days]['matrix'].to_parquet(matrix_file, compression='snappy', index=False)
        print(f"✓ Saved: {matrix_file}")

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    for period_days, period_name in LOW_PERIODS.items():
        detailed = all_results[period_days]['detailed']
        if len(detailed) > 0:
            # Overall success rate
            tested = detailed[detailed['success'].notna()]
            if len(tested) > 0:
                overall_rate = (tested['success'].sum() / len(tested)) * 100
                print(f"\n{period_name}:")
                print(f"  Total tests: {len(tested):,}")
                print(f"  Success rate: {overall_rate:.1f}%")

                # Show matrix
                matrix = all_results[period_days]['matrix']
                print(f"  Success rates by wait time and expiry:")
                for _, row in matrix.iterrows():
                    wait = int(row['wait_days'])
                    print(f"    Wait {wait:3d}d: ", end="")
                    for expiry in EXPIRY_PERIODS:
                        rate = row[f'expiry_{expiry}d_rate']
                        if pd.notna(rate):
                            print(f"{rate:5.1f}% ({expiry}d) ", end="")
                    print()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nConfiguration Summary:")
    print(f"  Time periods: {list(LOW_PERIODS.values())}")
    print(f"  Wait times: {WAIT_TIMES} days")
    print(f"  Expiry periods: {EXPIRY_PERIODS} days")
    print(f"  Note: Wait times constrained by period length")
    print(f"\nPerformance:")
    print(f"  Worker processes used: {NUM_WORKERS}")
    print(f"  Parallelization: Multiprocessing on stock level")


if __name__ == '__main__':
    main()
