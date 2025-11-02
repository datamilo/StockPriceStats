"""
Analyze Consecutive Support Break Patterns

When support breaks, breaks often cluster together (happen within a short time).
This script identifies and analyzes these consecutive break clusters.

Questions answered:
1. How many breaks happen consecutively (within short periods)?
2. What is the gap between consecutive breaks?
3. How often do clusters of 2, 3, 4+ breaks occur?
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

# Configuration
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'
OUTPUT_DIR = SCRIPT_DIR / 'consecutive_breaks_analysis'
OUTPUT_DIR.mkdir(exist_ok=True)


def calculate_rolling_low(stock_data, period_days):
    """Calculate rolling low using calendar days"""
    stock_data = stock_data.sort_values('date').reset_index(drop=True)

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
    return stock_data


def identify_support_breaks(stock_data):
    """Identify all dates where support was broken (rolling low decreased)"""
    stock_data = stock_data.sort_values('date').copy()
    stock_data['rolling_low_prev'] = stock_data['rolling_low'].shift(1)
    stock_data['support_break'] = stock_data['rolling_low'] < stock_data['rolling_low_prev']

    breaks = stock_data[stock_data['support_break'] == True].copy()
    breaks['prev_support'] = breaks['rolling_low_prev']
    breaks['new_support'] = breaks['rolling_low']
    breaks['drop_pct'] = ((breaks['new_support'] - breaks['prev_support']) / breaks['prev_support'] * 100)

    return breaks[['date', 'prev_support', 'new_support', 'drop_pct']].copy()


def analyze_consecutive_breaks(breaks_df, max_gap_days=30):
    """
    Identify clusters of consecutive breaks

    A cluster is a group of breaks where each break happens within max_gap_days
    of the previous break.

    Returns:
    - clusters: List of cluster dictionaries
    - cluster_stats: Summary statistics about clusters
    """
    if len(breaks_df) == 0:
        return [], {}

    breaks_df = breaks_df.sort_values('date').reset_index(drop=True)

    # Calculate days between consecutive breaks
    breaks_df['days_to_next'] = breaks_df['date'].diff(-1).abs().dt.days
    breaks_df['days_from_prev'] = breaks_df['date'].diff().dt.days

    # Identify cluster boundaries
    # A new cluster starts when gap from previous break > max_gap_days
    breaks_df['new_cluster'] = (breaks_df['days_from_prev'].isna()) | (breaks_df['days_from_prev'] > max_gap_days)
    breaks_df['cluster_id'] = breaks_df['new_cluster'].cumsum()

    # Analyze each cluster
    clusters = []
    for cluster_id, cluster_df in breaks_df.groupby('cluster_id'):
        cluster_df = cluster_df.sort_values('date')

        cluster_info = {
            'cluster_id': cluster_id,
            'num_breaks': len(cluster_df),
            'start_date': cluster_df['date'].min(),
            'end_date': cluster_df['date'].max(),
            'duration_days': (cluster_df['date'].max() - cluster_df['date'].min()).days,
            'avg_gap_days': cluster_df['days_from_prev'].mean() if len(cluster_df) > 1 else None,
            'max_gap_days': cluster_df['days_from_prev'].max() if len(cluster_df) > 1 else None,
            'min_gap_days': cluster_df['days_from_prev'].min() if len(cluster_df) > 1 else None,
            'total_drop_pct': cluster_df['drop_pct'].sum(),
            'avg_drop_pct': cluster_df['drop_pct'].mean(),
            'breaks': cluster_df[['date', 'prev_support', 'new_support', 'drop_pct', 'days_from_prev']].to_dict('records')
        }
        clusters.append(cluster_info)

    # Calculate cluster statistics
    cluster_sizes = [c['num_breaks'] for c in clusters]
    cluster_stats = {
        'total_clusters': len(clusters),
        'total_breaks': len(breaks_df),
        'single_break_clusters': sum(1 for s in cluster_sizes if s == 1),
        'multi_break_clusters': sum(1 for s in cluster_sizes if s > 1),
        'cluster_size_distribution': pd.Series(cluster_sizes).value_counts().sort_index().to_dict(),
        'avg_breaks_per_cluster': np.mean(cluster_sizes),
        'max_breaks_in_cluster': max(cluster_sizes),
        'avg_cluster_duration': np.mean([c['duration_days'] for c in clusters if c['num_breaks'] > 1]),
    }

    return clusters, cluster_stats


def analyze_all_stocks(period_days, max_gap_days=30):
    """Analyze consecutive breaks for all stocks for a given period"""
    print(f"\nAnalyzing {period_days}-day rolling low...")
    print(f"Max gap for consecutive breaks: {max_gap_days} days")

    # Load data
    df = pd.read_parquet(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])

    all_results = []
    stocks = sorted(df['name'].unique())

    for i, stock in enumerate(stocks, 1):
        print(f"  [{i}/{len(stocks)}] {stock}", end='')

        stock_data = df[df['name'] == stock].copy()

        # Calculate rolling low
        stock_data = calculate_rolling_low(stock_data, period_days)

        # Identify breaks
        breaks = identify_support_breaks(stock_data)

        if len(breaks) == 0:
            print(" - No breaks")
            continue

        # Analyze consecutive break patterns
        clusters, stats = analyze_consecutive_breaks(breaks, max_gap_days)

        print(f" - {len(breaks)} breaks, {stats['total_clusters']} clusters, max {stats['max_breaks_in_cluster']} consecutive")

        # Store results
        for cluster in clusters:
            all_results.append({
                'stock': stock,
                'period_days': period_days,
                'cluster_id': cluster['cluster_id'],
                'num_breaks': cluster['num_breaks'],
                'start_date': cluster['start_date'],
                'end_date': cluster['end_date'],
                'duration_days': cluster['duration_days'],
                'avg_gap_days': cluster['avg_gap_days'],
                'min_gap_days': cluster['min_gap_days'],
                'max_gap_days': cluster['max_gap_days'],
                'total_drop_pct': cluster['total_drop_pct'],
                'avg_drop_pct': cluster['avg_drop_pct'],
            })

    results_df = pd.DataFrame(all_results)

    # Overall statistics
    print("\n" + "="*80)
    print(f"OVERALL STATISTICS - {period_days}-day rolling low")
    print("="*80)

    if len(results_df) > 0:
        print(f"\nTotal clusters across all stocks: {len(results_df)}")
        print(f"Single-break clusters: {len(results_df[results_df['num_breaks'] == 1])}")
        print(f"Multi-break clusters: {len(results_df[results_df['num_breaks'] > 1])}")

        print("\nCluster size distribution:")
        size_dist = results_df['num_breaks'].value_counts().sort_index()
        for size, count in size_dist.items():
            pct = count / len(results_df) * 100
            print(f"  {size} breaks: {count} clusters ({pct:.1f}%)")

        print(f"\nLargest cluster: {results_df['num_breaks'].max()} consecutive breaks")
        largest = results_df[results_df['num_breaks'] == results_df['num_breaks'].max()].iloc[0]
        print(f"  Stock: {largest['stock']}")
        print(f"  Period: {largest['start_date'].strftime('%Y-%m-%d')} to {largest['end_date'].strftime('%Y-%m-%d')}")
        print(f"  Duration: {largest['duration_days']} days")

        multi_break = results_df[results_df['num_breaks'] > 1]
        if len(multi_break) > 0:
            print(f"\nFor multi-break clusters:")
            print(f"  Average cluster duration: {multi_break['duration_days'].mean():.1f} days")
            print(f"  Average gap between breaks: {multi_break['avg_gap_days'].mean():.1f} days")
            print(f"  Shortest gap ever: {multi_break['min_gap_days'].min():.0f} days")
            print(f"  Average total drop per cluster: {multi_break['total_drop_pct'].mean():.2f}%")

    return results_df


def main():
    """Run analysis for all periods"""
    print("="*80)
    print("CONSECUTIVE SUPPORT BREAK ANALYSIS")
    print("="*80)
    print(f"\nOutput directory: {OUTPUT_DIR}")

    # Define max gap (how many days between breaks to still consider them consecutive)
    MAX_GAP_DAYS = 30  # Breaks within 30 days are considered consecutive

    all_period_results = {}

    for period_days in [30, 90, 180, 270, 365]:
        period_name = {30: '1_month', 90: '3_month', 180: '6_month', 270: '9_month', 365: '1_year'}[period_days]

        results_df = analyze_all_stocks(period_days, MAX_GAP_DAYS)

        # Save results
        output_file = OUTPUT_DIR / f'{period_name}_consecutive_breaks.parquet'
        results_df.to_parquet(output_file, index=False)
        print(f"\nSaved: {output_file}")

        all_period_results[period_name] = results_df

    # Create summary comparison across all periods
    print("\n" + "="*80)
    print("COMPARISON ACROSS ALL PERIODS")
    print("="*80)

    summary_data = []
    for period_name, df in all_period_results.items():
        if len(df) > 0:
            multi_break = df[df['num_breaks'] > 1]
            summary_data.append({
                'Period': period_name.replace('_', '-').title(),
                'Total Clusters': len(df),
                'Single Break': len(df[df['num_breaks'] == 1]),
                'Multi Break': len(multi_break),
                'Multi Break %': len(multi_break) / len(df) * 100,
                'Avg Cluster Size': df['num_breaks'].mean(),
                'Max Cluster Size': df['num_breaks'].max(),
                'Avg Gap (Multi)': multi_break['avg_gap_days'].mean() if len(multi_break) > 0 else None,
            })

    summary_df = pd.DataFrame(summary_data)
    print("\n", summary_df.to_string(index=False))

    summary_file = OUTPUT_DIR / 'summary_comparison.csv'
    summary_df.to_csv(summary_file, index=False)
    print(f"\nSaved summary: {summary_file}")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)


if __name__ == '__main__':
    main()
