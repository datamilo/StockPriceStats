"""
Consolidated Utilities Module for Swedish Put Options Analysis

This module consolidates configuration, constants, and data loading utilities:
- Financial constants for options pricing
- Path configuration for Windows/WSL compatibility
- Data loading and preprocessing functions
- Business day calculations including Swedish holidays

Usage:
    from utils import TRADING_DAYS_PER_YEAR, PathConfig
    from utils import calculate_business_days_between, calculate_business_days_vectorized
"""

import sys
import yaml
import numpy as np
import pandas as pd
import datetime
import logging
import json
import requests
import holidays
import brotli
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm

# =============================================================================
# SECTION 1: FINANCIAL CONSTANTS
# =============================================================================

"""
Financial Constants

Single source of truth for financial calculation constants used throughout
the Swedish put options analysis system.

These constants ensure consistency across:
- Time-to-expiry calculations (DaysToExpiry / TRADING_DAYS_PER_YEAR)
- Black-Scholes pricing (T = DaysToExpiry / TRADING_DAYS_PER_YEAR)
- Implied volatility annualization (σ_annual = σ_daily * sqrt(TRADING_DAYS_PER_YEAR))
- Greeks calculations (all time-dependent Greeks use this convention)

CRITICAL: All parts of the system must use the same denominator to avoid
mixing trading-day and calendar-day conventions in calculations.
"""

TRADING_DAYS_PER_YEAR = 252
"""
Number of trading days (business days) per year in Swedish market.

This is the standard convention for options pricing:
- Used in Black-Scholes model for time parameter T
- Used for annualizing volatility: σ_annual = σ_daily * sqrt(252)
- Must be consistent with DaysToExpiry calculations (business days only)

Reference:
- NYSE: 252 days (standard)
- Swedish exchanges: ~252 business days (weekends + Swedish holidays excluded)
"""

CONTINUOUS_COMPOUNDING = True
"""
Whether to use continuous compounding for risk-free rate.

If True: Use exp(r * T) convention in Black-Scholes
If False: Use (1 + r)^T convention

Standard convention in finance is continuous compounding.
"""

IV_ANNUALIZATION_BASIS = TRADING_DAYS_PER_YEAR
"""
Number of trading days used when annualizing stored implied volatility.

Stored IV is typically calculated as:
  σ_stored = σ_daily * sqrt(IV_ANNUALIZATION_BASIS)

This is aliased to TRADING_DAYS_PER_YEAR for clarity.
Always use TRADING_DAYS_PER_YEAR as the canonical source.

Current status: IV is stored using 252 (trading days basis)
"""

VOLATILITY_ANNUALIZATION_CONSTANT = TRADING_DAYS_PER_YEAR
"""
Alias for TRADING_DAYS_PER_YEAR for clarity in volatility calculations.

Usage: annual_vol = daily_vol * math.sqrt(VOLATILITY_ANNUALIZATION_CONSTANT)

Note: Always use TRADING_DAYS_PER_YEAR as the canonical source.
This alias exists for code clarity only.
"""


def validate_constants():
    """
    Verify constants are internally consistent.

    This function is designed to be safe for import-time calls but can also
    be called explicitly from tests.

    Returns:
        bool: True if validation passed
    """
    logger = logging.getLogger(__name__)

    try:
        # Ensure annualization basis matches trading days
        assert IV_ANNUALIZATION_BASIS == TRADING_DAYS_PER_YEAR, \
            f"IV annualization basis ({IV_ANNUALIZATION_BASIS}) must equal " \
            f"trading days per year ({TRADING_DAYS_PER_YEAR})"

        # Ensure volatility annualization matches trading days
        assert VOLATILITY_ANNUALIZATION_CONSTANT == TRADING_DAYS_PER_YEAR, \
            f"Volatility annualization constant ({VOLATILITY_ANNUALIZATION_CONSTANT}) " \
            f"must equal trading days per year ({TRADING_DAYS_PER_YEAR})"

        return True
    except AssertionError as e:
        logger.warning(f"Constants validation failed: {e}")
        return False


# Safe import-time validation
_validation_passed = validate_constants()

# =============================================================================
# SECTION 2: PATH CONFIGURATION
# =============================================================================

