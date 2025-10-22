"""
Create ONE final HTML dashboard by:
1. Converting parquet data to JSON (one time)
2. Embedding it directly in HTML
Done.
"""

import pandas as pd
import json
from pathlib import Path

print("Converting parquet files to embeddable JSON...")

# Load all detailed results
periods = {
    '1_month': '1-Month',
    '3_month': '3-Month',
    '6_month': '6-Month',
    '9_month': '9-Month',
    '1_year': '1-Year'
}

all_chart_data = {}
price_data = pd.read_parquet('../../price_data_filtered.parquet')
price_data['date'] = pd.to_datetime(price_data['date'])

print(f"Loaded price data: {len(price_data)} rows")

for period_key, period_name in periods.items():
    print(f"\nProcessing {period_name}...")

    # Load detailed results
    df = pd.read_parquet(f'{period_key}_detailed_results.parquet')
    df['support_date'] = pd.to_datetime(df['support_date'])
    df['test_date'] = pd.to_datetime(df['test_date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])

    # Group by (stock, wait_days, expiry_days) and get one successful example from each
    for (stock, wait_days, expiry_days), group in df.groupby(['stock', 'wait_days', 'expiry_days']):
        # Prefer successful trades
        successful = group[group['success'] == True]
        if len(successful) > 0:
            row = successful.iloc[0]
        else:
            row = group.iloc[0]

        # Get price history
        start_date = row['support_date'] - pd.Timedelta(days=60)
        end_date = row['expiry_date'] + pd.Timedelta(days=30)

        price_subset = price_data[
            (price_data['name'] == stock) &
            (price_data['date'] >= start_date) &
            (price_data['date'] <= end_date)
        ].sort_values('date')

        if len(price_subset) == 0:
            continue

        # Build chart data
        price_history = []
        for _, p in price_subset.iterrows():
            price_history.append({
                'date': p['date'].strftime('%Y-%m-%d'),
                'close': float(p['close']),
                'high': float(p['high']) if pd.notna(p['high']) else None,
                'low': float(p['low']) if pd.notna(p['low']) else None
            })

        # Count stats for this combination
        total = len(group)
        success = (group['success'] == True).sum()

        # Store
        period_clean = period_name.replace(' ', '_').replace('-', '')
        key = f"{stock}_{period_clean}_{wait_days}_{expiry_days}"

        all_chart_data[key] = {
            'stock': stock,
            'period': period_name,
            'wait_days': int(wait_days),
            'expiry_days': int(expiry_days),
            'support_date': row['support_date'].strftime('%Y-%m-%d'),
            'support_level': float(row['support_level']),
            'test_date': row['test_date'].strftime('%Y-%m-%d'),
            'expiry_date': row['expiry_date'].strftime('%Y-%m-%d'),
            'success': bool(row['success']) if pd.notna(row['success']) else None,
            'price_history': price_history,
            'total_records': int(total),
            'success_count': int(success),
            'success_rate': float(success / total * 100) if total > 0 else 0
        }

    print(f"  Generated {len([k for k in all_chart_data.keys() if period_clean in k])} chart samples for {period_name}")

print(f"\nTotal chart data: {len(all_chart_data)} combinations")

# Read template HTML
html_template = Path('enhanced_multi_period_dashboard.html').read_text()

# Embed data
data_js = f"        window.CHART_DATA = {json.dumps(all_chart_data)};\n\n"
html_template = html_template.replace(
    "    <script>",
    f"    <script>\n{data_js}"
)

# Save
output = Path('dashboard.html')
output.write_text(html_template)

print(f"\n✅ DONE!")
print(f"📊 Created: dashboard.html ({output.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"📌 Contains: {len(all_chart_data)} price charts")
print(f"🎯 NO MORE SCRIPTS - just open dashboard.html in browser!")
