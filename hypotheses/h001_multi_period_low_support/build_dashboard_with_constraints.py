#!/usr/bin/env python3
"""
Build dashboard with CORRECTED constraint filters for wait times and expiry periods.

This enhanced dashboard includes:
1. Wait time filter constrained by period length
2. Expiry period filter
3. Updated matrix display based on selected parameters
"""

import json
import pandas as pd

print("Building dashboard with constraint filters...")
print("Loading results matrices...")

# Load matrices to understand structure
matrices = {}
for period in ['1_month', '3_month', '6_month', '9_month', '1_year']:
    try:
        df = pd.read_parquet(f'{period}_matrix.parquet')
        matrices[period] = df.to_dict('records')
    except:
        print(f"  Warning: Could not load {period}_matrix.parquet")

# Define wait time constraints for each period
WAIT_TIME_CONSTRAINTS = {
    '1-Month Low': [0, 30],
    '3-Month Low': [0, 30, 60, 90],
    '6-Month Low': [0, 30, 60, 90, 120, 180],
    '9-Month Low': [0, 30, 60, 90, 120, 180],
    '1-Year Low': [0, 30, 60, 90, 120, 180]
}

# All possible expiry periods
EXPIRY_PERIODS = [7, 14, 21, 30, 45]

# Load dashboard data
with open('multi_period_dashboard_data.json', 'r') as f:
    dashboard_data = json.load(f)

print(f"✓ Loaded dashboard data with {len(dashboard_data)} keys")
print(f"✓ Matrices loaded: {list(matrices.keys())}")

