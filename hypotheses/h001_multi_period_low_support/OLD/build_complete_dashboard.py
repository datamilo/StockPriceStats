"""
Build a complete, self-contained dashboard with embedded chart data
"""

import json
import subprocess
from pathlib import Path

print("Building complete dashboard with embedded chart data...")

# First, read the base HTML
dashboard_file = Path("enhanced_multi_period_dashboard.html")
html_content = dashboard_file.read_text()

# Generate chart data for multiple combinations
samples = [
    ("EQT AB", "1-Month", 30, 7),
    ("Fortnox AB", "3-Month", 90, 21),
    ("Atlas Copco AB ser. A", "6-Month", 120, 30),
    ("Volvo, AB ser. B", "9-Month", 180, 45),
    ("Alfa Laval AB", "1-Year", 90, 14),
    ("Hexagon AB ser. B", "1-Month", 30, 21),
]

print("Generating chart data samples...")
chart_data = {}

for stock, period, wait_days, expiry_days in samples:
    key = f"{stock}_{period.replace(' ', '_').replace('-', '')}_{wait_days}_{expiry_days}"

    try:
        print(f"  {stock} ({period}, {wait_days}d, {expiry_days}d expiry)...", end=" ")
        result = subprocess.run(
            ['python3', 'generate_chart_data.py', stock, period, str(wait_days), str(expiry_days)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            chart_data[key] = data
            print("✓")
        else:
            print("✗")

    except Exception as e:
        print(f"✗ ({e})")

# Create JavaScript variable for chart data
chart_data_js = f"""
        // Pre-generated chart data - embedded for offline use
        window.chartDataSamples = {json.dumps(chart_data)};
"""

# Insert the chart data before the closing </script> tag
if "</script>" in html_content:
    html_content = html_content.replace("</script>", chart_data_js + "\n    </script>", 1)

# Save the complete dashboard
output_file = Path("enhanced_multi_period_dashboard_complete.html")
output_file.write_text(html_content)

print(f"\n✓ Generated complete dashboard with {len(chart_data)} chart samples")
print(f"✓ File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
print(f"✓ Saved to: {output_file}")
print("\n📊 Open this file in your browser to view interactive charts!")
print("\n💡 The dashboard now includes:")
print("   • Sample price charts for 6 different stock/period/wait combinations")
print("   • Click on any stock/period/wait/expiry combination that's pre-generated to see the chart")
print("   • For other combinations, instructions will show how to generate the chart data")
