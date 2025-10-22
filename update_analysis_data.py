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


def push_to_github():
    """Commit and push updated files to GitHub"""
    print_header("SYNCING TO GITHUB")

    try:
        # Get the latest date from the data for commit message
        import pandas as pd
        df = pd.read_parquet(PROJECT_ROOT / 'price_data_filtered.parquet')
        latest_date = df['date'].max()

        # Stage files
        files_to_stage = [
            'price_data_all.parquet',
            'price_data_filtered.parquet',
            'hypotheses/h001_multi_period_low_support/1_month_detailed_results.parquet',
            'hypotheses/h001_multi_period_low_support/3_month_detailed_results.parquet',
            'hypotheses/h001_multi_period_low_support/6_month_detailed_results.parquet',
            'hypotheses/h001_multi_period_low_support/9_month_detailed_results.parquet',
            'hypotheses/h001_multi_period_low_support/1_year_detailed_results.parquet',
        ]

        print(f"Staging files for commit...")
        for file in files_to_stage:
            file_path = PROJECT_ROOT / file
            if file_path.exists():
                subprocess.run(
                    ['git', 'add', str(file_path)],
                    cwd=str(PROJECT_ROOT),
                    check=True,
                    capture_output=True
                )
                print(f"  ✓ Staged {file}")

        # Check if there are changes to commit
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True
        )

        if not result.stdout.strip():
            print("\n  No changes to commit (data already up-to-date)")
            return True

        # Create commit message
        commit_msg = f"""Update: Latest price data through {latest_date} with complete OHLC values

Updated datasets include candlestick data for Streamlit app:
- price_data_all.parquet: Latest records through {latest_date}
- price_data_filtered.parquet: 70 Nordic stocks updated
- H001 analysis results: All rolling low periods current

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"""

        # Commit
        print(f"\nCommitting changes...")
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=str(PROJECT_ROOT),
            check=True,
            capture_output=True
        )
        print(f"  ✓ Commit created")

        # Push
        print(f"Pushing to GitHub...")
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=str(PROJECT_ROOT),
            check=True,
            capture_output=True
        )
        print(f"  ✓ Pushed to origin/main")

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Git operation failed")
        print(f"Error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error during GitHub sync: {e}")
        return False


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

    # Step 3: Push to GitHub
    if not push_to_github():
        print("\n✗ GitHub sync failed.")
        print("⚠️  Data has been updated locally but NOT pushed to GitHub.")
        print("Run the following commands manually:")
        print("  git add .")
        print("  git commit -m 'Update: Latest price data'")
        print("  git push origin main")
        return 1

    # Success!
    print_header("✓ ALL UPDATES COMPLETE & SYNCED TO GITHUB!")

    print("""
The following files have been updated and pushed to GitHub:
  ✓ price_data_all.parquet  - Latest price data
  ✓ price_data_filtered.parquet  - Filtered stock price data (70 stocks)
  ✓ 1_month_detailed_results.parquet  - H001 analysis results
  ✓ 3_month_detailed_results.parquet  - H001 analysis results
  ✓ 6_month_detailed_results.parquet  - H001 analysis results
  ✓ 9_month_detailed_results.parquet  - H001 analysis results
  ✓ 1_year_detailed_results.parquet  - H001 analysis results

The Streamlit app will automatically use the updated data on next refresh.
GitHub and Streamlit Cloud will auto-deploy the changes.

To update again in the future:
  1. Place a new price_data_all.parquet in the main folder
  2. Run: python update_analysis_data.py
  3. That's it! Everything else is automated.
""")

    return 0


if __name__ == '__main__':
    sys.exit(main())
