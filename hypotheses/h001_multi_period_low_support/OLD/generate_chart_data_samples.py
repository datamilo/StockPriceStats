"""
Generate chart data samples for embedding in the dashboard
"""

import subprocess
import json
from pathlib import Path

# Sample combinations to generate
samples = [
    ("EQT AB", "1-Month", 30, 7),
    ("Fortnox AB", "3-Month", 90, 21),
    ("Atlas Copco AB ser. A", "6-Month", 120, 30),
    ("Volvo, AB ser. B", "9-Month", 180, 45),
    ("Alfa Laval AB", "1-Year", 90, 14),
]

print("Generating chart data samples...")
chart_data = {}

for stock, period, wait_days, expiry_days in samples:
    key = f"{stock}_{period.replace(' ', '_').replace('-', '')}_{wait_days}_{expiry_days}"

    try:
        print(f"  Generating: {stock} - {period} - {wait_days}d wait - {expiry_days}d expiry...", end=" ")
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
            print(f"✗ Error")

    except Exception as e:
        print(f"✗ Exception: {e}")

# Output as JavaScript
output = f"""
// Chart data samples - embedded for offline use
const chartDataSamples = {json.dumps(chart_data, indent=2)};
"""

output_file = Path(__file__).parent / "chart_data_samples.js"
with open(output_file, 'w') as f:
    f.write(output)

print(f"\n✓ Generated {len(chart_data)} chart samples")
print(f"✓ Saved to: {output_file}")
