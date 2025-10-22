#!/usr/bin/env python3
"""
Clean up the hypothesis folder to contain ONLY the multi-period analysis.
This is the one and only hypothesis - all other files are legacy/temporary.
"""

import os
import shutil

# Files to KEEP (the multi-period analysis)
KEEP_FILES = {
    # Main dashboard and data
    'multi_period_dashboard.html',
    'multi_period_dashboard_data.json',

    # Analysis script and results
    'multi_period_low_analysis.py',
    'multi_period_combined_matrix.csv',
    'multi_period_comparison_charts.png',

    # Detailed results for each period
    '1_month_low_detailed_results.csv',
    '1_month_low_matrix.csv',
    '3_month_low_detailed_results.csv',
    '3_month_low_matrix.csv',
    '6_month_low_detailed_results.csv',
    '6_month_low_matrix.csv',
    '9_month_low_detailed_results.csv',
    '9_month_low_matrix.csv',
    '1_year_low_detailed_results.csv',
    '1_year_low_matrix.csv',

    # Data preparation and dashboard building scripts
    'add_price_data_to_dashboard.py',
    'build_clean_dashboard.py',

    # Documentation (will be updated)
    'MULTI_PERIOD_FINDINGS.md',

    # This cleanup script itself
    'cleanup_hypothesis.py',
}

def main():
    print("=" * 70)
    print("CLEANING UP HYPOTHESIS FOLDER")
    print("Keeping ONLY multi-period analysis files")
    print("=" * 70)

    # Get all files in current directory
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]

    files_to_remove = [f for f in all_files if f not in KEEP_FILES]

    print(f"\nFound {len(all_files)} total files")
    print(f"Keeping {len(KEEP_FILES)} files")
    print(f"Removing {len(files_to_remove)} files")

    if files_to_remove:
        print("\n📝 Files to be removed:")
        for f in sorted(files_to_remove):
            size = os.path.getsize(f)
            size_mb = size / (1024 * 1024)
            print(f"  - {f:50s} ({size_mb:>6.2f} MB)")

        total_size = sum(os.path.getsize(f) for f in files_to_remove)
        total_mb = total_size / (1024 * 1024)
        print(f"\n  Total size to free: {total_mb:.2f} MB")

        print("\n🗑️  Removing files...")
        for f in files_to_remove:
            try:
                os.remove(f)
                print(f"  ✓ Removed: {f}")
            except Exception as e:
                print(f"  ✗ Error removing {f}: {e}")
    else:
        print("\n✓ No files to remove")

    print("\n" + "=" * 70)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 70)

    print("\n📁 Remaining files:")
    remaining = [f for f in os.listdir('.') if os.path.isfile(f) and f != 'cleanup_hypothesis.py']
    for f in sorted(remaining):
        size = os.path.getsize(f)
        size_mb = size / (1024 * 1024)
        print(f"  {f:50s} {size_mb:>6.2f} MB")

    total_remaining = sum(os.path.getsize(f) for f in remaining)
    total_remaining_mb = total_remaining / (1024 * 1024)
    print(f"\n  Total: {total_remaining_mb:.2f} MB")

if __name__ == '__main__':
    main()
