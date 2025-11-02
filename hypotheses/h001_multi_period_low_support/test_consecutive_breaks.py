"""
Quick test of consecutive break analysis on a sample stock
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load data
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'

df = pd.read_parquet(DATA_FILE)
df['date'] = pd.to_datetime(df['date'])

# Pick a stock with recent data - let's use AAK AB
test_stock = 'AAK AB'
stock_data = df[df['name'] == test_stock].copy()
stock_data = stock_data.sort_values('date').reset_index(drop=True)

print(f"Testing with: {test_stock}")
print(f"Date range: {stock_data['date'].min().date()} to {stock_data['date'].max().date()}")
print(f"Total days: {len(stock_data)}")

# Calculate 3-month (90-day) rolling low
period_days = 90
print(f"\nCalculating {period_days}-day rolling low...")

rolling_lows = []
for idx, row in stock_data.iterrows():
    current_date = row['date']
    lookback_date = current_date - pd.Timedelta(days=period_days)

    window_data = stock_data[
        (stock_data['date'] >= lookback_date) &
        (stock_data['date'] <= current_date)
    ]

    if len(window_data) > 0:
        rolling_lows.append(window_data['low'].min())
    else:
        rolling_lows.append(None)

stock_data['rolling_low'] = rolling_lows

# Identify breaks
stock_data['rolling_low_prev'] = stock_data['rolling_low'].shift(1)
stock_data['support_break'] = stock_data['rolling_low'] < stock_data['rolling_low_prev']

breaks = stock_data[stock_data['support_break'] == True].copy()
print(f"Total support breaks: {len(breaks)}")

if len(breaks) == 0:
    print("No breaks found!")
    exit()

# Calculate consecutive break clusters
breaks['drop_pct'] = ((breaks['rolling_low'] - breaks['rolling_low_prev']) / breaks['rolling_low_prev'] * 100)
breaks['days_from_prev'] = breaks['date'].diff().dt.days

max_gap_days = 30
breaks['new_cluster'] = (breaks['days_from_prev'].isna()) | (breaks['days_from_prev'] > max_gap_days)
breaks['cluster_id'] = breaks['new_cluster'].cumsum()

print(f"\n{'='*80}")
print(f"CONSECUTIVE BREAK ANALYSIS (max {max_gap_days} days between breaks)")
print(f"{'='*80}")

# Analyze each cluster
clusters = []
for cluster_id, cluster_df in breaks.groupby('cluster_id'):
    cluster_df = cluster_df.sort_values('date')
    num_breaks = len(cluster_df)

    cluster_info = {
        'cluster_id': int(cluster_id),
        'num_breaks': num_breaks,
        'start_date': cluster_df['date'].min(),
        'end_date': cluster_df['date'].max(),
        'duration_days': int((cluster_df['date'].max() - cluster_df['date'].min()).days),
        'avg_gap_days': float(cluster_df['days_from_prev'].mean()) if num_breaks > 1 else None,
        'min_gap_days': float(cluster_df['days_from_prev'].min()) if num_breaks > 1 else None,
        'total_drop_pct': float(cluster_df['drop_pct'].sum()),
    }
    clusters.append(cluster_info)

# Summary
cluster_sizes = [c['num_breaks'] for c in clusters]
print(f"\nTotal clusters: {len(clusters)}")
print(f"Single-break clusters: {sum(1 for s in cluster_sizes if s == 1)}")
print(f"Multi-break clusters: {sum(1 for s in cluster_sizes if s > 1)}")
print(f"Max consecutive breaks: {max(cluster_sizes)}")

# Cluster size distribution
print("\nCluster size distribution:")
size_dist = pd.Series(cluster_sizes).value_counts().sort_index()
for size, count in size_dist.items():
    pct = count / len(clusters) * 100
    print(f"  {size} breaks: {count} clusters ({pct:.1f}%)")

# Show top 5 largest clusters
multi_break = [c for c in clusters if c['num_breaks'] > 1]
if len(multi_break) > 0:
    print(f"\n{'='*80}")
    print(f"TOP MULTI-BREAK CLUSTERS")
    print(f"{'='*80}")

    for cluster in sorted(multi_break, key=lambda x: x['num_breaks'], reverse=True)[:5]:
        print(f"\nCluster #{cluster['cluster_id']}: {cluster['num_breaks']} consecutive breaks")
        print(f"  Period: {cluster['start_date'].strftime('%Y-%m-%d')} to {cluster['end_date'].strftime('%Y-%m-%d')}")
        print(f"  Duration: {cluster['duration_days']} days")
        if cluster['avg_gap_days']:
            print(f"  Avg gap: {cluster['avg_gap_days']:.1f} days")
            print(f"  Min gap: {cluster['min_gap_days']:.0f} days")
        print(f"  Total drop: {cluster['total_drop_pct']:.2f}%")

        # Show individual breaks
        cluster_breaks = breaks[breaks['cluster_id'] == cluster['cluster_id']][['date', 'rolling_low_prev', 'rolling_low', 'drop_pct', 'days_from_prev']]
        print(f"\n  Individual breaks:")
        for idx, row in cluster_breaks.iterrows():
            gap_str = f"(+{row['days_from_prev']:.0f}d)" if pd.notna(row['days_from_prev']) else "(start)"
            print(f"    {row['date'].strftime('%Y-%m-%d')} {gap_str}: {row['rolling_low_prev']:.2f} → {row['rolling_low']:.2f} kr ({row['drop_pct']:.2f}%)")

print(f"\n{'='*80}")
print("TEST COMPLETE")
print(f"{'='*80}")
