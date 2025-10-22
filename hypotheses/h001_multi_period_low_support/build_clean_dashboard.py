#!/usr/bin/env python3
"""
Build a clean multi-period dashboard using the EXACT structure from backup dashboard.
"""

import json

# Load the multi-period data
with open('multi_period_dashboard_data.json', 'r') as f:
    dashboard_data = json.load(f)

print("Building clean multi-period dashboard...")
print(f"Data loaded: {len(dashboard_data)} keys")

# Create the HTML - copying exact structure from backup dashboard
html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>H001 Multi-Period Analysis: 1-Month vs 3-Month vs 6-Month vs 9-Month vs 1-Year Lows</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
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
        .insight-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 1.1em;
            line-height: 1.6;
        }
        .insight-box strong { font-size: 1.3em; display: block; margin-bottom: 10px; }
        .success-box {
            background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 1.1em;
            line-height: 1.6;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 4px solid #667eea;
        }
        .stat-card.highlight { border-top-color: #27ae60; }
        .stat-value { font-size: 2.5em; font-weight: bold; color: #667eea; }
        .stat-card.highlight .stat-value { color: #27ae60; }
        .stat-label { color: #7f8c8d; margin-top: 10px; font-size: 0.9em; }
        .chart-container {
            position: relative;
            height: 400px;
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 8px;
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
        .controls {
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .control-group {
            flex: 1;
            min-width: 200px;
        }
        .control-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        .control-group select {
            width: 100%;
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
        .methodology {
            background: #e8f5e9;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #27ae60;
        }
        .methodology h3 {
            color: #27ae60;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Multi-Period Low Analysis Dashboard</h1>
            <p>Interactive Comparison: 1-Month vs 3-Month vs 6-Month vs 9-Month vs 1-Year Lows</p>
            <p style="font-size: 0.9em; opacity: 0.8; margin-top: 10px;">H001: Support Level Reliability Study</p>
        </div>

        <div class="content">
            <!-- What This Analysis Means -->
            <div class="section">
                <h2>📖 What This Analysis Means (Read This First!)</h2>

                <div class="methodology">
                    <h3>🎲 What Is a "Low Period"?</h3>
                    <p><strong>1-Month Low:</strong> The lowest price a stock reaches over any rolling 1-month (21 trading days) window.</p>
                    <p><strong>3-Month Low:</strong> The lowest price a stock reaches over any rolling 3-month (63 trading days) window.</p>
                    <p><strong>6-Month Low:</strong> The lowest price a stock reaches over any rolling 6-month (126 trading days) window.</p>
                    <p><strong>9-Month Low:</strong> The lowest price a stock reaches over any rolling 9-month (189 trading days) window.</p>
                    <p><strong>1-Year Low:</strong> The lowest price a stock reaches over any rolling 1-year (252 trading days) window.</p>
                    <p style="margin-top: 15px; padding: 15px; background: white; border-radius: 6px;">
                        <strong>Example:</strong> If a stock trades at 150 kr on March 1st, and that's the lowest price in the past 21 trading days,
                        then 150 kr is a <strong>1-Month Low</strong> set on March 1st. If it's also the lowest price in the past 63 days,
                        it's also a <strong>3-Month Low</strong>, and so on.
                    </p>
                </div>

                <div class="methodology">
                    <h3>✅ What Is a "Proven Support"?</h3>
                    <p>A low becomes a <strong>"proven support"</strong> when the price stays above it for at least <strong>30 consecutive days</strong>
                    after the low was set. This "proving period" filters out lows that break immediately.</p>
                    <p style="margin-top: 10px; padding: 15px; background: white; border-radius: 6px;">
                        <strong>Example:</strong> If a stock sets a 1-month low at 150 kr on March 1st, and the price stays above 150 kr
                        for the next 30 days (until March 31st), then 150 kr is a <strong>proven support level</strong>.
                    </p>
                </div>

                <div class="methodology">
                    <h3>📅 What Is "Support Age"?</h3>
                    <p><strong>Support age</strong> is the number of days since the low was originally set. We test supports at different ages:</p>
                    <ul style="margin-left: 25px; margin-top: 10px;">
                        <li><strong>30 days:</strong> The low was set 30 days ago</li>
                        <li><strong>60 days:</strong> The low was set 60 days ago</li>
                        <li><strong>90 days:</strong> The low was set 90 days ago (our key checkpoint!)</li>
                        <li><strong>120 days:</strong> The low was set 120 days ago</li>
                        <li><strong>180 days:</strong> The low was set 180 days ago</li>
                    </ul>
                    <p style="margin-top: 10px; padding: 15px; background: white; border-radius: 6px;">
                        <strong>Example:</strong> If a low was set on March 1st and today is June 1st (92 days later),
                        we'd test this at the <strong>90-day age checkpoint</strong>.
                    </p>
                </div>

                <div class="methodology">
                    <h3>🎯 What Does "Success" Mean?</h3>
                    <p>A support is considered <strong>successful</strong> if the stock price doesn't close below the support level
                    during the testing period (next 7, 14, 21, 30, or 45 days).</p>
                    <p style="margin-top: 10px; padding: 15px; background: white; border-radius: 6px;">
                        <strong>Example:</strong> A stock has a proven support at 150 kr set 90 days ago. We test "next 30 days"
                        (days 91-120 after the low was set). If the price never closes below 150 kr during those 30 days,
                        it's a <strong>SUCCESS</strong>. If it closes at 149.99 kr or lower even once, it's a <strong>FAILURE</strong>.
                    </p>
                </div>

                <div class="insight-box" style="margin-top: 20px;">
                    <strong>🔬 The Complete Testing Process:</strong>
                    <ol style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li>Stock sets a low (e.g., 1-month low at 150 kr on March 1st)</li>
                        <li>Wait 30 days to see if it holds → If yes, it's a "proven support"</li>
                        <li>At various ages (30d, 60d, 90d, 120d, 180d), test if the support still holds</li>
                        <li>For each age, test multiple forward periods (next 7d, 14d, 21d, 30d, 45d)</li>
                        <li>Calculate success rate: What % of the time does the support hold?</li>
                    </ol>
                </div>

                <div class="success-box" style="margin-top: 20px;">
                    <strong>💡 Why This Matters for Put Option Writing:</strong>
                    <p style="margin-top: 10px;">When you write (sell) a put option, you're betting the stock won't fall below the strike price.
                    If you write puts at proven support levels that have an 89-90% success rate, you're collecting premium
                    on a high-probability trade. The key insight here is that you don't need to wait for rare 1-year lows -
                    <strong>1-month and 3-month lows work just as well!</strong></p>
                </div>
            </div>

            <!-- Executive Summary -->
            <div class="section">
                <h2>🎯 Key Finding</h2>

                <div class="success-box">
                    <strong>Game-Changer: You Don't Need 1-Year Lows!</strong>
                    1-Month and 3-Month lows aged 90+ days work just as well (or BETTER) than 1-year lows,
                    with <strong>6-7x more trading opportunities!</strong>
                </div>

                <div class="stats-grid">
                    <div class="stat-card highlight">
                        <div class="stat-value">89.7%</div>
                        <div class="stat-label">1-Month Low Success<br>(90d age, next 30d)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">87.8%</div>
                        <div class="stat-label">1-Year Low Success<br>(90d age, next 30d)</div>
                    </div>
                    <div class="stat-card highlight">
                        <div class="stat-value">6.7x</div>
                        <div class="stat-label">More Opportunities<br>(1-Month vs 1-Year)</div>
                    </div>
                    <div class="stat-card highlight">
                        <div class="stat-value">2,488</div>
                        <div class="stat-label">1-Month Proven Supports<br>(vs 372 for 1-Year)</div>
                    </div>
                </div>
            </div>

            <!-- Period Comparison -->
            <div class="section">
                <h2>📊 Period Comparison Summary</h2>
                <p style="margin-bottom: 20px;">
                    Quick comparison of all low periods at key checkpoints.
                    <strong>Notice:</strong> Success rates are very similar across all periods when properly aged!
                </p>
                <div id="periodComparisonTable"></div>
            </div>

            <!-- Success Rate Comparison Chart -->
            <div class="section">
                <h2>📈 Success Rate Comparison: All Periods</h2>
                <p style="margin-bottom: 20px;">
                    This chart compares success rates across all low periods for 90-day aged supports.
                    <strong>The lines are very close together</strong>, showing that all periods perform similarly!
                </p>
                <div class="chart-container">
                    <canvas id="periodComparisonChart"></canvas>
                </div>
            </div>

            <!-- Detailed Matrix -->
            <div class="section">
                <h2>🔍 Detailed Success Rate Matrix</h2>
                <p style="margin-bottom: 20px;">
                    <strong>How to use:</strong> Find your desired low period, support age, and option duration
                    to get the historical success rate and sample size.
                </p>
                <div id="detailedMatrixTable"></div>
            </div>

            <!-- Stock-by-Stock Analysis -->
            <div class="section">
                <h2>🏢 Stock-by-Stock Analysis</h2>

                <div class="controls">
                    <div class="control-group">
                        <label for="periodSelect">Select Low Period:</label>
                        <select id="periodSelect">
                            <option value="1-Month Low">1-Month Low (Recommended - Most Opportunities)</option>
                            <option value="3-Month Low">3-Month Low (Balanced Approach)</option>
                            <option value="6-Month Low">6-Month Low</option>
                            <option value="9-Month Low">9-Month Low</option>
                            <option value="1-Year Low">1-Year Low (Original Study)</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="stockSelect">Select Stock:</label>
                        <select id="stockSelect">
                            <option value="">-- Choose a stock --</option>
                        </select>
                    </div>
                </div>

                <div id="stockAnalysis" style="display: none;">
                    <h3 id="stockTitle" style="margin: 20px 0; color: #2c3e50;"></h3>
                    <div id="stockStats" class="stats-grid"></div>
                    <div id="stockMatrixTable"></div>
                </div>
            </div>

            <!-- Price Chart -->
            <div class="section">
                <h2>📉 Stock Price Chart with Support Levels</h2>
                <p style="margin-bottom: 20px;">
                    View price history and support events. Use the filters to select a low period and stock.
                    <strong>Blue circles</strong> = Low set, <strong>Green markers</strong> = 30d Success, <strong>Red X</strong> = 30d Failure
                </p>

                <div class="controls">
                    <div class="control-group">
                        <label for="chartPeriodSelect">Low Period:</label>
                        <select id="chartPeriodSelect">
                            <option value="1-Month Low">1-Month Low</option>
                            <option value="3-Month Low">3-Month Low</option>
                            <option value="6-Month Low">6-Month Low</option>
                            <option value="9-Month Low">9-Month Low</option>
                            <option value="1-Year Low">1-Year Low</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="chartStockSelect">Stock:</label>
                        <select id="chartStockSelect">
                            <option value="">-- Choose a stock --</option>
                        </select>
                    </div>
                </div>

                <div style="display: flex; gap: 15px; margin: 20px 0; align-items: center; flex-wrap: wrap;">
                    <div>
                        <label style="font-weight: 600; margin-right: 8px;">From:</label>
                        <input type="date" id="chartDateFrom" style="padding: 8px; border: 2px solid #667eea; border-radius: 6px;">
                    </div>
                    <div>
                        <label style="font-weight: 600; margin-right: 8px;">To:</label>
                        <input type="date" id="chartDateTo" style="padding: 8px; border: 2px solid #667eea; border-radius: 6px;">
                    </div>
                    <button id="resetChartDates" style="padding: 10px 20px; background: #95a5a6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Reset Dates</button>
                </div>

                <div style="margin: 20px 0;">
                    <label style="font-weight: 600; display: block; margin-bottom: 10px;">📅 Date Range Slider:</label>
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <input type="range" id="dateRangeStart" min="0" max="100" value="0" style="flex: 1; height: 8px; cursor: pointer;">
                        <input type="range" id="dateRangeEnd" min="0" max="100" value="100" style="flex: 1; height: 8px; cursor: pointer;">
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 0.9em; color: #7f8c8d;">
                        <span id="sliderStartLabel">Start</span>
                        <span id="sliderEndLabel">End</span>
                    </div>
                </div>

                <div id="priceChartContainer" style="display: none;">
                    <div class="chart-container" style="height: 500px;">
                        <canvas id="priceChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Methodology -->
            <div class="section">
                <h2>📖 How to Use This Dashboard</h2>

                <div class="insight-box" style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);">
                    <strong>⚠️ IMPORTANT: Read "What This Analysis Means" Section First!</strong>
                    <p style="margin-top: 10px;">Before exploring the data, scroll back to the top and read the
                    <strong>"What This Analysis Means (Read This First!)"</strong> section. It explains all key concepts:
                    what a "low period" is, what "proven support" means, what "support age" means, and what "success" means.
                    Understanding these definitions is essential for interpreting the results correctly!</p>
                </div>

                <div class="methodology">
                    <h3>Step 1: Understand the Key Finding</h3>
                    <p>The executive summary shows that 1-month and 3-month lows work just as well as 1-year lows, with many more opportunities.
                    This is the main takeaway: <strong>you don't need to wait for rare 1-year lows!</strong></p>
                </div>

                <div class="methodology">
                    <h3>Step 2: Compare All Low Periods</h3>
                    <p>Use the Period Comparison table and chart to see how different low periods (1-month, 3-month, 6-month, 9-month, 1-year)
                    perform at key age checkpoints. Notice the success rates are very similar across all periods!</p>
                    <p style="margin-top: 8px;"><strong>What to look for:</strong> The "90d Age → Next 30d" column shows the most practical scenario
                    for put option writing (supports that have aged 90 days, tested over the next 30 days).</p>
                </div>

                <div class="methodology">
                    <h3>Step 3: Review the Detailed Matrix</h3>
                    <p>The Detailed Success Rate Matrix shows success rates for every combination of:
                    Low Period × Support Age × Testing Duration. This lets you look up the exact historical success rate
                    for your specific trading scenario.</p>
                    <p style="margin-top: 8px;"><strong>Example:</strong> "If I want to write a 30-day put on a 1-month low
                    that was set 90 days ago, what's the success rate?" → Look for "1-Month Low, 90d Age, Next 30d" in the matrix.</p>
                </div>

                <div class="methodology">
                    <h3>Step 4: Explore Individual Stocks</h3>
                    <p>Select a low period (recommend starting with <strong>1-Month Low</strong> for most opportunities),
                    then choose a stock to see its detailed performance history. This shows you how many support events
                    that specific stock has had and their success rates.</p>
                    <p style="margin-top: 8px;"><strong>Why this matters:</strong> Some stocks may have more reliable supports than others.
                    The stock-level data helps you identify the best candidates for your watchlist.</p>
                </div>

                <div class="methodology">
                    <h3>Step 5: Visualize with Price Charts</h3>
                    <p>Use the price chart section to visually see support events plotted on the actual stock price history.
                    <strong>Blue circles</strong> show when lows were set, <strong>green diamond markers</strong> show 30-day successes,
                    and <strong>red X markers</strong> show 30-day failures.</p>
                    <p style="margin-top: 8px;"><strong>Interactive features:</strong> Filter by low period and stock, zoom into date ranges,
                    and hover over markers to see event details.</p>
                </div>

                <div class="success-box" style="margin-top: 20px;">
                    <strong>💼 Practical Trading Application:</strong>
                    <ol style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li><strong>Identify a stock at a 1-month or 3-month low</strong> (check your trading platform or screener)</li>
                        <li><strong>Verify it's a proven support</strong> (has held for at least 30 days without breaking)</li>
                        <li><strong>Calculate the support age</strong> (how many days since the low was set)</li>
                        <li><strong>Look up the success rate</strong> in this dashboard for your desired option duration</li>
                        <li><strong>If age ≥ 90 days and success rate ≥ 89%</strong>, this is a high-probability put writing opportunity!</li>
                        <li><strong>Write put options</strong> at or near the support level, collect premium, and let probability work in your favor</li>
                    </ol>
                    <p style="margin-top: 15px; padding-top: 15px; border-top: 2px solid rgba(255,255,255,0.3);">
                        <strong>Risk Management:</strong> No strategy is 100% successful. The ~10% failure rate means supports CAN break.
                        Always size positions appropriately, use stop losses, and never risk more than you can afford to lose.
                        This analysis shows historical probabilities, not guarantees.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Price chart variable
        let priceChartInstance = null;

        // Data embedded directly
        const dashboardData = ''' + json.dumps(dashboard_data) + ''';

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Dashboard loaded, initializing...');
            initializeDashboard();
        });

        function initializeDashboard() {
            renderPeriodComparisonTable();
            renderPeriodComparisonChart();
            renderDetailedMatrix();
            setupStockControls();
            setupPriceChartControls();
        }

        function renderPeriodComparisonTable() {
            const stats = dashboardData.period_stats;

            let html = '<table><thead><tr>';
            html += '<th>Low Period</th>';
            html += '<th>Proven Supports</th>';
            html += '<th>90d Age → Next 30d<br>Success / Samples</th>';
            html += '<th>90d Age → Next 45d<br>Success / Samples</th>';
            html += '<th>180d Age → Next 30d<br>Success / Samples</th>';
            html += '<th>180d Age → Next 45d<br>Success / Samples</th>';
            html += '</tr></thead><tbody>';

            stats.forEach(stat => {
                html += '<tr>';
                html += `<td><strong>${stat.period_name}</strong></td>`;
                html += `<td>${stat.total_proven_supports.toLocaleString()}</td>`;
                html += `<td>${formatSuccessRate(stat.age90_next30_success)} <br><small>(n=${stat.age90_next30_samples})</small></td>`;
                html += `<td>${formatSuccessRate(stat.age90_next45_success)} <br><small>(n=${stat.age90_next45_samples})</small></td>`;
                html += `<td>${formatSuccessRate(stat.age180_next30_success)} <br><small>(n=${stat.age180_next30_samples})</small></td>`;
                html += `<td>${formatSuccessRate(stat.age180_next45_success)} <br><small>(n=${stat.age180_next45_samples})</small></td>`;
                html += '</tr>';
            });

            html += '</tbody></table>';
            document.getElementById('periodComparisonTable').innerHTML = html;
        }

        function renderPeriodComparisonChart() {
            const ctx = document.getElementById('periodComparisonChart').getContext('2d');

            const periods = dashboardData.periods;
            const matrix = dashboardData.comparison_matrix;

            // Filter for 90-day aged supports
            const age90Data = matrix.filter(row => row.support_age_days === 90);

            const datasets = periods.map((period, idx) => {
                const periodData = age90Data.find(row => row.low_period === period);

                const colors = [
                    '#27ae60', // 1-Month (green - recommended)
                    '#3498db', // 3-Month (blue)
                    '#9b59b6', // 6-Month (purple)
                    '#e67e22', // 9-Month (orange)
                    '#e74c3c'  // 1-Year (red)
                ];

                return {
                    label: period,
                    data: [
                        periodData.next_7d_success_rate,
                        periodData.next_14d_success_rate,
                        periodData.next_21d_success_rate,
                        periodData.next_30d_success_rate,
                        periodData.next_45d_success_rate
                    ],
                    borderColor: colors[idx],
                    backgroundColor: colors[idx] + '20',
                    borderWidth: 3,
                    tension: 0.1,
                    fill: false
                };
            });

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Next 7d', 'Next 14d', 'Next 21d', 'Next 30d', 'Next 45d'],
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Success Rates by Option Duration (90-Day Aged Supports)',
                            font: { size: 16 }
                        },
                        legend: {
                            display: true,
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 75,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Success Rate (%)'
                            }
                        }
                    }
                }
            });
        }

        function renderDetailedMatrix() {
            const matrix = dashboardData.comparison_matrix;

            let html = '<table><thead><tr>';
            html += '<th>Low Period</th>';
            html += '<th>Support Age</th>';
            html += '<th>Next 7d</th>';
            html += '<th>Next 14d</th>';
            html += '<th>Next 21d</th>';
            html += '<th>Next 30d</th>';
            html += '<th>Next 45d</th>';
            html += '</tr></thead><tbody>';

            matrix.forEach(row => {
                html += '<tr>';
                html += `<td><strong>${row.low_period}</strong></td>`;
                html += `<td>${row.support_age_days}d</td>`;
                html += `<td>${formatSuccessRate(row.next_7d_success_rate)}<br><small>(n=${row.next_7d_sample_size})</small></td>`;
                html += `<td>${formatSuccessRate(row.next_14d_success_rate)}<br><small>(n=${row.next_14d_sample_size})</small></td>`;
                html += `<td>${formatSuccessRate(row.next_21d_success_rate)}<br><small>(n=${row.next_21d_sample_size})</small></td>`;
                html += `<td>${formatSuccessRate(row.next_30d_success_rate)}<br><small>(n=${row.next_30d_sample_size})</small></td>`;
                html += `<td>${formatSuccessRate(row.next_45d_success_rate)}<br><small>(n=${row.next_45d_sample_size})</small></td>`;
                html += '</tr>';
            });

            html += '</tbody></table>';
            document.getElementById('detailedMatrixTable').innerHTML = html;
        }

        function setupStockControls() {
            const periodSelect = document.getElementById('periodSelect');
            const stockSelect = document.getElementById('stockSelect');

            // Populate stock dropdown for initial period
            updateStockDropdown(periodSelect.value);

            // Event listeners
            periodSelect.addEventListener('change', function() {
                updateStockDropdown(this.value);
                document.getElementById('stockAnalysis').style.display = 'none';
                stockSelect.value = '';
            });

            stockSelect.addEventListener('change', function() {
                if (this.value) {
                    renderStockAnalysis(periodSelect.value, this.value);
                } else {
                    document.getElementById('stockAnalysis').style.display = 'none';
                }
            });
        }

        function updateStockDropdown(periodName) {
            const stockSelect = document.getElementById('stockSelect');
            const stocks = dashboardData.stock_summaries[periodName];

            stockSelect.innerHTML = '<option value="">-- Choose a stock --</option>';

            stocks.forEach(stock => {
                const option = document.createElement('option');
                option.value = stock.stock;
                option.textContent = `${stock.stock} (${stock.total_proven_supports} supports)`;
                stockSelect.appendChild(option);
            });
        }

        function renderStockAnalysis(periodName, stockName) {
            const stocks = dashboardData.stock_summaries[periodName];
            const stockData = stocks.find(s => s.stock === stockName);

            if (!stockData) {
                console.error('Stock not found:', stockName);
                return;
            }

            document.getElementById('stockTitle').textContent =
                `${stockName} - ${periodName} Performance`;

            // Summary stats
            let statsHtml = '';
            statsHtml += `<div class="stat-card"><div class="stat-value">${stockData.total_proven_supports}</div><div class="stat-label">Total Proven Supports</div></div>`;

            if (stockData.age90_next30_success_rate !== null) {
                statsHtml += `<div class="stat-card"><div class="stat-value">${stockData.age90_next30_success_rate.toFixed(1)}%</div><div class="stat-label">90d Age → Next 30d<br>(n=${stockData.age90_next30_events})</div></div>`;
            }

            if (stockData.age180_next30_success_rate !== null) {
                statsHtml += `<div class="stat-card"><div class="stat-value">${stockData.age180_next30_success_rate.toFixed(1)}%</div><div class="stat-label">180d Age → Next 30d<br>(n=${stockData.age180_next30_events})</div></div>`;
            }

            document.getElementById('stockStats').innerHTML = statsHtml;

            // Detailed matrix
            let matrixHtml = '<h4 style="margin: 30px 0 15px 0;">Detailed Success Rates</h4>';
            matrixHtml += '<table><thead><tr>';
            matrixHtml += '<th>Age</th>';
            matrixHtml += '<th>Next 7d</th>';
            matrixHtml += '<th>Next 14d</th>';
            matrixHtml += '<th>Next 21d</th>';
            matrixHtml += '<th>Next 30d</th>';
            matrixHtml += '<th>Next 45d</th>';
            matrixHtml += '</tr></thead><tbody>';

            [30, 60, 90, 120, 180].forEach(age => {
                matrixHtml += '<tr>';
                matrixHtml += `<td><strong>${age}d</strong></td>`;

                [7, 14, 21, 30, 45].forEach(next => {
                    const rate = stockData[`age${age}_next${next}_success_rate`];
                    const events = stockData[`age${age}_next${next}_events`];

                    if (rate !== null && events > 0) {
                        matrixHtml += `<td>${formatSuccessRate(rate)}<br><small>(n=${events})</small></td>`;
                    } else {
                        matrixHtml += '<td>-</td>';
                    }
                });

                matrixHtml += '</tr>';
            });

            matrixHtml += '</tbody></table>';
            document.getElementById('stockMatrixTable').innerHTML = matrixHtml;

            document.getElementById('stockAnalysis').style.display = 'block';
        }

        // Global variables for date range
        let globalMinDate = null;
        let globalMaxDate = null;
        let allDates = [];

        function setupPriceChartControls() {
            const periodSelect = document.getElementById('chartPeriodSelect');
            const stockSelect = document.getElementById('chartStockSelect');
            const resetDatesBtn = document.getElementById('resetChartDates');
            const dateRangeStart = document.getElementById('dateRangeStart');
            const dateRangeEnd = document.getElementById('dateRangeEnd');

            // Calculate global min/max dates from all price history
            calculateGlobalDateRange();

            // Populate stock dropdown for initial period
            updateChartStockDropdown(periodSelect.value);

            // Event listeners
            periodSelect.addEventListener('change', function() {
                updateChartStockDropdown(this.value);
                document.getElementById('priceChartContainer').style.display = 'none';
                stockSelect.value = '';
            });

            stockSelect.addEventListener('change', function() {
                if (this.value) {
                    const period = periodSelect.value;
                    createPriceChart(this.value, period);
                } else {
                    document.getElementById('priceChartContainer').style.display = 'none';
                }
            });

            resetDatesBtn.addEventListener('click', function() {
                resetDateFilters();
                const stock = stockSelect.value;
                const period = periodSelect.value;
                if (stock) {
                    createPriceChart(stock, period);
                }
            });

            // Date range change handlers
            document.getElementById('chartDateFrom').addEventListener('change', function() {
                updateSlidersFromDates();
                const stock = stockSelect.value;
                const period = periodSelect.value;
                if (stock) {
                    createPriceChart(stock, period);
                }
            });

            document.getElementById('chartDateTo').addEventListener('change', function() {
                updateSlidersFromDates();
                const stock = stockSelect.value;
                const period = periodSelect.value;
                if (stock) {
                    createPriceChart(stock, period);
                }
            });

            // Slider event handlers
            dateRangeStart.addEventListener('input', function() {
                if (parseInt(this.value) >= parseInt(dateRangeEnd.value)) {
                    this.value = parseInt(dateRangeEnd.value) - 1;
                }
                updateDatesFromSliders();
            });

            dateRangeEnd.addEventListener('input', function() {
                if (parseInt(this.value) <= parseInt(dateRangeStart.value)) {
                    this.value = parseInt(dateRangeStart.value) + 1;
                }
                updateDatesFromSliders();
            });

            dateRangeStart.addEventListener('change', function() {
                const stock = stockSelect.value;
                const period = periodSelect.value;
                if (stock) {
                    createPriceChart(stock, period);
                }
            });

            dateRangeEnd.addEventListener('change', function() {
                const stock = stockSelect.value;
                const period = periodSelect.value;
                if (stock) {
                    createPriceChart(stock, period);
                }
            });
        }

        function calculateGlobalDateRange() {
            // Get all unique dates from all price history
            const allDatesSet = new Set();

            Object.values(dashboardData.price_history).forEach(priceData => {
                priceData.forEach(point => {
                    allDatesSet.add(point.date);
                });
            });

            allDates = Array.from(allDatesSet).sort();

            if (allDates.length > 0) {
                globalMinDate = new Date(allDates[0]);
                globalMaxDate = new Date(allDates[allDates.length - 1]);

                console.log('Global date range:', globalMinDate, 'to', globalMaxDate);

                // Set initial values
                resetDateFilters();
            }
        }

        function resetDateFilters() {
            if (globalMinDate && globalMaxDate) {
                document.getElementById('chartDateFrom').value = formatDateForInput(globalMinDate);
                document.getElementById('chartDateTo').value = formatDateForInput(globalMaxDate);
                document.getElementById('dateRangeStart').value = 0;
                document.getElementById('dateRangeEnd').value = 100;
                updateSliderLabels();
            }
        }

        function formatDateForInput(date) {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }

        function updateDatesFromSliders() {
            const startSlider = document.getElementById('dateRangeStart');
            const endSlider = document.getElementById('dateRangeEnd');

            const startPercent = parseInt(startSlider.value) / 100;
            const endPercent = parseInt(endSlider.value) / 100;

            const startIndex = Math.floor(startPercent * (allDates.length - 1));
            const endIndex = Math.floor(endPercent * (allDates.length - 1));

            const startDate = new Date(allDates[startIndex]);
            const endDate = new Date(allDates[endIndex]);

            document.getElementById('chartDateFrom').value = formatDateForInput(startDate);
            document.getElementById('chartDateTo').value = formatDateForInput(endDate);

            updateSliderLabels();
        }

        function updateSlidersFromDates() {
            const fromDate = document.getElementById('chartDateFrom').value;
            const toDate = document.getElementById('chartDateTo').value;

            if (fromDate && toDate && allDates.length > 0) {
                const fromIndex = allDates.findIndex(d => d >= fromDate);
                const toIndex = allDates.findIndex(d => d >= toDate);

                if (fromIndex !== -1 && toIndex !== -1) {
                    const startPercent = Math.round((fromIndex / (allDates.length - 1)) * 100);
                    const endPercent = Math.round((toIndex / (allDates.length - 1)) * 100);

                    document.getElementById('dateRangeStart').value = startPercent;
                    document.getElementById('dateRangeEnd').value = endPercent;
                }
            }

            updateSliderLabels();
        }

        function updateSliderLabels() {
            const fromDate = document.getElementById('chartDateFrom').value;
            const toDate = document.getElementById('chartDateTo').value;

            document.getElementById('sliderStartLabel').textContent = fromDate || 'Start';
            document.getElementById('sliderEndLabel').textContent = toDate || 'End';
        }

        function updateChartStockDropdown(periodName) {
            const stockSelect = document.getElementById('chartStockSelect');

            // Get stocks that have events for this period
            const periodEvents = dashboardData.events_by_period[periodName] || {};
            const stocks = Object.keys(periodEvents).sort();

            stockSelect.innerHTML = '<option value="">-- Choose a stock --</option>';

            stocks.forEach(stock => {
                const option = document.createElement('option');
                option.value = stock;
                const eventCount = periodEvents[stock].length;
                option.textContent = `${stock} (${eventCount} events)`;
                stockSelect.appendChild(option);
            });
        }

        function createPriceChart(stockName, periodName) {
            console.log('Creating price chart for:', stockName, periodName);

            let priceData = dashboardData.price_history[stockName];
            const events = (dashboardData.events_by_period[periodName] || {})[stockName] || [];

            console.log('Price data points:', priceData ? priceData.length : 0);
            console.log('Events:', events.length);

            if (!priceData || priceData.length === 0) {
                console.error('No price data for', stockName);
                alert('No price data available for ' + stockName);
                return;
            }

            // Apply date range filter
            const dateFromValue = document.getElementById('chartDateFrom').value;
            const dateToValue = document.getElementById('chartDateTo').value;

            if (dateFromValue && dateToValue) {
                const fromDate = new Date(dateFromValue);
                const toDate = new Date(dateToValue);
                toDate.setHours(23, 59, 59, 999);

                priceData = priceData.filter(d => {
                    const date = new Date(d.date);
                    return date >= fromDate && date <= toDate;
                });

                console.log('Filtered price data points:', priceData.length);
            }

            // Prepare chart data
            const chartData = {
                labels: priceData.map(d => d.date),
                datasets: [{
                    label: 'Close Price',
                    data: priceData.map(d => ({x: d.date, y: d.close})),
                    borderColor: '#34495e',
                    backgroundColor: 'rgba(52, 73, 94, 0.05)',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    fill: true,
                    tension: 0.1
                }]
            };

            // Add event markers
            const supportSetPoints = [];
            const supportSuccessPoints = [];
            const supportFailurePoints = [];

            const supportSetMeta = [];
            const supportSuccessMeta = [];
            const supportFailureMeta = [];

            // Get date range for filtering events
            const fromDate = dateFromValue ? new Date(dateFromValue) : null;
            const toDate = dateToValue ? new Date(dateToValue) : null;
            if (toDate) {
                toDate.setHours(23, 59, 59, 999);
            }

            events.forEach(event => {
                // Blue circle: when support was set
                if (event.event_date && event.support_level) {
                    const eventDate = new Date(event.event_date);
                    if (!fromDate || !toDate || (eventDate >= fromDate && eventDate <= toDate)) {
                        supportSetPoints.push({
                            x: event.event_date,
                            y: event.support_level
                        });
                        supportSetMeta.push({
                            date: event.event_date,
                            supportLevel: event.support_level,
                            testEndDate: event.test_end_date
                        });
                    }
                }

                // Check 30-day success/failure
                if (event.test_end_date && event.support_level) {
                    const eventDate = new Date(event.test_end_date);
                    if (!fromDate || !toDate || (eventDate >= fromDate && eventDate <= toDate)) {
                        if (event.success_30d === true) {
                            supportSuccessPoints.push({
                                x: event.test_end_date,
                                y: event.support_level
                            });
                            supportSuccessMeta.push({
                                date: event.test_end_date,
                                supportLevel: event.support_level,
                                setDate: event.event_date
                            });
                        } else if (event.success_30d === false) {
                            supportFailurePoints.push({
                                x: event.test_end_date,
                                y: event.support_level
                            });
                            supportFailureMeta.push({
                                date: event.test_end_date,
                                supportLevel: event.support_level,
                                daysToBreak: event.days_to_break_30d,
                                decline30d: event.decline_30d
                            });
                        }
                    }
                }
            });

            // Add marker datasets
            if (supportSetPoints.length > 0) {
                chartData.datasets.push({
                    label: periodName + ' Set',
                    data: supportSetPoints,
                    backgroundColor: '#3498db',
                    borderColor: '#2980b9',
                    borderWidth: 3,
                    pointRadius: 8,
                    pointHoverRadius: 12,
                    showLine: false,
                    metadata: supportSetMeta
                });
            }

            if (supportFailurePoints.length > 0) {
                chartData.datasets.push({
                    label: '30d Failure',
                    data: supportFailurePoints,
                    backgroundColor: '#e74c3c',
                    borderColor: '#c0392b',
                    borderWidth: 3,
                    pointRadius: 10,
                    pointHoverRadius: 14,
                    pointStyle: 'crossRot',
                    showLine: false,
                    metadata: supportFailureMeta
                });
            }

            if (supportSuccessPoints.length > 0) {
                chartData.datasets.push({
                    label: '30d Success',
                    data: supportSuccessPoints,
                    backgroundColor: '#27ae60',
                    borderColor: '#229954',
                    borderWidth: 3,
                    pointRadius: 10,
                    pointHoverRadius: 14,
                    pointStyle: 'rectRot',
                    showLine: false,
                    metadata: supportSuccessMeta
                });
            }

            console.log('Chart datasets:', chartData.datasets.length);
            console.log('Support set markers:', supportSetPoints.length);
            console.log('Support failure markers:', supportFailurePoints.length);
            console.log('Support success markers:', supportSuccessPoints.length);

            // Destroy existing chart
            if (priceChartInstance) {
                priceChartInstance.destroy();
            }

            // Create chart
            const ctx = document.getElementById('priceChart');
            priceChartInstance = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'point',
                        intersect: true
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    return context[0].label;
                                },
                                label: function(context) {
                                    const datasetLabel = context.dataset.label;
                                    const dataIndex = context.dataIndex;
                                    const metadata = context.dataset.metadata;

                                    let lines = [];

                                    if (datasetLabel.endsWith(' Set') && metadata && metadata[dataIndex]) {
                                        const meta = metadata[dataIndex];
                                        lines.push('🔵 Low Set');
                                        lines.push('Support Level: ' + meta.supportLevel.toFixed(2));
                                        lines.push('30-day test ends: ' + meta.testEndDate);
                                    }
                                    else if (datasetLabel === '30d Failure' && metadata && metadata[dataIndex]) {
                                        const meta = metadata[dataIndex];
                                        lines.push('❌ Support Broke (30d test)');
                                        lines.push('Support Level: ' + meta.supportLevel.toFixed(2));
                                        if (meta.daysToBreak) {
                                            lines.push('Days to break: ' + meta.daysToBreak);
                                        }
                                        if (meta.decline30d) {
                                            lines.push('Decline: ' + meta.decline30d.toFixed(2) + '%');
                                        }
                                    }
                                    else if (datasetLabel === '30d Success' && metadata && metadata[dataIndex]) {
                                        const meta = metadata[dataIndex];
                                        lines.push('✅ Support Held (30d test)');
                                        lines.push('Support Level: ' + meta.supportLevel.toFixed(2));
                                        lines.push('Low set on: ' + meta.setDate);
                                    }
                                    else if (datasetLabel === 'Close Price') {
                                        lines.push('Price: ' + context.parsed.y.toFixed(2));
                                    }

                                    return lines;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'month'
                            },
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Price'
                            }
                        }
                    }
                }
            });

            // Show the chart container
            document.getElementById('priceChartContainer').style.display = 'block';
        }

        function formatSuccessRate(rate) {
            if (rate === null || rate === undefined) return '-';

            const rateNum = parseFloat(rate);
            let className = '';

            if (rateNum >= 90) {
                className = 'success-high';
            } else if (rateNum >= 80) {
                className = 'success-medium';
            } else {
                className = 'success-low';
            }

            return `<span class="${className}">${rateNum.toFixed(1)}%</span>`;
        }
    </script>
</body>
</html>
'''

# Write the HTML file
with open('multi_period_dashboard.html', 'w') as f:
    f.write(html)

import os
file_size_mb = os.path.getsize('multi_period_dashboard.html') / (1024 * 1024)

print(f"\n✓ Clean dashboard created successfully!")
print(f"  File size: {file_size_mb:.2f} MB")
print(f"  Open multi_period_dashboard.html in your browser!")