class PathConfig:
    """Centralized path configuration loader with platform-aware conversions"""

    def __init__(self, config_file: str = "config/paths_config.yaml"):
        """
        Initialize path configuration.

        Args:
            config_file: Path to paths_config.yaml (relative to project root)

        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If config file is malformed
        """
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Path configuration file not found: {config_path.absolute()}\n"
                f"Expected location: {config_path}"
            )

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        if not self.config:
            raise ValueError(f"Path configuration is empty: {config_path}")

    @staticmethod
    def convert_windows_to_wsl(windows_path: str) -> str:
        """
        Convert Windows path to WSL path if running on WSL/Linux.

        Args:
            windows_path: Path in Windows format (e.g., C:/Users/...)

        Returns:
            Path in native format (WSL format on Linux, unchanged on Windows)
        """
        if sys.platform == 'win32':
            return windows_path

        # Running on WSL/Linux - convert Windows path to WSL mount path
        windows_path = windows_path.replace('\\', '/')
        if windows_path.startswith('C:/') or windows_path.startswith('C:\\'):
            return '/mnt/c' + windows_path[2:]

        return windows_path

    def _resolve_path(self, path_str: str) -> str:
        """Resolve a single path string, converting to appropriate format."""
        if not path_str:
            return None
        return self.convert_windows_to_wsl(path_str)

    def _resolve_path_list(self, path_list: List[str]) -> List[str]:
        """Resolve a list of paths, converting each to appropriate format."""
        if not path_list:
            return []
        return [self.convert_windows_to_wsl(p) for p in path_list if p]

    # Path accessor methods
    def get_onedrive_options_data_dir(self) -> str:
        return self._resolve_path(self.config['onedrive']['options_data'])

    def get_onedrive_nasdaq_stock_data_dir(self) -> str:
        return self._resolve_path(self.config['onedrive']['nasdaq_stock_data'])

    def get_price_data_path(self) -> str:
        sources = self.config['price_data_strategy']['sources']
        resolved_sources = self._resolve_path_list(sources)
        for source in resolved_sources:
            if Path(source).exists():
                return source
        return self._resolve_path(sources[0])

    def get_price_data_parquet(self) -> str:
        return self._resolve_path(self.config['input_data']['price_data_parquet'])

    def get_price_data_csv_legacy(self) -> str:
        return self._resolve_path(self.config['price_data_strategy']['sources'][-1])

    def get_options_data_parquet(self) -> str:
        return self._resolve_path(self.config['input_data']['options_data_parquet'])

    def get_iv_historical_parquet(self) -> str:
        return self._resolve_path(self.config['input_data']['iv_historical_parquet'])

    def get_drawdown_parquet(self) -> str:
        return self._resolve_path(self.config['input_data']['drawdown_parquet'])

    def get_main_analysis_output(self) -> str:
        return self._resolve_path(self.config['output_data']['main_analysis'])

    def get_iv_potential_decline_output(self) -> str:
        return self._resolve_path(self.config['output_data']['iv_potential_decline'])

    def get_stock_data_output(self) -> str:
        return self._resolve_path(self.config['output_data']['stock_data'])

    def get_probability_history_output(self) -> str:
        return self._resolve_path(self.config['output_data']['probability_history'])

    def get_last_updated_metadata(self) -> str:
        return self._resolve_path(self.config['output_data']['last_updated_metadata'])

    def get_monthly_stats_file(self) -> str:
        return self._resolve_path(self.config['monthly_data']['monthly_stats'])

    def get_volatility_data_file(self) -> str:
        return self._resolve_path(self.config['monthly_data']['volatility_data'])

    def get_monthly_reference_dir(self) -> str:
        return self._resolve_path(self.config['monthly_data']['reference_data_dir'])

    def get_options_available_file(self) -> str:
        return self._resolve_path(self.config['monthly_data']['options_available'])

    def get_mfn_links_file(self) -> str:
        return self._resolve_path(self.config['monthly_data']['mfn_links'])

    def get_previous_events_file(self) -> str:
        return self._resolve_path(self.config['monthly_data']['previous_events'])

    def get_name_mapping_file(self) -> str:
        return self._resolve_path(self.config['monthly_data']['name_mapping'])

    def get_weekly_maintenance_dir(self) -> str:
        return self._resolve_path(self.config['weekly_maintenance']['data_dir'])

    def get_probability_history_onedrive_dir(self) -> str:
        return self._resolve_path(self.config['probability_history']['onedrive_dir'])

    def get_backup_onedrive_dir(self) -> str:
        return self._resolve_path(self.config['backup']['onedrive_dir'])

    def get_backup_timestamped_dir(self) -> str:
        return self._resolve_path(self.config['backup']['timestamped_backups'])

    def get_files_to_backup(self) -> List[str]:
        return self._resolve_path_list(self.config['backup']['files'])

    def get_backup_retention_days(self) -> int:
        return self.config['backup']['retention_days']

    def get_logs_dir(self) -> str:
        return self._resolve_path(self.config['project_dirs']['logs'])

    def get_input_dir(self) -> str:
        return self._resolve_path(self.config['project_dirs']['input'])

    def get_output_dir(self) -> str:
        return self._resolve_path(self.config['project_dirs']['output'])

    def get_config_dir(self) -> str:
        return self._resolve_path(self.config['project_dirs']['config'])

    def get_archive_dir(self) -> str:
        return self._resolve_path(self.config['project_dirs']['archive'])


