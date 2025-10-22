"""
Fast data generation for enhanced dashboard - processes data efficiently
"""

import pandas as pd
import json
from pathlib import Path

def load_and_aggregate_stats():
    """Load detailed results and aggregate statistics efficiently"""

    base_path = Path(__file__).parent
    periods = ['1_month', '3_month', '6_month', '9_month', '1_year']

    print("Aggregating statistics from detailed results...")
    stats = {}
    stock_stats = {}
    all_stocks = set()

    for period in periods:
        path = base_path / f'{period}_detailed_results.parquet'
        if not path.exists():
            print(f"  Skipping {period} - file not found")
            continue

        print(f"  Processing {period}...")

        # Load with only necessary columns
        df = pd.read_parquet(path, columns=[
            'stock', 'success', 'wait_days', 'expiry_days',
            'support_date', 'break_pct', 'days_to_break'
        ])

        # Collect all stocks
        period_stocks = df['stock'].unique()
        all_stocks.update(period_stocks)

        # Calculate statistics
        total_trades = len(df)
        successful_trades = (df['success'] == True).sum()
        failed_trades = (df['success'] == False).sum()

        # By wait days
        by_wait_days = {}
        for wait_days in sorted(df['wait_days'].unique()):
            subset = df[df['wait_days'] == wait_days]
            success = (subset['success'] == True).sum()
            total = len(subset)
            by_wait_days[str(wait_days)] = {
                'success_count': int(success),
                'total_count': int(total),
                'success_rate': float(success / total * 100) if total > 0 else 0
            }

        # By expiry days
        by_expiry_days = {}
        for expiry_days in sorted(df['expiry_days'].unique()):
            subset = df[df['expiry_days'] == expiry_days]
            success = (subset['success'] == True).sum()
            total = len(subset)
            by_expiry_days[str(expiry_days)] = {
                'success_count': int(success),
                'total_count': int(total),
                'success_rate': float(success / total * 100) if total > 0 else 0
            }

        stats[period] = {
            'total_trades': int(total_trades),
            'successful_trades': int(successful_trades),
            'failed_trades': int(failed_trades),
            'success_rate': float(successful_trades / total_trades * 100) if total_trades > 0 else 0,
            'by_wait_days': by_wait_days,
            'by_expiry_days': by_expiry_days,
            'unique_stocks': int(df['stock'].nunique()),
            'unique_support_dates': int(df['support_date'].nunique())
        }

        # Per-stock statistics
        stock_stats[period] = {}
        for stock in period_stocks:
            stock_df = df[df['stock'] == stock]
            total = len(stock_df)
            success = (stock_df['success'] == True).sum()
            stock_stats[period][stock] = {
                'total_trades': int(total),
                'successful_trades': int(success),
                'success_rate': float(success / total * 100) if total > 0 else 0
            }

    all_stocks_list = sorted(list(all_stocks))

    # Build final data
    dashboard_data = {
        'statistics': stats,
        'stock_statistics': stock_stats,
        'all_stocks': all_stocks_list,
        'wait_time_constraints': {
            '1-Month': [0, 30],
            '3-Month': [0, 30, 60, 90],
            '6-Month': [0, 30, 60, 90, 120, 180],
            '9-Month': [0, 30, 60, 90, 120, 180],
            '1-Year': [0, 30, 60, 90, 120, 180]
        },
        'expiry_periods': [7, 14, 21, 30, 45]
    }

    return dashboard_data

def main():
    try:
        print("Starting fast dashboard data generation...")

        data = load_and_aggregate_stats()

        base_path = Path(__file__).parent
        output_path = base_path / 'enhanced_dashboard_data.json'

        print(f"\nSaving to {output_path}...")
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        file_size = output_path.stat().st_size / 1024 / 1024
        print(f"✓ Done! File size: {file_size:.1f} MB")
        print(f"\nSummary:")
        print(f"  Periods: {len(data['statistics'])}")
        print(f"  Stocks: {len(data['all_stocks'])}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
