#!/usr/bin/env python3
"""
Delete CSV files after successful conversion to Parquet.
Only deletes files if their corresponding .parquet files exist.
"""

import os
from pathlib import Path

# CSV files to delete (only if parquet equivalents exist)
CSV_FILES = [
    '1_month_detailed_results.csv',
    '1_month_matrix.csv',
    '3_month_detailed_results.csv',
    '3_month_matrix.csv',
    '6_month_detailed_results.csv',
    '6_month_matrix.csv',
    '9_month_detailed_results.csv',
    '9_month_matrix.csv',
    '1_year_detailed_results.csv',
    '1_year_matrix.csv',
    'multi_period_combined_matrix.csv',
]

def get_file_size_mb(filepath):
    """Get file size in MB"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0

def main():
    print("=" * 80)
    print("DELETING CSV FILES")
    print("=" * 80)

    total_csv_size = 0
    deleted_count = 0
    skipped_count = 0

    print("\nChecking files...\n")

    for csv_file in CSV_FILES:
        parquet_file = csv_file.replace('.csv', '.parquet')

        if not os.path.exists(csv_file):
            print(f"  ⚠ Skipped (not found): {csv_file}")
            skipped_count += 1
            continue

        if not os.path.exists(parquet_file):
            print(f"  ✗ KEEP: {csv_file} (parquet version not found!)")
            skipped_count += 1
            continue

        # Both files exist, safe to delete CSV
        csv_size = get_file_size_mb(csv_file)
        print(f"  Deleting: {csv_file} ({csv_size:.1f}MB)...", end=" ", flush=True)

        try:
            os.remove(csv_file)
            total_csv_size += csv_size
            deleted_count += 1
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n" + "=" * 80)
    print("DELETION COMPLETE")
    print("=" * 80)

    print(f"\n✓ Deleted: {deleted_count} files")
    print(f"  Space freed: {total_csv_size:.1f}MB")
    print(f"  Kept: {skipped_count} files")

if __name__ == '__main__':
    main()