def get_path_config() -> PathConfig:
    """
    Convenience function to get PathConfig instance.

    Returns:
        PathConfig instance

    Example:
        config = get_path_config()
        price_data = config.get_price_data_path()
    """
    return PathConfig()


# Initialize path configuration for data access
try:
    PATH_CONFIG = get_path_config()
except (FileNotFoundError, Exception):
    PATH_CONFIG = None

# =============================================================================
# SECTION 3: DATA LOADING UTILITIES
# =============================================================================

def load_configuration():
    """Load configuration constants"""
    return {
        'stock_value_limit': 100000,
        'courtage': 150,
        'folder_path': 'input',
        'current_year': datetime.datetime.now().year,
        'todays_date': datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    }


def calculate_business_days_between(start_date, end_date):
    """
    Calculate number of business days (trading days) between two dates.

    Excludes weekends and Swedish public holidays.

    Args:
        start_date: datetime or date object (start of range, inclusive)
        end_date: datetime or date object (end of range, exclusive)

    Returns:
        Integer number of business days
    """
    # Convert to dates if datetime objects
    if isinstance(start_date, pd.Timestamp):
        start_date = start_date.date()
    elif isinstance(start_date, datetime.datetime):
        start_date = start_date.date()

    if isinstance(end_date, pd.Timestamp):
        end_date = end_date.date()
    elif isinstance(end_date, datetime.datetime):
        end_date = end_date.date()

    # Get Swedish holidays for the relevant years
    years = set()
    current = start_date
    while current <= end_date:
        years.add(current.year)
        current += datetime.timedelta(days=1)

    se_holidays = holidays.country_holidays('SE', years=sorted(list(years)))

    # Count business days
    business_days = 0
    current = start_date

    while current < end_date:
        # Check if weekday (Monday=0 to Friday=4)
        if current.weekday() < 5:
            # Check if not Swedish holiday
            if current not in se_holidays:
                business_days += 1
        current += datetime.timedelta(days=1)

    return business_days


def calculate_business_days_vectorized(df, date_col_start, date_col_end):
    """
    VECTORIZED version of business days calculation - MUCH FASTER for large datasets.

    Use this instead of df.apply(calculate_business_days_between) for DataFrames.
    Approximately 100x faster than apply() for large datasets.

    Args:
        df: DataFrame with date columns
        date_col_start: Name of start date column
        date_col_end: Name of end date column

    Returns:
        NumPy array of business days
    """
    # Convert to numpy datetime64 for busday_count
    start_dates_np = df[date_col_start].values.astype('datetime64[D]')
    end_dates_np = df[date_col_end].values.astype('datetime64[D]')

    # Get all unique years to pre-load holidays once
    all_dates = pd.concat([df[date_col_start], df[date_col_end]])
    years = set(all_dates.dt.year.unique())
    se_holidays = holidays.country_holidays('SE', years=list(years))

    # Step 1: Use numpy.busday_count for weekday calculation (fast)
    weekday_count = np.busday_count(start_dates_np, end_dates_np)

    # Step 2: Subtract Swedish holidays in date range (vectorized)
    holiday_dates = np.array(list(se_holidays.keys()), dtype='datetime64[D]')

    # For each row, count holidays between start and end dates
    holiday_count = np.zeros(len(df), dtype=int)
    for i in range(len(df)):
        start = start_dates_np[i]
        end = end_dates_np[i]

        # Holidays in range
        holidays_in_range = holiday_dates[(holiday_dates >= start) & (holiday_dates < end)]

        # Count only weekday holidays
        for hdate in holidays_in_range:
            h_py = hdate.astype('datetime64[D]').astype('O')
            if h_py.weekday() < 5:
                holiday_count[i] += 1

    # Step 3: Return business days
    return weekday_count - holiday_count


