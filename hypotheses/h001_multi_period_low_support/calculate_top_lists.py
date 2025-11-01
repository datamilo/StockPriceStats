#!/usr/bin/env python3
"""
Pre-calculate top lists statistics for all stocks and save to parquet files.

Run this script whenever price data is updated to regenerate the top lists.
The Streamlit app will then load these pre-calculated files instantly.

Usage:
    python calculate_top_lists.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'
OUTPUT_DIR = SCRIPT_DIR / 'top_lists'

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)

def load_price_data():
    """Load all price data"""
    print("Loading price data...")
    df = pd.read_parquet(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['name', 'date']).reset_index(drop=True)
    df = df.rename(columns={
        'date': 'Date',
        'name': 'Stock',
        'low': 'Low',
        'high': 'High',
        'close': 'Close',
        'open': 'Open'
    })
    print(f"Loaded {len(df):,} rows for {df['Stock'].nunique()} stocks")
    return df


def calculate_rolling_low(stock_data, period_days):
    """Calculate rolling low using calendar days"""
    stock_data = stock_data.sort_values('Date').reset_index(drop=True)
    rolling_lows = []

    for idx, row in stock_data.iterrows():
        current_date = row['Date']
        lookback_date = current_date - pd.Timedelta(days=period_days)

        window_data = stock_data[
            (stock_data['Date'] >= lookback_date) &
            (stock_data['Date'] <= current_date)
        ]

        if len(window_data) > 0:
            rolling_lows.append(window_data['Low'].min())
        else:
            rolling_lows.append(None)

    stock_data['rolling_low'] = rolling_lows
    return stock_data


def analyze_support_breaks(stock_data):
    """Analyze support level breaks"""
    stock_data = stock_data.sort_values('Date').copy()

    # Identify where rolling low decreased
    stock_data['rolling_low_prev'] = stock_data['rolling_low'].shift(1)
    stock_data['support_break'] = stock_data['rolling_low'] < stock_data['rolling_low_prev']

    breaks = stock_data[stock_data['support_break'] == True].copy()

    if len(breaks) == 0:
        return None

    # Calculate break magnitude
    breaks['prev_support'] = breaks['rolling_low_prev']
    breaks['new_support'] = breaks['rolling_low']
    breaks['drop_amount'] = breaks['new_support'] - breaks['prev_support']
    breaks['drop_pct'] = (breaks['drop_amount'] / breaks['prev_support'] * 100)

    # Calculate time between breaks
    if len(breaks) > 1:
        breaks['days_since_last_break'] = breaks['Date'].diff().dt.days

    # Calculate metrics
    days_since_last_break = (stock_data['Date'].max() - breaks['Date'].max()).days
    stability_pct = ((len(stock_data) - len(breaks)) / len(stock_data) * 100) if len(stock_data) > 0 else 0

    stats = {
        'total_breaks': len(breaks),
        'avg_days_between': breaks['days_since_last_break'].mean() if len(breaks) > 1 else None,
        'median_days_between': breaks['days_since_last_break'].median() if len(breaks) > 1 else None,
        'avg_drop_pct': breaks['drop_pct'].mean(),
        'max_drop_pct': breaks['drop_pct'].min(),
        'total_trading_days': len(stock_data),
        'trading_days_per_break': len(stock_data) / len(breaks) if len(breaks) > 0 else None,
        'days_since_last_break': days_since_last_break,
        'stability_pct': stability_pct,
    }

    return stats


def calculate_statistics_for_period(df, period_days, period_name):
    """Calculate statistics for all stocks for a given period"""
    print(f"\nCalculating statistics for {period_name} ({period_days} days)...")
    all_stocks_stats = []

    for i, stock in enumerate(sorted(df['Stock'].unique()), 1):
        print(f"  [{i:2d}/68] Processing {stock}...", end='\r')
        stock_data = df[df['Stock'] == stock].copy()

        if len(stock_data) < period_days:
            continue

        stock_data_with_low = calculate_rolling_low(stock_data, period_days)
        stats = analyze_support_breaks(stock_data_with_low)

        if stats is not None and stats['total_breaks'] > 0:
            all_stocks_stats.append({
                'Stock': stock,
                'Total Breaks': stats['total_breaks'],
                'Avg Days Between': round(stats['avg_days_between'], 1) if stats['avg_days_between'] else None,
                'Median Days Between': round(stats['median_days_between'], 1) if stats['median_days_between'] else None,
                'Trading Days per Break': round(stats['trading_days_per_break'], 1) if stats['trading_days_per_break'] else None,
                'Stability %': round(stats['stability_pct'], 1),
                'Avg Break %': round(stats['avg_drop_pct'], 2),
                'Max Break %': round(stats['max_drop_pct'], 2),
                'Days Since Last': stats['days_since_last_break']
            })

    print(f"  Completed! {len(all_stocks_stats)} stocks with statistics")

    if all_stocks_stats:
        df_stats = pd.DataFrame(all_stocks_stats)
        output_file = OUTPUT_DIR / f'{period_name.lower().replace("-", "_")}_top_lists.parquet'
        df_stats.to_parquet(output_file, index=False)
        print(f"  Saved to: {output_file}")
        return df_stats
    return None


def main():
    """Main execution"""
    print("=" * 80)
    print("TOP LISTS CALCULATION")
    print("=" * 80)

    # Load data
    df = load_price_data()

    # Calculate for all periods
    periods = [
        (30, '1-Month'),
        (90, '3-Month'),
        (180, '6-Month'),
        (270, '9-Month'),
        (365, '1-Year')
    ]

    for period_days, period_name in periods:
        calculate_statistics_for_period(df, period_days, period_name)

    print("\n" + "=" * 80)
    print("✓ All calculations complete!")
    print(f"✓ Files saved to: {OUTPUT_DIR}")
    print("=" * 80)


if __name__ == '__main__':
    main()
