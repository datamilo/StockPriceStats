"""
Generate comprehensive data for enhanced dashboard including:
- Statistics by period
- Chart data for each stock/period/wait_days/expiry_days combination
- Aggregate metrics and visualizations
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path

# Load data
print("Loading data...")
base_path = Path(__file__).parent
price_data = pd.read_parquet(base_path.parent.parent / 'price_data_filtered.parquet')
price_data['date'] = pd.to_datetime(price_data['date'])

# Load all detailed results
results_data = {}
periods = ['1_month', '3_month', '6_month', '9_month', '1_year']
for period in periods:
    path = base_path / f'{period}_detailed_results.parquet'
    if path.exists():
        df = pd.read_parquet(path)
        df['support_date'] = pd.to_datetime(df['support_date'])
        df['test_date'] = pd.to_datetime(df['test_date'])
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        results_data[period] = df
        print(f"  Loaded {period}: {len(df)} rows")

# Generate comprehensive statistics
print("\nGenerating comprehensive statistics...")

def generate_statistics():
    """Generate statistics for each period"""
    stats = {}

    for period, df in results_data.items():
        # Overall stats
        total_trades = len(df)
        successful_trades = (df['success'] == True).sum()
        failed_trades = (df['success'] == False).sum()
        success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0

        # By wait days
        by_wait_days = {}
        for wait_days in sorted(df['wait_days'].unique()):
            subset = df[df['wait_days'] == wait_days]
            success = (subset['success'] == True).sum()
            total = len(subset)
            by_wait_days[wait_days] = {
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
            by_expiry_days[expiry_days] = {
                'success_count': int(success),
                'total_count': int(total),
                'success_rate': float(success / total * 100) if total > 0 else 0
            }

        # Average metrics
        df_success = df[df['success'] == True]
        avg_break_pct = float(df_success['break_pct'].mean()) if len(df_success) > 0 else None
        avg_days_to_break = float(df_success['days_to_break'].mean()) if len(df_success) > 0 else None

        stats[period] = {
            'total_trades': int(total_trades),
            'successful_trades': int(successful_trades),
            'failed_trades': int(failed_trades),
            'success_rate': float(success_rate),
            'by_wait_days': by_wait_days,
            'by_expiry_days': by_expiry_days,
            'avg_break_pct': avg_break_pct,
            'avg_days_to_break': avg_days_to_break,
            'unique_stocks': int(df['stock'].nunique()),
            'unique_support_dates': int(df['support_date'].nunique())
        }

    return stats

stats = generate_statistics()

# Generate per-stock statistics
print("Generating per-stock statistics...")
stock_stats = {}
for period, df in results_data.items():
    stock_stats[period] = {}
    for stock in df['stock'].unique():
        stock_df = df[df['stock'] == stock]
        total = len(stock_df)
        success = (stock_df['success'] == True).sum()
        stock_stats[period][stock] = {
            'total_trades': int(total),
            'successful_trades': int(success),
            'success_rate': float(success / total * 100) if total > 0 else 0
        }

# Note: Chart data will be generated on-demand by the dashboard JavaScript
# For now, we'll just include references to what data is available
print("Preparing chart data references...")

# Get all stocks
all_stocks = sorted(list(set(
    stock for period_df in results_data.values()
    for stock in period_df['stock'].unique()
)))

print(f"Total stocks: {len(all_stocks)}")

# Build comprehensive data
dashboard_data = {
    'statistics': stats,
    'stock_statistics': stock_stats,
    'all_stocks': all_stocks,
    'wait_time_constraints': {
        '1-Month': [0, 30],
        '3-Month': [0, 30, 60, 90],
        '6-Month': [0, 30, 60, 90, 120, 180],
        '9-Month': [0, 30, 60, 90, 120, 180],
        '1-Year': [0, 30, 60, 90, 120, 180]
    },
    'expiry_periods': [7, 14, 21, 30, 45]
}

# Save to JSON
output_path = base_path / 'enhanced_dashboard_data.json'
print(f"\nSaving to {output_path}...")
with open(output_path, 'w') as f:
    json.dump(dashboard_data, f, indent=2)

file_size = output_path.stat().st_size / 1024 / 1024
print(f"Done! File size: {file_size:.1f} MB")
print("\nSummary:")
print(f"  Periods: {len(stats)}")
print(f"  Stocks: {len(all_stocks)}")
