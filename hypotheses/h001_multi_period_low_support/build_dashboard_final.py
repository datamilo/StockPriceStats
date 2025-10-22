"""
Build a complete dashboard with properly embedded chart data
"""

import json
import subprocess
from pathlib import Path

print("Building final dashboard with chart data...")

# Generate chart data for multiple combinations
samples = [
    ("EQT AB", "1-Month", 30, 7),
    ("Fortnox AB", "3-Month", 90, 21),
    ("Atlas Copco AB ser. A", "6-Month", 120, 30),
    ("Volvo, AB ser. B", "9-Month", 180, 45),
    ("Alfa Laval AB", "1-Year", 90, 14),
    ("Hexagon AB ser. B", "1-Month", 30, 21),
    ("AAK AB", "1-Month", 30, 14),
    ("Axfood AB", "3-Month", 60, 21),
]

print("Generating chart data samples...")
chart_data = {}

for stock, period, wait_days, expiry_days in samples:
    # Build key exactly as dashboard expects it
    period_key = period.replace(' ', '_').replace('-', '')
    key = f"{stock}_{period_key}_{wait_days}_{expiry_days}"

    try:
        print(f"  {stock} ({period}, {wait_days}d, {expiry_days}d)...", end=" ")
        result = subprocess.run(
            ['python3', 'generate_chart_data.py', stock, period, str(wait_days), str(expiry_days)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            chart_data[key] = data
            print(f"✓")
        else:
            print(f"✗")

    except Exception as e:
        print(f"✗ ({str(e)[:30]})")

print(f"\nGenerated {len(chart_data)} chart samples")

# Read base HTML
base_html = Path("enhanced_multi_period_dashboard.html").read_text()

# Find the point to insert data (right before initializeCharts function)
insertion_point = "        function initializeCharts()"

if insertion_point not in base_html:
    print("ERROR: Could not find insertion point in HTML")
    exit(1)

# Create data embedding code
data_code = f"""        // Pre-generated chart data samples - embedded for instant display
        window.chartDataSamples = {json.dumps(chart_data)};

        // Quick reference for available samples
        const availableSamples = {json.dumps({
            key: {
                'stock': data['stock'],
                'period': data['period'],
                'wait_days': data['wait_days'],
                'expiry_days': data['expiry_days']
            }
            for key, data in chart_data.items()
        })};

"""

# Insert the data code
new_html = base_html.replace(insertion_point, data_code + insertion_point)

# Save
output_file = Path("enhanced_dashboard_with_charts.html")
output_file.write_text(new_html)

print(f"\n✅ Dashboard ready!")
print(f"📊 File: enhanced_dashboard_with_charts.html")
print(f"💾 Size: {output_file.stat().st_size / 1024:.1f} KB\n")
print("Pre-loaded chart combinations:")
for key in sorted(chart_data.keys()):
    data = chart_data[key]
    print(f"  • {data['stock']:35} | {data['period']:10} | Wait: {data['wait_days']:3}d | Expiry: {data['expiry_days']:2}d")

print(f"\n🎉 Open the dashboard and try these combinations to see price charts!")
