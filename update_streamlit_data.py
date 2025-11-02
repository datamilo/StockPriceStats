#!/usr/bin/env python3
"""
MASTER STREAMLIT DATA UPDATE SCRIPT

This script updates ALL data used by the Streamlit app:
1. Filters price_data_all.parquet to relevant stocks
2. Runs incremental H001 analysis (fast - only new dates)
3. Regenerates top lists (slow - full recalculation)
4. Commits and pushes everything to GitHub

USAGE:
    Simply place an updated price_data_all.parquet in the main folder, then run:
    
    python update_streamlit_data.py

That's it! Everything else is automated.
"""

import subprocess
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
H001_DIR = PROJECT_ROOT / 'hypotheses' / 'h001_multi_period_low_support'
FILTER_SCRIPT = PROJECT_ROOT / 'filter_relevant_stocks.py'
INCREMENTAL_SCRIPT = H001_DIR / 'multi_period_low_analysis_incremental.py'
TOP_LISTS_SCRIPT = H001_DIR / 'calculate_top_lists.py'
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
    """Verify that price_data_all.parquet exists, copy from OneDrive if needed"""
    import shutil
    
    print_header("PRE-FLIGHT CHECKS")
    
    # Source path in OneDrive (WSL path)
    ONEDRIVE_SOURCE = Path("/mnt/c/Users/Gustaf/OneDrive/OptionsData/price_data_all.parquet")
    
    # Check if OneDrive source exists and is newer
    if ONEDRIVE_SOURCE.exists():
        onedrive_mtime = ONEDRIVE_SOURCE.stat().st_mtime
        
        # Check if local file exists and compare modification times
        if PRICE_DATA_ALL.exists():
            local_mtime = PRICE_DATA_ALL.stat().st_mtime
            if onedrive_mtime > local_mtime:
                print(f"✓ Found newer price data in OneDrive")
                print(f"  Copying from: {ONEDRIVE_SOURCE}")
                shutil.copy2(ONEDRIVE_SOURCE, PRICE_DATA_ALL)
                print(f"  ✓ Updated local copy")
            else:
                print(f"✓ Local price_data_all.parquet is up to date")
        else:
            print(f"✓ Copying price data from OneDrive")
            print(f"  Source: {ONEDRIVE_SOURCE}")
            shutil.copy2(ONEDRIVE_SOURCE, PRICE_DATA_ALL)
            print(f"  ✓ Copied to project folder")
    
    # Verify local file now exists
    if not PRICE_DATA_ALL.exists():
        print(f"✗ Input file not found: {PRICE_DATA_ALL}")
        print(f"✗ OneDrive source also not found: {ONEDRIVE_SOURCE}")
        print("\nPlease ensure price_data_all.parquet is in one of these locations:")
        print(f"  1. {PROJECT_ROOT}/")
        print(f"  2. {ONEDRIVE_SOURCE}")
        return False
    
    size_mb = PRICE_DATA_ALL.stat().st_size / (1024*1024)
    print(f"✓ Using price_data_all.parquet ({size_mb:.1f} MB)")
    
    if not FILTER_SCRIPT.exists():
        print(f"✗ Filter script not found: {FILTER_SCRIPT}")
        return False
    
    print(f"✓ Found filter script")
    
    if not INCREMENTAL_SCRIPT.exists():
        print(f"✗ Incremental analysis script not found: {INCREMENTAL_SCRIPT}")
        return False
    
    print(f"✓ Found incremental analysis script")
    
    if not TOP_LISTS_SCRIPT.exists():
        print(f"✗ Top lists script not found: {TOP_LISTS_SCRIPT}")
        return False
    
    print(f"✓ Found top lists script")
    
    return True


def main():
    """Main update workflow"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "STREAMLIT DATA UPDATE - ALL DATA FOR DASHBOARD".center(78) + "║")
    print("║" + "(Filters, H001 Analysis, Top Lists, GitHub Push)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Verify everything exists
    if not verify_input_file():
        print("\n✗ Pre-flight checks failed. Cannot continue.")
        return 1
    
    # Step 1: Filter data
    if not run_command(
        "Filter price data to relevant stocks (68 stocks)",
        FILTER_SCRIPT,
        working_dir=PROJECT_ROOT
    ):
        print("\n✗ Data filtering failed. Cannot continue with analysis.")
        return 1
    
    # Step 2: Run incremental H001 analysis
    if not run_command(
        "Run incremental H001 analysis (FAST - only new dates)",
        INCREMENTAL_SCRIPT,
        working_dir=H001_DIR
    ):
        print("\n✗ Incremental analysis failed.")
        return 1
    
    # Step 3: Regenerate top lists
    print_header("STEP: Regenerate top lists for Streamlit")
    print("⚠️  NOTE: This step takes 30-40 minutes (full recalculation)")
    print("   Future optimization: Make this incremental too!")
    
    if not run_command(
        "Regenerate top lists (SLOW - full recalculation)",
        TOP_LISTS_SCRIPT,
        working_dir=H001_DIR
    ):
        print("\n✗ Top lists regeneration failed.")
        print("⚠️  H001 data updated but top lists may be stale.")
        print(f"Run manually: python {TOP_LISTS_SCRIPT}")
        return 1
    
    # Success! (Git push is handled by calculate_top_lists.py)
    print_header("✓ ALL STREAMLIT DATA UPDATED & SYNCED TO GITHUB!")
    
    print("""
The following files have been updated and pushed to GitHub:

DATA FILES:
  ✓ price_data_all.parquet           - Latest price data
  ✓ price_data_filtered.parquet      - Filtered stock price data (68 stocks)

H001 ANALYSIS RESULTS:
  ✓ 1_month_detailed_results.parquet - H001 analysis results
  ✓ 3_month_detailed_results.parquet - H001 analysis results
  ✓ 6_month_detailed_results.parquet - H001 analysis results
  ✓ 9_month_detailed_results.parquet - H001 analysis results
  ✓ 1_year_detailed_results.parquet  - H001 analysis results

TOP LISTS (PRE-CALCULATED):
  ✓ top_lists/1_month_top_lists.parquet
  ✓ top_lists/3_month_top_lists.parquet
  ✓ top_lists/6_month_top_lists.parquet
  ✓ top_lists/9_month_top_lists.parquet
  ✓ top_lists/1_year_top_lists.parquet

The Streamlit app will automatically use the updated data on next refresh.
GitHub and Streamlit Cloud will auto-deploy the changes.

To update again in the future:
  1. Place a new price_data_all.parquet in the main folder (or it will auto-copy from OneDrive)
  2. Run: python update_streamlit_data.py
  3. That's it! Everything else is automated.

TIMING:
  - Step 1 (Filter): ~1 minute
  - Step 2 (H001 Incremental): ~5-10 minutes
  - Step 3 (Top Lists): ~30-40 minutes
  - Total: ~35-50 minutes
""")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
