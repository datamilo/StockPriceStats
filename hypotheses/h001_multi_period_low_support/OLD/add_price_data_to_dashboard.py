#!/usr/bin/env python3
"""
Add price chart data to the multi-period dashboard.
Uses the same simple format as the backup dashboard.
"""

import pandas as pd
import json

def load_events_for_period(period_file_prefix, period_name):
    """Load events for a specific low period in simple format."""
    filename = f'{period_file_prefix}_detailed_results.parquet'

    try:
        df = pd.read_parquet(filename)
        print(f"  Loading {period_name}: {len(df)} rows")

        # Group by stock and event_date to get unique events
        # For each event, we'll take the 30-day testing results
        events_by_stock = {}

        for stock in df['stock'].unique():
            stock_data = df[df['stock'] == stock].copy()

            events_list = []

            # Group by event_date - each unique event_date is one support event
            for event_date in stock_data['event_date'].unique():
                event_rows = stock_data[stock_data['event_date'] == event_date]

                # Get support level (same for all rows)
                support_level = float(event_rows['support_level'].iloc[0])

                # For now, just use the 30-day checkpoint results
                # This matches the original dashboard format
                checkpoint_30d = event_rows[event_rows['age_checkpoint_days'] == 30]

                if len(checkpoint_30d) == 0:
                    continue  # Skip if no 30-day checkpoint

                # Get checkpoint date (30 days after event_date = test_end_date)
                test_end_date = checkpoint_30d['checkpoint_date'].iloc[0]

                event_data = {
                    'event_date': event_date,
                    'support_level': support_level,
                    'test_end_date': test_end_date,
                }

                # Add success flags and break info for each next period
                for next_days in [7, 14, 21, 30, 45]:
                    row = checkpoint_30d[checkpoint_30d['next_period_days'] == next_days]

                    if len(row) > 0:
                        row = row.iloc[0]
                        event_data[f'success_{next_days}d'] = bool(row['success'])

                        if pd.notna(row['days_to_break']):
                            event_data[f'days_to_break_{next_days}d'] = int(row['days_to_break'])
                        else:
                            event_data[f'days_to_break_{next_days}d'] = None

                        if pd.notna(row['decline_pct']):
                            event_data[f'decline_{next_days}d'] = round(float(row['decline_pct']), 2)
                        else:
                            event_data[f'decline_{next_days}d'] = None
                    else:
                        event_data[f'success_{next_days}d'] = None
                        event_data[f'days_to_break_{next_days}d'] = None
                        event_data[f'decline_{next_days}d'] = None

                events_list.append(event_data)

            if events_list:
                events_by_stock[stock] = events_list

        print(f"    {period_name}: {len(events_by_stock)} stocks, {sum(len(v) for v in events_by_stock.values())} events")
        return events_by_stock

    except FileNotFoundError:
        print(f"  ⚠ {filename} not found")
        return {}

def main():
    print("=" * 60)
    print("Adding Price Chart Data to Multi-Period Dashboard")
    print("=" * 60)

    # Load existing multi-period dashboard data
    print("\nLoading existing dashboard data...")
    with open('multi_period_dashboard_data.json', 'r') as f:
        dashboard_data = json.load(f)
    print(f"✓ Loaded existing data ({len(dashboard_data)} keys)")

    # Load price_history from the short-term dashboard data
    print("\nLoading price history...")
    with open('dashboard_data_short_term.json', 'r') as f:
        short_term_data = json.load(f)
        price_history = short_term_data['price_history']
    print(f"✓ Loaded price history for {len(price_history)} stocks")

    # Load events for each period
    print("\nLoading support events for each period...")
    periods = [
        ('1_month_low', '1-Month Low'),
        ('3_month_low', '3-Month Low'),
        ('6_month_low', '6-Month Low'),
        ('9_month_low', '9-Month Low'),
        ('1_year_low', '1-Year Low')
    ]

    events_by_period = {}
    for period_file, period_name in periods:
        events_by_period[period_name] = load_events_for_period(period_file, period_name)

    # Add to dashboard data
    dashboard_data['price_history'] = price_history
    dashboard_data['events_by_period'] = events_by_period

    # Save updated dashboard data
    print("\n💾 Saving updated dashboard data...")
    with open('multi_period_dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)

    # Calculate file size
    import os
    file_size_mb = os.path.getsize('multi_period_dashboard_data.json') / (1024 * 1024)

    print(f"\n✓ Dashboard data updated successfully!")
    print(f"  File size: {file_size_mb:.2f} MB")
    print(f"  Price history stocks: {len(price_history)}")
    print(f"  Event periods: {len(events_by_period)}")

    total_events = sum(
        sum(len(events) for events in period_events.values())
        for period_events in events_by_period.values()
    )
    print(f"  Total support events: {total_events}")

    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
