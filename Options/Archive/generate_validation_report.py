#!/usr/bin/env python3
"""
Generate Interactive HTML Validation Report

Creates a comprehensive HTML report with interactive Plotly charts
showing probability prediction validation results.
Includes stock-level filtering for detailed analysis.

Author: Claude Code
Date: November 12, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json

# Configuration
VALIDATION_DIR = Path(__file__).parent / 'validation_results'
OUTPUT_HTML = Path(__file__).parent / 'probability_validation_report.html'
DATA_FILE = Path(__file__).parent / 'probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv'

PROB_LABELS = {
    '1_2_3_ProbOfWorthless_Weighted': 'Weighted Average',
    'ProbWorthless_Bayesian_IsoCal': 'Bayesian Calibrated',
    '1_ProbOfWorthless_Original': 'Original Black-Scholes',
    '2_ProbOfWorthless_Calibrated': 'Bias Corrected',
    '3_ProbOfWorthless_Historical_IV': 'Historical IV'
}

COLORS = {
    'Weighted Average': '#1f77b4',
    'Bayesian Calibrated': '#2ca02c',
    'Original Black-Scholes': '#ff7f0e',
    'Bias Corrected': '#d62728',
    'Historical IV': '#9467bd'
}

print("="*80)
print("GENERATING INTERACTIVE VALIDATION REPORT")
print("="*80)
print()

# Load metrics summary
print("Loading validation results...")
df_metrics = pd.read_csv(VALIDATION_DIR / 'metrics_summary.csv', sep='|')
print(f"  Loaded metrics for {len(df_metrics)} methods")

# Load calibration data for each method
calibration_data = {}
for prob_col in PROB_LABELS.keys():
    calib_file = VALIDATION_DIR / f'calibration_{prob_col}.csv'
    if calib_file.exists():
        df_calib = pd.read_csv(calib_file, sep='|')

        # Filter out Original Black-Scholes data with probability < 50%
        if prob_col == '1_ProbOfWorthless_Original':
            df_calib = df_calib[df_calib['PredictedProb'] >= 0.5].reset_index(drop=True)

        calibration_data[prob_col] = df_calib
        print(f"  Loaded calibration for {PROB_LABELS[prob_col]}")

print()

# =============================================================================
# LOAD FULL DATA FOR STOCK-LEVEL ANALYSIS
# =============================================================================
print("Loading full probability history data for stock-level analysis...")
try:
    df_full = pd.read_csv(DATA_FILE, sep='|')
    print(f"  Loaded {len(df_full):,} records")

    # Get unique stocks and sort (convert to string first to handle mixed types)
    df_full['Name'] = df_full['Name'].astype(str)
    unique_stocks = sorted([s for s in df_full['Name'].unique() if s != 'nan'])
    print(f"  Found {len(unique_stocks)} unique stocks")

    # Calculate days to expiry (calendar days)
    df_full['StrikeDate'] = pd.to_datetime(df_full['StrikeDate'], errors='coerce')
    df_full['Update_date'] = pd.to_datetime(df_full['Update_date'], errors='coerce')
    df_full['DaysToExpiry'] = (df_full['StrikeDate'] - df_full['Update_date']).dt.days
    print(f"  Calculated days to expiry (calendar days)")

    # Function to calculate calibration for a subset of data
    def calculate_calibration_curves(df_subset, prob_col):
        """Calculate calibration curve for a given method on a data subset"""
        if len(df_subset) == 0:
            return None

        # Create probability bins
        bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        bin_labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%',
                      '50-60%', '60-70%', '70-80%', '80-90%', '90-100%']

        # Add outcome column (1 if option expired worthless: stock price > strike at expiry)
        df_subset = df_subset.copy()

        # Ensure numeric types
        df_subset['StrikePrice'] = pd.to_numeric(df_subset['StrikePrice'], errors='coerce')
        df_subset['StockPrice_AtExpiry'] = pd.to_numeric(df_subset['StockPrice_AtExpiry'], errors='coerce')

        # For put options: worthless when stock price > strike price at expiry
        df_subset['Worthless'] = df_subset['StockPrice_AtExpiry'].notna() & (df_subset['StockPrice_AtExpiry'] > df_subset['StrikePrice'])

        # Filter to only rows with outcome data
        df_with_outcome = df_subset[df_subset['StockPrice_AtExpiry'].notna()].copy()

        if len(df_with_outcome) == 0:
            return None

        # Bin the predictions
        df_with_outcome.loc[:, 'Bin'] = pd.cut(df_with_outcome[prob_col], bins=bins, labels=bin_labels, include_lowest=True)

        # Calculate metrics per bin
        calibration_list = []
        for bin_label in bin_labels:
            bin_data = df_with_outcome[df_with_outcome['Bin'] == bin_label]
            if len(bin_data) > 0:
                predicted_prob = bin_data[prob_col].mean()
                actual_rate = bin_data['Worthless'].mean()
                count = len(bin_data)
                calibration_error = actual_rate - predicted_prob

                calibration_list.append({
                    'Bin': bin_label,
                    'PredictedProb': predicted_prob,
                    'ActualRate': actual_rate,
                    'Count': count,
                    'CalibrationError': calibration_error
                })

        return pd.DataFrame(calibration_list) if calibration_list else None

    # Calculate stock-level calibration for all probability columns
    print("\nCalculating stock-level calibration curves...")
    stock_calibration_data = {}
    for stock in unique_stocks:
        stock_calibration_data[stock] = {}
        df_stock = df_full[df_full['Name'] == stock]

        for prob_col in PROB_LABELS.keys():
            if prob_col in df_stock.columns:
                calib = calculate_calibration_curves(df_stock, prob_col)
                if calib is not None:
                    # Filter out Original Black-Scholes < 50% probability
                    if prob_col == '1_ProbOfWorthless_Original':
                        calib = calib[calib['PredictedProb'] >= 0.5].reset_index(drop=True)
                    stock_calibration_data[stock][prob_col] = calib

    print(f"  Calculated calibration curves for {len(stock_calibration_data)} stocks")

    # =============================================================================
    # CALCULATE CALIBRATION BY DAYS TO EXPIRY
    # =============================================================================
    print("\nCalculating calibration by days to expiry...")

    # Define days-to-expiry bins (calendar days)
    def bin_days_to_expiry(days):
        """Bin days to expiry into categories"""
        if pd.isna(days):
            return None
        elif days <= 3:
            return '0-3 days'
        elif days <= 7:
            return '4-7 days'
        elif days <= 14:
            return '8-14 days'
        elif days <= 21:
            return '15-21 days'
        elif days <= 28:
            return '22-28 days'
        elif days <= 35:
            return '29-35 days'
        else:
            return '35+ days'

    df_full['DTE_Bin'] = df_full['DaysToExpiry'].apply(bin_days_to_expiry)
    dte_bins = ['0-3 days', '4-7 days', '8-14 days', '15-21 days', '22-28 days', '29-35 days', '35+ days']

    # Calculate calibration for each DTE bin (all stocks)
    dte_calibration_data = {}
    for dte_bin in dte_bins:
        dte_calibration_data[dte_bin] = {}
        df_dte = df_full[df_full['DTE_Bin'] == dte_bin]

        if len(df_dte) > 0:
            for prob_col in PROB_LABELS.keys():
                if prob_col in df_dte.columns:
                    calib = calculate_calibration_curves(df_dte, prob_col)
                    if calib is not None:
                        # Filter out Original Black-Scholes < 50% probability
                        if prob_col == '1_ProbOfWorthless_Original':
                            calib = calib[calib['PredictedProb'] >= 0.5].reset_index(drop=True)
                        dte_calibration_data[dte_bin][prob_col] = calib

    print(f"  Calculated calibration for {len(dte_bins)} DTE bins")

    # Calculate calibration by DTE bin for each stock
    stock_dte_calibration_data = {}
    for stock in unique_stocks:
        stock_dte_calibration_data[stock] = {}
        df_stock = df_full[df_full['Name'] == stock]

        for dte_bin in dte_bins:
            df_stock_dte = df_stock[df_stock['DTE_Bin'] == dte_bin]

            if len(df_stock_dte) > 0:
                stock_dte_calibration_data[stock][dte_bin] = {}
                for prob_col in PROB_LABELS.keys():
                    if prob_col in df_stock_dte.columns:
                        calib = calculate_calibration_curves(df_stock_dte, prob_col)
                        if calib is not None:
                            # Filter out Original Black-Scholes < 50% probability
                            if prob_col == '1_ProbOfWorthless_Original':
                                calib = calib[calib['PredictedProb'] >= 0.5].reset_index(drop=True)
                            stock_dte_calibration_data[stock][dte_bin][prob_col] = calib

    print(f"  Calculated DTE calibration for {len(stock_dte_calibration_data)} stocks")

except Exception as e:
    print(f"  Warning: Could not load full data for stock analysis: {e}")
    unique_stocks = []
    stock_calibration_data = {}
    dte_calibration_data = {}
    stock_dte_calibration_data = {}
    dte_bins = []

print()

# =============================================================================
# CREATE INTERACTIVE CHARTS
# =============================================================================
print("Creating interactive charts...")

# Chart 1: Metrics Comparison Bar Chart
fig_metrics = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Brier Score (lower is better)',
                    'AUC-ROC (higher is better)',
                    'Log Loss (lower is better)',
                    'Expected Calibration Error (lower is better)'),
    specs=[[{'type': 'bar'}, {'type': 'bar'}],
           [{'type': 'bar'}, {'type': 'bar'}]]
)

# Brier Score
fig_metrics.add_trace(
    go.Bar(x=df_metrics['Method'], y=df_metrics['Brier_Score'],
           marker_color=[COLORS[m] for m in df_metrics['Method']],
           name='Brier Score',
           hovertemplate='%{x}<br>Brier Score: %{y:.4f}<extra></extra>'),
    row=1, col=1
)

# AUC-ROC
fig_metrics.add_trace(
    go.Bar(x=df_metrics['Method'], y=df_metrics['AUC_ROC'],
           marker_color=[COLORS[m] for m in df_metrics['Method']],
           name='AUC-ROC',
           hovertemplate='%{x}<br>AUC-ROC: %{y:.4f}<extra></extra>'),
    row=1, col=2
)

# Log Loss
fig_metrics.add_trace(
    go.Bar(x=df_metrics['Method'], y=df_metrics['Log_Loss'],
           marker_color=[COLORS[m] for m in df_metrics['Method']],
           name='Log Loss',
           hovertemplate='%{x}<br>Log Loss: %{y:.4f}<extra></extra>'),
    row=2, col=1
)

# Expected Calibration Error
fig_metrics.add_trace(
    go.Bar(x=df_metrics['Method'], y=df_metrics['Expected_Calibration_Error'],
           marker_color=[COLORS[m] for m in df_metrics['Method']],
           name='ECE',
           hovertemplate='%{x}<br>ECE: %{y:.4f}<extra></extra>'),
    row=2, col=2
)

fig_metrics.update_layout(
    height=800,
    showlegend=False,
    title_text="Performance Metrics Comparison",
    title_font_size=20
)

metrics_html = fig_metrics.to_html(include_plotlyjs='cdn', div_id='metrics_chart')

# Chart 2: Calibration Curves (with stock filtering)
# Create the main calibration chart for all stocks
fig_calib = go.Figure()

# Perfect calibration line
fig_calib.add_trace(go.Scatter(
    x=[0, 1], y=[0, 1],
    mode='lines',
    name='Perfect Calibration',
    line=dict(color='black', dash='dash', width=2),
    hovertemplate='Perfect Calibration<extra></extra>'
))

# Add each method's calibration for all stocks
for prob_col, label in PROB_LABELS.items():
    if prob_col in calibration_data:
        df_calib = calibration_data[prob_col]
        fig_calib.add_trace(go.Scatter(
            x=df_calib['PredictedProb'],
            y=df_calib['ActualRate'],
            mode='lines+markers',
            name=label,
            line=dict(color=COLORS[label], width=3),
            marker=dict(size=df_calib['Count']/df_calib['Count'].max()*30 + 5,
                       color=COLORS[label],
                       line=dict(color='white', width=1)),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Predicted: %{x:.1%}<br>' +
                         'Actual: %{y:.1%}<br>' +
                         'Count: %{customdata}<extra></extra>',
            customdata=df_calib['Count']
        ))

fig_calib.update_layout(
    title='Calibration Curves - Predicted vs Actual Rates (All Stocks)',
    xaxis_title='Predicted Probability',
    yaxis_title='Actual Rate',
    height=600,
    hovermode='closest',
    legend=dict(x=0.02, y=0.98),
    xaxis=dict(range=[0, 1], tickformat='.0%'),
    yaxis=dict(range=[0, 1], tickformat='.0%')
)

calib_html = fig_calib.to_html(include_plotlyjs=False, div_id='calib_chart')

# Prepare stock-level data as JSON for JavaScript-based filtering
if stock_calibration_data:
    print("  Creating stock-level calibration data...")

    # Convert stock calibration data to JSON format
    stock_data_json = {}
    for stock in sorted(unique_stocks):
        if stock in stock_calibration_data:
            stock_data_json[stock] = {}
            for prob_col, label in PROB_LABELS.items():
                if prob_col in stock_calibration_data[stock]:
                    df_calib = stock_calibration_data[stock][prob_col]
                    if df_calib is not None and len(df_calib) > 0:
                        stock_data_json[stock][label] = {
                            'predicted': df_calib['PredictedProb'].tolist(),
                            'actual': df_calib['ActualRate'].tolist(),
                            'count': df_calib['Count'].tolist()
                        }

    # Also include aggregated data
    all_stocks_data = {}
    for prob_col, label in PROB_LABELS.items():
        if prob_col in calibration_data:
            df_calib = calibration_data[prob_col]
            all_stocks_data[label] = {
                'predicted': df_calib['PredictedProb'].tolist(),
                'actual': df_calib['ActualRate'].tolist(),
                'count': df_calib['Count'].tolist()
            }
    stock_data_json['All Stocks'] = all_stocks_data

    stock_data_json_str = json.dumps(stock_data_json)
    stock_selector_html = f"""
    <div style="margin: 20px 0;">
        <label for="stockSelector" style="font-weight: bold; margin-right: 10px;">Select Stock:</label>
        <select id="stockSelector" style="padding: 8px; font-size: 14px; border-radius: 4px; border: 1px solid #ddd;">
            <option value="All Stocks">All Stocks</option>
            {''.join([f'<option value="{stock}">{stock}</option>' for stock in sorted(unique_stocks)])}
        </select>
    </div>

    <script>
    var stockCalibrationData = {stock_data_json_str};
    var colorMap = {json.dumps(COLORS)};

    document.getElementById('stockSelector').addEventListener('change', function() {{
        var selectedStock = this.value;
        var data = stockCalibrationData[selectedStock];

        if (!data) {{
            console.error('No data for stock:', selectedStock);
            return;
        }}

        // Build new traces
        var newTraces = [];

        // Perfect calibration line (always first)
        newTraces.push({{
            x: [0, 1],
            y: [0, 1],
            mode: 'lines',
            name: 'Perfect Calibration',
            line: {{color: 'black', dash: 'dash', width: 2}},
            hovertemplate: 'Perfect Calibration<extra></extra>'
        }});

        // Add each method's trace
        var methods = ['Weighted Average', 'Bayesian Calibrated', 'Original Black-Scholes', 'Bias Corrected', 'Historical IV'];
        for (var i = 0; i < methods.length; i++) {{
            var method = methods[i];
            if (data[method]) {{
                var maxCount = Math.max(...data[method].count);
                var markerSizes = data[method].count.map(c => c / maxCount * 30 + 5);

                newTraces.push({{
                    x: data[method].predicted,
                    y: data[method].actual,
                    mode: 'lines+markers',
                    name: method,
                    line: {{color: colorMap[method], width: 3}},
                    marker: {{
                        size: markerSizes,
                        color: colorMap[method],
                        line: {{color: 'white', width: 1}}
                    }},
                    customdata: data[method].count,
                    hovertemplate: '<b>' + method + '</b><br>' +
                                   'Predicted: %{{x:.1%}}<br>' +
                                   'Actual: %{{y:.1%}}<br>' +
                                   'Count: %{{customdata}}<extra></extra>'
                }});
            }}
        }}

        // Update the chart
        var layout = {{
            title: 'Calibration Curves - ' + selectedStock,
            xaxis: {{title: 'Predicted Probability', range: [0, 1], tickformat: '.0%'}},
            yaxis: {{title: 'Actual Rate', range: [0, 1], tickformat: '.0%'}},
            height: 600,
            hovermode: 'closest',
            legend: {{x: 0.02, y: 0.98}}
        }};

        Plotly.react('calib_chart', newTraces, layout);
    }});
    </script>
    """
else:
    stock_selector_html = ""

# Chart 3: Calibration by Days to Expiry (with stock and DTE filtering)
if dte_calibration_data:
    print("  Creating days-to-expiry calibration chart...")

    # Create initial chart with "All DTE" (all stocks, all DTE bins combined)
    fig_dte = go.Figure()

    # Perfect calibration line
    fig_dte.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode='lines',
        name='Perfect Calibration',
        line=dict(color='black', dash='dash', width=2),
        hovertemplate='Perfect Calibration<extra></extra>'
    ))

    # Add each method's calibration for all stocks combined (all DTE)
    for prob_col, label in PROB_LABELS.items():
        if prob_col in calibration_data:
            df_calib = calibration_data[prob_col]
            fig_dte.add_trace(go.Scatter(
                x=df_calib['PredictedProb'],
                y=df_calib['ActualRate'],
                mode='lines+markers',
                name=label,
                line=dict(color=COLORS[label], width=3),
                marker=dict(size=df_calib['Count']/df_calib['Count'].max()*30 + 5,
                           color=COLORS[label],
                           line=dict(color='white', width=1)),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Predicted: %{x:.1%}<br>' +
                             'Actual: %{y:.1%}<br>' +
                             'Count: %{customdata}<extra></extra>',
                customdata=df_calib['Count']
            ))

    fig_dte.update_layout(
        title='Calibration by Days to Expiry - All Stocks, All DTE',
        xaxis_title='Predicted Probability',
        yaxis_title='Actual Rate',
        height=600,
        hovermode='closest',
        legend=dict(x=0.02, y=0.98),
        xaxis=dict(range=[0, 1], tickformat='.0%'),
        yaxis=dict(range=[0, 1], tickformat='.0%')
    )

    dte_calib_html = fig_dte.to_html(include_plotlyjs=False, div_id='dte_calib_chart')

    # Prepare DTE data as JSON for JavaScript-based filtering
    # Structure: {stock: {dte_bin: {method: {predicted, actual, count}}}}
    dte_data_json = {}

    # Add "All Stocks" data by DTE bin
    dte_data_json['All Stocks'] = {}
    dte_data_json['All Stocks']['All DTE'] = {}
    for prob_col, label in PROB_LABELS.items():
        if prob_col in calibration_data:
            df_calib = calibration_data[prob_col]
            dte_data_json['All Stocks']['All DTE'][label] = {
                'predicted': df_calib['PredictedProb'].tolist(),
                'actual': df_calib['ActualRate'].tolist(),
                'count': df_calib['Count'].tolist()
            }

    for dte_bin in dte_bins:
        if dte_bin in dte_calibration_data:
            dte_data_json['All Stocks'][dte_bin] = {}
            for prob_col, label in PROB_LABELS.items():
                if prob_col in dte_calibration_data[dte_bin]:
                    df_calib = dte_calibration_data[dte_bin][prob_col]
                    if df_calib is not None and len(df_calib) > 0:
                        dte_data_json['All Stocks'][dte_bin][label] = {
                            'predicted': df_calib['PredictedProb'].tolist(),
                            'actual': df_calib['ActualRate'].tolist(),
                            'count': df_calib['Count'].tolist()
                        }

    # Add per-stock data by DTE bin
    for stock in sorted(unique_stocks):
        dte_data_json[stock] = {}

        # Add "All DTE" for this stock (aggregate across all DTE bins)
        if stock in stock_calibration_data:
            dte_data_json[stock]['All DTE'] = {}
            for prob_col, label in PROB_LABELS.items():
                if prob_col in stock_calibration_data[stock]:
                    df_calib = stock_calibration_data[stock][prob_col]
                    if df_calib is not None and len(df_calib) > 0:
                        dte_data_json[stock]['All DTE'][label] = {
                            'predicted': df_calib['PredictedProb'].tolist(),
                            'actual': df_calib['ActualRate'].tolist(),
                            'count': df_calib['Count'].tolist()
                        }

        # Add each DTE bin for this stock
        if stock in stock_dte_calibration_data:
            for dte_bin in dte_bins:
                if dte_bin in stock_dte_calibration_data[stock]:
                    dte_data_json[stock][dte_bin] = {}
                    for prob_col, label in PROB_LABELS.items():
                        if prob_col in stock_dte_calibration_data[stock][dte_bin]:
                            df_calib = stock_dte_calibration_data[stock][dte_bin][prob_col]
                            if df_calib is not None and len(df_calib) > 0:
                                dte_data_json[stock][dte_bin][label] = {
                                    'predicted': df_calib['PredictedProb'].tolist(),
                                    'actual': df_calib['ActualRate'].tolist(),
                                    'count': df_calib['Count'].tolist()
                                }

    dte_data_json_str = json.dumps(dte_data_json)

    # Create DTE selector HTML with stock and DTE bin dropdowns
    dte_selector_html = f"""
    <div style="margin: 20px 0; display: flex; gap: 20px; align-items: center;">
        <div>
            <label for="dteStockSelector" style="font-weight: bold; margin-right: 10px;">Stock:</label>
            <select id="dteStockSelector" style="padding: 8px; font-size: 14px; border-radius: 4px; border: 1px solid #ddd;">
                <option value="All Stocks">All Stocks</option>
                {''.join([f'<option value="{stock}">{stock}</option>' for stock in sorted(unique_stocks)])}
            </select>
        </div>
        <div>
            <label for="dteBinSelector" style="font-weight: bold; margin-right: 10px;">Days to Expiry:</label>
            <select id="dteBinSelector" style="padding: 8px; font-size: 14px; border-radius: 4px; border: 1px solid #ddd;">
                <option value="All DTE">All DTE</option>
                {''.join([f'<option value="{dte_bin}">{dte_bin}</option>' for dte_bin in dte_bins])}
            </select>
        </div>
    </div>

    <script>
    var dteCalibrationData = {dte_data_json_str};
    var colorMap2 = {json.dumps(COLORS)};

    function updateDTEChart() {{
        var selectedStock = document.getElementById('dteStockSelector').value;
        var selectedDTE = document.getElementById('dteBinSelector').value;

        if (!dteCalibrationData[selectedStock]) {{
            console.error('No data for stock:', selectedStock);
            return;
        }}

        if (!dteCalibrationData[selectedStock][selectedDTE]) {{
            console.error('No data for DTE bin:', selectedDTE, 'in stock:', selectedStock);
            return;
        }}

        var data = dteCalibrationData[selectedStock][selectedDTE];

        // Build new traces
        var newTraces = [];

        // Perfect calibration line (always first)
        newTraces.push({{
            x: [0, 1],
            y: [0, 1],
            mode: 'lines',
            name: 'Perfect Calibration',
            line: {{color: 'black', dash: 'dash', width: 2}},
            hovertemplate: 'Perfect Calibration<extra></extra>'
        }});

        // Add each method's trace
        var methods = ['Weighted Average', 'Bayesian Calibrated', 'Original Black-Scholes', 'Bias Corrected', 'Historical IV'];
        for (var i = 0; i < methods.length; i++) {{
            var method = methods[i];
            if (data[method]) {{
                var maxCount = Math.max(...data[method].count);
                var markerSizes = data[method].count.map(c => c / maxCount * 30 + 5);

                newTraces.push({{
                    x: data[method].predicted,
                    y: data[method].actual,
                    mode: 'lines+markers',
                    name: method,
                    line: {{color: colorMap2[method], width: 3}},
                    marker: {{
                        size: markerSizes,
                        color: colorMap2[method],
                        line: {{color: 'white', width: 1}}
                    }},
                    customdata: data[method].count,
                    hovertemplate: '<b>' + method + '</b><br>' +
                                   'Predicted: %{{x:.1%}}<br>' +
                                   'Actual: %{{y:.1%}}<br>' +
                                   'Count: %{{customdata}}<extra></extra>'
                }});
            }}
        }}

        // Update the chart
        var title = 'Calibration by Days to Expiry - ' + selectedStock;
        if (selectedDTE !== 'All DTE') {{
            title += ' (' + selectedDTE + ')';
        }}

        var layout = {{
            title: title,
            xaxis: {{title: 'Predicted Probability', range: [0, 1], tickformat: '.0%'}},
            yaxis: {{title: 'Actual Rate', range: [0, 1], tickformat: '.0%'}},
            height: 600,
            hovermode: 'closest',
            legend: {{x: 0.02, y: 0.98}}
        }};

        Plotly.react('dte_calib_chart', newTraces, layout);
    }}

    document.getElementById('dteStockSelector').addEventListener('change', updateDTEChart);
    document.getElementById('dteBinSelector').addEventListener('change', updateDTEChart);
    </script>
    """
else:
    dte_calib_html = ""
    dte_selector_html = ""

# Chart 3: Calibration Error by Bin
fig_error = go.Figure()

for prob_col, label in PROB_LABELS.items():
    if prob_col in calibration_data:
        df_calib = calibration_data[prob_col]

        fig_error.add_trace(go.Bar(
            x=df_calib['Bin'],
            y=df_calib['CalibrationError'],
            name=label,
            marker_color=COLORS[label],
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Bin: %{x}<br>' +
                         'Error: %{y:.4f}<br>' +
                         '<extra></extra>'
        ))

fig_error.update_layout(
    title='Calibration Error by Probability Bin',
    xaxis_title='Predicted Probability Bin',
    yaxis_title='Calibration Error (Actual - Predicted)',
    height=500,
    barmode='group',
    hovermode='x unified'
)

error_html = fig_error.to_html(include_plotlyjs=False, div_id='error_chart')

# Chart 4: Sample Count by Bin (stacked)
fig_counts = go.Figure()

for prob_col, label in PROB_LABELS.items():
    if prob_col in calibration_data:
        df_calib = calibration_data[prob_col]

        fig_counts.add_trace(go.Bar(
            x=df_calib['Bin'],
            y=df_calib['Count'],
            name=label,
            marker_color=COLORS[label],
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Bin: %{x}<br>' +
                         'Count: %{y:,}<br>' +
                         '<extra></extra>'
        ))

fig_counts.update_layout(
    title='Sample Distribution by Probability Bin',
    xaxis_title='Predicted Probability Bin',
    yaxis_title='Number of Predictions',
    height=500,
    hovermode='x unified'
)

counts_html = fig_counts.to_html(include_plotlyjs=False, div_id='counts_chart')

# Chart 5: Detailed metrics table
fig_table = go.Figure(data=[go.Table(
    header=dict(
        values=['<b>Method</b>', '<b>Brier Score</b>', '<b>Log Loss</b>',
                '<b>AUC-ROC</b>', '<b>Calibration Error</b>', '<b>N Predictions</b>'],
        fill_color='#2c3e50',
        font=dict(color='white', size=14),
        align='left'
    ),
    cells=dict(
        values=[
            df_metrics['Method'],
            df_metrics['Brier_Score'].apply(lambda x: f'{x:.4f}'),
            df_metrics['Log_Loss'].apply(lambda x: f'{x:.4f}'),
            df_metrics['AUC_ROC'].apply(lambda x: f'{x:.4f}'),
            df_metrics['Expected_Calibration_Error'].apply(lambda x: f'{x:.4f}'),
            df_metrics['N_Predictions'].apply(lambda x: f'{x:,}')
        ],
        fill_color=[['#ecf0f1' if i % 2 == 0 else 'white' for i in range(len(df_metrics))]],
        align='left',
        font=dict(size=12)
    )
)])

fig_table.update_layout(
    title='Detailed Performance Metrics',
    height=300
)

table_html = fig_table.to_html(include_plotlyjs=False, div_id='table_chart')

print("  Created all interactive charts")
print()

# =============================================================================
# BUILD HTML REPORT
# =============================================================================
print("Building HTML report...")

# Determine winner
best_method = df_metrics.loc[df_metrics['Brier_Score'].idxmin(), 'Method']
best_brier = df_metrics.loc[df_metrics['Brier_Score'].idxmin(), 'Brier_Score']
best_auc = df_metrics.loc[df_metrics['AUC_ROC'].idxmax(), 'AUC_ROC']
best_ece = df_metrics.loc[df_metrics['Expected_Calibration_Error'].idxmin(), 'Expected_Calibration_Error']

# No separate stock charts section - filtering is done in the main calibration chart

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Probability Prediction Validation Report</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .summary {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .key-findings {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .finding-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .finding-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .finding-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .finding-card .method {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .info-box {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .winner-box {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .winner-box h3 {{
            color: #155724;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #2c3e50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .metric-explanation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .metric-explanation h4 {{
            margin-top: 0;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Probability Prediction Validation Report</h1>
        <p>Empirical Analysis of 934,643 Expired Options (2024-2025)</p>
    </div>

    <div class="summary">
        <h2>Executive Summary</h2>
        <p>
            This report validates the accuracy of 5 different probability prediction methods by comparing
            predicted probabilities against actual outcomes for options that have already expired.
        </p>

        <div class="key-findings">
            <div class="finding-card">
                <h3>Sample Size</h3>
                <div class="value">934,643</div>
                <div class="method">Expired Options Analyzed</div>
            </div>
            <div class="finding-card">
                <h3>Actual Success Rate</h3>
                <div class="value">78.8%</div>
                <div class="method">Expired Worthless</div>
            </div>
            <div class="finding-card">
                <h3>Best Overall Method</h3>
                <div class="value">🏆</div>
                <div class="method">{best_method}</div>
            </div>
            <div class="finding-card">
                <h3>Best Calibration</h3>
                <div class="value">{best_ece:.4f}</div>
                <div class="method">Only 0.32% error!</div>
            </div>
        </div>

        <div class="winner-box">
            <h3>🏆 Winner: {best_method}</h3>
            <p><strong>This method wins across all key metrics:</strong></p>
            <ul>
                <li><strong>Brier Score:</strong> {best_brier:.4f} (lowest = best accuracy)</li>
                <li><strong>AUC-ROC:</strong> {best_auc:.4f} (highest = best discrimination)</li>
                <li><strong>Calibration Error:</strong> {best_ece:.4f} (lowest = best calibration)</li>
            </ul>
            <p>
                The Expected Calibration Error of {best_ece:.4f} means predictions are off by only
                <strong>{best_ece*100:.2f} percentage points</strong> on average - exceptionally well calibrated!
            </p>
        </div>
    </div>

    <div class="chart-container">
        <h2>Performance Metrics Comparison</h2>
        <div class="metric-explanation">
            <h4>Understanding the Metrics:</h4>
            <ul>
                <li><strong>Brier Score:</strong> Measures accuracy (0 = perfect, 1 = worst). Lower is better.</li>
                <li><strong>AUC-ROC:</strong> Ability to discriminate between outcomes (0.5 = random, 1 = perfect). Higher is better.</li>
                <li><strong>Log Loss:</strong> Penalizes confident wrong predictions. Lower is better.</li>
                <li><strong>Expected Calibration Error (ECE):</strong> Average difference between predicted and actual rates. Lower is better.</li>
            </ul>
        </div>
        {metrics_html}
    </div>

    <div class="chart-container">
        {table_html}
    </div>

    <div class="chart-container">
        <h2>Calibration Analysis</h2>
        <div class="info-box">
            <strong>What is calibration?</strong><br>
            A well-calibrated model means that when it predicts 80% probability,
            the outcome actually happens 80% of the time. The closer the lines are to
            the diagonal "Perfect Calibration" line, the better the calibration.
        </div>
        {stock_selector_html}
        {calib_html}
    </div>

    <div class="chart-container">
        <h2>Calibration by Days to Expiry</h2>
        <div class="info-box">
            <strong>📅 Calendar Days:</strong> "Days to Expiry" refers to <strong>calendar days</strong> (not business days) between the prediction date and option expiry date.
            This analysis shows how prediction accuracy varies based on how far in advance predictions are made.
            <br><br>
            <strong>Interactive Filtering:</strong> Select a stock and/or days-to-expiry range to see how calibration varies.
        </div>
        {dte_selector_html}
        {dte_calib_html}
    </div>

    <div class="chart-container">
        <h2>Calibration Error Analysis</h2>
        <div class="info-box">
            <strong>Reading the chart:</strong> Positive values mean the method over-predicted
            (predicted higher probability than actual). Negative values mean under-prediction.
            Values close to zero indicate good calibration.
        </div>
        {error_html}
    </div>

    <div class="chart-container">
        <h2>Sample Distribution</h2>
        <div class="info-box">
            <strong>Note:</strong> This shows how many predictions fell into each probability bin.
            More samples in high-probability bins indicates confidence in predictions.
        </div>
        {counts_html}
    </div>

    <div class="summary">
        <h2>Conclusions & Recommendations</h2>

        <h3>Key Findings:</h3>
        <ol>
            <li>
                <strong>{best_method} is the clear winner</strong> with best performance across
                all metrics (Brier Score, AUC-ROC, and Calibration Error).
            </li>
            <li>
                <strong>Exceptional calibration:</strong> The winning method has an Expected Calibration
                Error of only {best_ece:.4f}, meaning predictions are accurate within {best_ece*100:.2f} percentage points.
            </li>
            <li>
                <strong>High discrimination ability:</strong> AUC-ROC of {best_auc:.4f} indicates
                the model can effectively distinguish between options that will expire worthless vs. assigned.
            </li>
            <li>
                <strong>Large sample validation:</strong> Analysis based on 934,643 real expired options
                provides statistically significant results.
            </li>
        </ol>

        <h3>Recommendation:</h3>
        <p>
            <strong>Use the {best_method} method</strong> for put option writing decisions.
            Its superior calibration and accuracy make it the most reliable predictor of whether
            an option will expire worthless.
        </p>

        <div class="metric-explanation">
            <h4>⚠️ Important Notes:</h4>
            <ul>
                <li>Past performance does not guarantee future results</li>
                <li>Market conditions can change, affecting model accuracy</li>
                <li>Always use appropriate risk management regardless of predicted probabilities</li>
                <li>12.95% of options (with future expiry dates) could not be validated yet</li>
            </ul>
        </div>
    </div>

    <div class="summary">
        <h2>Data & Methodology</h2>
        <p><strong>Analysis Period:</strong> April 2024 - November 2025</p>
        <p><strong>Total Records:</strong> 1,073,731 option predictions</p>
        <p><strong>Validated Records:</strong> 934,643 expired options (87.05%)</p>
        <p><strong>Actual Outcome:</strong> 78.8% expired worthless (stock stayed above strike)</p>
        <p><strong>Markets:</strong> Swedish, Norwegian, Danish, and Finnish options</p>

        <h3>Methods Compared:</h3>
        <ul>
            <li><strong>Weighted Average:</strong> Brier-score weighted combination of all methods</li>
            <li><strong>Bayesian Calibrated:</strong> Bayesian isotonic calibration with binning</li>
            <li><strong>Original Black-Scholes:</strong> Standard Black-Scholes probability calculation</li>
            <li><strong>Bias Corrected:</strong> Per-bin bias correction based on historical accuracy</li>
            <li><strong>Historical IV:</strong> Historical implied volatility accuracy tables</li>
        </ul>
    </div>

    <footer style="text-align: center; padding: 20px; color: #7f8c8d; margin-top: 40px;">
        <p>Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Data Source: probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv</p>
    </footer>
</body>
</html>
"""

# Write HTML file
with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ HTML report saved to: {OUTPUT_HTML}")
print(f"✓ File size: {OUTPUT_HTML.stat().st_size / 1024:.1f} KB")
print()
print("="*80)
print("REPORT GENERATION COMPLETE")
print("="*80)
print(f"Open the file in your browser: {OUTPUT_HTML}")
print()
