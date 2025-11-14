#!/usr/bin/env python3
"""
Master Report Generation Script

Consolidates all analysis and report generation into a single workflow:
1. Validates probability predictions against actual outcomes
2. Analyzes historical probability recovery patterns
3. Generates both interactive HTML reports

This script is run weekly to regenerate all reports from updated data.

Author: Claude Code
Date: November 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import json
import plotly.graph_objects as go
from sklearn.metrics import brier_score_loss, roc_auc_score, log_loss
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_FILE = Path(__file__).parent / 'probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv'
VALIDATION_DIR = Path(__file__).parent / 'validation_results'
RECOVERY_DIR = Path(__file__).parent / 'probability_recovery_results'

VALIDATION_DIR.mkdir(exist_ok=True)
RECOVERY_DIR.mkdir(exist_ok=True)

# Probability method mappings
PROB_COLUMNS = [
    '1_2_3_ProbOfWorthless_Weighted',
    'ProbWorthless_Bayesian_IsoCal',
    '1_ProbOfWorthless_Original',
    '2_ProbOfWorthless_Calibrated',
    '3_ProbOfWorthless_Historical_IV'
]

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
    'Historical IV': '#9467bd',
    'Recovery Candidates': '#28a745',
    'Baseline': '#dc3545'
}

# Historical probability recovery analysis parameters
HISTORICAL_PEAK_THRESHOLDS = [0.80, 0.85, 0.90, 0.95]
CURRENT_PROB_BINS = [(0.60, 0.70), (0.70, 0.80), (0.80, 0.90)]
DTE_BINS = [(0, 7), (8, 14), (15, 21), (22, 28), (29, 35), (36, 999)]

print("="*80)
print("COMPREHENSIVE REPORT GENERATION")
print("="*80)
print()

# =============================================================================
# PART 1: LOAD DATA
# =============================================================================
print("STEP 1: Loading probability history data...")
df = pd.read_csv(DATA_FILE, sep='|')
print(f"  Loaded {len(df):,} total records")

# Filter to expired options
df_expired = df[df['StockPrice_AtExpiry'].notna()].copy()
print(f"  Filtered to {len(df_expired):,} expired options with outcomes")

# Calculate actual outcome
df_expired['ActualWorthless'] = (df_expired['StockPrice_AtExpiry'] > df_expired['StrikePrice']).astype(int)
worthless_count = df_expired['ActualWorthless'].sum()
print(f"  Actual outcomes: {worthless_count:,} expired worthless ({worthless_count/len(df_expired)*100:.1f}%)")
print()

# =============================================================================
# PART 2: VALIDATION ANALYSIS
# =============================================================================
print("STEP 2: Performing probability validation analysis...")

# Define probability bins
bins = np.linspace(0, 1, 11)
bin_labels = [f"{int(bins[i]*100)}-{int(bins[i+1]*100)}%" for i in range(len(bins)-1)]

calibration_results = {}
for prob_col in PROB_COLUMNS:
    df_valid = df_expired[df_expired[prob_col].notna()].copy()
    if len(df_valid) == 0:
        continue

    df_valid['ProbBin'] = pd.cut(df_valid[prob_col], bins=bins, labels=bin_labels, include_lowest=True)
    bin_stats = df_valid.groupby('ProbBin', observed=True).agg({
        prob_col: ['mean', 'count'],
        'ActualWorthless': 'mean'
    }).reset_index()

    bin_stats.columns = ['Bin', 'PredictedProb', 'Count', 'ActualRate']
    bin_stats['CalibrationError'] = bin_stats['ActualRate'] - bin_stats['PredictedProb']

    calibration_results[prob_col] = {
        'bin_stats': bin_stats,
        'n_valid': len(df_valid)
    }

# Calculate metrics
metrics_summary = []
for prob_col in PROB_COLUMNS:
    if prob_col not in calibration_results:
        continue

    df_valid = df_expired[df_expired[prob_col].notna()].copy()
    y_true = df_valid['ActualWorthless'].values
    y_pred = df_valid[prob_col].values
    y_pred_clipped = np.clip(y_pred, 1e-15, 1 - 1e-15)

    brier = brier_score_loss(y_true, y_pred)
    try:
        logloss = log_loss(y_true, y_pred_clipped)
    except:
        logloss = np.nan

    try:
        auc = roc_auc_score(y_true, y_pred)
    except:
        auc = np.nan

    bin_stats = calibration_results[prob_col]['bin_stats']
    mce = np.abs(bin_stats['CalibrationError']).mean()
    ece = np.sum(np.abs(bin_stats['CalibrationError']) * bin_stats['Count']) / bin_stats['Count'].sum()

    metrics_summary.append({
        'Method': PROB_LABELS[prob_col],
        'Column': prob_col,
        'N_Predictions': len(df_valid),
        'Brier_Score': brier,
        'Log_Loss': logloss,
        'AUC_ROC': auc,
        'Mean_Calibration_Error': mce,
        'Expected_Calibration_Error': ece
    })

df_metrics = pd.DataFrame(metrics_summary)

# Export validation results
for prob_col in PROB_COLUMNS:
    if prob_col not in calibration_results:
        continue
    bin_stats = calibration_results[prob_col]['bin_stats']
    output_file = VALIDATION_DIR / f'calibration_{prob_col}.csv'
    bin_stats.to_csv(output_file, sep='|', index=False)

metrics_file = VALIDATION_DIR / 'metrics_summary.csv'
df_metrics.to_csv(metrics_file, sep='|', index=False)
print(f"  ✓ Exported validation results to {VALIDATION_DIR}/")
print()

# =============================================================================
# PART 3: HISTORICAL PROBABILITY RECOVERY ANALYSIS
# =============================================================================
print("STEP 3: Performing historical probability recovery analysis...")

# Prepare data
df['Update_date'] = pd.to_datetime(df['Update_date'], errors='coerce')
df['StrikeDate'] = pd.to_datetime(df['StrikeDate'], errors='coerce')
df['DaysToExpiry'] = (df['StrikeDate'] - df['Update_date']).dt.days

df_expired_recovery = df[df['StockPrice_AtExpiry'].notna()].copy()
df_expired_recovery['ActualWorthless'] = (df_expired_recovery['StockPrice_AtExpiry'] > df_expired_recovery['StrikePrice']).astype(int)

# Identify recovery candidates
option_groups = df_expired_recovery.groupby('OptionName')
recovery_results = defaultdict(list)

for prob_col, prob_label in PROB_LABELS.items():
    for option_name, option_df in option_groups:
        option_df = option_df.sort_values('Update_date')

        if option_df[prob_col].isna().all():
            continue

        peak_prob = option_df[prob_col].max()

        for idx, row in option_df.iterrows():
            current_prob = row[prob_col]
            if pd.isna(current_prob):
                continue

            for bin_min, bin_max in CURRENT_PROB_BINS:
                if bin_min <= current_prob < bin_max:
                    dte = row['DaysToExpiry']
                    for dte_min, dte_max in DTE_BINS:
                        if dte_min <= dte <= dte_max:
                            for threshold in HISTORICAL_PEAK_THRESHOLDS:
                                is_recovery = peak_prob >= threshold
                                recovery_results[prob_col].append({
                                    'OptionName': option_name,
                                    'Stock': row['Name'],
                                    'Update_date': row['Update_date'],
                                    'DaysToExpiry': dte,
                                    'DTE_Bin': f'{dte_min}-{dte_max}' if dte_max < 999 else f'{dte_min}+',
                                    'CurrentProb': current_prob,
                                    'CurrentProb_Bin': f'{int(bin_min*100)}-{int(bin_max*100)}%',
                                    'PeakProb': peak_prob,
                                    'HistoricalPeakThreshold': threshold,
                                    'IsRecoveryCandidate': is_recovery,
                                    'ActualWorthless': row['ActualWorthless'],
                                    'ProbMethod': prob_label
                                })
                            break
                    break

# Combine results
all_results = []
for prob_col, results in recovery_results.items():
    all_results.extend(results)

df_results = pd.DataFrame(all_results)

# Calculate statistics
summary_stats = []
for threshold in df_results['HistoricalPeakThreshold'].unique():
    df_threshold = df_results[df_results['HistoricalPeakThreshold'] == threshold]

    for prob_method in df_threshold['ProbMethod'].unique():
        df_method = df_threshold[df_threshold['ProbMethod'] == prob_method]

        for current_bin in df_method['CurrentProb_Bin'].unique():
            df_bin = df_method[df_method['CurrentProb_Bin'] == current_bin]

            for dte_bin in df_bin['DTE_Bin'].unique():
                df_dte = df_bin[df_bin['DTE_Bin'] == dte_bin]

                if len(df_dte) == 0:
                    continue

                df_recovery = df_dte[df_dte['IsRecoveryCandidate'] == True]
                recovery_n = len(df_recovery)
                recovery_worthless_rate = df_recovery['ActualWorthless'].mean() if recovery_n > 0 else np.nan

                df_baseline = df_dte[df_dte['IsRecoveryCandidate'] == False]
                baseline_n = len(df_baseline)
                baseline_worthless_rate = df_baseline['ActualWorthless'].mean() if baseline_n > 0 else np.nan

                advantage = (recovery_worthless_rate - baseline_worthless_rate) * 100 if not pd.isna(recovery_worthless_rate) and not pd.isna(baseline_worthless_rate) else np.nan

                summary_stats.append({
                    'HistoricalPeakThreshold': threshold,
                    'ProbMethod': prob_method,
                    'CurrentProb_Bin': current_bin,
                    'DTE_Bin': dte_bin,
                    'Recovery_N': recovery_n,
                    'Recovery_WorthlessRate': recovery_worthless_rate,
                    'Baseline_N': baseline_n,
                    'Baseline_WorthlessRate': baseline_worthless_rate,
                    'Advantage_pp': advantage
                })

df_summary = pd.DataFrame(summary_stats)

# Calculate per-stock statistics
stock_stats = []
for threshold in df_results['HistoricalPeakThreshold'].unique():
    df_threshold = df_results[df_results['HistoricalPeakThreshold'] == threshold]

    for prob_method in df_threshold['ProbMethod'].unique():
        df_method = df_threshold[df_threshold['ProbMethod'] == prob_method]

        for stock in df_method['Stock'].unique():
            df_stock = df_method[df_method['Stock'] == stock]

            for current_bin in df_stock['CurrentProb_Bin'].unique():
                df_bin = df_stock[df_stock['CurrentProb_Bin'] == current_bin]

                for dte_bin in df_bin['DTE_Bin'].unique():
                    df_dte = df_bin[df_bin['DTE_Bin'] == dte_bin]

                    df_recovery = df_dte[df_dte['IsRecoveryCandidate'] == True]
                    recovery_n = len(df_recovery)
                    recovery_worthless_rate = df_recovery['ActualWorthless'].mean() if recovery_n > 0 else np.nan

                    df_baseline = df_dte[df_dte['IsRecoveryCandidate'] == False]
                    baseline_n = len(df_baseline)
                    baseline_worthless_rate = df_baseline['ActualWorthless'].mean() if baseline_n > 0 else np.nan

                    advantage = (recovery_worthless_rate - baseline_worthless_rate) * 100 if not pd.isna(recovery_worthless_rate) and not pd.isna(baseline_worthless_rate) else np.nan

                    if recovery_n > 0 or baseline_n > 0:
                        stock_stats.append({
                            'HistoricalPeakThreshold': threshold,
                            'Stock': stock,
                            'ProbMethod': prob_method,
                            'CurrentProb_Bin': current_bin,
                            'DTE_Bin': dte_bin,
                            'Recovery_N': recovery_n,
                            'Recovery_WorthlessRate': recovery_worthless_rate,
                            'Baseline_N': baseline_n,
                            'Baseline_WorthlessRate': baseline_worthless_rate,
                            'Advantage_pp': advantage
                        })

df_stock_stats = pd.DataFrame(stock_stats)

# Export recovery analysis results
summary_file = RECOVERY_DIR / 'probability_recovery_summary.csv'
df_summary.to_csv(summary_file, index=False)

stock_file = RECOVERY_DIR / 'probability_recovery_by_stock.csv'
df_stock_stats.to_csv(stock_file, index=False)

details_file = RECOVERY_DIR / 'probability_recovery_details.csv'
df_results.to_csv(details_file, index=False)

print(f"  ✓ Exported recovery analysis to {RECOVERY_DIR}/")
print()

# =============================================================================
# PART 4: GENERATE VALIDATION HTML REPORT
# =============================================================================
print("STEP 4: Generating probability validation report...")

OUTPUT_HTML_VALIDATION = Path(__file__).parent / 'probability_validation_report.html'

# Load full data for stock-level analysis
df_full = pd.read_csv(DATA_FILE, sep='|')
df_full['StrikeDate'] = pd.to_datetime(df_full['StrikeDate'], errors='coerce')
df_full['Update_date'] = pd.to_datetime(df_full['Update_date'], errors='coerce')
df_full['DaysToExpiry'] = (df_full['StrikeDate'] - df_full['Update_date']).dt.days

unique_stocks = sorted([s for s in df_full['Name'].unique() if s != 'nan'])

# Prepare stock calibration data
stock_calibration_data = {}
for stock in unique_stocks:
    stock_calibration_data[stock] = {}
    df_stock = df_full[df_full['Name'] == stock]

    for prob_col in PROB_COLUMNS:
        if prob_col in df_stock.columns:
            df_stock_valid = df_stock[df_stock[prob_col].notna()].copy()
            df_stock_valid['ActualWorthless'] = (df_stock_valid['StockPrice_AtExpiry'] > df_stock_valid['StrikePrice']).astype(int)
            df_stock_valid['ProbBin'] = pd.cut(df_stock_valid[prob_col], bins=bins, labels=bin_labels, include_lowest=True)

            bin_stats = df_stock_valid.groupby('ProbBin', observed=True).agg({
                prob_col: ['mean', 'count'],
                'ActualWorthless': 'mean'
            }).reset_index()

            if len(bin_stats) > 0:
                bin_stats.columns = ['Bin', 'PredictedProb', 'Count', 'ActualRate']
                stock_calibration_data[stock][PROB_LABELS[prob_col]] = {
                    'predicted': bin_stats['PredictedProb'].tolist(),
                    'actual': bin_stats['ActualRate'].tolist(),
                    'count': bin_stats['Count'].tolist()
                }

# Prepare aggregated data
all_stocks_data = {}
for prob_col in PROB_COLUMNS:
    if prob_col in calibration_results:
        df_calib = calibration_results[prob_col]['bin_stats']
        all_stocks_data[PROB_LABELS[prob_col]] = {
            'predicted': df_calib['PredictedProb'].tolist(),
            'actual': df_calib['ActualRate'].tolist(),
            'count': df_calib['Count'].tolist()
        }

stock_data_json = {}
for stock in sorted(unique_stocks):
    if stock in stock_calibration_data:
        stock_data_json[stock] = stock_calibration_data[stock]
stock_data_json['All Stocks'] = all_stocks_data

# Create metrics chart
fig_metrics = go.Figure()
for idx, row in df_metrics.iterrows():
    fig_metrics.add_trace(go.Bar(
        x=['Brier Score'],
        y=[row['Brier_Score']],
        name=row['Method'],
        marker_color=COLORS[row['Method']],
        visible=True if idx == 0 else 'legendonly'
    ))

best_method = df_metrics.loc[df_metrics['Brier_Score'].idxmin(), 'Method']
best_brier = df_metrics.loc[df_metrics['Brier_Score'].idxmin(), 'Brier_Score']
best_ece = df_metrics.loc[df_metrics['Expected_Calibration_Error'].idxmin(), 'Expected_Calibration_Error']

html_validation = f"""
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
        }}
        .finding-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .winner-box {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Probability Prediction Validation Report</h1>
        <p>Empirical Analysis of {len(df_expired):,} Expired Options</p>
    </div>

    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="key-findings">
            <div class="finding-card">
                <h3>Sample Size</h3>
                <div class="value">{len(df_expired):,}</div>
                <div>Expired Options</div>
            </div>
            <div class="finding-card">
                <h3>Success Rate</h3>
                <div class="value">{worthless_count/len(df_expired)*100:.1f}%</div>
                <div>Expired Worthless</div>
            </div>
            <div class="finding-card">
                <h3>Best Method</h3>
                <div class="value">🏆</div>
                <div>{best_method}</div>
            </div>
        </div>

        <div class="winner-box">
            <h3>Winner: {best_method}</h3>
            <ul>
                <li><strong>Brier Score:</strong> {best_brier:.4f} (lower is better)</li>
                <li><strong>Calibration Error:</strong> {best_ece:.4f} (only {best_ece*100:.2f}pp off)</li>
            </ul>
        </div>
    </div>

    <div class="chart-container">
        <h2>Performance Metrics</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #2c3e50; color: white;">
                    <th style="padding: 10px; text-align: left;">Method</th>
                    <th style="padding: 10px; text-align: right;">Brier Score</th>
                    <th style="padding: 10px; text-align: right;">Log Loss</th>
                    <th style="padding: 10px; text-align: right;">AUC-ROC</th>
                    <th style="padding: 10px; text-align: right;">Calibration Error</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''<tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px;">{row['Method']}</td>
                    <td style="padding: 10px; text-align: right;">{row['Brier_Score']:.4f}</td>
                    <td style="padding: 10px; text-align: right;">{row['Log_Loss']:.4f}</td>
                    <td style="padding: 10px; text-align: right;">{row['AUC_ROC']:.4f}</td>
                    <td style="padding: 10px; text-align: right;">{row['Expected_Calibration_Error']:.4f}</td>
                </tr>''' for _, row in df_metrics.iterrows()])}
            </tbody>
        </table>
    </div>

    <footer style="text-align: center; padding: 20px; color: #7f8c8d; margin-top: 40px;">
        <p>Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>
"""

with open(OUTPUT_HTML_VALIDATION, 'w', encoding='utf-8') as f:
    f.write(html_validation)

print(f"  ✓ Generated {OUTPUT_HTML_VALIDATION.name}")
print()

# =============================================================================
# PART 5: GENERATE PROBABILITY RECOVERY HTML REPORT
# =============================================================================
print("STEP 5: Generating historical probability recovery analysis report...")

OUTPUT_HTML_RECOVERY = Path(__file__).parent / 'probability_recovery_analysis_report.html'

# Prepare data for interactive filtering
methods = sorted(df_summary['ProbMethod'].unique())
prob_bins = sorted(df_summary['CurrentProb_Bin'].unique())
dte_bins_order = ['0-7', '8-14', '15-21', '22-28', '29-35', '36+']
dte_bins = [b for b in dte_bins_order if b in df_summary['DTE_Bin'].values]
thresholds = sorted(df_summary['HistoricalPeakThreshold'].unique())

top_scenarios = df_summary[df_summary['Recovery_N'] >= 1000].nlargest(5, 'Advantage_pp')

best_scenario = top_scenarios.iloc[0] if len(top_scenarios) > 0 else df_summary.iloc[0]
best_advantage = best_scenario['Advantage_pp']

# Prepare chart data for JavaScript
chart_data = {}
for threshold in thresholds:
    chart_data[str(threshold)] = {}
    df_threshold = df_summary[df_summary['HistoricalPeakThreshold'] == threshold]

    for method in methods:
        chart_data[str(threshold)][method] = {}
        df_method = df_threshold[df_threshold['ProbMethod'] == method]

        for prob_bin in prob_bins:
            chart_data[str(threshold)][method][prob_bin] = {}
            df_pb = df_method[df_method['CurrentProb_Bin'] == prob_bin]

            for dte_bin in dte_bins:
                df_dte = df_pb[df_pb['DTE_Bin'] == dte_bin]
                if len(df_dte) > 0:
                    row = df_dte.iloc[0]
                    chart_data[str(threshold)][method][prob_bin][dte_bin] = {
                        'recovery_n': int(row['Recovery_N']),
                        'recovery_rate': float(row['Recovery_WorthlessRate']) if pd.notna(row['Recovery_WorthlessRate']) else None,
                        'baseline_n': int(row['Baseline_N']),
                        'baseline_rate': float(row['Baseline_WorthlessRate']) if pd.notna(row['Baseline_WorthlessRate']) else None,
                        'advantage': float(row['Advantage_pp']) if pd.notna(row['Advantage_pp']) else None
                    }

chart_data_json = json.dumps(chart_data)

# Load stocks for dropdown
unique_stocks_recovery = sorted(df_stock_stats['Stock'].unique())

html_recovery = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historical Probability Recovery Analysis</title>
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
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #28a745;
            padding-bottom: 10px;
        }}
        .key-findings {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .finding-card {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
        }}
        .finding-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .controls {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .control-group {{
            display: flex;
            flex-direction: column;
        }}
        .control-group label {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .control-group select {{
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #ced4da;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Historical Probability Recovery Analysis</h1>
        <p>Options with Earlier High Probability Peaks</p>
    </div>

    <div class="summary">
        <h2>Executive Summary</h2>
        <p>This analysis examines options that previously reached high probability levels (80%+) but have since dropped.
        The question: do they still expire worthless more often than their current probability suggests?</p>

        <div class="key-findings">
            <div class="finding-card">
                <h3>Best Advantage</h3>
                <div class="value">+{best_advantage:.1f}pp</div>
            </div>
            <div class="finding-card">
                <h3>Recovery Candidates</h3>
                <div class="value">{int(df_summary['Recovery_N'].sum()):,}</div>
                <div>Total Analyzed</div>
            </div>
            <div class="finding-card">
                <h3>Success Rate</h3>
                <div class="value">{df_summary['Recovery_WorthlessRate'].mean()*100:.1f}%</div>
                <div>Average Recovery Rate</div>
            </div>
        </div>
    </div>

    <div class="chart-container">
        <h2>Interactive Analysis</h2>
        <div class="controls">
            <div class="control-group">
                <label for="thresholdSelect">Historical Peak Threshold:</label>
                <select id="thresholdSelect">
                    {''.join([f'<option value="{t}" {"selected" if t == 0.90 else ""}>{int(t*100)}%+</option>' for t in thresholds])}
                </select>
            </div>
            <div class="control-group">
                <label for="methodSelect">Probability Method:</label>
                <select id="methodSelect">
                    {''.join([f'<option value="{m}">{m}</option>' for m in methods])}
                </select>
            </div>
            <div class="control-group">
                <label for="probBinSelect">Current Probability:</label>
                <select id="probBinSelect">
                    {''.join([f'<option value="{p}">{p}</option>' for p in prob_bins])}
                </select>
            </div>
        </div>
        <div id="comparisonChart"></div>
    </div>

    <footer style="text-align: center; padding: 20px; color: #7f8c8d; margin-top: 40px;">
        <p>Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Analysis Period: 2024-2025 | {len(df_expired_recovery):,} Expired Options</p>
    </footer>

    <script>
    var chartData = {chart_data_json};
    var colorRecovery = '#28a745';
    var colorBaseline = '#dc3545';

    function updateChart() {{
        var threshold = document.getElementById('thresholdSelect').value;
        var method = document.getElementById('methodSelect').value;
        var probBin = document.getElementById('probBinSelect').value;

        if (!chartData[threshold] || !chartData[threshold][method] || !chartData[threshold][method][probBin]) {{
            document.getElementById('comparisonChart').innerHTML = '<p style="text-align: center; color: #dc3545;">No data available for this combination</p>';
            return;
        }}

        var data = chartData[threshold][method][probBin];
        var dteBins = {json.dumps(dte_bins)};
        dteBins = dteBins.slice().reverse();

        var recoveryRates = [];
        var baselineRates = [];
        var recoveryText = [];
        var baselineText = [];

        for (var i = 0; i < dteBins.length; i++) {{
            var dte = dteBins[i];
            if (data[dte]) {{
                recoveryRates.push(data[dte].recovery_rate !== null ? data[dte].recovery_rate * 100 : null);
                baselineRates.push(data[dte].baseline_rate !== null ? data[dte].baseline_rate * 100 : null);
                recoveryText.push(data[dte].recovery_rate !== null ? data[dte].recovery_rate.toFixed(1) + '% (' + data[dte].recovery_n.toLocaleString() + ')' : 'N/A');
                baselineText.push(data[dte].baseline_rate !== null ? data[dte].baseline_rate.toFixed(1) + '% (' + data[dte].baseline_n.toLocaleString() + ')' : 'N/A');
            }} else {{
                recoveryRates.push(null);
                baselineRates.push(null);
                recoveryText.push('N/A');
                baselineText.push('N/A');
            }}
        }}

        var traces = [
            {{
                x: dteBins,
                y: recoveryRates,
                name: 'Recovery Candidates',
                type: 'bar',
                marker: {{color: colorRecovery}},
                text: recoveryText,
                textposition: 'outside',
                hovertemplate: '%{{x}} days<br>Worthless Rate: %{{y:.1f}}%<br>%{{text}}<extra></extra>'
            }},
            {{
                x: dteBins,
                y: baselineRates,
                name: 'Baseline',
                type: 'bar',
                marker: {{color: colorBaseline}},
                text: baselineText,
                textposition: 'outside',
                hovertemplate: '%{{x}} days<br>Worthless Rate: %{{y:.1f}}%<br>%{{text}}<extra></extra>'
            }}
        ];

        var layout = {{
            title: method + ' - ' + probBin + ' (Threshold: ' + Math.round(parseFloat(threshold) * 100) + '%+)',
            xaxis: {{title: 'Days to Expiry (Calendar Days)'}},
            yaxis: {{title: 'Worthless Rate (%)'}},
            barmode: 'group',
            height: 500
        }};

        Plotly.newPlot('comparisonChart', traces, layout);
    }}

    document.getElementById('thresholdSelect').addEventListener('change', updateChart);
    document.getElementById('methodSelect').addEventListener('change', updateChart);
    document.getElementById('probBinSelect').addEventListener('change', updateChart);

    updateChart();
    </script>
</body>
</html>
"""

with open(OUTPUT_HTML_RECOVERY, 'w', encoding='utf-8') as f:
    f.write(html_recovery)

print(f"  ✓ Generated {OUTPUT_HTML_RECOVERY.name}")
print()

# =============================================================================
# COMPLETION
# =============================================================================
print("="*80)
print("REPORT GENERATION COMPLETE")
print("="*80)
print()
print("Generated files:")
print(f"  • Validation analysis: {VALIDATION_DIR}/")
print(f"  • Recovery analysis: {RECOVERY_DIR}/")
print(f"  • Validation report: {OUTPUT_HTML_VALIDATION}")
print(f"  • Recovery report: {OUTPUT_HTML_RECOVERY}")
print()
print("Next steps: Open the HTML files in your browser to view the reports")
print()
