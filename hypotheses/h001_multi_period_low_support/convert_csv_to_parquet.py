#!/usr/bin/env python3
"""
Convert CSV result files to Parquet format for better compression and performance.
Parquet typically compresses to 10-20% of CSV file size.
"""

import pandas as pd
import os
from pathlib import Path

# CSV files to convert (only the current analysis results, not legacy files)
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
    return os.path.getsize(filepath) / (1024 * 1024)

def convert_file(csv_file):
    """Convert single CSV to Parquet"""
    parquet_file = csv_file.replace('.csv', '.parquet')

    if not os.path.exists(csv_file):
        print(f"  ⚠ Skipped (not found): {csv_file}")
        return None, None, None

    csv_size = get_file_size_mb(csv_file)

    print(f"  Converting: {csv_file} ({csv_size:.1f}MB)...", end=" ", flush=True)

    try:
        # Read CSV
        df = pd.read_csv(csv_file)

        # Write to Parquet with compression
        df.to_parquet(parquet_file, compression='snappy', index=False)

        parquet_size = get_file_size_mb(parquet_file)
        compression_ratio = (1 - parquet_size / csv_size) * 100

        print(f"✓ ({parquet_size:.1f}MB, {compression_ratio:.1f}% smaller)")

        return csv_file, csv_size, parquet_size
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None, None

def main():
    print("=" * 80)
    print("CONVERTING CSV FILES TO PARQUET")
    print("=" * 80)

    total_csv_size = 0
    total_parquet_size = 0
    converted_count = 0

    print(f"\nProcessing {len(CSV_FILES)} files...\n")

    for csv_file in CSV_FILES:
        result = convert_file(csv_file)
        csv_name, csv_size, parquet_size = result

        if csv_size is not None:
            total_csv_size += csv_size
            total_parquet_size += parquet_size
            converted_count += 1

    print("\n" + "=" * 80)
    print("CONVERSION COMPLETE")
    print("=" * 80)

    if converted_count > 0:
        overall_compression = (1 - total_parquet_size / total_csv_size) * 100
        print(f"\n✓ Converted: {converted_count} files")
        print(f"  Original size:  {total_csv_size:.1f}MB")
        print(f"  Parquet size:   {total_parquet_size:.1f}MB")
        print(f"  Compression:    {overall_compression:.1f}% smaller")
        print(f"  Space saved:    {total_csv_size - total_parquet_size:.1f}MB")
        print(f"\nNext step: Run 'python delete_csv_files.py' to remove CSV files")
    else:
        print("No files converted!")

if __name__ == '__main__':
    main()
