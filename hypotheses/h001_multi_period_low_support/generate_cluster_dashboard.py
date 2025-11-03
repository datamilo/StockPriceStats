"""
Generate a standalone HTML dashboard for Consecutive Break Analysis.
Shows clustering of support breaks when multiple breaks happen within a short period.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'
OUTPUT_FILE = SCRIPT_DIR / 'consecutive_breaks_dashboard.html'

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

# Create HTML with embedded data
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consecutive Break Analysis Dashboard</title>
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

        h3 {{
            color: #555;
            margin: 20px 0 10px 0;
            font-size: 1.2em;
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

        select, input[type="date"], input[type="number"] {{
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            background: white;
        }}

        select:focus, input:focus {{
            outline: none;
            border-color: #ff9800;
        }}

        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: #fff3e0;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #ff9800;
        }}

        .metric-label {{
            color: #666;
            font-size: 0.85em;
            margin-bottom: 5px;
        }}

        .metric-value {{
            font-size: 1.8em;
            font-weight: 600;
            color: #e65100;
        }}

        #chart {{
            width: 100%;
            height: 600px;
            margin-bottom: 30px;
        }}

        #clusterChart {{
            width: 100%;
            height: 400px;
            margin-bottom: 30px;
        }}

        .info-box {{
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}

        .cluster-container {{
            margin-bottom: 30px;
        }}

        .cluster-item {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 20px;
            margin: 15px 0;
            border-radius: 4px;
        }}

        .cluster-header {{
            font-weight: 600;
            color: #e65100;
            font-size: 1.1em;
            margin-bottom: 10px;
        }}

        .cluster-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}

        .cluster-stat {{
            background: white;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ffe0b2;
        }}

        .cluster-stat-label {{
            color: #999;
            font-size: 0.85em;
        }}

        .cluster-stat-value {{
            font-size: 1.3em;
            font-weight: 600;
            color: #ff6f00;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}

        th {{
            background: #fff3e0;
            font-weight: 600;
            color: #e65100;
        }}

        tr:hover {{
            background: #fafafa;
        }}

        .break-count-1 {{ color: #ffc107; }}
        .break-count-2 {{ color: #ff9800; }}
        .break-count-3 {{ color: #ff6f00; }}
        .break-count-multi {{ color: #e65100; font-weight: 600; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .stat-card {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }}

        .stat-card h4 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}

        .stat-card .value {{
            font-size: 1.5em;
            font-weight: 600;
            color: #ff6f00;
        }}

        .empty-state {{
            background: #f9f9f9;
            padding: 40px;
            border-radius: 6px;
            text-align: center;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Consecutive Break Analysis Dashboard</h1>
        <p class="subtitle">Clustering of support breaks - when multiple breaks happen within a short period</p>

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
                <label for="maxGap">Max Days Between Breaks:</label>
                <input type="number" id="maxGap" value="30" min="1" max="90" step="1">
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
            💡 <strong>Tip:</strong> Adjust "Max Days Between Breaks" to identify clusters of consecutive breaks. Breaks within this many days are grouped together.
        </div>

        <div class="metrics" id="metricsContainer"></div>

        <h2>Support Breaks Timeline</h2>
        <div id="chart"></div>

        <h2>Break Cluster Distribution</h2>
        <div id="clusterChart"></div>

        <div class="cluster-container" id="clusterContainer"></div>

        <div class="stats-section">
            <h2>Cluster Statistics</h2>
            <div class="stats-grid" id="statsGrid"></div>
        </div>

        <div class="stats-section">
            <h2>Support Break Statistics</h2>
            <div class="stats-grid" id="breakStatsGrid"></div>
        </div>
    </div>

    <script>
        // Embedded data
        const STOCK_DATA = {json.dumps(data_dict)};

        let currentStock = '{stocks[0]}';
        let currentPeriod = 90;
        let maxGapDays = 30;
        let currentData = null;
        let currentBreaks = null;
        let currentClusters = null;

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
                        const daysSince = breaks.length > 0
                            ? Math.floor((new Date(data[i].date) - new Date(breaks[breaks.length - 1].date)) / (1000 * 60 * 60 * 24))
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

        // Calculate support break statistics
        function calculateBreakStats(data, breaks) {{
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

            const medianDaysBetween = daysBetween.length > 0
                ? daysBetween.sort((a, b) => a - b)[Math.floor(daysBetween.length / 2)]
                : null;

            const minDaysBetween = daysBetween.length > 0 ? Math.min(...daysBetween) : null;
            const maxDaysBetween = daysBetween.length > 0 ? Math.max(...daysBetween) : null;

            const lastBreak = new Date(breaks[breaks.length - 1].date);
            const lastDate = new Date(data[data.length - 1].date);
            const daysSinceLastBreak = Math.floor((lastDate - lastBreak) / (1000 * 60 * 60 * 24));

            const firstBreak = new Date(breaks[0].date);
            const firstDate = new Date(data[0].date);
            const daysBeforeFirstBreak = Math.floor((firstBreak - firstDate) / (1000 * 60 * 60 * 24));

            return {{
                totalBreaks: breaks.length,
                stability: stability,
                avgDrop: avgDrop,
                maxDrop: maxDrop,
                avgDaysBetween: avgDaysBetween,
                medianDaysBetween: medianDaysBetween,
                minDaysBetween: minDaysBetween,
                maxDaysBetween: maxDaysBetween,
                daysSinceLastBreak: daysSinceLastBreak,
                daysBeforeFirstBreak: daysBeforeFirstBreak,
                tradingDaysPerBreak: totalDays / breaks.length,
                firstBreakDate: breaks[0].date,
                lastBreakDate: breaks[breaks.length - 1].date
            }};
        }}

        // Analyze consecutive breaks (clusters)
        function analyzeConsecutiveBreaks(breaks, maxGap) {{
            if (breaks.length === 0) return [];

            const clusters = [];
            let currentCluster = [breaks[0]];
            let clusterId = 0;

            for (let i = 1; i < breaks.length; i++) {{
                const currentDate = new Date(breaks[i].date);
                const prevDate = new Date(breaks[i-1].date);
                const daysDiff = (currentDate - prevDate) / (1000 * 60 * 60 * 24);

                if (daysDiff <= maxGap) {{
                    currentCluster.push(breaks[i]);
                }} else {{
                    // Save current cluster
                    if (currentCluster.length > 0) {{
                        const clusterData = {{
                            id: clusterId,
                            breaks: currentCluster,
                            num_breaks: currentCluster.length,
                            start_date: currentCluster[0].date,
                            end_date: currentCluster[currentCluster.length - 1].date,
                            duration_days: Math.floor((new Date(currentCluster[currentCluster.length - 1].date) - new Date(currentCluster[0].date)) / (1000 * 60 * 60 * 24))
                        }};

                        // Calculate gaps
                        const gaps = [];
                        for (let j = 1; j < currentCluster.length; j++) {{
                            const d = (new Date(currentCluster[j].date) - new Date(currentCluster[j-1].date)) / (1000 * 60 * 60 * 24);
                            gaps.push(d);
                        }}

                        if (gaps.length > 0) {{
                            clusterData.avg_gap = gaps.reduce((a, b) => a + b) / gaps.length;
                            clusterData.min_gap = Math.min(...gaps);
                            clusterData.max_gap = Math.max(...gaps);
                        }}

                        clusterData.total_drop = currentCluster.reduce((sum, b) => sum + b.drop_pct, 0);
                        clusterData.avg_drop = clusterData.total_drop / currentCluster.length;

                        clusters.push(clusterData);
                        clusterId++;
                    }}

                    // Start new cluster
                    currentCluster = [breaks[i]];
                }}
            }}

            // Add last cluster
            if (currentCluster.length > 0) {{
                const clusterData = {{
                    id: clusterId,
                    breaks: currentCluster,
                    num_breaks: currentCluster.length,
                    start_date: currentCluster[0].date,
                    end_date: currentCluster[currentCluster.length - 1].date,
                    duration_days: Math.floor((new Date(currentCluster[currentCluster.length - 1].date) - new Date(currentCluster[0].date)) / (1000 * 60 * 60 * 24))
                }};

                const gaps = [];
                for (let j = 1; j < currentCluster.length; j++) {{
                    const d = (new Date(currentCluster[j].date) - new Date(currentCluster[j-1].date)) / (1000 * 60 * 60 * 24);
                    gaps.push(d);
                }}

                if (gaps.length > 0) {{
                    clusterData.avg_gap = gaps.reduce((a, b) => a + b) / gaps.length;
                    clusterData.min_gap = Math.min(...gaps);
                    clusterData.max_gap = Math.max(...gaps);
                }}

                clusterData.total_drop = currentCluster.reduce((sum, b) => sum + b.drop_pct, 0);
                clusterData.avg_drop = clusterData.total_drop / currentCluster.length;

                clusters.push(clusterData);
            }}

            return clusters;
        }}

        // Update metrics display
        function updateMetrics(breaks, clusters) {{
            const singleBreakClusters = clusters.filter(c => c.num_breaks === 1).length;
            const multiBreakClusters = clusters.filter(c => c.num_breaks > 1).length;
            const maxBreaks = clusters.length > 0 ? Math.max(...clusters.map(c => c.num_breaks)) : 0;

            const html = `
                <div class="metric-card">
                    <div class="metric-label">Total Breaks</div>
                    <div class="metric-value">${{breaks.length}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Clusters</div>
                    <div class="metric-value">${{clusters.length}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Multi-Break Clusters</div>
                    <div class="metric-value">${{multiBreakClusters}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Consecutive Breaks</div>
                    <div class="metric-value">${{maxBreaks}}</div>
                </div>
            `;

            document.getElementById('metricsContainer').innerHTML = html;

            // Update stats
            if (multiBreakClusters > 0) {{
                const multiClusters = clusters.filter(c => c.num_breaks > 1);
                const avgDuration = multiClusters.reduce((sum, c) => sum + c.duration_days, 0) / multiClusters.length;
                const avgGaps = multiClusters.filter(c => c.avg_gap).map(c => c.avg_gap);
                const avgGapValue = avgGaps.length > 0 ? avgGaps.reduce((a, b) => a + b) / avgGaps.length : 0;

                const minGaps = multiClusters.filter(c => c.min_gap).map(c => c.min_gap);
                const minGapValue = minGaps.length > 0 ? Math.min(...minGaps) : 0;

                const statsHtml = `
                    <div class="stat-card">
                        <h4>Avg Multi-Break Duration</h4>
                        <div class="value">${{avgDuration.toFixed(0)}} days</div>
                    </div>
                    <div class="stat-card">
                        <h4>Avg Gap Between Breaks</h4>
                        <div class="value">${{avgGapValue.toFixed(1)}} days</div>
                    </div>
                    <div class="stat-card">
                        <h4>Shortest Gap Ever</h4>
                        <div class="value">${{minGapValue.toFixed(0)}} days</div>
                    </div>
                `;
                document.getElementById('statsGrid').innerHTML = statsHtml;
            }} else {{
                document.getElementById('statsGrid').innerHTML = '<div class="empty-state">No multi-break clusters found</div>';
            }}
        }}

        // Create timeline chart
        function createTimelineChart(data, breaks) {{
            const trace1 = {{
                type: 'candlestick',
                x: data.map(d => d.date),
                open: data.map(d => d.open),
                high: data.map(d => d.high),
                low: data.map(d => d.low),
                close: data.map(d => d.close),
                name: 'Price'
            }};

            const trace2 = {{
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
                title: `Support Breaks Timeline - ${{currentStock}}`,
                yaxis: {{
                    title: 'Price (kr)',
                    autorange: true
                }},
                xaxis: {{
                    title: 'Date',
                    rangeslider: {{ visible: false }}
                }},
                hovermode: 'x unified',
                height: 600,
                margin: {{ l: 50, r: 50, t: 60, b: 50 }}
            }};

            Plotly.newPlot('chart', [trace1, trace2], layout, {{
                responsive: true,
                displayModeBar: true,
                displaylogo: false
            }});

            // Dynamic y-axis on zoom
            const chartDiv = document.getElementById('chart');
            chartDiv.on('plotly_relayout', function(eventdata) {{
                if (eventdata['xaxis.range[0]'] && eventdata['xaxis.range[1]']) {{
                    const xMin = new Date(eventdata['xaxis.range[0]']);
                    const xMax = new Date(eventdata['xaxis.range[1]']);

                    let yMin = Infinity;
                    let yMax = -Infinity;

                    for (let i = 0; i < data.length; i++) {{
                        const date = new Date(data[i].date);
                        if (date >= xMin && date <= xMax) {{
                            yMin = Math.min(yMin, data[i].low);
                            yMax = Math.max(yMax, data[i].high);
                        }}
                    }}

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
                    Plotly.relayout('chart', {{'yaxis.autorange': true}});
                }}
            }});
        }}

        // Create cluster distribution chart
        function createClusterChart(clusters) {{
            const clusterSizes = clusters.map(c => c.num_breaks);
            const sizeCounts = {{}};
            for (let size of clusterSizes) {{
                sizeCounts[size] = (sizeCounts[size] || 0) + 1;
            }}

            const sizes = Object.keys(sizeCounts).map(Number).sort((a, b) => a - b);
            const counts = sizes.map(s => sizeCounts[s]);

            const trace = {{
                x: sizes,
                y: counts,
                type: 'bar',
                marker: {{
                    color: sizes.map(s => s === 1 ? '#ffc107' : s === 2 ? '#ff9800' : s === 3 ? '#ff6f00' : '#e65100')
                }},
                text: counts,
                textposition: 'outside',
                hovertemplate: '<b>%{{x}} breaks</b><br>Count: %{{y}}<extra></extra>'
            }};

            const layout = {{
                title: 'Distribution of Cluster Sizes',
                xaxis: {{ title: 'Number of Consecutive Breaks in Cluster' }},
                yaxis: {{ title: 'Number of Clusters' }},
                height: 400,
                margin: {{ l: 50, r: 50, t: 60, b: 50 }}
            }};

            Plotly.newPlot('clusterChart', [trace], layout, {{
                responsive: true,
                displayModeBar: false,
                displaylogo: false
            }});
        }}

        // Display clusters details
        function displayClusters(clusters) {{
            if (clusters.length === 0) {{
                document.getElementById('clusterContainer').innerHTML = '<div class="empty-state">No clusters found</div>';
                return;
            }}

            let html = '<h2>All Break Clusters</h2>';

            for (let cluster of clusters) {{
                const emoji = cluster.num_breaks > 1 ? '🔴' : '🟡';
                const breakLabel = cluster.num_breaks === 1 ? 'break' : 'breaks';

                html += `
                    <div class="cluster-item">
                        <div class="cluster-header">
                            ${{emoji}} Cluster #${{cluster.id}}: ${{cluster.num_breaks}} ${{breakLabel}}
                            (${{cluster.start_date}} to ${{cluster.end_date}})
                        </div>

                        <div class="cluster-stats">
                            <div class="cluster-stat">
                                <div class="cluster-stat-label">Duration</div>
                                <div class="cluster-stat-value">${{cluster.duration_days}} days</div>
                            </div>
                `;

                if (cluster.avg_gap) {{
                    html += `
                        <div class="cluster-stat">
                            <div class="cluster-stat-label">Avg Gap</div>
                            <div class="cluster-stat-value">${{cluster.avg_gap.toFixed(1)}} days</div>
                        </div>
                    `;
                }}

                html += `
                            <div class="cluster-stat">
                                <div class="cluster-stat-label">Total Drop</div>
                                <div class="cluster-stat-value">${{cluster.total_drop.toFixed(2)}}%</div>
                            </div>
                        </div>

                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Previous Support</th>
                                    <th>New Support</th>
                                    <th>Drop %</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                for (let breakItem of cluster.breaks) {{
                    html += `
                        <tr>
                            <td>${{breakItem.date}}</td>
                            <td>${{breakItem.prev_support.toFixed(2)}} kr</td>
                            <td>${{breakItem.new_support.toFixed(2)}} kr</td>
                            <td>${{breakItem.drop_pct.toFixed(2)}}%</td>
                        </tr>
                    `;
                }}

                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            }}

            document.getElementById('clusterContainer').innerHTML = html;
        }}

        // Update display
        function updateDisplay() {{
            const stockData = STOCK_DATA[currentStock];
            if (!stockData) return;

            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            maxGapDays = parseInt(document.getElementById('maxGap').value);

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
            currentBreaks = analyzeSupportBreaks(filteredData);

            // Analyze clusters
            currentClusters = analyzeConsecutiveBreaks(currentBreaks, maxGapDays);

            // Calculate break statistics
            const breakStats = calculateBreakStats(filteredData, currentBreaks);

            // Update UI
            updateMetrics(currentBreaks, currentClusters);
            createTimelineChart(filteredData, currentBreaks);
            createClusterChart(currentClusters);
            displayClusters(currentClusters);
            displayBreakStatistics(breakStats);
        }}

        // Display break statistics
        function displayBreakStatistics(stats) {{
            if (!stats) {{
                document.getElementById('breakStatsGrid').innerHTML = '<div class="empty-state">No breaks to analyze</div>';
                return;
            }}

            const html = `
                <div class="stat-card">
                    <h4>Support Breaks</h4>
                    <div class="value">${{stats.totalBreaks}}</div>
                </div>
                <div class="stat-card">
                    <h4>Days Since Last Break</h4>
                    <div class="value">${{stats.daysSinceLastBreak}}d</div>
                </div>
                <div class="stat-card">
                    <h4>Stability</h4>
                    <div class="value">${{stats.stability.toFixed(1)}}%</div>
                </div>
                <div class="stat-card">
                    <h4>Trading Days per Break</h4>
                    <div class="value">${{stats.tradingDaysPerBreak.toFixed(0)}}</div>
                </div>
                <div class="stat-card">
                    <h4>Days Before First Break</h4>
                    <div class="value">${{stats.daysBeforeFirstBreak}}d</div>
                </div>
                <div class="stat-card">
                    <h4>Avg Days Between Breaks</h4>
                    <div class="value">${{stats.avgDaysBetween ? stats.avgDaysBetween.toFixed(0) + 'd' : 'N/A'}}</div>
                </div>
                <div class="stat-card">
                    <h4>Median Days Between Breaks</h4>
                    <div class="value">${{stats.medianDaysBetween ? stats.medianDaysBetween + 'd' : 'N/A'}}</div>
                </div>
                <div class="stat-card">
                    <h4>Shortest Break Duration</h4>
                    <div class="value">${{stats.minDaysBetween ? stats.minDaysBetween + 'd' : 'N/A'}}</div>
                </div>
                <div class="stat-card">
                    <h4>Longest Break Duration</h4>
                    <div class="value">${{stats.maxDaysBetween ? stats.maxDaysBetween + 'd' : 'N/A'}}</div>
                </div>
                <div class="stat-card">
                    <h4>Avg Break Magnitude</h4>
                    <div class="value">${{stats.avgDrop.toFixed(2)}}%</div>
                </div>
                <div class="stat-card">
                    <h4>Biggest Break</h4>
                    <div class="value">${{stats.maxDrop.toFixed(2)}}%</div>
                </div>
            `;

            document.getElementById('breakStatsGrid').innerHTML = html;
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

        document.getElementById('maxGap').addEventListener('change', updateDisplay);
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

print(f"✅ Consecutive Breaks Dashboard created successfully!")
print(f"📄 File: {OUTPUT_FILE}")
print(f"📊 Stocks: {len(stocks)}")
print(f"\n🌐 Open the file in your browser to analyze break clusters.")
print(f"   Adjust 'Max Days Between Breaks' to customize clustering.")
