"""
Incremental Multi-Period Support Level Analysis

This script APPENDS new data to existing results instead of regenerating everything.
It only processes support levels that have a support_date AFTER the last date in the
existing parquet files, making updates MUCH faster (minutes instead of hours).

Performance:
- Full analysis: 2-3 hours for 70 stocks across 5 time periods
- Incremental: 1-2 minutes for 5 new days of data

Usage:
    python multi_period_low_analysis_incremental.py

The script will:
1. Load existing detailed_results files
2. Find the max support_date in each
3. Load new price data (price_data_filtered.parquet)
4. Only analyze days AFTER the max support_date
5. Append new results to existing parquet files
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from pathlib import Path
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

# Maximum wait time for each period
MAX_WAIT_BY_PERIOD = {
    30: 30,
    90: 90,
    180: 180,
    270: 270,
    365: 365
}

DATA_FILE = '../../price_data_filtered.parquet'
RESULTS_DIR = Path('.')
NUM_WORKERS = max(1, os.cpu_count() - 1)


def load_new_price_data(start_date):
    """
    Load price data filtered to dates AFTER start_date.

    Args:
        start_date: Only load data after this date

    Returns:
        DataFrame with price data for new dates only
    """
    print(f"Loading price data from {DATA_FILE}...")
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

    # Filter to new data only
    df_new = df[df['Date'] > start_date].copy()

    print(f"✓ Loaded {len(df):,} total records for {df['Stock'].nunique()} stocks")
    print(f"✓ Filtering to new data (after {start_date.date()}): {len(df_new):,} new records")

    return df, df_new


def get_last_analysis_date(period_name):
    """
    Get the maximum support_date from an existing results file.

    Args:
        period_name: Period name (e.g., '1-Month')

    Returns:
        Datetime of the last analyzed date, or None if file doesn't exist
    """
    file_prefix = period_name.lower().replace(' ', '_').replace('-', '_')
    file_path = RESULTS_DIR / f'{file_prefix}_detailed_results.parquet'

    if not file_path.exists():
        return None

    try:
        df = pd.read_parquet(file_path, columns=['support_date'])
        max_date = pd.to_datetime(df['support_date']).max()
        return max_date
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return None


def analyze_stock_for_period_incremental(args):
    """
    Analyze NEW support levels for a single stock and period.
    Only processes data after the last known support_date.

    Args:
        args: Tuple of (stock, stock_data, period_days, period_name, wait_times, min_analyze_date)
    """
    stock, stock_data, period_days, period_name, wait_times, min_analyze_date = args

    results = []

    if len(stock_data) < period_days:
        return results

    # We need HISTORICAL data to calculate rolling lows for new dates
    # So we can't just filter to new dates - we need the full history
    stock_data_full = stock_data.copy()
    stock_data = stock_data.sort_values('Date').reset_index(drop=True)

    # Process only NEW support dates (after min_analyze_date)
    for idx in range(period_days - 1, len(stock_data)):
        current_date = stock_data.loc[idx, 'Date']

        # Only process if this is a new support date
        if current_date <= min_analyze_date:
            continue

        # Calculate rolling low for this day
        window_start_idx = idx - period_days + 1
        window_data = stock_data.iloc[window_start_idx:idx+1]
        rolling_low = window_data['Low'].min()

        # Test each valid wait time
        for wait_days in wait_times:
            test_date = current_date + timedelta(days=wait_days)

            # Get data from current_date to test_date
            wait_period_data = stock_data[
                (stock_data['Date'] > current_date) &
                (stock_data['Date'] <= test_date)
            ]

            # Check if support was broken during wait period
            if len(wait_period_data) > 0:
                min_during_wait = wait_period_data['Low'].min()
                if min_during_wait < rolling_low:
                    continue  # Support broke during wait, skip

            # Test each expiry period
            for expiry_days in EXPIRY_PERIODS:
                expiry_date = test_date + timedelta(days=expiry_days)

                # Get data during the option period
                option_period_data = stock_data[
                    (stock_data['Date'] > test_date) &
                    (stock_data['Date'] <= expiry_date)
                ]

                if len(option_period_data) == 0:
                    success = None
                    min_during_option = None
                    days_to_break = None
                    break_pct = None
                else:
                    min_during_option = option_period_data['Low'].min()

                    if min_during_option >= rolling_low:
                        success = True
                        days_to_break = None
                        break_pct = None
                    else:
                        success = False
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


def analyze_period_incremental(df_all, period_days, period_name, min_analyze_date):
    """
    Analyze NEW support levels for a single period using multiprocessing.
    """
    print(f"\n{'='*80}")
    print(f"ANALYZING NEW DATA: {period_name} LOW ({period_days} days)")
    print(f"Processing dates AFTER: {min_analyze_date.date()}")
    print(f"{'='*80}")

    stocks = df_all['Stock'].unique()
    valid_wait_times = [w for w in WAIT_TIMES if w <= MAX_WAIT_BY_PERIOD[period_days]]

    print(f"Using {NUM_WORKERS} worker processes...")
    print(f"Processing {len(stocks)} stocks with {len(valid_wait_times)} wait times...")

    # Prepare arguments for worker processes
    worker_args = []
    for stock in stocks:
        stock_data = df_all[df_all['Stock'] == stock].copy().reset_index(drop=True)
        worker_args.append((stock, stock_data, period_days, period_name, valid_wait_times, min_analyze_date))

    # Process in parallel
    all_results = []
    completed = 0

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(analyze_stock_for_period_incremental, worker_arg): worker_arg[0]
                   for worker_arg in worker_args}

        for future in as_completed(futures):
            completed += 1
            stock_results = future.result()
            all_results.extend(stock_results)

            if completed % 10 == 0:
                print(f"  Progress: {completed}/{len(stocks)} stocks processed...")

    results_df = pd.DataFrame(all_results)
    print(f"✓ Generated {len(results_df):,} new test cases")

    return results_df


def append_results(new_results, period_name):
    """
    Append new results to existing parquet file.

    Args:
        new_results: DataFrame with new analysis results
        period_name: Period name (e.g., '1-Month')
    """
    file_prefix = period_name.lower().replace(' ', '_').replace('-', '_')
    file_path = RESULTS_DIR / f'{file_prefix}_detailed_results.parquet'

    if len(new_results) == 0:
        print(f"  No new data to append for {period_name}")
        return

    if not file_path.exists():
        print(f"  File doesn't exist: {file_path}")
        print(f"  Creating new file with {len(new_results):,} results")
        new_results.to_parquet(file_path, compression='snappy', index=False)
        return

    # Load existing data
    print(f"  Loading existing {file_path.name}...")
    existing = pd.read_parquet(file_path)

    # Ensure datetime columns are properly typed
    for col in ['support_date', 'test_date', 'expiry_date']:
        if col in new_results.columns:
            new_results[col] = pd.to_datetime(new_results[col])
        if col in existing.columns:
            existing[col] = pd.to_datetime(existing[col])

    # Append new results
    combined = pd.concat([existing, new_results], ignore_index=True)

    # Remove duplicates (if any) - keep the most recent
    combined = combined.drop_duplicates(
        subset=['stock', 'support_date', 'wait_days', 'expiry_days'],
        keep='last'
    )

    # Save back to parquet
    print(f"  Saving updated {file_path.name}...")
    combined.to_parquet(file_path, compression='snappy', index=False)

    print(f"✓ Updated {file_path.name}")
    print(f"  - Old size: {len(existing):,} rows")
    print(f"  - New size: {len(combined):,} rows")
    print(f"  - Added: {len(new_results):,} rows")


def main():
    """Main incremental analysis pipeline"""
    print("="*80)
    print("INCREMENTAL MULTI-PERIOD SUPPORT LEVEL ANALYSIS")
    print("Appending new data to existing results (FAST!)")
    print("="*80)
    print(f"\nSystem Configuration:")
    print(f"  CPU Cores Available: {os.cpu_count()}")
    print(f"  Worker Processes: {NUM_WORKERS}")

    # Find the minimum date we need to analyze (1 day after last date in results)
    print(f"\n{'='*80}")
    print("FINDING LAST ANALYZED DATES")
    print(f"{'='*80}")

    last_dates = {}
    for period_days, period_name in LOW_PERIODS.items():
        last_date = get_last_analysis_date(period_name)
        last_dates[period_days] = last_date

        if last_date is None:
            print(f"{period_name}: No existing data (will create new file)")
        else:
            print(f"{period_name}: Last analyzed date: {last_date.date()}")

    # Determine the earliest last date (most conservative)
    min_last_date = min([d for d in last_dates.values() if d is not None])
    min_analyze_date = min_last_date

    print(f"\nWill analyze dates AFTER: {min_analyze_date.date()}")

    # Load data
    print(f"\n{'='*80}")
    print("LOADING DATA")
    print(f"{'='*80}")

    df_all, df_new = load_new_price_data(min_analyze_date)

    if len(df_new) == 0:
        print("\n⚠ No new data to analyze!")
        print("All results are already up to date.")
        return

    # Analyze each period
    print(f"\n{'='*80}")
    print("ANALYZING NEW DATA")
    print(f"{'='*80}")

    for period_days, period_name in LOW_PERIODS.items():
        new_results = analyze_period_incremental(df_all, period_days, period_name, min_analyze_date)

        print(f"\n{'='*80}")
        print("APPENDING RESULTS")
        print(f"{'='*80}")
        append_results(new_results, period_name)

    print("\n" + "="*80)
    print("✓ INCREMENTAL ANALYSIS COMPLETE!")
    print("="*80)
    print("\nResults have been appended to:")
    for period_name in LOW_PERIODS.values():
        file_prefix = period_name.lower().replace(' ', '_').replace('-', '_')
        print(f"  - {file_prefix}_detailed_results.parquet")


if __name__ == '__main__':
    main()