# Build HTML with constraint filters
html_start = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>H001 Multi-Period Analysis with Constraint Filters</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #2c3e50;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .content { padding: 40px; }
        .section {
            margin-bottom: 50px;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            border-left: 5px solid #667eea;
        }
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .control-group {
            display: flex;
            flex-direction: column;
        }
        .control-group label {
            font-weight: 600;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        .control-group select {
            padding: 12px;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 1em;
            background: white;
            cursor: pointer;
        }
        .control-group select:hover {
            border-color: #764ba2;
        }
        .control-group select:disabled {
            background: #ecf0f1;
            cursor: not-allowed;
            opacity: 0.6;
        }
        .constraint-info {
            background: #fff3cd;
            padding: 12px;
            border-radius: 6px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #856404;
            border-left: 4px solid #ffc107;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        th {
            background: #2c3e50;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
        }
        tr:hover { background: #f8f9fa; }
        .success-high { color: #27ae60; font-weight: bold; }
        .success-medium { color: #f39c12; font-weight: bold; }
        .success-low { color: #e74c3c; font-weight: bold; }
        #matrixTable {
            max-height: 600px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Multi-Period Low Analysis Dashboard</h1>
            <p>H001: Support Level Reliability for Put Option Writing</p>
            <p style="font-size: 0.9em; opacity: 0.8; margin-top: 10px;">With Dynamic Constraint Filters</p>
        </div>

        <div class="content">
            <!-- Success Rate Matrix with Filters -->
            <div class="section">
                <h2>🎯 Success Rate Matrix with Filters</h2>
                <p style="margin-bottom: 20px;">
                    Select a low period, wait time, and option expiry to see historical success rates.
                    <strong>Wait time options are automatically limited by the selected period length.</strong>
                </p>

                <div class="controls">
                    <div class="control-group">
                        <label for="periodSelect">Low Period:</label>
                        <select id="periodSelect">
                            <option value="1-Month Low">1-Month Low (Max wait: 30 days)</option>
                            <option value="3-Month Low">3-Month Low (Max wait: 90 days)</option>
                            <option value="6-Month Low">6-Month Low (Max wait: 180 days)</option>
                            <option value="9-Month Low">9-Month Low (Max wait: 180 days)</option>
                            <option value="1-Year Low">1-Year Low (Max wait: 180 days)</option>
                        </select>
                        <div class="constraint-info">
                            You can only wait as long as the period itself. E.g., a 1-month low can be tested for max 30 days.
                        </div>
                    </div>

                    <div class="control-group">
                        <label for="waitSelect">Wait Days (before writing put):</label>
                        <select id="waitSelect">
                            <option value="">-- Select wait time --</option>
                        </select>
                        <div class="constraint-info" id="waitInfo"></div>
                    </div>

                    <div class="control-group">
                        <label for="expirySelect">Put Option Expiry (days):</label>
                        <select id="expirySelect">
                            <option value="">-- Select expiry --</option>
                        </select>
                    </div>
                </div>

                <div id="matrixTable" style="margin-top: 30px;"></div>
            </div>

            <!-- Key Concepts -->
            <div class="section">
                <h2>📖 Understanding the Constraints</h2>

                <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #27ae60;">
                    <h3 style="color: #27ae60; margin-bottom: 10px;">Why Wait Time Constraints Exist</h3>
                    <p>
                        A "1-month low" is only valid for up to 1 month. Once that month has passed, it's no longer a "1-month low"
                        (it becomes part of a larger rolling window). Therefore:
                    </p>
                    <ul style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li><strong>1-Month Low:</strong> Can wait 0-30 days maximum</li>
                        <li><strong>3-Month Low:</strong> Can wait 0-90 days maximum</li>
                        <li><strong>6-Month Low:</strong> Can wait 0-180 days maximum</li>
                        <li><strong>9-Month Low:</strong> Can wait 0-180 days maximum (within 9-month window)</li>
                        <li><strong>1-Year Low:</strong> Can wait 0-180 days maximum (within 1-year window)</li>
                    </ul>
                </div>

                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196F3;">
                    <h3 style="color: #1976D2; margin-bottom: 10px;">Example: Using the Filters</h3>
                    <p><strong>Scenario:</strong> You want to write a 30-day put on a 3-month low</p>
                    <ol style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li>Select "3-Month Low" → Wait time options: 0, 30, 60, 90 days</li>
                        <li>Select "Wait 60 days" → You'll write the put 60 days after the low</li>
                        <li>Select "Expiry 30 days" → The put option lasts 30 days</li>
                        <li>Result: Success rate for 3-month lows tested after 60 days, over next 30 days</li>
                    </ol>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Data embedded
        const dashboardData = ''' + json.dumps(dashboard_data) + ''';
        const matrices = ''' + json.dumps(matrices) + ''';

        const WAIT_TIME_CONSTRAINTS = ''' + json.dumps(WAIT_TIME_CONSTRAINTS) + ''';
        const EXPIRY_PERIODS = ''' + json.dumps(EXPIRY_PERIODS) + ''';

        document.addEventListener('DOMContentLoaded', function() {
            initializeFilters();
        });

        function initializeFilters() {
            const periodSelect = document.getElementById('periodSelect');
            const waitSelect = document.getElementById('waitSelect');
            const expirySelect = document.getElementById('expirySelect');

            // Populate expiry periods
            EXPIRY_PERIODS.forEach(days => {
                const option = document.createElement('option');
                option.value = days;
                option.textContent = `${days} days`;
                expirySelect.appendChild(option);
            });

            // Update wait times when period changes
            periodSelect.addEventListener('change', function() {
                updateWaitTimes();
                updateMatrix();
            });

            // Update matrix when wait or expiry changes
            waitSelect.addEventListener('change', updateMatrix);
            expirySelect.addEventListener('change', updateMatrix);

            // Initial population
            updateWaitTimes();
        }

        function updateWaitTimes() {
            const periodSelect = document.getElementById('periodSelect');
            const waitSelect = document.getElementById('waitSelect');
            const waitInfo = document.getElementById('waitInfo');

            const period = periodSelect.value;
            const validWaitTimes = WAIT_TIME_CONSTRAINTS[period] || [];

            // Clear and repopulate
            waitSelect.innerHTML = '<option value="">-- Select wait time --</option>';

            validWaitTimes.forEach(days => {
                const option = document.createElement('option');
                option.value = days;
                option.textContent = `${days} days`;
                waitSelect.appendChild(option);
            });

            // Update info
            waitInfo.textContent = `Valid wait times for ${period}: ${validWaitTimes.join(', ')} days`;
            waitInfo.style.display = 'block';
        }

        function updateMatrix() {
            const periodSelect = document.getElementById('periodSelect');
            const waitSelect = document.getElementById('waitSelect');
            const expirySelect = document.getElementById('expirySelect');
            const matrixTable = document.getElementById('matrixTable');

            const period = periodSelect.value;
            const waitDays = parseInt(waitSelect.value);
            const expiryDays = parseInt(expirySelect.value);

            if (!waitSelect.value || !expirySelect.value) {
                matrixTable.innerHTML = '<p style="color: #7f8c8d;">Select wait time and expiry period to view results.</p>';
                return;
            }

            // Find matching data
            const periodKey = period.toLowerCase().replace(/ /g, '_').replace(/-/g, '_');
            const periodData = matrices[periodKey];

            if (!periodData) {
                matrixTable.innerHTML = '<p style="color: #e74c3c;">Data not available for this period.</p>';
                return;
            }

            // Find the row matching wait_days
            const row = periodData.find(r => r.wait_days === waitDays);
            if (!row) {
                matrixTable.innerHTML = '<p style="color: #e74c3c;">No data for this wait time.</p>';
                return;
            }

            // Extract rate and count
            const rateKey = `expiry_${expiryDays}d_rate`;
            const countKey = `expiry_${expiryDays}d_count`;
            const rate = row[rateKey];
            const count = row[countKey];

            if (rate === null || rate === undefined) {
                matrixTable.innerHTML = '<p style="color: #e74c3c;">No data for this combination.</p>';
                return;
            }

            // Determine color class
            let colorClass = 'success-low';
            if (rate >= 90) colorClass = 'success-high';
            else if (rate >= 85) colorClass = 'success-medium';

            // Build result table
            let html = `
                <table>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Low Period</td>
                        <td><strong>${period}</strong></td>
                    </tr>
                    <tr>
                        <td>Wait Days (after low set)</td>
                        <td><strong>${waitDays} days</strong></td>
                    </tr>
                    <tr>
                        <td>Put Option Expiry</td>
                        <td><strong>${expiryDays} days</strong></td>
                    </tr>
                    <tr style="background: #f0f0f0; font-weight: bold;">
                        <td>Success Rate</td>
                        <td class="${colorClass}">${rate.toFixed(1)}%</td>
                    </tr>
                    <tr>
                        <td>Historical Samples</td>
                        <td><strong>${count.toLocaleString()}</strong> test cases</td>
                    </tr>
                </table>
            `;

            matrixTable.innerHTML = html;
        }
    </script>
</body>
</html>'''

# Write HTML file
output_file = 'multi_period_dashboard.html'
with open(output_file, 'w') as f:
    f.write(html_start)

print(f"\n✓ Dashboard built successfully!")
print(f"✓ Saved to: {output_file}")
print(f"\nFeatures:")
print(f"  - Period selector (1/3/6/9/12 months)")
print(f"  - Wait time filter (constrained by period)")
print(f"  - Expiry period filter (7/14/21/30/45 days)")
print(f"  - Dynamic constraint info")
print(f"  - Real-time result display")
