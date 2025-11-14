#!/usr/bin/env python3
"""
Master Script: Generate Complete Probability History with All Enrichments

Consolidates two steps into a single workflow:
1. Generate base probability predictions (from probability_history_generator_FULL_HISTORICAL.py)
2. Enrich with strike & price data (from build_probability_history_complete.py)

Output: probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv

This is the ONLY script needed to generate the enriched probability history file.

Author: Claude Code
Date: November 14, 2025
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import json
import os
import sys
from pathlib import Path
import scipy.stats as st
import requests
import multiprocessing as mp
from functools import partial
from tqdm import tqdm

# Import local utilities
from utils import (
    calculate_business_days_between,
    calculate_business_days_vectorized,
    TRADING_DAYS_PER_YEAR,
    get_path_config
)

try:
    PATH_CONFIG = get_path_config()
except (ImportError, FileNotFoundError):
    PATH_CONFIG = None

# Parallel processing configuration
N_JOBS = max(1, mp.cpu_count() - 1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION & PATHS
# =============================================================================

# Constants
STOCK_VALUE_LIMIT = 100000
COURTAGE = 150

# Define output file paths
OPTIONS_DIR = Path(__file__).parent
INTERMEDIATE_FILE = OPTIONS_DIR / 'probability_history_FULL_HISTORICAL.csv'
FINAL_OUTPUT_FILE = OPTIONS_DIR / 'probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv'

# Get paths from config or use fallback
if PATH_CONFIG:
    PROJECT_ROOT = OPTIONS_DIR
    OUTPUT_DIR = Path(PATH_CONFIG.get_output_dir())
    WEEKLY_MAINT_DIR = Path(PATH_CONFIG.get_weekly_maintenance_dir())
    ONEDRIVE_ROOT = Path(PATH_CONFIG.get_probability_history_onedrive_dir())
    NASDAQ_DATA_DIR = ONEDRIVE_ROOT / 'Nasdaq_Options_Data'
    # OneDrive data file paths (primary source)
    OPTIONS_DATA_PATH = PATH_CONFIG.get_options_data_parquet()
    PRICE_DATA_PATH = PATH_CONFIG.get_price_data_parquet()
    IV_HISTORICAL_PATH = PATH_CONFIG.get_iv_historical_parquet()
else:
    # Fallback paths (Windows and WSL)
    PROJECT_ROOT = OPTIONS_DIR
    OUTPUT_DIR = OPTIONS_DIR / 'output'

    if sys.platform == 'win32':
        # Windows
        ONEDRIVE_ROOT = Path('C:/Users/Gustaf/OneDrive')
    else:
        # WSL/Linux
        ONEDRIVE_ROOT = Path('/mnt/c/Users/Gustaf/OneDrive')

    WEEKLY_MAINT_DIR = ONEDRIVE_ROOT / 'OptionsData' / 'WeeklyMaintenance'
    NASDAQ_DATA_DIR = ONEDRIVE_ROOT / 'Nasdaq_Options_Data'
    # OneDrive data file paths (fallback)
    OPTIONS_DATA_PATH = ONEDRIVE_ROOT / 'OptionsData' / 'All_Options_Data.parquet'
    PRICE_DATA_PATH = ONEDRIVE_ROOT / 'OptionsData' / 'price_data_all.parquet'
    IV_HISTORICAL_PATH = ONEDRIVE_ROOT / 'OptionsData' / 'Implied_Volatility_Historical_ALL.parquet'

# Required calibration files from weekly maintenance
CALIBRATION_FILES = {
    'stats_per_stock': WEEKLY_MAINT_DIR / 'stats_per_stock.csv',
    'bayesian_params': WEEKLY_MAINT_DIR / 'ProbWorthless_Bayesian_IsoCal_Parameters.json',
    'bayesian_lookup': WEEKLY_MAINT_DIR / 'ProbWorthless_Bayesian_IsoCal_ExpiryBins_and_ProbBins.csv',
    'bayesian_losses': WEEKLY_MAINT_DIR / 'Stats_Historical_Losses_using_ProbWorthless_Bayesian_IsoCal.csv',
    'iv_accuracy': WEEKLY_MAINT_DIR / 'IV_Closest_to_Strike_Accuracy_Per_Day_to_Expiry.csv',
    'brier_wins': WEEKLY_MAINT_DIR / 'brier_score_wins.json'
}

# =============================================================================
# PART 1: PROBABILITY GENERATION FUNCTIONS
# =============================================================================

def load_input_data():
    """Load required input data files from OneDrive"""
    logger.info("[LOAD] Loading input data files from OneDrive...")

    options_path = Path(OPTIONS_DATA_PATH)
    if not options_path.exists():
        raise FileNotFoundError(f"Required file not found: {options_path}")

    df_options = pd.read_parquet(options_path)
    df_options['ExpiryDate'] = pd.to_datetime(df_options['ExpiryDate'])
    df_options['Update_date'] = pd.to_datetime(df_options['Update_date'])
    logger.info(f"  Loaded {len(df_options):,} options records")

    stock_path = Path(PRICE_DATA_PATH)
    if not stock_path.exists():
        raise FileNotFoundError(f"Required file not found: {stock_path}")

    df_stock = pd.read_parquet(stock_path)
    df_stock['date'] = pd.to_datetime(df_stock['date'])
    df_stock = df_stock[['date', 'name', 'close']].copy()
    df_stock.columns = ['Update_date', 'Name', 'StockPrice']
    logger.info(f"  Loaded {len(df_stock):,} stock price records")

    iv_path = Path(IV_HISTORICAL_PATH)
    if not iv_path.exists():
        raise FileNotFoundError(f"Required file not found: {iv_path}")

    df_iv = pd.read_parquet(iv_path)
    df_iv['Update_date'] = pd.to_datetime(df_iv['Update_date'])
    df_iv['ExpiryDate'] = pd.to_datetime(df_iv['ExpiryDate'])
    logger.info(f"  Loaded {len(df_iv):,} IV historical records")

    return df_options, df_stock, df_iv


def load_calibration_files():
    """Load all required calibration files from weekly maintenance"""
    logger.info("[LOAD] Loading calibration files from weekly maintenance...")

    calibration_data = {}

    # Check all files exist
    missing_files = []
    for name, path in CALIBRATION_FILES.items():
        if not path.exists():
            missing_files.append(f"{name}: {path}")

    if missing_files:
        raise FileNotFoundError(
            f"Missing required calibration files:\n" +
            "\n".join(f"  - {f}" for f in missing_files)
        )

    # Load CSV files
    calibration_data['stats_per_stock'] = pd.read_csv(CALIBRATION_FILES['stats_per_stock'], sep='|')
    calibration_data['stats_per_stock'] = calibration_data['stats_per_stock'].loc[
        calibration_data['stats_per_stock']['count'] >= 5
    ]

    calibration_data['bayesian_lookup'] = pd.read_csv(CALIBRATION_FILES['bayesian_lookup'], sep='|')
    calibration_data['bayesian_losses'] = pd.read_csv(CALIBRATION_FILES['bayesian_losses'], sep='|')

    calibration_data['iv_accuracy'] = pd.read_csv(CALIBRATION_FILES['iv_accuracy'], sep='|')
    calibration_data['iv_accuracy'] = calibration_data['iv_accuracy'].loc[
        calibration_data['iv_accuracy']['SampleSize'] >= 5
    ]

    # Load JSON files
    with open(CALIBRATION_FILES['bayesian_params'], 'r') as f:
        params = json.load(f)

    def restore_inf(obj):
        if isinstance(obj, list):
            return [restore_inf(x) for x in obj]
        if isinstance(obj, str) and obj == "Infinity":
            return np.inf
        return obj

    calibration_data['bayesian_params'] = {
        'TIME_BINS': restore_inf(params['TIME_BINS']),
        'TIME_LABELS': params['TIME_LABELS'],
        'PROB_EDGES': params['PROB_EDGES'],
        'PROB_LABELS': params['PROB_LABELS']
    }

    with open(CALIBRATION_FILES['brier_wins'], 'r') as f:
        wins = json.load(f)

    total = sum(wins.values())
    calibration_data['brier_weights'] = {method: wins[method] / total for method in wins}

    logger.info("  Loaded all calibration files")
    return calibration_data


def download_risk_free_rate():
    """Download current Swedish 10-year bond rate from DI.se"""
    logger.info("[DOWNLOAD] Fetching Swedish 10-year bond rate...")

    import re
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def is_valid_number(text):
        if not text:
            return False
        pattern = r'^-?\d+([.,]\d+)?$'
        return bool(re.match(pattern, text.strip()))

    url = "https://www.di.se/market/instrument-history/33383/"
    headers = {
        "Referer": "https://www.di.se/rantor/stat-10y-33383/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        raw_points = data.get("points", [])

        df_bond = pd.DataFrame(raw_points, columns=["timestamp_ms", "value"])
        df_bond["date"] = pd.to_datetime(df_bond["timestamp_ms"], unit='ms').dt.date
        df_bond = df_bond[["date", "value"]]
        df_bond["date"] = pd.to_datetime(df_bond["date"])
        df_bond.columns = ['Update_date', 'interest_rate']
        df_bond['interest_rate'] = df_bond['interest_rate'] / 100

        has_todays_data = len(df_bond.loc[df_bond['Update_date'] == today]) > 0

        if not has_todays_data and len(df_bond) > 0:
            most_recent_date = df_bond['Update_date'].max()
            most_recent_rate = df_bond.loc[df_bond['Update_date'] == most_recent_date, 'interest_rate'].iloc[0]
            df_bond.loc[len(df_bond)] = [today, most_recent_rate]
            logger.info(f"  Using most recent rate from {most_recent_date.date()}")
        else:
            logger.info(f"  Successfully loaded interest rate data")

        return df_bond

    except Exception as e:
        logger.error(f"  Error loading interest rate data: {e}")
        raise ValueError(f"Could not download risk-free interest rate data: {e}")


def parallel_apply(df, func, desc="Processing", **kwargs):
    """Apply a function to DataFrame rows in parallel with progress bar"""
    from joblib import Parallel, delayed

    results = Parallel(n_jobs=N_JOBS, backend='threading')(
        delayed(func)(row, **kwargs)
        for idx, row in tqdm(df.iterrows(), total=len(df), desc=desc)
    )
    return pd.Series(results, index=df.index)


def calculate_black_scholes_probability(row):
    """Calculate probability of worthlessness using Black-Scholes formula"""
    S = row['StockPrice']
    K = row['StrikePrice']
    T = (row['ExpiryDate'] - row['Update_date']).days / TRADING_DAYS_PER_YEAR
    r = row['interest_rate']
    vol = row['ImpliedVolatility']

    if T > 0:
        d1 = (np.log(S/K) + (r + vol**2/2)*T) / (vol*np.sqrt(T))
        d2 = d1 - vol*np.sqrt(T)
        prob_worthless = (100 - (st.norm.cdf(-d2)) * 100) / 100
    else:
        prob_worthless = np.nan

    return prob_worthless


def apply_bias_correction(df, stats_per_stock):
    """Apply per-bin bias correction to raw probability estimates"""
    df_with_stats = df.merge(stats_per_stock, on=['Name', 'ExpiryBin', 'ProbBin'], how='left')
    correction = df_with_stats['freq_actual'] - df_with_stats['avg_pred']
    calibrated = df_with_stats['ProbOfWorthless'] + correction
    calibrated = calibrated.where(df_with_stats['count'].notna(), df['ProbOfWorthless'])
    calibrated = calibrated.clip(0, 1)
    return calibrated


def calculate_historical_iv_probability(row, accuracy_df):
    """Estimate probability using historical IV accuracy tables"""
    stock_price = row['StockPrice']
    strike = row['StrikePrice']
    iv = row['ImpliedVolatilityUntilExpiry_Median']
    expiry_bin = row['ExpiryBin']
    name = row['Name']

    if pd.isna(expiry_bin) or iv == 0:
        return np.nan

    distance = stock_price - strike
    iv_range = stock_price * iv
    pct_reduction_needed = 1 - (distance / iv_range)
    pct_reduction_needed = min(max(pct_reduction_needed, 0), 0.9)

    iv_buckets = [0] + [i / 100 for i in range(10, 95, 5)]
    nearest_bucket = min(iv_buckets, key=lambda x: abs(x - pct_reduction_needed))

    if nearest_bucket == 0:
        col = 'Accuracy_on_ExpiryDate_Lower_Bound'
    else:
        col = f'Accuracy_on_ExpiryDate_Lower_Bound_Minus_{int(nearest_bucket * 100)}%'

    try:
        prob = accuracy_df.loc[
            (accuracy_df['Name'] == name) & (accuracy_df['ExpiryBin'] == expiry_bin),
            col
        ].values[0]
        return prob
    except (IndexError, KeyError):
        return np.nan


def calculate_weighted_average(row, weights):
    """Calculate weighted average of multiple probability methods"""
    weighted_sum = 0
    total_weight = 0

    for col, weight in weights.items():
        val = row[col]
        if pd.notna(val):
            weighted_sum += val * weight
            total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else np.nan


# =============================================================================
# STEP 1: GENERATE BASE PROBABILITIES
# =============================================================================

def generate_base_probabilities():
    """Generate probability_history_FULL_HISTORICAL.csv"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("STEP 1: GENERATING BASE PROBABILITY PREDICTIONS")
    logger.info("=" * 80)
    logger.info("")

    # Load all data
    df_options, df_stock, df_iv_hist = load_input_data()
    calibration = load_calibration_files()
    df_bond = download_risk_free_rate()

    # Prepare options data
    logger.info("[PREP] Preparing options data...")
    columns = ['Name', 'OptionName', 'StrikePrice', 'ExpiryYear', 'ExpiryMonth',
               'ExpiryDate', 'Update_date', 'Bid', 'Ask', 'Bid_vol', 'Ask_vol',
               'Volume', 'High', 'Low', 'Last', 'Opening_price', 'Closing_price']

    df = df_options[columns].copy()

    # Filter
    df['Bid'] = df['Bid'].fillna(0)
    df['Ask'] = df['Ask'].fillna(0)
    df['BidAskSpreadPct'] = (df['Ask'] - df['Bid']) / df['Bid']
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(subset=['BidAskSpreadPct'], inplace=True)

    logger.info(f"  After bid-ask filter: {len(df):,} options")

    # Merge stock prices
    logger.info("[MERGE] Merging stock prices...")
    df = df.merge(df_stock, on=['Update_date', 'Name'], how='left')

    # Calculate metrics
    df['StrikeCloseDistance'] = (df['StrikePrice'] - df['StockPrice']) / df['StockPrice']
    df['Bid_Ask_Mid_Price'] = (df['Bid'] + df['Ask']) / 2

    # Filter ITM puts with bids
    logger.info("[FILTER] Applying filters (ITM puts with bids > 0.01)...")
    df = df.loc[
        (df['StockPrice'] >= df['StrikePrice']) &
        (df['Bid'] > 0.01)
    ].copy().reset_index(drop=True)

    logger.info(f"  After ITM/bid filters: {len(df):,} options")

    # Calculate days to expiry and merge rates
    df['DaysToExpiry'] = calculate_business_days_vectorized(df, 'Update_date', 'ExpiryDate')
    df['AskBidSpread'] = (df['Ask'] / df['Bid']).round(2)

    logger.info("[MERGE] Merging risk-free rates...")
    df = df.merge(df_bond, on='Update_date', how='left')

    if df['interest_rate'].isna().any():
        df = df.sort_values('Update_date')
        df['interest_rate'] = df['interest_rate'].fillna(method='ffill')
        if df['interest_rate'].isna().any():
            first_rate = df['interest_rate'].dropna().iloc[0] if len(df['interest_rate'].dropna()) > 0 else 0.02
            df['interest_rate'] = df['interest_rate'].fillna(first_rate)

    # Merge IV data
    logger.info("[MERGE] Merging IV historical data...")
    df_iv_subset = df_iv_hist[['OptionName', 'Update_date', 'ImpliedVolatility',
                                 'ImpliedVolatilityUntilExpiry']].drop_duplicates()
    df = df.merge(df_iv_subset, on=['OptionName', 'Update_date'], how='inner')

    # Calculate median IV
    logger.info("[CALC] Calculating median IV closest to strike...")
    df_iv_filtered = df_iv_hist.loc[df_iv_hist['ImpliedVolatilityUntilExpiry'].notna()].copy()
    df_iv_filtered['StrikeCloseDistance_ABS'] = df_iv_filtered['StrikeCloseDistance'].abs()
    df_closest = df_iv_filtered.groupby(['Name', 'Update_date', 'DaysToExpiry'])['StrikeCloseDistance_ABS'].min().reset_index()
    df_closest = df_closest.loc[(df_closest['DaysToExpiry'] <= 100) & (df_closest['DaysToExpiry'] >= 7)]
    df_iv_median = df_iv_filtered.merge(df_closest, on=['Name', 'Update_date', 'StrikeCloseDistance_ABS', 'DaysToExpiry'])
    df_iv_median = df_iv_median.groupby(['Name', 'Update_date'])['ImpliedVolatilityUntilExpiry'].median().reset_index()
    df_iv_median.columns = ['Name', 'Update_date', 'ImpliedVolatilityUntilExpiry_Median']
    df = df.merge(df_iv_median, on=['Name', 'Update_date'], how='left')

    # Calculate contract metrics
    df['StockValueLimit'] = STOCK_VALUE_LIMIT
    df['NumberOfContractsBasedOnLimit'] = ((df['StockValueLimit'] / df['StrikePrice']) / 100).round()
    df['Premium'] = (df['Bid_Ask_Mid_Price'] * df['NumberOfContractsBasedOnLimit'] * 100) - COURTAGE
    df['Premium'] = df['Premium'].round(0).astype(int)

    # Calculate probabilities
    logger.info("[CALC] Method 1: Black-Scholes probability...")
    df['ProbOfWorthless'] = parallel_apply(df, calculate_black_scholes_probability, desc="Method 1")

    logger.info("[CALC] Method 2: Bias-corrected calibration...")
    time_bins = [3, 7, 14, 30, 35, 45, np.inf]
    bin_labels = ['4-7', '8-14', '15-30', '31-35', '36-45', '46+']
    df['ExpiryBin'] = pd.cut(df['DaysToExpiry'], bins=time_bins, labels=bin_labels, right=True)
    bins = np.linspace(0, 1, 11)
    df['ProbBin'] = pd.cut(df['ProbOfWorthless'], bins=bins, include_lowest=True)
    df['ProbBin'] = df['ProbBin'].astype(str)
    df['ExpiryBin'] = df['ExpiryBin'].astype(str)
    df['ProbCalibrated'] = apply_bias_correction(df, calibration['stats_per_stock']).round(3)

    logger.info("[CALC] Method 3: Historical IV-based probability...")
    iv_acc = calibration['iv_accuracy'].copy()
    iv_acc['ExpiryBin'] = pd.cut(iv_acc['DaysToExpiry'], bins=time_bins, labels=bin_labels, right=True)
    iv_acc = iv_acc.dropna(subset=['ExpiryBin'])
    accuracy_cols = ['Accuracy_on_ExpiryDate_Lower_Bound'] + [f'Accuracy_on_ExpiryDate_Lower_Bound_Minus_{i}%' for i in range(10, 95, 5)]
    hist_acc = iv_acc.groupby(['Name', 'ExpiryBin'], observed=False)[accuracy_cols].mean()
    n_obs = iv_acc.groupby(['Name', 'ExpiryBin'], observed=False)['SampleSize'].sum().rename('TotalSampleSize')
    hist_acc = hist_acc.join(n_obs, how='left').reset_index()
    df['EstimatedProbAboveStrike'] = parallel_apply(df, calculate_historical_iv_probability, desc="Method 3", accuracy_df=hist_acc).round(3)

    logger.info("[CALC] Bayesian isotonic calibration...")
    params = calibration['bayesian_params']
    GROUP_COLS = ['Name', 'ExpiryBin_Bayesian', 'ProbBin_Bayesian']
    df['ExpiryBin_Bayesian'] = pd.cut(df['DaysToExpiry'], bins=params['TIME_BINS'], labels=params['TIME_LABELS'], right=True).astype(str)
    df['ProbBin_Bayesian'] = pd.cut(df['ProbOfWorthless'], bins=params['PROB_EDGES'], labels=params['PROB_LABELS'], include_lowest=True).astype(str)
    df = df.merge(calibration['bayesian_lookup'], on=GROUP_COLS, how='left')

    logger.info("[CALC] Computing weighted average of methods...")
    weights = {
        'EstimatedProbAboveStrike': calibration['brier_weights']['EstimatedProbAboveStrike'],
        'ProbOfWorthless': calibration['brier_weights']['ProbOfWorthless'],
        'ProbCalibrated': calibration['brier_weights']['ProbCalibrated']
    }
    df['ProbFinal_Weighted'] = parallel_apply(df, calculate_weighted_average, desc="Weighted Average", weights=weights)

    # Prepare output
    logger.info("[SAVE] Preparing final output...")
    df_final = df[[
        'OptionName', 'Update_date', 'ProbFinal_Weighted',
        'ProbWorthless_Bayesian_IsoCal', 'ProbOfWorthless',
        'ProbCalibrated', 'EstimatedProbAboveStrike'
    ]].copy()

    df_final.columns = [
        'OptionName', 'Update_date', '1_2_3_ProbOfWorthless_Weighted',
        'ProbWorthless_Bayesian_IsoCal', '1_ProbOfWorthless_Original',
        '2_ProbOfWorthless_Calibrated', '3_ProbOfWorthless_Historical_IV'
    ]

    df_final = df_final.dropna(subset=['1_ProbOfWorthless_Original'])
    df_final['Update_date'] = pd.to_datetime(df_final['Update_date'])

    # Save to intermediate file
    df_final.to_csv(INTERMEDIATE_FILE, sep='|', index=False)

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✓ STEP 1 COMPLETE: Generated {len(df_final):,} probability records")
    logger.info(f"  Output: {INTERMEDIATE_FILE}")
    logger.info("=" * 80)
    logger.info("")

    return df_final


