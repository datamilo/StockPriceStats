"""
Data Loading and Preprocessing Module for Swedish Put Options Analysis
Handles all CSV file loading, data merging, and preprocessing operations.
"""

import numpy as np
import pandas as pd
import datetime
import requests
import holidays
import brotli
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
from constants import TRADING_DAYS_PER_YEAR
from config_utils import get_path_config

# Initialize path configuration for OneDrive data access
PATH_CONFIG = get_path_config()

def load_configuration():
    """Load configuration constants"""
    return {
        'stock_value_limit': 100000,
        'courtage': 150,
        'folder_path': 'input',  # Uses input folder - this is intentional new functionality
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
    Approximately 100x faster than apply() for 4,879+ options.

    Algorithm:
    1. Use numpy.busday_count for weekday counting (extremely fast)
    2. Subtract Swedish holidays that fall in the date range
    3. Return correct business days excluding both weekends and holidays

    Args:
        df: DataFrame with date columns
        date_col_start: Name of start date column
        date_col_end: Name of end date column

    Returns:
        NumPy array of business days
    """
    import numpy as np
    from datetime import datetime as dt_class

    # Convert to numpy datetime64 for busday_count
    start_dates_np = df[date_col_start].values.astype('datetime64[D]')
    end_dates_np = df[date_col_end].values.astype('datetime64[D]')

    # Get all unique years to pre-load holidays once
    all_dates = pd.concat([df[date_col_start], df[date_col_end]])
    years = set(all_dates.dt.year.unique())
    se_holidays = holidays.country_holidays('SE', years=list(years))

    # Step 1: Use numpy.busday_count for weekday calculation (fast)
    # This counts Monday-Friday, excluding weekends
    weekday_count = np.busday_count(start_dates_np, end_dates_np)

    # Step 2: Subtract Swedish holidays in date range (vectorized)
    # Convert holidays to numpy array for vectorized comparison
    holiday_dates = np.array(list(se_holidays.keys()), dtype='datetime64[D]')

    # For each row, count holidays between start and end dates
    holiday_count = np.zeros(len(df), dtype=int)
    for i in range(len(df)):
        # Count holidays that fall within the date range AND are weekdays
        start = start_dates_np[i]
        end = end_dates_np[i]

        # Holidays in range
        holidays_in_range = holiday_dates[(holiday_dates >= start) & (holiday_dates < end)]

        # Count only weekday holidays
        for hdate in holidays_in_range:
            # Convert numpy datetime64 to python date for weekday check
            h_py = hdate.astype('datetime64[D]').astype('O')  # Convert to Python object
            if h_py.weekday() < 5:  # Only count if it's a weekday
                holiday_count[i] += 1

    # Step 3: Return business days (weekdays - weekday holidays)
    return weekday_count - holiday_count

def load_options_data(folder_path):
    """Load and preprocess options price data"""
    print("Loading options data...")

    # Read from OneDrive location (primary storage)
    # Note: folder_path parameter kept for backward compatibility but not used for parquet
    try:
        options_file = PATH_CONFIG.get_options_data_parquet()
        df_options = pd.read_parquet(options_file)
    except FileNotFoundError:
        # Fallback to CSV in local folder
        df_options = pd.read_csv(f'{folder_path}/All_Options_Data.csv', sep='|')
    df_options['ExpiryDate'] = pd.to_datetime(df_options['ExpiryDate'])
    df_options['Update_date'] = pd.to_datetime(df_options['Update_date'])

    # Clean column names
    columns = ['Name', 'OptionName','StrikePrice', 'ExpiryYear',
               'ExpiryMonth', 'ExpiryDate', 'Update date', 'Bid', 'Ask',
               'Bid vol.', 'Ask vol.', 'Volume', 'High', 'Low', 'Last',
               'Opening price', 'Closing price']

    columns = [i.replace('(','').replace(')','').replace(' ','_').replace('.','') for i in columns]
    df_options = df_options[columns]

    # Filter to most recent date
    df_options = df_options.loc[df_options['Update_date'] == df_options['Update_date'].max()]
    df_options = df_options.reset_index(drop=True)

    # Clean bid/ask data
    df_options['Bid'] = df_options['Bid'].fillna(0)
    df_options['Ask'] = df_options['Ask'].fillna(0)
    df_options['BidAskSpreadPct'] = (df_options['Ask'] - df_options['Bid']) / df_options['Bid']
    df_options.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_options.dropna(subset=['BidAskSpreadPct'], inplace=True)

    return df_options

def load_stock_price_data(folder_path):
    """Load and merge stock price data from multiple sources"""
    print("Loading stock price data...")

    # Load main stock price data from OneDrive (primary storage)
    # Note: folder_path parameter kept for backward compatibility but not used for parquet
    try:
        price_file = PATH_CONFIG.get_price_data_parquet()
        df_stock_prices = pd.read_parquet(price_file)
    except FileNotFoundError:
        # Fallback to CSV
        df_stock_prices = pd.read_csv(f'{folder_path}/price_data_all.csv', sep='|', low_memory=False)
    df_stock_prices['date'] = pd.to_datetime(df_stock_prices['date'])

    # Load additional price data
    df_price_data = pd.read_csv(f'{folder_path}/price_data_all_stocks.csv', sep='|')
    df_price_data['Nordnet_Name'] = df_price_data.groupby('name')['Nordnet_Name'].ffill()
    df_price_data['date'] = pd.to_datetime(df_price_data['date'])

    # Standardize columns and merge
    df_price_data = df_price_data[['date', 'Nordnet_Name', 'open', 'high', 'low', 'close', 'volume']]
    df_price_data.columns = ['date', 'name', 'open', 'high', 'low', 'close', 'volume']

    df_stock_prices = pd.concat([df_stock_prices, df_price_data])
    df_stock_prices = df_stock_prices.drop_duplicates(subset=['date', 'name'], keep='first')

    # Prepare for merging with options data
    df_stock_prices = df_stock_prices[['date', 'name', 'close']]
    df_stock_prices.columns = ['Update_date', 'Name', 'StockPrice']
    df_stock_prices['Update_date'] = pd.to_datetime(df_stock_prices['Update_date'])

    return df_stock_prices

def load_dividend_data(folder_path, todays_date):
    """Load and process dividend and financial report dates"""
    print("Loading dividend data...")

    df_important_dates = pd.read_csv(f'{folder_path}/last_prices.csv', sep='|')
    df_important_dates.rename(columns={'name':'Name'}, inplace=True)
    df_important_dates['dividend_date'] = pd.to_datetime(df_important_dates['dividend_date'])
    df_important_dates['report_date'] = pd.to_datetime(df_important_dates['report_date'])
    df_important_dates['excluding_date'] = pd.to_datetime(df_important_dates['excluding_date'])

    # Remove past excluding dates
    df_important_dates.loc[df_important_dates['excluding_date'] <= todays_date, 'excluding_date'] = np.nan

    return df_important_dates[['Name','excluding_date', 'dividend_date', 'report_date', 'dividend_amount']]

def load_drawdown_data(folder_path):
    """Load and process historical drawdown data"""
    print("Loading drawdown data...")

    # Load from OneDrive (primary storage)
    drawdown_file = PATH_CONFIG.get_drawdown_parquet()
    df_drawdowns = pd.read_parquet(drawdown_file)

    # Convert date columns
    df_drawdowns['WorstTimeStartDate'] = pd.to_datetime(df_drawdowns['WorstTimeStartDate'])
    df_drawdowns['WorstTimeEndDate'] = pd.to_datetime(df_drawdowns['WorstTimeEndDate'])
    df_drawdowns['WorstDayInRange'] = pd.to_datetime(df_drawdowns['WorstDayInRange'])

    # Add month columns
    df_drawdowns['WorstTimeStartDate_Month'] = df_drawdowns['WorstTimeStartDate'].dt.month
    df_drawdowns['WorstTimeEndDate_Month'] = df_drawdowns['WorstTimeEndDate'].dt.month
    df_drawdowns['WorstDayInRange_Month'] = df_drawdowns['WorstDayInRange'].dt.month

    # CRITICAL: Rename columns to match legacy logic (missing from reorganized script!)
    # Keep both DeclineInRange (for bad_drawdown) and HistoricalWorstDecline (for worst_drawdown)
    df_drawdowns['HistoricalWorstDecline'] = df_drawdowns['DeclineInRange']
    df_drawdowns.rename(columns={'BusinessDaysInRange': 'BusinessDaysUntilExpire'}, inplace=True)

    # Keep full dataset for bad decline calculations (legacy script uses ALL data, not just post-2010)
    df_drawdowns_full = df_drawdowns.copy()
    df_drawdowns_full['RankNthWorstTimeRange'] = df_drawdowns_full.groupby(['Name', 'BusinessDaysUntilExpire'])['HistoricalWorstDecline'].rank(method="dense", ascending=True)

    # Split data pre- and post-2010 (matching legacy logic)
    df_drawdowns_2008 = df_drawdowns.loc[df_drawdowns['WorstTimeStartDate'].dt.year < 2010].copy()
    df_drawdowns = df_drawdowns.loc[df_drawdowns['WorstTimeStartDate'].dt.year >= 2010].copy()
    df_drawdowns['RankNthWorstTimeRange'] = df_drawdowns.groupby(['Name', 'BusinessDaysUntilExpire'])['HistoricalWorstDecline'].rank(method="dense", ascending=True)

    return df_drawdowns, df_drawdowns_2008, df_drawdowns_full

def load_risk_free_rate(todays_date):
    """Download and process risk-free interest rate data with fallback to most recent available"""
    import re

    print("Loading risk-free interest rate data...")

    def is_valid_number(text):
        """Check if text is a valid number (handles commas, dots, negative numbers)"""
        if not text:
            return False
        # Pattern matches: optional negative, digits, optional decimal (. or ,), optional more digits
        pattern = r'^-?\d+([.,]\d+)?$'
        return bool(re.match(pattern, text.strip()))

    # First attempt: API endpoint
    url = "https://www.di.se/market/instrument-history/33383/"
    headers = {
        "Referer": "https://www.di.se/rantor/stat-10y-33383/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
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
        df_10year_bond['interest_rate'] = df_10year_bond['interest_rate']/100

        # Check if today's data is missing from API
        has_todays_data = len(df_10year_bond.loc[df_10year_bond['Update_date'] == todays_date]) > 0

        if not has_todays_data:
            print("Today's bond data missing from API. Attempting web scraping...")

            # Second attempt: web scraping
            url = "https://www.di.se/rantor/stat-10y-33383/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "br",
                "Accept-Language": "en-SE,en;q=0.9",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1"
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.headers.get("Content-Encoding") == "br":
                try:
                    html = brotli.decompress(response.content).decode("utf-8")
                except:
                    html = response.text
            else:
                html = response.text

            soup = BeautifulSoup(html, "html.parser")
            price_div = soup.find("div", class_="js_instrument-details__price instrument-details__price-main")

            if price_div:
                rate_text = price_div.text.strip()

                # Validate that scraped text is a valid number
                if is_valid_number(rate_text):
                    try:
                        # Convert to float (handle comma as decimal separator)
                        interest_rate = float(rate_text.replace(',', '.')) / 100
                        df_10year_bond.loc[len(df_10year_bond)] = [todays_date, interest_rate]
                        df_10year_bond = df_10year_bond.reset_index(drop=True)
                        has_todays_data = True
                        print(f"Successfully scraped today's rate: {interest_rate*100:.4f}%")
                    except (ValueError, TypeError) as e:
                        print(f"Failed to convert scraped rate '{rate_text}' to number: {e}")
                else:
                    print(f"Scraped value '{rate_text}' is not a valid number (rate not yet published)")

        # Final check: if today's data is still missing, use most recent available
        if not has_todays_data and len(df_10year_bond) > 0:
            most_recent_date = df_10year_bond['Update_date'].max()
            most_recent_rate = df_10year_bond.loc[df_10year_bond['Update_date'] == most_recent_date, 'interest_rate'].iloc[0]

            print(f"WARNING: Today's rate not available. Using most recent rate from {most_recent_date.date()}: {most_recent_rate*100:.4f}%")

            # Add today's date with most recent rate
            df_10year_bond.loc[len(df_10year_bond)] = [todays_date, most_recent_rate]
            df_10year_bond = df_10year_bond.reset_index(drop=True)

        elif not has_todays_data and len(df_10year_bond) == 0:
            print('CRITICAL WARNING: No interest rate data available at all!')
        else:
            current_rate = df_10year_bond.loc[df_10year_bond['Update_date'] == todays_date, 'interest_rate'].iloc[0]
            print(f"Interest rate data successfully loaded. Current rate: {current_rate*100:.4f}%")

        return df_10year_bond

    except Exception as e:
        print(f'Error loading interest rate data: {e}')
        import traceback
        traceback.print_exc()
        # Return empty dataframe with proper structure
        return pd.DataFrame(columns=['Update_date', 'interest_rate'])

def load_historical_iv_data(folder_path):
    """Load historical implied volatility data"""
    print("Loading historical IV data...")

    # Load from OneDrive (primary storage)
    try:
        iv_file = PATH_CONFIG.get_iv_historical_parquet()
        df_iv_historical = pd.read_parquet(iv_file)
    except FileNotFoundError:
        # Fallback to CSV if Parquet doesn't exist yet
        df_iv_historical = pd.read_csv(f'{folder_path}/Implied_Volatility_Historical_ALL.csv', sep='|', low_memory=False)
    df_iv_historical = df_iv_historical.loc[(df_iv_historical['ImpliedVolatilityUntilExpiry'].notna())].reset_index(drop=True)

    # Convert date columns
    df_iv_historical['Update_date'] = pd.to_datetime(df_iv_historical['Update_date'])
    df_iv_historical['Min_Future_StockPrice_Date'] = pd.to_datetime(df_iv_historical['Min_Future_StockPrice_Date'])
    df_iv_historical['Max_Future_StockPrice_Date'] = pd.to_datetime(df_iv_historical['Max_Future_StockPrice_Date'])
    df_iv_historical['ExpiryDate'] = pd.to_datetime(df_iv_historical['ExpiryDate'])

    # Calculate derived metrics
    df_iv_historical['StockValueLimit'] = 100000
    df_iv_historical['NumberOfContractsBasedOnLimit'] = round((df_iv_historical['StockValueLimit']/df_iv_historical['StockPrice'])/100)
    df_iv_historical['Premium'] = df_iv_historical['Bid_Ask_Mid_Price'] * df_iv_historical['NumberOfContractsBasedOnLimit'] * 100
    df_iv_historical['YearsToExpiry'] = df_iv_historical['DaysToExpiry'] / TRADING_DAYS_PER_YEAR
    df_iv_historical['ImpliedVolatility'] = df_iv_historical['ImpliedVolatilityUntilExpiry']/np.sqrt(df_iv_historical['YearsToExpiry'])
    df_iv_historical['StrikeCloseDistance_ABS'] = df_iv_historical['StrikeCloseDistance'].abs()

    return df_iv_historical

def load_probability_data(folder_path):
    """Load probability and statistical data files"""
    print("Loading probability and statistical data...")

    # Load probability of worthless data
    df_pow = pd.read_csv(f'{folder_path}/Historical_Outcome_ProbOfWorthless_Above_80pct_POW.csv', sep='|')
    df_pow_stats = pd.read_csv(f'{folder_path}/Stats_Historical_Outcome_ProbOfWorthless_Above_80pct_POW.csv', sep='|')
    df_pow_stats_per_stock = pd.read_csv(f'{folder_path}/stats_per_stock.csv', sep='|')
    df_pow_stats_per_stock = df_pow_stats_per_stock.loc[df_pow_stats_per_stock['count'] >= 5]

    # Load Bayesian calibration parameters
    with open(f"{folder_path}/ProbWorthless_Bayesian_IsoCal_Parameters.json", "r") as f:
        params = json.load(f)

    # Load lookup tables
    lookup = pd.read_csv(f'{folder_path}/ProbWorthless_Bayesian_IsoCal_ExpiryBins_and_ProbBins.csv', sep='|')
    df_losses_bayesian = pd.read_csv(f'{folder_path}/Stats_Historical_Losses_using_ProbWorthless_Bayesian_IsoCal.csv', sep='|')
    df_losses_bayesian = df_losses_bayesian[['Name', 'ProbBin_Bayesian', 'ExpiryBin_Bayesian', '100k_Invested_Loss_Mean', '100k_Invested_Loss_Median']]

    # Load accuracy data
    df_accuracy = pd.read_csv(f'{folder_path}/IV_Closest_to_Strike_Accuracy_Per_Day_to_Expiry.csv', sep='|')
    # Note: SampleSize filtering moved to accuracy calculation function to match legacy logic

    # Load brier score wins
    with open(f'{folder_path}/brier_score_wins.json', 'r') as f:
        wins = json.load(f)

    return {
        'df_pow': df_pow,
        'df_pow_stats': df_pow_stats,
        'df_pow_stats_per_stock': df_pow_stats_per_stock,
        'bayesian_params': params,
        'lookup': lookup,
        'df_losses_bayesian': df_losses_bayesian,
        'df_accuracy': df_accuracy,
        'brier_wins': wins
    }

def load_nasdaq_mapping(folder_path):
    """Load NASDAQ to Nordnet name mapping"""
    df_mapping = pd.read_csv(f'{folder_path}/nasdaq_nordnet_stock_names.csv', sep='|')
    df_mapping['StockName'] = df_mapping['StockName'].str.replace('Sagax_B', 'Sagax_AB_B')
    df_mapping.columns = ['name', 'NordnetName']
    return df_mapping

def load_omx_data(folder_path):
    """Load OMX30 index data for correlation calculations"""
    df_omx = pd.read_csv(f'{folder_path}/omxs30.csv', sep='|')
    df_omx['date'] = pd.to_datetime(df_omx['date'])
    return df_omx

def merge_options_with_stock_data(df_options, df_stock_prices):
    """Merge options data with stock prices and calculate basic metrics"""
    print("Merging options with stock price data...")

    df_merged = df_options.merge(df_stock_prices, on=['Update_date', 'Name'], how='left')

    # Calculate derived metrics
    df_merged['StrikeCloseDistance'] = round((df_merged['StrikePrice'] - df_merged['StockPrice']) / df_merged['StockPrice'], 4)
    df_merged['Bid_Ask_Mid_Price'] = (df_merged['Bid'] + df_merged['Ask'])/2

    return df_merged

def apply_dividend_adjustments(df, df_dividend_data, todays_date):
    """Apply dividend adjustments and financial report indicators"""
    print("Applying dividend adjustments...")

    df = df.merge(df_dividend_data, on='Name', how='left')

    # Set to 'Y' based on conditions (exactly like legacy - NO initialization)
    df.loc[(df['report_date'] <= df['ExpiryDate']) & (df['report_date'] > todays_date), 'FinancialReport'] = 'Y'
    df.loc[(df['excluding_date'] <= df['ExpiryDate']) & (df['excluding_date'] > todays_date), 'X-Day'] = 'Y'


    df.loc[df['X-Day'] == 'Y', 'StockPrice'] = df['StockPrice'] - df['dividend_amount']

    return df

def filter_valid_options(df):
    """Filter for valid options meeting minimum criteria"""
    print("Filtering valid options...")

    df = df.loc[(df['StockPrice'] >= df['StrikePrice']) & (df['Bid'] > 0.01)].copy().reset_index(drop=True)

    # Calculate days to expiry and spread metrics
    # Use business days (trading days) instead of calendar days
    # Use vectorized version for performance (100x faster than df.apply)
    df['DaysToExpiry'] = calculate_business_days_vectorized(df, 'Update_date', 'ExpiryDate')
    df['AskBidSpread'] = round(df['Ask']/df['Bid'], 2)

    return df[['Name', 'OptionName', 'StrikePrice', 'Update_date', 'ExpiryDate', 'DaysToExpiry',
              'StockPrice','Bid', 'Ask', 'Bid_Ask_Mid_Price', 'AskBidSpread', 'FinancialReport', 'X-Day']].reset_index(drop=True)

def load_all_data():
    """Main function to load and preprocess all data"""
    print("Starting data loading pipeline...")

    config = load_configuration()
    folder_path = config['folder_path']
    todays_date = config['todays_date']

    # Load all data sources
    df_options = load_options_data(folder_path)
    df_stock_prices = load_stock_price_data(folder_path)
    df_dividend_data = load_dividend_data(folder_path, todays_date)
    df_drawdowns, df_drawdowns_2008, df_drawdowns_full = load_drawdown_data(folder_path)
    df_interest_rate = load_risk_free_rate(todays_date)
    df_iv_historical = load_historical_iv_data(folder_path)
    prob_data = load_probability_data(folder_path)
    df_nasdaq_mapping = load_nasdaq_mapping(folder_path)
    df_omx = load_omx_data(folder_path)

    # Merge and process main dataset
    df = merge_options_with_stock_data(df_options, df_stock_prices)
    df = apply_dividend_adjustments(df, df_dividend_data, todays_date)
    df = filter_valid_options(df)

    # Process drawdown data into aggregated historical decline fields (missing from reorganized script!)
    print("Processing drawdown data...")

    # Process current period (post-2010) drawdown data
    df_worst_days_100 = df_drawdowns.loc[(df_drawdowns['BusinessDaysUntilExpire'] <= 130)].sort_values(['Name', 'BusinessDaysUntilExpire', 'RankNthWorstTimeRange'],ascending=[True, False, True]).copy()
    df_worst_days_100 = df_worst_days_100.drop_duplicates(subset=['Name', 'RankNthWorstTimeRange'], keep='first')

    df_worst_days_50 = df_drawdowns.loc[(df_drawdowns['BusinessDaysUntilExpire'] <= 50)].sort_values(['Name', 'BusinessDaysUntilExpire', 'RankNthWorstTimeRange'],ascending=[True, False, True]).copy()
    df_worst_days_50 = df_worst_days_50.drop_duplicates(subset=['Name', 'RankNthWorstTimeRange'], keep='first')

    # Create aggregated decline fields for current period
    df_drawdowns_worst_100 = df_worst_days_100[df_worst_days_100['RankNthWorstTimeRange'] == 1][['Name', 'HistoricalWorstDecline']].drop_duplicates()
    df_drawdowns_worst_100.columns = ['Name', 'Historical100DaysWorstDecline']

    df_drawdowns_worst_50 = df_worst_days_50[df_worst_days_50['RankNthWorstTimeRange'] == 1][['Name', 'HistoricalWorstDecline']].drop_duplicates()
    df_drawdowns_worst_50.columns = ['Name', 'Historical50DaysWorstDecline']

    # Process 2008 period data
    df_drawdowns_2008['RankNthWorstTimeRange'] = df_drawdowns_2008.groupby(['Name', 'BusinessDaysUntilExpire'])['HistoricalWorstDecline'].rank(method="dense", ascending=True)

    df_worst_days_100_2008 = df_drawdowns_2008.loc[(df_drawdowns_2008['BusinessDaysUntilExpire'] <= 130)].sort_values(['Name', 'BusinessDaysUntilExpire', 'RankNthWorstTimeRange'],ascending=[True, False, True]).copy()
    df_worst_days_100_2008 = df_worst_days_100_2008.drop_duplicates(subset=['Name', 'RankNthWorstTimeRange'], keep='first')

    df_worst_days_50_2008 = df_drawdowns_2008.loc[(df_drawdowns_2008['BusinessDaysUntilExpire'] <= 130)].sort_values(['Name', 'BusinessDaysUntilExpire', 'RankNthWorstTimeRange'],ascending=[True, False, True]).copy()
    df_worst_days_50_2008 = df_worst_days_50_2008.drop_duplicates(subset=['Name', 'RankNthWorstTimeRange'], keep='first')

    # Create aggregated decline fields for 2008 period
    df_drawdowns_worst_100_2008 = df_worst_days_100_2008[df_worst_days_100_2008['RankNthWorstTimeRange'] == 1][['Name', 'HistoricalWorstDecline']].drop_duplicates()
    df_drawdowns_worst_100_2008.columns = ['Name', '2008_100DaysWorstDecline']

    df_drawdowns_worst_50_2008 = df_worst_days_50_2008[df_worst_days_50_2008['RankNthWorstTimeRange'] == 1][['Name', 'HistoricalWorstDecline']].drop_duplicates()
    df_drawdowns_worst_50_2008.columns = ['Name', '2008_50DaysWorstDecline']

    # Merge all aggregated fields into a single drawdown summary
    # CRITICAL FIX: Use LEFT JOIN for 2008 data to exactly match legacy script behavior
    df_drawdown_summary = df_drawdowns_worst_100.merge(df_drawdowns_worst_50, on='Name', how='outer')
    df_drawdown_summary = df_drawdown_summary.merge(df_drawdowns_worst_100_2008, on='Name', how='left')
    df_drawdown_summary = df_drawdown_summary.merge(df_drawdowns_worst_50_2008, on='Name', how='left')

    print(f"Data loading complete. Processed {len(df)} valid options.")

    return {
        'df_main': df,
        'df_stock_prices': df_stock_prices,
        'df_drawdowns': df_drawdowns,
        'df_drawdowns_full': df_drawdowns_full,
        'df_drawdown_summary': df_drawdown_summary,
        'df_interest_rate': df_interest_rate,
        'df_iv_historical': df_iv_historical,
        'df_nasdaq_mapping': df_nasdaq_mapping,
        'df_omx': df_omx,
        'prob_data': prob_data,
        'config': config
    }

if __name__ == "__main__":
    # Test the data loading pipeline
    data = load_all_data()
    print(f"Loaded data with {len(data['df_main'])} options")