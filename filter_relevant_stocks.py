"""
Filter Relevant Stocks from Price Data

This script filters the price_data_all.parquet file to include only stocks
that have options available, based on the nasdaq_options_available.csv file.

Usage:
    python filter_relevant_stocks.py

Output:
    - price_data_filtered.parquet: Filtered price data (parquet format)
    - price_data_filtered.csv: Filtered price data (CSV format, pipe-delimited)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockDataFilter:
    """Filter stock price data to only include relevant stocks with options"""

    def __init__(self, project_root: str = None):
        """
        Initialize the filter.

        Args:
            project_root: Project root directory (defaults to current directory)
        """
        if project_root is None:
            self.project_root = Path.cwd()
        else:
            self.project_root = Path(project_root)

    def load_options_stocks(self) -> list:
        """
        Load list of stocks that have options available.

        Returns:
            List of stock names (NordnetName format)
        """
        logger.info("Loading stocks with options available...")

        # First try nasdaq_options_available.csv (definitive list)
        options_file = self.project_root / 'nasdaq_options_available.csv'

        if options_file.exists():
            try:
                df = pd.read_csv(options_file, sep='|')

                # Get stock names from NordnetName column
                if 'NordnetName' in df.columns:
                    stocks = df['NordnetName'].dropna().unique().tolist()
                    # Remove empty strings
                    stocks = [s for s in stocks if s and str(s).strip()]
                    logger.info(f"✓ Found {len(stocks)} stocks with options")
                    return stocks
                else:
                    logger.error(f"'NordnetName' column not found in {options_file}")

            except Exception as e:
                logger.error(f"Error reading {options_file}: {e}")

        # Fallback: try nasdaq_nordnet_stock_names.csv
        nordnet_file = self.project_root / 'nasdaq_nordnet_stock_names.csv'

        if nordnet_file.exists():
            try:
                df = pd.read_csv(nordnet_file, sep='|')

                if 'NordnetName' in df.columns:
                    stocks = df['NordnetName'].dropna().unique().tolist()
                    stocks = [s for s in stocks if s and str(s).strip()]
                    logger.info(f"✓ Found {len(stocks)} stocks (from nordnet names file)")
                    return stocks

            except Exception as e:
                logger.error(f"Error reading {nordnet_file}: {e}")

        raise FileNotFoundError(
            "Could not find stock list files. Expected: "
            "nasdaq_options_available.csv or nasdaq_nordnet_stock_names.csv"
        )

    def load_price_data(self) -> pd.DataFrame:
        """
        Load stock price data from parquet file.

        Returns:
            DataFrame with all stock price data
        """
        logger.info("Loading price data...")

        parquet_file = self.project_root / 'price_data_all.parquet'

        if not parquet_file.exists():
            raise FileNotFoundError(f"Price data file not found: {parquet_file}")

        try:
            df = pd.read_parquet(parquet_file)
            logger.info(f"✓ Loaded {len(df):,} records from {parquet_file.name}")
            logger.info(f"  - Columns: {', '.join(df.columns.tolist())}")
            logger.info(f"  - Total unique stocks: {df['name'].nunique()}")
            logger.info(f"  - Date range: {df['date'].min()} to {df['date'].max()}")
            return df

        except Exception as e:
            logger.error(f"Error loading price data: {e}")
            raise

    def filter_data(self, df: pd.DataFrame, stocks_to_keep: list) -> pd.DataFrame:
        """
        Filter price data to only include specified stocks.

        Args:
            df: Stock price DataFrame
            stocks_to_keep: List of stock names to keep

        Returns:
            Filtered DataFrame
        """
        logger.info(f"Filtering data to {len(stocks_to_keep)} stocks...")

        # Show initial stats
        initial_count = len(df)
        initial_stocks = df['name'].nunique()

        # Filter to stocks in the list
        df_filtered = df[df['name'].isin(stocks_to_keep)].copy()

        # Show filtered stats
        filtered_count = len(df_filtered)
        filtered_stocks = df_filtered['name'].nunique()

        logger.info(f"✓ Filtering complete:")
        logger.info(f"  - Records: {initial_count:,} → {filtered_count:,} "
                   f"({filtered_count/initial_count*100:.1f}% retained)")
        logger.info(f"  - Stocks: {initial_stocks} → {filtered_stocks}")

        # Show which stocks from options list were found
        found_stocks = set(df_filtered['name'].unique())
        expected_stocks = set(stocks_to_keep)
        missing_stocks = expected_stocks - found_stocks

        if missing_stocks:
            logger.warning(f"  ⚠ {len(missing_stocks)} stocks from options list not found in price data:")
            for stock in sorted(list(missing_stocks))[:10]:  # Show first 10
                logger.warning(f"    - {stock}")
            if len(missing_stocks) > 10:
                logger.warning(f"    ... and {len(missing_stocks) - 10} more")

        return df_filtered

    def save_filtered_data(self, df: pd.DataFrame,
                          parquet_output: str = 'price_data_filtered.parquet',
                          csv_output: str = 'price_data_filtered.csv'):
        """
        Save filtered data to both parquet and CSV formats.

        Args:
            df: Filtered DataFrame to save
            parquet_output: Output parquet filename
            csv_output: Output CSV filename
        """
        logger.info("Saving filtered data...")

        # Save as parquet
        parquet_path = self.project_root / parquet_output
        df.to_parquet(parquet_path, index=False)
        parquet_size = parquet_path.stat().st_size / 1024 / 1024  # MB
        logger.info(f"✓ Saved parquet: {parquet_path.name} ({parquet_size:.2f} MB)")

        # Save as CSV (pipe-delimited)
        csv_path = self.project_root / csv_output
        df.to_csv(csv_path, sep='|', index=False)
        csv_size = csv_path.stat().st_size / 1024 / 1024  # MB
        logger.info(f"✓ Saved CSV: {csv_path.name} ({csv_size:.2f} MB)")

    def run(self):
        """Execute the complete filtering process"""
        logger.info("="*80)
        logger.info("FILTERING STOCK PRICE DATA TO RELEVANT STOCKS")
        logger.info("="*80)

        try:
            # Load list of stocks with options
            stocks_with_options = self.load_options_stocks()

            # Load all price data
            df_all = self.load_price_data()

            # Filter to relevant stocks
            df_filtered = self.filter_data(df_all, stocks_with_options)

            # Save filtered data
            self.save_filtered_data(df_filtered)

            logger.info("")
            logger.info("="*80)
            logger.info("✓ FILTERING COMPLETE!")
            logger.info("="*80)
            logger.info(f"Filtered dataset contains:")
            logger.info(f"  - {len(df_filtered):,} records")
            logger.info(f"  - {df_filtered['name'].nunique()} unique stocks")
            logger.info(f"  - Date range: {df_filtered['date'].min()} to {df_filtered['date'].max()}")
            logger.info("")
            logger.info("Output files:")
            logger.info(f"  - price_data_filtered.parquet")
            logger.info(f"  - price_data_filtered.csv")
            logger.info("="*80)

            return True

        except Exception as e:
            logger.error(f"✗ Error during filtering: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    filter_tool = StockDataFilter()
    success = filter_tool.run()

    if success:
        print("\n✓ Success! You can now use price_data_filtered.parquet for your analysis.")
    else:
        print("\n✗ Filtering failed. Check the error messages above.")

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