# =============================================================================
# STEP 2: ENRICH WITH STRIKE & PRICE DATA
# =============================================================================

def enrich_with_strike_and_prices(df_prob):
    """Enrich probability data with strike and price information"""
    logger.info("=" * 80)
    logger.info("STEP 2: ENRICHING WITH STRIKE & PRICE DATA")
    logger.info("=" * 80)
    logger.info("")

    # Load enrichment data
    logger.info("LOADING ENRICHMENT DATA...")
    df_options = pd.read_parquet(OPTIONS_DATA_PATH)
    df_options['ExpiryDate'] = pd.to_datetime(df_options['ExpiryDate'])
    df_options['Update_date'] = pd.to_datetime(df_options['Update_date'])
    logger.info(f"  Options data: {len(df_options):,} records")

    df_prices = pd.read_parquet(PRICE_DATA_PATH)
    df_prices['date'] = pd.to_datetime(df_prices['date'])
    logger.info(f"  Price data: {len(df_prices):,} records")

    # Merge with strike information
    logger.info("MERGING WITH STRIKE INFORMATION...")
    df_options_for_merge = df_options[['OptionName', 'Update_date', 'StrikePrice', 'ExpiryDate', 'Name']].copy()
    df_options_for_merge.rename(columns={'ExpiryDate': 'StrikeDate'}, inplace=True)

    df_merged = df_prob.merge(
        df_options_for_merge,
        on=['OptionName', 'Update_date'],
        how='left',
        validate='m:1'
    )
    logger.info(f"  After merge: {len(df_merged):,} records")
    logger.info(f"  Rows with missing StrikePrice: {df_merged['StrikePrice'].isna().sum()}")

    # Merge with current stock prices
    logger.info("MERGING WITH CURRENT STOCK PRICES...")
    df_prices_for_current = df_prices[['date', 'name', 'close']].drop_duplicates().reset_index(drop=True)
    df_prices_for_current.columns = ['Update_date', 'Name', 'StockPrice']

    df_merged = df_merged.merge(
        df_prices_for_current,
        on=['Name', 'Update_date'],
        how='left',
        validate='m:1'
    )
    logger.info(f"  After merge: {len(df_merged):,} records")
    logger.info(f"  Rows with missing StockPrice: {df_merged['StockPrice'].isna().sum()}")

    # Merge with expiry prices
    logger.info("MERGING WITH EXPIRY STOCK PRICES...")
    df_prices_for_expiry = df_prices[['date', 'name', 'close']].drop_duplicates().reset_index(drop=True)
    df_prices_for_expiry.columns = ['StrikeDate', 'Name', 'StockPrice_AtExpiry']
    df_prices_for_expiry['StrikeDate'] = pd.to_datetime(df_prices_for_expiry['StrikeDate'])

    df_final = df_merged.merge(
        df_prices_for_expiry,
        on=['StrikeDate', 'Name'],
        how='left',
        validate='m:1'
    )
    logger.info(f"  After merge: {len(df_final):,} records")

    missing_expiry = df_final['StockPrice_AtExpiry'].isna().sum()
    logger.info(f"  Rows with missing StockPrice_AtExpiry: {missing_expiry}")
    if missing_expiry > 0:
        missing_pct = missing_expiry / len(df_final) * 100
        logger.info(f"  (Note: {missing_pct:.2f}% missing - these are options expiring in the future)")

    # Verify data integrity
    logger.info("VERIFYING DATA INTEGRITY...")
    unique_pairs = df_final[['OptionName', 'Update_date']].drop_duplicates().shape[0]
    logger.info(f"  Total records: {len(df_final):,}")
    logger.info(f"  Unique (OptionName, Update_date) pairs: {unique_pairs:,}")
    if unique_pairs == len(df_final):
        logger.info("  ✓ No duplicates - data integrity verified")
    else:
        logger.info(f"  ✗ WARNING: {len(df_final) - unique_pairs} duplicate rows found!")

    # Organize output columns
    logger.info("ORGANIZING OUTPUT COLUMNS...")
    original_prob_cols = [col for col in df_prob.columns]
    output_columns = (
        ['StrikePrice', 'StrikeDate', 'Name', 'StockPrice', 'OptionName', 'Update_date'] +
        [col for col in original_prob_cols if col not in ['OptionName', 'Update_date']] +
        ['StockPrice_AtExpiry']
    )
    output_columns = [col for col in output_columns if col in df_final.columns]
    df_final = df_final[output_columns].copy()

    # Summary statistics
    logger.info("SUMMARY STATISTICS")
    logger.info(f"  Total records: {len(df_final):,}")
    logger.info(f"  Unique stocks: {df_final['Name'].nunique()}")
    logger.info(f"  Unique options: {df_final['OptionName'].nunique()}")
    logger.info(f"  Update date range: {df_final['Update_date'].min()} to {df_final['Update_date'].max()}")
    logger.info(f"  Expiry date range: {df_final['StrikeDate'].min()} to {df_final['StrikeDate'].max()}")

    logger.info("DATA QUALITY CHECKS")
    logger.info(f"  Missing StrikePrice: {df_final['StrikePrice'].isna().sum():,} ({df_final['StrikePrice'].isna().sum()/len(df_final)*100:.2f}%)")
    logger.info(f"  Missing StockPrice: {df_final['StockPrice'].isna().sum():,} ({df_final['StockPrice'].isna().sum()/len(df_final)*100:.2f}%)")
    logger.info(f"  Missing StockPrice_AtExpiry: {df_final['StockPrice_AtExpiry'].isna().sum():,} ({df_final['StockPrice_AtExpiry'].isna().sum()/len(df_final)*100:.2f}%)")

    # Save final output
    logger.info("SAVING COMPLETE PROBABILITY HISTORY...")
    df_final.to_csv(FINAL_OUTPUT_FILE, sep='|', index=False)

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✓ STEP 2 COMPLETE: Enriched with strike & price data")
    logger.info(f"  Output: {FINAL_OUTPUT_FILE}")
    logger.info(f"  File size: {FINAL_OUTPUT_FILE.stat().st_size / (1024**2):.1f} MB")
    logger.info(f"  Total columns: {len(output_columns)}")
    logger.info(f"  Total rows: {len(df_final):,}")
    logger.info("=" * 80)
    logger.info("")

    return df_final


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    """
    Master script: Generate complete probability history in one command
    """
    try:
        logger.info("")
        logger.info("=" * 80)
        logger.info("GENERATE COMPLETE PROBABILITY HISTORY")
        logger.info("=" * 80)
        logger.info("")

        # Step 1: Generate base probabilities
        df_prob = generate_base_probabilities()

        # Step 2: Enrich with strike and prices
        df_final = enrich_with_strike_and_prices(df_prob)

        logger.info("")
        logger.info("=" * 80)
        logger.info("SUCCESS - COMPLETE PROBABILITY HISTORY GENERATED")
        logger.info("=" * 80)
        logger.info(f"Final output: {FINAL_OUTPUT_FILE}")
        logger.info("")

    except Exception as e:
        logger.error(f"[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
