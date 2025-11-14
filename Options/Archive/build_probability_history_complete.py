#!/usr/bin/env python3
"""
Build Complete Probability History with All Enrichments

This is a unified master script that consolidates three separate enrichment processes
into a single pipeline to create the final probability history file with all fields:

1. Load probability history from CSV
2. Merge with All_Options_Data.parquet for strike information (StrikePrice, StrikeDate, Name)
3. Merge with price_data_all.parquet for current stock price (StockPrice_Update)
4. Merge with price_data_all.parquet for expiry stock price (StockPrice_AtExpiry)

Output: probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv

Author: Claude Code
Date: November 12, 2025
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
options_dir = Path(__file__).parent
sys.path.insert(0, str(options_dir))

try:
    from config_utils import get_path_config
    import os
    # Change to Options directory so config file is found
    original_cwd = os.getcwd()
    os.chdir(options_dir)
    PATH_CONFIG = get_path_config()
    os.chdir(original_cwd)
except (ImportError, FileNotFoundError) as e:
    print(f"WARNING: config_utils failed ({e}), using fallback paths")
    PATH_CONFIG = None

# Define paths
if PATH_CONFIG:
    PROBABILITY_HISTORY = Path(__file__).parent / 'probability_history_FULL_HISTORICAL.csv'
    OPTIONS_DATA = Path(PATH_CONFIG.get_options_data_parquet())
    PRICE_DATA = Path(PATH_CONFIG.get_price_data_parquet())
    OUTPUT_FILE = Path(__file__).parent / 'probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv'
else:
    # Fallback paths
    import sys
    ONEDRIVE_ROOT = Path('/mnt/c/Users/Gustaf/OneDrive') if 'linux' in sys.platform.lower() else Path('C:/Users/Gustaf/OneDrive')
    PROBABILITY_HISTORY = Path(__file__).parent / 'probability_history_FULL_HISTORICAL.csv'
    OPTIONS_DATA = ONEDRIVE_ROOT / 'OptionsData' / 'All_Options_Data.parquet'
    PRICE_DATA = ONEDRIVE_ROOT / 'OptionsData' / 'price_data_all.parquet'
    OUTPUT_FILE = Path(__file__).parent / 'probability_history_FULL_HISTORICAL_WITH_EXPIRY_PRICE.csv'

print("="*80)
print("BUILD COMPLETE PROBABILITY HISTORY WITH ALL ENRICHMENTS")
print("="*80)
print()

# Validate input files
print("VALIDATING INPUT FILES...")
if not PROBABILITY_HISTORY.exists():
    print(f"ERROR: Probability history file not found: {PROBABILITY_HISTORY}")
    sys.exit(1)
if not OPTIONS_DATA.exists():
    print(f"ERROR: Options data file not found: {OPTIONS_DATA}")
    sys.exit(1)
if not PRICE_DATA.exists():
    print(f"ERROR: Price data file not found: {PRICE_DATA}")
    sys.exit(1)

print(f"✓ Probability history: {PROBABILITY_HISTORY}")
print(f"✓ Options data: {OPTIONS_DATA}")
print(f"✓ Price data: {PRICE_DATA}")
print()

# =============================================================================
# STEP 1: Load probability history
# =============================================================================
print("STEP 1: Loading probability history...")
df_prob = pd.read_csv(PROBABILITY_HISTORY, sep='|')
print(f"  Loaded {len(df_prob):,} records")
print(f"  Columns: {df_prob.columns.tolist()}")

# Convert Update_date to datetime
df_prob['Update_date'] = pd.to_datetime(df_prob['Update_date'])
print(f"  Update_date range: {df_prob['Update_date'].min()} to {df_prob['Update_date'].max()}")
print()

# =============================================================================
# STEP 2: Load and merge with options data (strike information)
# =============================================================================
print("STEP 2: Loading and merging with options data...")
df_options = pd.read_parquet(OPTIONS_DATA)
print(f"  Loaded {len(df_options):,} total option records")

# Convert dates to datetime
df_options['ExpiryDate'] = pd.to_datetime(df_options['ExpiryDate'])
df_options['Update_date'] = pd.to_datetime(df_options['Update_date'])

# Select relevant columns and rename ExpiryDate to StrikeDate
df_options_for_merge = df_options[['OptionName', 'Update_date', 'StrikePrice', 'ExpiryDate', 'Name']].copy()
df_options_for_merge.rename(columns={'ExpiryDate': 'StrikeDate'}, inplace=True)
print(f"  Prepared columns for merge: {df_options_for_merge.columns.tolist()}")

# Merge on (OptionName, Update_date)
print("  Merging probability history with options data on (OptionName, Update_date)...")
df_merged = df_prob.merge(
    df_options_for_merge,
    on=['OptionName', 'Update_date'],
    how='left',
    validate='m:1'
)
print(f"  After merge: {len(df_merged):,} records")
print(f"  Rows with missing StrikePrice: {df_merged['StrikePrice'].isna().sum()}")
print()

# =============================================================================
# STEP 3: Load and merge with price data (current stock price)
# =============================================================================
print("STEP 3: Loading and merging with price data (current stock price)...")
df_prices = pd.read_parquet(PRICE_DATA)
print(f"  Loaded {len(df_prices):,} price records")

# Standardize columns
df_prices['date'] = pd.to_datetime(df_prices['date'])
df_prices_for_current = df_prices[['date', 'name', 'close']].drop_duplicates().reset_index(drop=True)
df_prices_for_current.columns = ['Update_date', 'Name', 'StockPrice']
print(f"  After standardization: {len(df_prices_for_current):,} unique price records")
print(f"  Date range: {df_prices_for_current['Update_date'].min()} to {df_prices_for_current['Update_date'].max()}")

# Merge with stock prices on (Name, Update_date)
print("  Merging with stock prices on (Name, Update_date)...")
df_merged = df_merged.merge(
    df_prices_for_current,
    on=['Name', 'Update_date'],
    how='left',
    validate='m:1'
)
print(f"  After merge: {len(df_merged):,} records")
print(f"  Rows with missing StockPrice: {df_merged['StockPrice'].isna().sum()}")
print()

# =============================================================================
# STEP 4: Merge with price data (stock price at expiry)
# =============================================================================
print("STEP 4: Merging with price data (stock price at expiry)...")

# Prepare price data for expiry lookup
df_prices_for_expiry = df_prices[['date', 'name', 'close']].drop_duplicates().reset_index(drop=True)
df_prices_for_expiry.columns = ['StrikeDate', 'Name', 'StockPrice_AtExpiry']
df_prices_for_expiry['StrikeDate'] = pd.to_datetime(df_prices_for_expiry['StrikeDate'])
print(f"  Prepared {len(df_prices_for_expiry):,} price records for expiry lookup")

# Merge on (StrikeDate, Name)
print("  Merging on (StrikeDate, Name)...")
df_final = df_merged.merge(
    df_prices_for_expiry,
    on=['StrikeDate', 'Name'],
    how='left',
    validate='m:1'
)
print(f"  After merge: {len(df_final):,} records")
print(f"  Rows with missing StockPrice_AtExpiry: {df_final['StockPrice_AtExpiry'].isna().sum()}")

if df_final['StockPrice_AtExpiry'].isna().sum() > 0:
    missing_pct = df_final['StockPrice_AtExpiry'].isna().sum() / len(df_final) * 100
    print(f"  (Note: {missing_pct:.2f}% missing - these are options expiring in the future)")
print()

# =============================================================================
# STEP 5: Verify data integrity
# =============================================================================
print("STEP 5: Verifying data integrity...")
unique_pairs = df_final[['OptionName', 'Update_date']].drop_duplicates().shape[0]
print(f"  Total records: {len(df_final):,}")
print(f"  Unique (OptionName, Update_date) pairs: {unique_pairs:,}")
if unique_pairs == len(df_final):
    print("  ✓ No duplicates - data integrity verified")
else:
    print(f"  ✗ WARNING: {len(df_final) - unique_pairs} duplicate rows found!")
print()

# =============================================================================
# STEP 6: Organize output columns
# =============================================================================
print("STEP 6: Organizing output columns...")

# Define output column order - keep all original columns and add new enrichment columns
original_prob_cols = [col for col in df_prob.columns]
output_columns = (
    ['StrikePrice', 'StrikeDate', 'Name', 'StockPrice', 'OptionName', 'Update_date'] +
    [col for col in original_prob_cols if col not in ['OptionName', 'Update_date']] +
    ['StockPrice_AtExpiry']
)

# Keep only valid columns (some might not exist)
output_columns = [col for col in output_columns if col in df_final.columns]

df_final = df_final[output_columns].copy()
print(f"  Output columns ({len(output_columns)}): {output_columns}")
print()

# =============================================================================
# STEP 7: Summary statistics
# =============================================================================
print("STEP 7: Summary Statistics")
print(f"  Total records: {len(df_final):,}")
print(f"  Unique stocks: {df_final['Name'].nunique()}")
print(f"  Unique options: {df_final['OptionName'].nunique()}")
print(f"  Update date range: {df_final['Update_date'].min()} to {df_final['Update_date'].max()}")
print(f"  Expiry date range: {df_final['StrikeDate'].min()} to {df_final['StrikeDate'].max()}")
print()

# Data quality checks
print("  Data Quality Checks:")
print(f"    - Missing StrikePrice: {df_final['StrikePrice'].isna().sum():,} ({df_final['StrikePrice'].isna().sum()/len(df_final)*100:.2f}%)")
print(f"    - Missing StrikeDate: {df_final['StrikeDate'].isna().sum():,} ({df_final['StrikeDate'].isna().sum()/len(df_final)*100:.2f}%)")
print(f"    - Missing StockPrice (update): {df_final['StockPrice'].isna().sum():,} ({df_final['StockPrice'].isna().sum()/len(df_final)*100:.2f}%)")
print(f"    - Missing Name (stock): {df_final['Name'].isna().sum():,} ({df_final['Name'].isna().sum()/len(df_final)*100:.2f}%)")
print(f"    - Missing StockPrice_AtExpiry: {df_final['StockPrice_AtExpiry'].isna().sum():,} ({df_final['StockPrice_AtExpiry'].isna().sum()/len(df_final)*100:.2f}%)")
print()

# =============================================================================
# STEP 8: Save output
# =============================================================================
print(f"STEP 8: Saving complete probability history to {OUTPUT_FILE}...")
df_final.to_csv(OUTPUT_FILE, sep='|', index=False)
print(f"✓ Successfully saved {len(df_final):,} records")
print()

print("="*80)
print("COMPLETE - PROBABILITY HISTORY BUILD SUCCESSFUL")
print("="*80)
print(f"Output file: {OUTPUT_FILE}")
print(f"File size: {OUTPUT_FILE.stat().st_size / (1024**2):.1f} MB")
print(f"Total columns: {len(output_columns)}")
print(f"Total rows: {len(df_final):,}")
print()
