"""
Generate a standalone HTML dashboard with embedded data for support level analysis.
This creates a single HTML file that can be opened in any browser without needing a server.
"""

import pandas as pd
import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'
OUTPUT_FILE = SCRIPT_DIR / 'support_analysis_dashboard.html'

print("Loading data...")
df = pd.read_parquet(DATA_FILE)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['name', 'date']).reset_index(drop=True)

# Convert to JSON format for embedding
print("Converting data to JSON...")
data_dict = {}
for stock in df['name'].unique():
    stock_data = df[df['name'] == stock].copy()
    data_dict[stock] = {
        'dates': stock_data['date'].dt.strftime('%Y-%m-%d').tolist(),
        'open': stock_data['open'].tolist(),
        'high': stock_data['high'].tolist(),
        'low': stock_data['low'].tolist(),
        'close': stock_data['close'].tolist()
    }

# Get stock list
stocks = sorted(df['name'].unique())

# Get date range
min_date = df['date'].min().strftime('%Y-%m-%d')
max_date = df['date'].max().strftime('%Y-%m-%d')
default_start = max(df['date'].min(), pd.Timestamp('2024-01-01')).strftime('%Y-%m-%d')

print(f"Data loaded: {len(stocks)} stocks, {len(df)} records")
print(f"Date range: {min_date} to {max_date}")

