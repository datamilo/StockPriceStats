#!/usr/bin/env python3
"""
Probability Prediction Validation Analysis

This script validates the accuracy of probability predictions by comparing
predicted probabilities against actual outcomes for expired options.

Analysis includes:
- Calibration analysis (predicted vs actual by bin)
- Performance metrics (Brier score, log loss, AUC-ROC)
- Comparative analysis of all 5 probability methods
- Visualizations (calibration curves, reliability diagrams)

Author: Claude Code
Date: November 12, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import brier_score_loss, roc_auc_score, log_loss
import warnings
warnings.filterwarnings('ignore')

# Configuration
INPUT_FILE = Path(__file__).parent / 'probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'
OUTPUT_DIR.mkdir(exist_ok=True)

# Probability columns to validate
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

print("="*80)
print("PROBABILITY PREDICTION VALIDATION ANALYSIS")
print("="*80)
print()

# =============================================================================
# 1. LOAD AND PREPARE DATA
# =============================================================================
print("STEP 1: Loading enriched probability history...")
df = pd.read_csv(INPUT_FILE, sep='|')
print(f"  Loaded {len(df):,} total records")

# Filter to expired options (those with StockPrice_AtExpiry)
df_expired = df[df['StockPrice_AtExpiry'].notna()].copy()
print(f"  Filtered to {len(df_expired):,} expired options with known outcomes")

# Calculate actual outcome
df_expired['ActualWorthless'] = (df_expired['StockPrice_AtExpiry'] > df_expired['StrikePrice']).astype(int)
worthless_count = df_expired['ActualWorthless'].sum()
print(f"  Actual outcomes: {worthless_count:,} expired worthless ({worthless_count/len(df_expired)*100:.1f}%)")
print()

# =============================================================================
# 2. CALIBRATION ANALYSIS
# =============================================================================
print("STEP 2: Performing calibration analysis...")

# Define bins
bins = np.linspace(0, 1, 11)  # 0-10%, 10-20%, ..., 90-100%
bin_labels = [f"{int(bins[i]*100)}-{int(bins[i+1]*100)}%" for i in range(len(bins)-1)]

calibration_results = {}

for prob_col in PROB_COLUMNS:
    print(f"  Analyzing: {PROB_LABELS[prob_col]}...")

    # Filter to valid predictions
    df_valid = df_expired[df_expired[prob_col].notna()].copy()

    if len(df_valid) == 0:
        print(f"    WARNING: No valid predictions for {prob_col}")
        continue

    # Bin predictions
    df_valid['ProbBin'] = pd.cut(df_valid[prob_col], bins=bins, labels=bin_labels, include_lowest=True)

    # Calculate statistics per bin
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

print()

# =============================================================================
# 3. PERFORMANCE METRICS
# =============================================================================
print("STEP 3: Calculating performance metrics...")

metrics_summary = []

for prob_col in PROB_COLUMNS:
    if prob_col not in calibration_results:
        continue

    # Filter to valid predictions
    df_valid = df_expired[df_expired[prob_col].notna()].copy()
    y_true = df_valid['ActualWorthless'].values
    y_pred = df_valid[prob_col].values

    # Clip predictions to avoid log(0) errors
    y_pred_clipped = np.clip(y_pred, 1e-15, 1 - 1e-15)

    # Calculate metrics
    brier = brier_score_loss(y_true, y_pred)
    try:
        logloss = log_loss(y_true, y_pred_clipped)
    except:
        logloss = np.nan

    try:
        auc = roc_auc_score(y_true, y_pred)
    except:
        auc = np.nan

    # Mean calibration error
    bin_stats = calibration_results[prob_col]['bin_stats']
    mce = np.abs(bin_stats['CalibrationError']).mean()

    # Expected calibration error (weighted by count)
    ece = np.sum(
        np.abs(bin_stats['CalibrationError']) * bin_stats['Count']
    ) / bin_stats['Count'].sum()

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
print("\n" + "="*80)
print("PERFORMANCE METRICS SUMMARY")
print("="*80)
print(df_metrics.to_string(index=False))
print()

# =============================================================================
# 4. GENERATE VISUALIZATIONS
# =============================================================================
print("STEP 4: Generating visualizations...")

# 4A. Calibration Curves
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

for idx, prob_col in enumerate(PROB_COLUMNS):
    if prob_col not in calibration_results:
        axes[idx].text(0.5, 0.5, 'No data', ha='center', va='center')
        axes[idx].set_title(PROB_LABELS[prob_col])
        continue

    bin_stats = calibration_results[prob_col]['bin_stats']

    ax = axes[idx]

    # Plot perfect calibration line
    ax.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration', alpha=0.3)

    # Plot actual calibration
    x = bin_stats['PredictedProb'].values
    y = bin_stats['ActualRate'].values
    sizes = bin_stats['Count'].values / bin_stats['Count'].max() * 300

    ax.scatter(x, y, s=sizes, alpha=0.6, label='Actual')
    ax.plot(x, y, 'b-', alpha=0.5)

    ax.set_xlabel('Predicted Probability')
    ax.set_ylabel('Actual Rate')
    ax.set_title(PROB_LABELS[prob_col])
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

# Remove extra subplot
axes[-1].remove()

plt.tight_layout()
calibration_plot_path = OUTPUT_DIR / 'calibration_curves.png'
plt.savefig(calibration_plot_path, dpi=150, bbox_inches='tight')
print(f"  Saved calibration curves: {calibration_plot_path}")
plt.close()

# 4B. Reliability Diagram with histogram
fig, axes = plt.subplots(len(PROB_COLUMNS), 2, figsize=(14, 4*len(PROB_COLUMNS)))

for idx, prob_col in enumerate(PROB_COLUMNS):
    if prob_col not in calibration_results:
        continue

    bin_stats = calibration_results[prob_col]['bin_stats']
    df_valid = df_expired[df_expired[prob_col].notna()].copy()

    # Left: Reliability diagram
    ax1 = axes[idx, 0]
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.3)

    x = bin_stats['PredictedProb'].values
    y = bin_stats['ActualRate'].values
    sizes = bin_stats['Count'].values / bin_stats['Count'].max() * 300

    ax1.scatter(x, y, s=sizes, alpha=0.6)
    ax1.plot(x, y, 'b-', alpha=0.5)

    ax1.set_xlabel('Predicted Probability')
    ax1.set_ylabel('Observed Frequency')
    ax1.set_title(f'{PROB_LABELS[prob_col]} - Reliability')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)

    # Right: Distribution of predictions
    ax2 = axes[idx, 1]
    ax2.hist(df_valid[prob_col], bins=50, alpha=0.6, edgecolor='black')
    ax2.set_xlabel('Predicted Probability')
    ax2.set_ylabel('Count')
    ax2.set_title(f'{PROB_LABELS[prob_col]} - Distribution')
    ax2.grid(True, alpha=0.3)

plt.tight_layout()
reliability_plot_path = OUTPUT_DIR / 'reliability_diagrams.png'
plt.savefig(reliability_plot_path, dpi=150, bbox_inches='tight')
print(f"  Saved reliability diagrams: {reliability_plot_path}")
plt.close()

# 4C. Metrics Comparison Bar Chart
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

metrics_to_plot = ['Brier_Score', 'Log_Loss', 'AUC_ROC', 'Expected_Calibration_Error']
titles = ['Brier Score (lower is better)', 'Log Loss (lower is better)',
          'AUC-ROC (higher is better)', 'Expected Calibration Error (lower is better)']

for idx, (metric, title) in enumerate(zip(metrics_to_plot, titles)):
    ax = axes[idx // 2, idx % 2]

    data = df_metrics[['Method', metric]].dropna()
    if len(data) == 0:
        continue

    data = data.sort_values(metric, ascending=(metric != 'AUC_ROC'))

    ax.barh(data['Method'], data[metric], alpha=0.7)
    ax.set_xlabel(metric)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
metrics_plot_path = OUTPUT_DIR / 'metrics_comparison.png'
plt.savefig(metrics_plot_path, dpi=150, bbox_inches='tight')
print(f"  Saved metrics comparison: {metrics_plot_path}")
plt.close()

print()

# =============================================================================
# 5. EXPORT RESULTS
# =============================================================================
print("STEP 5: Exporting results...")

# Export calibration data for each method
for prob_col in PROB_COLUMNS:
    if prob_col not in calibration_results:
        continue

    bin_stats = calibration_results[prob_col]['bin_stats']
    output_file = OUTPUT_DIR / f'calibration_{prob_col}.csv'
    bin_stats.to_csv(output_file, sep='|', index=False)
    print(f"  Saved {PROB_LABELS[prob_col]} calibration: {output_file}")

# Export metrics summary
metrics_file = OUTPUT_DIR / 'metrics_summary.csv'
df_metrics.to_csv(metrics_file, sep='|', index=False)
print(f"  Saved metrics summary: {metrics_file}")

print()

# =============================================================================
# 6. PRINT SUMMARY FINDINGS
# =============================================================================
print("="*80)
print("KEY FINDINGS")
print("="*80)
print()

# Best method by Brier score
best_brier = df_metrics.loc[df_metrics['Brier_Score'].idxmin()]
print(f"Best Brier Score: {best_brier['Method']} ({best_brier['Brier_Score']:.4f})")

# Best method by AUC
if df_metrics['AUC_ROC'].notna().any():
    best_auc = df_metrics.loc[df_metrics['AUC_ROC'].idxmax()]
    print(f"Best AUC-ROC: {best_auc['Method']} ({best_auc['AUC_ROC']:.4f})")

# Best method by calibration
best_cal = df_metrics.loc[df_metrics['Expected_Calibration_Error'].idxmin()]
print(f"Best Calibration: {best_cal['Method']} ({best_cal['Expected_Calibration_Error']:.4f})")

print()
print("="*80)
print("VALIDATION COMPLETE")
print("="*80)
print(f"Results saved to: {OUTPUT_DIR}")
print()
