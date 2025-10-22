#!/usr/bin/env python3
"""
MASTER UPDATE SCRIPT - Updates all analysis data with one command!

This script automates the entire data update workflow:
1. Filters price_data_all.parquet to create price_data_filtered.parquet
2. Runs incremental H001 analysis to append only new data
3. Takes only a few minutes (not hours)

USAGE:
    Simply place an updated price_data_all.parquet in the main folder, then run:

    python update_analysis_data.py

That's it! The script will:
- Detect the new data
- Filter it automatically
- Analyze only the new dates
- Append results to existing files
- Display a summary

NO CONFIGURATION NEEDED. Just drop the file and run the script.
"""

import subprocess
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
H001_DIR = PROJECT_ROOT / 'hypotheses' / 'h001_multi_period_low_support'
FILTER_SCRIPT = PROJECT_ROOT / 'filter_relevant_stocks.py'
INCREMENTAL_SCRIPT = H001_DIR / 'multi_period_low_analysis_incremental.py'
PRICE_DATA_ALL = PROJECT_ROOT / 'price_data_all.parquet'


def print_header(title):
    """Print a nice header"""
    print("\n" + "="*80)
    print(title.center(80))
    print("="*80)


def run_command(description, script_path, working_dir=None):
    """
    Run a Python script and handle errors.

    Args:
        description: What we're doing (for display)
        script_path: Path to script to run
        working_dir: Directory to run script from (optional)

    Returns:
        True if successful, False otherwise
    """
    print_header(f"STEP: {description}")

    if not script_path.exists():
        print(f"✗ Error: Script not found: {script_path}")
        return False

    try:
        cmd = [sys.executable, str(script_path)]
        result = subprocess.run(cmd, cwd=working_dir, check=True)
        print(f"\n✓ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error during {description}")
        print(f"Return code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def verify_input_file():
    """Verify that price_data_all.parquet exists"""
    print_header("PRE-FLIGHT CHECKS")

    if not PRICE_DATA_ALL.exists():
        print(f"✗ Input file not found: {PRICE_DATA_ALL}")
        print("\nPlease ensure price_data_all.parquet is in the main folder:")
        print(f"  {PROJECT_ROOT}/")
        return False

    size_mb = PRICE_DATA_ALL.stat().st_size / (1024*1024)
    print(f"✓ Found price_data_all.parquet ({size_mb:.1f} MB)")

    if not FILTER_SCRIPT.exists():
        print(f"✗ Filter script not found: {FILTER_SCRIPT}")
        return False

    print(f"✓ Found filter script")

    if not INCREMENTAL_SCRIPT.exists():
        print(f"✗ Incremental analysis script not found: {INCREMENTAL_SCRIPT}")
        return False

    print(f"✓ Found incremental analysis script")

    return True


def main():
    """Main update workflow"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "STOCKPRICESTATS - MASTER DATA UPDATE SCRIPT".center(78) + "║")
    print("║" + "(Updates H001 analysis with one command)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")

    # Verify everything exists
    if not verify_input_file():
        print("\n✗ Pre-flight checks failed. Cannot continue.")
        return 1

    # Step 1: Filter data
    if not run_command(
        "Filter price data to relevant stocks",
        FILTER_SCRIPT,
        working_dir=PROJECT_ROOT
    ):
        print("\n✗ Data filtering failed. Cannot continue with analysis.")
        return 1

    # Step 2: Run incremental analysis
    if not run_command(
        "Analyze new data and append to H001 results",
        INCREMENTAL_SCRIPT,
        working_dir=H001_DIR
    ):
        print("\n✗ Incremental analysis failed.")
        return 1

    # Success!
    print_header("✓ ALL UPDATES COMPLETE!")

    print("""
The following files have been updated:
  ✓ price_data_filtered.parquet  - Filtered stock price data (70 stocks)
  ✓ 1_month_detailed_results.parquet  - H001 analysis results
  ✓ 3_month_detailed_results.parquet  - H001 analysis results
  ✓ 6_month_detailed_results.parquet  - H001 analysis results
  ✓ 9_month_detailed_results.parquet  - H001 analysis results
  ✓ 1_year_detailed_results.parquet  - H001 analysis results

The Streamlit app will automatically use the updated data on next refresh.

Next steps:
  1. Commit these changes to git
  2. Push to GitHub
  3. Streamlit Cloud will redeploy automatically

To update again in the future:
  1. Place a new price_data_all.parquet in the main folder
  2. Run: python update_analysis_data.py
  3. That's it!
""")

    return 0


if __name__ == '__main__':
    sys.exit(main())