# Create HTML with embedded data
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Support Level Analysis Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}

        h1 {{
            color: #1f1f1f;
            margin-bottom: 10px;
            font-size: 2em;
        }}

        h2 {{
            color: #333;
            margin: 30px 0 15px 0;
            font-size: 1.5em;
        }}

        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .controls {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 6px;
        }}

        .control-group {{
            display: flex;
            flex-direction: column;
        }}

        label {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            font-size: 0.9em;
        }}

        select, input[type="date"] {{
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            background: white;
        }}

        select:focus, input:focus {{
            outline: none;
            border-color: #4CAF50;
        }}

        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #4CAF50;
        }}

        .metric-label {{
            color: #666;
            font-size: 0.85em;
            margin-bottom: 5px;
        }}

        .metric-value {{
            font-size: 1.8em;
            font-weight: 600;
            color: #1f1f1f;
        }}

        #chart {{
            width: 100%;
            height: 600px;
            margin-bottom: 30px;
        }}

        .info-box {{
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}

        .stats-section {{
            margin-top: 30px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .stat-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
        }}

        .stat-card h4 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}

        .stat-card .value {{
            font-size: 1.5em;
            font-weight: 600;
            color: #1f1f1f;
        }}

        button {{
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            margin: 5px;
        }}

        button:hover {{
            background: #45a049;
        }}

        .loading {{
            text-align: center;
            padding: 50px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Support Level Analysis Dashboard</h1>
        <p class="subtitle">Analyze rolling low support levels and break patterns - Standalone HTML Version</p>

        <div class="controls">
            <div class="control-group">
                <label for="stockSelect">Select Stock:</label>
                <select id="stockSelect">
                    {' '.join([f'<option value="{stock}">{stock}</option>' for stock in stocks])}
                </select>
            </div>

            <div class="control-group">
                <label for="periodSelect">Rolling Low Period:</label>
                <select id="periodSelect">
                    <option value="30">1-Month (30 days)</option>
                    <option value="90" selected>3-Month (90 days)</option>
                    <option value="180">6-Month (180 days)</option>
                    <option value="270">9-Month (270 days)</option>
                    <option value="365">1-Year (365 days)</option>
                </select>
            </div>

            <div class="control-group">
                <label for="startDate">Start Date:</label>
                <input type="date" id="startDate" value="{default_start}" min="{min_date}" max="{max_date}">
            </div>

            <div class="control-group">
                <label for="endDate">End Date:</label>
                <input type="date" id="endDate" value="{max_date}" min="{min_date}" max="{max_date}">
            </div>
        </div>

        <div class="info-box">
            💡 <strong>Tip:</strong> Click and drag on the chart to zoom. The y-axis automatically rescales to fit visible data. Double-click to reset zoom.
        </div>

        <div class="metrics" id="metricsContainer"></div>

        <div id="chart"></div>

        <div class="stats-section">
            <h2>Support Break Statistics</h2>
            <div class="stats-grid" id="statsGrid"></div>
        </div>
    </div>

    <script>
        // Embedded data
        const STOCK_DATA = {json.dumps(data_dict)};

        let currentStock = '{stocks[0]}';
        let currentPeriod = 90;
        let currentData = null;

        // Calculate rolling low
        function calculateRollingLow(data, periodDays) {{
            const result = [];

            for (let i = 0; i < data.dates.length; i++) {{
                const currentDate = new Date(data.dates[i]);
                const lookbackDate = new Date(currentDate);
                lookbackDate.setDate(lookbackDate.getDate() - periodDays);

                let minLow = Infinity;
                for (let j = 0; j <= i; j++) {{
                    const checkDate = new Date(data.dates[j]);
                    if (checkDate >= lookbackDate && checkDate <= currentDate) {{
                        minLow = Math.min(minLow, data.low[j]);
                    }}
                }}

                result.push({{
                    date: data.dates[i],
                    open: data.open[i],
                    high: data.high[i],
                    low: data.low[i],
                    close: data.close[i],
                    rolling_low: minLow === Infinity ? null : minLow
                }});
            }}

            return result;
        }}

        // Filter data by date range
        function filterByDateRange(data, startDate, endDate) {{
            const start = new Date(startDate);
            const end = new Date(endDate);

            return data.filter(d => {{
                const date = new Date(d.date);
                return date >= start && date <= end;
            }});
        }}

        // Analyze support breaks
        function analyzeSupportBreaks(data) {{
            const breaks = [];

            for (let i = 1; i < data.length; i++) {{
                if (data[i].rolling_low && data[i-1].rolling_low) {{
                    if (data[i].rolling_low < data[i-1].rolling_low) {{
                        const daysSince = i > 1 && breaks.length > 0
                            ? Math.floor((new Date(data[i].date) - new Date(breaks[breaks.length-1].date)) / (1000 * 60 * 60 * 24))
                            : null;

                        breaks.push({{
                            date: data[i].date,
                            prev_support: data[i-1].rolling_low,
                            new_support: data[i].rolling_low,
                            drop_pct: ((data[i].rolling_low - data[i-1].rolling_low) / data[i-1].rolling_low * 100),
                            days_since: daysSince
                        }});
                    }}
                }}
            }}

            return breaks;
        }}

        // Calculate statistics
        function calculateStats(data, breaks) {{
            if (breaks.length === 0) return null;

            const totalDays = data.length;
            const stability = ((totalDays - breaks.length) / totalDays * 100);

            const dropPcts = breaks.map(b => b.drop_pct);
            const avgDrop = dropPcts.reduce((a, b) => a + b, 0) / dropPcts.length;
            const maxDrop = Math.min(...dropPcts);

            const daysBetween = breaks.filter(b => b.days_since !== null).map(b => b.days_since);
            const avgDaysBetween = daysBetween.length > 0
                ? daysBetween.reduce((a, b) => a + b, 0) / daysBetween.length
                : null;

            const lastBreak = new Date(breaks[breaks.length - 1].date);
            const lastDate = new Date(data[data.length - 1].date);
            const daysSinceLastBreak = Math.floor((lastDate - lastBreak) / (1000 * 60 * 60 * 24));

            return {{
                totalBreaks: breaks.length,
                stability: stability,
                avgDrop: avgDrop,
                maxDrop: maxDrop,
                avgDaysBetween: avgDaysBetween,
                daysSinceLastBreak: daysSinceLastBreak,
                tradingDaysPerBreak: totalDays / breaks.length
            }};
        }}

        // Update metrics display
        function updateMetrics(data, breaks) {{
            const stats = calculateStats(data, breaks);

            const html = `
                <div class="metric-card">
                    <div class="metric-label">Data Points</div>
                    <div class="metric-value">${{data.length}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Latest Price</div>
                    <div class="metric-value">${{data[data.length-1].close.toFixed(2)}} kr</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Period Low</div>
                    <div class="metric-value">${{Math.min(...data.map(d => d.low)).toFixed(2)}} kr</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Support Breaks</div>
                    <div class="metric-value">${{breaks.length}}</div>
                </div>
            `;

            document.getElementById('metricsContainer').innerHTML = html;

            // Update stats grid
            if (stats) {{
                const statsHtml = `
                    <div class="stat-card">
                        <h4>Stability</h4>
                        <div class="value">${{stats.stability.toFixed(1)}}%</div>
                    </div>
                    <div class="stat-card">
                        <h4>Days Since Last Break</h4>
                        <div class="value">${{stats.daysSinceLastBreak}}d</div>
                    </div>
                    <div class="stat-card">
                        <h4>Avg Days Between Breaks</h4>
                        <div class="value">${{stats.avgDaysBetween ? stats.avgDaysBetween.toFixed(0) + 'd' : 'N/A'}}</div>
                    </div>
                    <div class="stat-card">
                        <h4>Avg Break Magnitude</h4>
                        <div class="value">${{stats.avgDrop.toFixed(2)}}%</div>
                    </div>
                    <div class="stat-card">
                        <h4>Biggest Break</h4>
                        <div class="value">${{stats.maxDrop.toFixed(2)}}%</div>
                    </div>
                    <div class="stat-card">
                        <h4>Trading Days per Break</h4>
                        <div class="value">${{stats.tradingDaysPerBreak.toFixed(0)}}</div>
                    </div>
                `;
                document.getElementById('statsGrid').innerHTML = statsHtml;
            }}
        }}

        // Create chart with dynamic y-axis
        function createChart(data, breaks, periodName) {{
            const trace1 = {{
                type: 'candlestick',
                x: data.map(d => d.date),
                open: data.map(d => d.open),
                high: data.map(d => d.high),
                low: data.map(d => d.low),
                close: data.map(d => d.close),
                name: 'Price',
                increasing: {{ line: {{ color: '#26a69a' }} }},
                decreasing: {{ line: {{ color: '#ef5350' }} }}
            }};

            const trace2 = {{
                type: 'scatter',
                mode: 'lines',
                x: data.map(d => d.date),
                y: data.map(d => d.rolling_low),
                name: `${{periodName}} Rolling Low`,
                line: {{ color: 'blue', width: 2, dash: 'dash' }}
            }};

            const trace3 = {{
                type: 'scatter',
                mode: 'markers',
                x: breaks.map(b => b.date),
                y: breaks.map(b => b.new_support),
                name: 'Support Broken',
                marker: {{ color: 'red', size: 10, symbol: 'circle' }},
                text: breaks.map(b => `Drop: ${{b.drop_pct.toFixed(2)}}%`),
                hovertemplate: '<b>%{{x}}</b><br>Support: %{{y:.2f}} kr<br>%{{text}}<extra></extra>'
            }};

            const layout = {{
                title: `${{currentStock}} - ${{periodName}} Rolling Low Support Levels`,
                yaxis: {{
                    title: 'Price (kr)',
                    autorange: true
                }},
                xaxis: {{
                    title: 'Date',
                    rangeslider: {{ visible: false }},
                    rangeselector: {{
                        buttons: [
                            {{ count: 1, label: '1m', step: 'month', stepmode: 'backward' }},
                            {{ count: 3, label: '3m', step: 'month', stepmode: 'backward' }},
                            {{ count: 6, label: '6m', step: 'month', stepmode: 'backward' }},
                            {{ count: 1, label: '1y', step: 'year', stepmode: 'backward' }},
                            {{ step: 'all', label: 'All' }}
                        ],
                        x: 1.0,
                        y: 1.0,
                        xanchor: 'right',
                        yanchor: 'bottom'
                    }}
                }},
                hovermode: 'x unified',
                height: 600,
                margin: {{ l: 50, r: 50, t: 80, b: 50 }}
            }};

            const config = {{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d']
            }};

            Plotly.newPlot('chart', [trace1, trace2, trace3], layout, config);

            // Add dynamic y-axis rescaling on zoom
            const chartDiv = document.getElementById('chart');
            chartDiv.on('plotly_relayout', function(eventdata) {{
                if (eventdata['xaxis.range[0]'] && eventdata['xaxis.range[1]']) {{
                    const xMin = new Date(eventdata['xaxis.range[0]']);
                    const xMax = new Date(eventdata['xaxis.range[1]']);

                    let yMin = Infinity;
                    let yMax = -Infinity;

                    // Find min/max in visible range
                    for (let i = 0; i < data.length; i++) {{
                        const date = new Date(data[i].date);
                        if (date >= xMin && date <= xMax) {{
                            yMin = Math.min(yMin, data[i].low);
                            yMax = Math.max(yMax, data[i].high);
                            if (data[i].rolling_low) {{
                                yMin = Math.min(yMin, data[i].rolling_low);
                            }}
                        }}
                    }}

                    // Add 5% padding
                    if (yMin !== Infinity && yMax !== -Infinity) {{
                        const padding = (yMax - yMin) * 0.05;
                        yMin -= padding;
                        yMax += padding;

                        Plotly.relayout('chart', {{
                            'yaxis.range': [yMin, yMax],
                            'yaxis.autorange': false
                        }});
                    }}
                }} else if (eventdata['xaxis.autorange']) {{
                    // Reset y-axis when x-axis is reset
                    Plotly.relayout('chart', {{
                        'yaxis.autorange': true
                    }});
                }}
            }});
        }}

        // Update display
        function updateDisplay() {{
            const stockData = STOCK_DATA[currentStock];
            if (!stockData) return;

            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;

            // Calculate rolling low on full dataset
            const fullData = calculateRollingLow(stockData, currentPeriod);

            // Filter by date range for display
            const filteredData = filterByDateRange(fullData, startDate, endDate);

            if (filteredData.length === 0) {{
                alert('No data available for selected date range');
                return;
            }}

            currentData = filteredData;

            // Analyze breaks
            const breaks = analyzeSupportBreaks(filteredData);

            // Get period name
            const periodMap = {{
                30: '1-Month',
                90: '3-Month',
                180: '6-Month',
                270: '9-Month',
                365: '1-Year'
            }};
            const periodName = periodMap[currentPeriod];

            // Update UI
            updateMetrics(filteredData, breaks);
            createChart(filteredData, breaks, periodName);
        }}

        // Event listeners
        document.getElementById('stockSelect').addEventListener('change', function() {{
            currentStock = this.value;
            updateDisplay();
        }});

        document.getElementById('periodSelect').addEventListener('change', function() {{
            currentPeriod = parseInt(this.value);
            updateDisplay();
        }});

        document.getElementById('startDate').addEventListener('change', updateDisplay);
        document.getElementById('endDate').addEventListener('change', updateDisplay);

        // Initialize
        updateDisplay();
    </script>
</body>
</html>
"""

# Write HTML file
print(f"Writing HTML file to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Dashboard created successfully!")
print(f"📄 File: {OUTPUT_FILE}")
print(f"📊 Stocks: {len(stocks)}")
print(f"📅 Date range: {min_date} to {max_date}")
print(f"\n🌐 Open the file in your browser to use the dashboard.")
print(f"   The y-axis will automatically rescale when you zoom on the x-axis!")