def load_options_data(folder_path):
    """Load and preprocess options price data"""
    try:
        if PATH_CONFIG:
            options_file = PATH_CONFIG.get_options_data_parquet()
            df_options = pd.read_parquet(options_file)
        else:
            df_options = pd.read_csv(f'{folder_path}/All_Options_Data.csv', sep='|')
    except (FileNotFoundError, Exception):
        df_options = pd.read_csv(f'{folder_path}/All_Options_Data.csv', sep='|')

    df_options['ExpiryDate'] = pd.to_datetime(df_options['ExpiryDate'])
    df_options['Update_date'] = pd.to_datetime(df_options['Update_date'])

    return df_options


def load_stock_price_data(folder_path):
    """Load and merge stock price data from multiple sources"""
    try:
        if PATH_CONFIG:
            price_file = PATH_CONFIG.get_price_data_parquet()
            df_stock_prices = pd.read_parquet(price_file)
        else:
            df_stock_prices = pd.read_csv(f'{folder_path}/price_data_all.csv', sep='|', low_memory=False)
    except (FileNotFoundError, Exception):
        df_stock_prices = pd.read_csv(f'{folder_path}/price_data_all.csv', sep='|', low_memory=False)

    df_stock_prices['date'] = pd.to_datetime(df_stock_prices['date'])

    # Standardize columns
    df_stock_prices = df_stock_prices[['date', 'name', 'close']].copy()
    df_stock_prices.columns = ['Update_date', 'Name', 'StockPrice']
    df_stock_prices['Update_date'] = pd.to_datetime(df_stock_prices['Update_date'])

    return df_stock_prices


def load_risk_free_rate(todays_date):
    """Download and process risk-free interest rate data"""
    print("Loading risk-free interest rate data...")

    def is_valid_number(text):
        """Check if text is a valid number"""
        if not text:
            return False
        import re
        pattern = r'^-?\d+([.,]\d+)?$'
        return bool(re.match(pattern, text.strip()))

    # First attempt: API endpoint
    url = "https://www.di.se/market/instrument-history/33383/"
    headers = {
        "Referer": "https://www.di.se/rantor/stat-10y-33383/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        raw_points = data.get("points", [])

        df_10year_bond = pd.DataFrame(raw_points, columns=["timestamp_ms", "value"])
        df_10year_bond["date"] = pd.to_datetime(df_10year_bond["timestamp_ms"], unit='ms').dt.date
        df_10year_bond = df_10year_bond[["date", "value"]]
        df_10year_bond["date"] = pd.to_datetime(df_10year_bond["date"])
        df_10year_bond.columns = ['Update_date', 'interest_rate']
        df_10year_bond['interest_rate'] = df_10year_bond['interest_rate'] / 100

        # Check if today's data is missing from API
        has_todays_data = len(df_10year_bond.loc[df_10year_bond['Update_date'] == todays_date]) > 0

        if not has_todays_data and len(df_10year_bond) > 0:
            most_recent_date = df_10year_bond['Update_date'].max()
            most_recent_rate = df_10year_bond.loc[df_10year_bond['Update_date'] == most_recent_date, 'interest_rate'].iloc[0]
            df_10year_bond.loc[len(df_10year_bond)] = [todays_date, most_recent_rate]
            df_10year_bond = df_10year_bond.reset_index(drop=True)

        return df_10year_bond

    except Exception as e:
        print(f'Error loading interest rate data: {e}')
        return pd.DataFrame(columns=['Update_date', 'interest_rate'])


def load_historical_iv_data(folder_path):
    """Load historical implied volatility data"""
    try:
        if PATH_CONFIG:
            iv_file = PATH_CONFIG.get_iv_historical_parquet()
            df_iv_historical = pd.read_parquet(iv_file)
        else:
            df_iv_historical = pd.read_csv(f'{folder_path}/Implied_Volatility_Historical_ALL.csv', sep='|', low_memory=False)
    except (FileNotFoundError, Exception):
        df_iv_historical = pd.read_csv(f'{folder_path}/Implied_Volatility_Historical_ALL.csv', sep='|', low_memory=False)

    df_iv_historical = df_iv_historical.loc[(df_iv_historical['ImpliedVolatilityUntilExpiry'].notna())].reset_index(drop=True)

    # Convert date columns
    df_iv_historical['Update_date'] = pd.to_datetime(df_iv_historical['Update_date'])
    df_iv_historical['ExpiryDate'] = pd.to_datetime(df_iv_historical['ExpiryDate'])

    return df_iv_historical
