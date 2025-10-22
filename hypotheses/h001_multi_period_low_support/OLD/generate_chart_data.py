"""
Generate chart data for a specific stock/period/wait_days/expiry_days combination.
This script is called from the dashboard to get price history for visualization.
Usage: python generate_chart_data.py <stock_name> <period_name> <wait_days> <expiry_days>
"""

import sys
import json
import pandas as pd
from datetime import timedelta
from pathlib import Path

def generate_chart_data(stock_name, period_name, wait_days, expiry_days, max_examples=5):
    """Generate chart data for a specific combination"""

    base_path = Path(__file__).parent

    # Map period names to file names
    period_map = {
        '1-Month': '1_month',
        '3-Month': '3_month',
        '6-Month': '6_month',
        '9-Month': '9_month',
        '1-Year': '1_year'
    }

    period_key = period_map.get(period_name)
    if not period_key:
        print(json.dumps({'error': 'Invalid period name'}))
        return

    # Load results data
    results_path = base_path / f'{period_key}_detailed_results.parquet'
    if not results_path.exists():
        print(json.dumps({'error': 'Data file not found'}))
        return

    results_df = pd.read_parquet(results_path)
    results_df['support_date'] = pd.to_datetime(results_df['support_date'])
    results_df['test_date'] = pd.to_datetime(results_df['test_date'])
    results_df['expiry_date'] = pd.to_datetime(results_df['expiry_date'])

    # Load price data
    price_path = base_path.parent.parent / 'price_data_filtered.parquet'
    price_df = pd.read_parquet(price_path)
    price_df['date'] = pd.to_datetime(price_df['date'])

    # Filter for this combination
    subset = results_df[
        (results_df['stock'] == stock_name) &
        (results_df['wait_days'] == wait_days) &
        (results_df['expiry_days'] == expiry_days)
    ]

    if len(subset) == 0:
        print(json.dumps({'error': 'No data found for this combination', 'records': 0}))
        return

    # Get examples (limit to max_examples)
    examples = []
    for idx, row in subset.head(max_examples).iterrows():
        support_date = row['support_date']
        test_date = row['test_date']
        expiry_date = row['expiry_date']

        # Get price data: 60 days before support to 30 days after expiry
        start_date = support_date - timedelta(days=60)
        end_date = expiry_date + timedelta(days=30)

        price_subset = price_df[
            (price_df['name'] == stock_name) &
            (price_df['date'] >= start_date) &
            (price_df['date'] <= end_date)
        ].copy()

        if len(price_subset) == 0:
            continue

        price_subset = price_subset.sort_values('date')

        # Format price data
        price_points = [
            {
                'date': str(p['date'].date()),
                'close': float(p['close']),
                'high': float(p['high']),
                'low': float(p['low']),
            }
            for _, p in price_subset.iterrows()
        ]

        examples.append({
            'support_date': str(support_date.date()),
            'support_level': float(row['support_level']),
            'test_date': str(test_date.date()),
            'expiry_date': str(expiry_date.date()),
            'success': bool(row['success']) if pd.notna(row['success']) else None,
            'min_during_option': float(row['min_during_option']) if pd.notna(row['min_during_option']) else None,
            'days_to_break': float(row['days_to_break']) if pd.notna(row['days_to_break']) else None,
            'break_pct': float(row['break_pct']) if pd.notna(row['break_pct']) else None,
            'price_history': price_points
        })

    output = {
        'stock': stock_name,
        'period': period_name,
        'wait_days': int(wait_days),
        'expiry_days': int(expiry_days),
        'total_records': len(subset),
        'examples': examples,
        'summary': {
            'success_count': int((subset['success'] == True).sum()),
            'failure_count': int((subset['success'] == False).sum()),
            'total_count': len(subset),
            'success_rate': float((subset['success'] == True).sum() / len(subset) * 100) if len(subset) > 0 else 0
        }
    }

    print(json.dumps(output))

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(json.dumps({'error': 'Usage: generate_chart_data.py <stock> <period> <wait_days> <expiry_days>'}))
        sys.exit(1)

    stock_name = sys.argv[1]
    period_name = sys.argv[2]
    wait_days = int(sys.argv[3])
    expiry_days = int(sys.argv[4])

    generate_chart_data(stock_name, period_name, wait_days, expiry_days)
