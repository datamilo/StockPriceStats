"""
Support Level Analysis Dashboard

Analyzes support levels based on rolling lows:
- When support levels break (rolling low decreases)
- How long support levels last
- Magnitude of breaks
- Frequency of breaks
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
import plotly.graph_objects as go
from pathlib import Path
import warnings

# Suppress Plotly's deprecation warnings about keyword arguments
warnings.filterwarnings('ignore', message='The keyword arguments have been deprecated')

# Configuration - paths relative to this script file
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'
H001_RESULTS_DIR = SCRIPT_DIR

# Page config
st.set_page_config(page_title="Support Level Analysis", layout="wide")
st.title("📊 Support Level Analysis")

# Cache data loading for performance
@st.cache_data
def load_all_price_data():
    """Load price data once and cache it"""
    data_file = str(DATA_FILE)

    try:
        df = pd.read_parquet(data_file)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(['name', 'date']).reset_index(drop=True)
        df = df.rename(columns={
            'date': 'Date',
            'name': 'Stock',
            'low': 'Low',
            'high': 'High',
            'close': 'Close',
            'open': 'Open'
        })
        return df
    except FileNotFoundError as e:
        st.error(f"❌ Data file not found at: {data_file}")
        st.info(f"Expected to find price_data_filtered.parquet in the StockPriceStats root directory")
        raise
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        raise

@st.cache_data
def load_results_for_period(period_name):
    """Load detailed results for a specific period with memory optimization"""
    file = f'{period_name.lower().replace(" ", "_").replace("-", "_")}_detailed_results.parquet'
    filepath = Path(H001_RESULTS_DIR) / file

    if not filepath.exists():
        return None

    try:
        # Load with only essential columns to reduce memory usage
        # This is much faster than loading all columns
        cols_to_load = [
            'stock', 'support_date', 'support_level',
            'wait_days', 'success', 'days_to_break', 'break_pct',
            'expiry_days'
        ]

        # Try to load only the columns we need
        df = pd.read_parquet(str(filepath), columns=cols_to_load)
        return df
    except Exception as e:
        # If loading fails (timeout, memory), return None
        # The app will still work without the H001 analysis
        print(f"Warning: Could not load H001 results for {period_name}: {str(e)[:100]}")
        return None

def calculate_rolling_low(stock_data, period_days):
    """Calculate rolling low using calendar days, not trading days"""
    stock_data = stock_data.sort_values('Date').reset_index(drop=True)

    # Calculate rolling low based on actual calendar days (not row count)
    # For each date, find the minimum price in the past N calendar days
    rolling_lows = []

    for idx, row in stock_data.iterrows():
        current_date = row['Date']
        lookback_date = current_date - pd.Timedelta(days=period_days)

        # Get all data within the period
        window_data = stock_data[
            (stock_data['Date'] >= lookback_date) &
            (stock_data['Date'] <= current_date)
        ]

        if len(window_data) > 0:
            rolling_lows.append(window_data['Low'].min())
        else:
            rolling_lows.append(None)

    stock_data['rolling_low'] = rolling_lows
    return stock_data


def analyze_support_breaks(stock_data):
    """Analyze support level breaks

    Returns:
    - breaks: DataFrame with all support breaks
    - stats: Dictionary with summary statistics
    """
    stock_data = stock_data.sort_values('Date').copy()

    # Identify where rolling low decreased (support broken)
    stock_data['rolling_low_prev'] = stock_data['rolling_low'].shift(1)
    stock_data['support_break'] = stock_data['rolling_low'] < stock_data['rolling_low_prev']

    breaks = stock_data[stock_data['support_break'] == True].copy()

    if len(breaks) == 0:
        return None, None

    # Calculate break magnitude
    breaks['prev_support'] = breaks['rolling_low_prev']
    breaks['new_support'] = breaks['rolling_low']
    breaks['drop_amount'] = breaks['new_support'] - breaks['prev_support']
    breaks['drop_pct'] = (breaks['drop_amount'] / breaks['prev_support'] * 100)

    # Calculate time between breaks
    if len(breaks) > 1:
        breaks['days_since_last_break'] = breaks['Date'].diff().dt.days

    # Calculate days since last break (to today)
    days_since_last_break = (stock_data['Date'].max() - breaks['Date'].max()).days

    # Calculate days before first break
    days_before_first_break = (breaks['Date'].min() - stock_data['Date'].min()).days

    # Stability percentage (days without breaks)
    stability_pct = ((len(stock_data) - len(breaks)) / len(stock_data) * 100) if len(stock_data) > 0 else 0

    # Summary statistics
    stats = {
        'total_breaks': len(breaks),
        'avg_days_between': breaks['days_since_last_break'].mean() if len(breaks) > 1 else None,
        'median_days_between': breaks['days_since_last_break'].median() if len(breaks) > 1 else None,
        'min_days_between': breaks['days_since_last_break'].min() if len(breaks) > 1 else None,
        'max_days_between': breaks['days_since_last_break'].max() if len(breaks) > 1 else None,
        'avg_drop_pct': breaks['drop_pct'].mean(),
        'max_drop_pct': breaks['drop_pct'].min(),  # Most negative = biggest drop
        'total_trading_days': len(stock_data),
        'trading_days_per_break': len(stock_data) / len(breaks) if len(breaks) > 0 else None,
        'days_since_last_break': days_since_last_break,
        'days_before_first_break': days_before_first_break,
        'stability_pct': stability_pct,
        'first_break_date': breaks['Date'].min(),
        'last_break_date': breaks['Date'].max()
    }

    return breaks, stats

def calculate_stock_success_rates(period_name):
    """Calculate success rates for all stocks in a given period

    Note: Success rate is calculated PER OPTION CONTRACT TEST, not per unique support.
    This is correct because we're testing different expiry periods on the same support.
    """
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    # Convert to datetime
    results['support_date'] = pd.to_datetime(results['support_date'])

    # Get only immediate supports (wait_days == 0)
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    # Calculate success rate per stock
    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock]

        # Count successes and failures across all option tests
        successful = (stock_results['success'] == True).sum()
        failed = (stock_results['success'] == False).sum()
        total = successful + failed

        if total > 0:
            success_rate = (successful / total) * 100

            # Count unique support levels tested
            unique_supports = stock_results.groupby(
                stock_results['support_level'].astype(str) + '_' +
                stock_results['support_date'].dt.strftime('%Y-%m')
            ).size()

            stock_stats.append({
                'Stock': stock,
                'Option Tests': total,
                'Successful': successful,
                'Failed': failed,
                'Success Rate %': round(success_rate, 1),
                'Unique Supports': len(unique_supports)
            })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        df_stats = df_stats.sort_values('Success Rate %', ascending=False)
        return df_stats

    return None


def calculate_stock_resilience(period_name):
    """Calculate average days to break support for all stocks in a given period

    This uses UNIQUE support levels only (deduplicates consecutive days with same support).
    For each unique support, we calculate how long it lasted before breaking.

    Note: 'days_to_break' represents calendar days, not market/trading days
    """
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    # Convert to datetime
    results['support_date'] = pd.to_datetime(results['support_date'])

    # Get only immediate supports (wait_days == 0)
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    # Calculate resilience (days to break) per stock using UNIQUE supports
    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock].copy()

        # Get failed supports with days to break
        failed_results = stock_results[
            (stock_results['success'] == False) &
            (stock_results['days_to_break'].notna())
        ].copy()

        if len(failed_results) > 0:
            # For each unique support level, find the maximum days_to_break
            # (which represents the first identification of that support)
            failed_results['support_key'] = (
                failed_results['support_level'].astype(str) + '_' +
                failed_results['support_date'].dt.strftime('%Y-%m')
            )

            # Group by support level and take the max days_to_break for each unique support
            unique_supports = failed_results.groupby('support_key').agg({
                'days_to_break': 'max',  # Max = earliest identification
                'support_level': 'first'
            }).reset_index()

            avg_days_to_break = unique_supports['days_to_break'].mean()
            total_unique_failures = len(unique_supports)

            stock_stats.append({
                'Stock': stock,
                'Avg Days to Break': round(avg_days_to_break, 1),
                'Unique Breaks': total_unique_failures,
                'Median Days': round(unique_supports['days_to_break'].median(), 1)
            })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        # Sort by average days to break (higher is better - takes longer to break)
        df_stats = df_stats.sort_values('Avg Days to Break', ascending=False)
        return df_stats

    return None


def calculate_support_frequency(period_name):
    """Calculate how often each stock creates new support levels (support identification frequency)"""
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    results['support_date'] = pd.to_datetime(results['support_date'])
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock]
        total_supports = len(stock_results)
        unique_support_dates = stock_results['support_date'].nunique()

        # Frequency = how many supports per trading day on average
        date_range = (stock_results['support_date'].max() - stock_results['support_date'].min()).days
        supports_per_trading_day = (total_supports / max(date_range, 1)) * 252  # 252 trading days/year

        stock_stats.append({
            'Stock': stock,
            'Total Supports': total_supports,
            'Unique Dates': unique_support_dates,
            'Supports/Year': round(supports_per_trading_day, 1)
        })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        df_stats = df_stats.sort_values('Supports/Year', ascending=False)
        return df_stats

    return None


def calculate_support_consistency(period_name):
    """Calculate consistency of support breaks (lower stddev = more predictable)"""
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    results['support_date'] = pd.to_datetime(results['support_date'])
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock]

        # Get failed supports with days to break
        failed_results = stock_results[
            (stock_results['success'] == False) &
            (stock_results['days_to_break'].notna())
        ]

        if len(failed_results) > 3:  # Need at least 4 data points for meaningful stddev
            days_to_break = failed_results['days_to_break'].values
            consistency = round(days_to_break.std(), 1)

            stock_stats.append({
                'Stock': stock,
                'Stddev Days': consistency,
                'Mean Days': round(days_to_break.mean(), 1),
                'Breaks Analyzed': len(failed_results)
            })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        # Sort by consistency (lower stddev = more consistent/predictable)
        df_stats = df_stats.sort_values('Stddev Days', ascending=True)
        return df_stats

    return None


def calculate_downside_risk(period_name):
    """Calculate average downside when support breaks (how far below support price goes)"""
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    # Check if break_pct column exists
    if 'break_pct' not in results.columns:
        return None

    results['support_date'] = pd.to_datetime(results['support_date'])
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock].copy()

        # Get failed supports with break percentage
        # break_pct is negative when price goes below support
        try:
            failed_results = stock_results.loc[
                (stock_results['success'] == False) &
                (stock_results['break_pct'].notna())
            ]

            if len(failed_results) > 0:
                # Convert to series to avoid issues
                break_pcts = pd.to_numeric(failed_results['break_pct'], errors='coerce')
                break_pcts = break_pcts.dropna()

                if len(break_pcts) > 0:
                    # break_pct is already in decimal format (e.g., -0.087796 = -8.78%)
                    # Keep as negative (already negative, just multiply by 100 for percentage)
                    avg_downside = break_pcts.mean() * 100  # Negative percentage
                    max_downside = break_pcts.min() * 100   # Worst case (most negative)

                    stock_stats.append({
                        'Stock': stock,
                        'Avg Downside %': round(avg_downside, 2),
                        'Max Downside %': round(max_downside, 2),
                        'Breaks Analyzed': len(break_pcts)
                    })
        except KeyError:
            # Skip if break_pct column is missing for this stock
            continue

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        # Sort by average downside (lower is better - less downside risk)
        df_stats = df_stats.sort_values('Avg Downside %', ascending=True)
        return df_stats

    return None


def calculate_expiry_effectiveness(period_name):
    """Calculate which option expiry periods work best for each stock"""
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    results['support_date'] = pd.to_datetime(results['support_date'])
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock]

        # Calculate success rate by expiry period
        expiry_stats = {}
        for expiry in [7, 14, 21, 30, 45]:
            expiry_data = stock_results[stock_results['expiry_days'] == expiry]
            if len(expiry_data) > 0:
                success_rate = (expiry_data['success'] == True).sum() / len(expiry_data) * 100
                expiry_stats[f'{expiry}d'] = round(success_rate, 1)

        if expiry_stats:
            best_expiry = max(expiry_stats, key=expiry_stats.get)
            stock_stats.append({
                'Stock': stock,
                'Best Expiry': best_expiry,
                'Best Rate %': expiry_stats[best_expiry],
                **expiry_stats
            })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        df_stats = df_stats.sort_values('Best Rate %', ascending=False)
        return df_stats

    return None


def calculate_wait_time_effectiveness(period_name):
    """Calculate if waiting after support identification improves success rates"""
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    results['support_date'] = pd.to_datetime(results['support_date'])
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        all_stock_results = results[results['stock'] == stock]

        # Calculate success rate for wait_days=0 vs >0
        wait_zero = all_stock_results[all_stock_results['wait_days'] == 0]
        wait_positive = all_stock_results[all_stock_results['wait_days'] > 0]

        if len(wait_zero) > 0 and len(wait_positive) > 0:
            rate_zero = (wait_zero['success'] == True).sum() / len(wait_zero) * 100
            rate_positive = (wait_positive['success'] == True).sum() / len(wait_positive) * 100
            improvement = rate_positive - rate_zero

            stock_stats.append({
                'Stock': stock,
                'Immediate %': round(rate_zero, 1),
                'After Wait %': round(rate_positive, 1),
                'Improvement %': round(improvement, 1)
            })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        df_stats = df_stats.sort_values('Improvement %', ascending=False)
        return df_stats

    return None


def calculate_temporal_patterns(period_name):
    """Calculate seasonal patterns - which months have best support performance"""
    results = load_results_for_period(period_name)

    if results is None or len(results) == 0:
        return None

    results['support_date'] = pd.to_datetime(results['support_date'])
    immediate_supports = results[results['wait_days'] == 0].copy()

    if len(immediate_supports) == 0:
        return None

    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock].copy()
        stock_results['month'] = stock_results['support_date'].dt.month

        # Calculate success rate by month
        month_stats = {}
        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                      7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

        for month in range(1, 13):
            month_data = stock_results[stock_results['month'] == month]
            if len(month_data) > 0:
                success_rate = (month_data['success'] == True).sum() / len(month_data) * 100
                month_stats[month_names[month]] = round(success_rate, 1)

        if month_stats:
            best_month = max(month_stats, key=month_stats.get)
            worst_month = min(month_stats, key=month_stats.get)

            stock_stats.append({
                'Stock': stock,
                'Best Month': best_month,
                'Best Rate %': month_stats[best_month],
                'Worst Month': worst_month,
                'Worst Rate %': month_stats[worst_month]
            })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        df_stats = df_stats.sort_values('Best Rate %', ascending=False)
        return df_stats

    return None


def main():
    """Main app logic"""

    # Debug info (will show in Streamlit Cloud logs)
    import sys
    print(f"DEBUG: Python path: {sys.executable}")
    print(f"DEBUG: Script dir: {SCRIPT_DIR}")
    print(f"DEBUG: Data file path: {DATA_FILE}")
    print(f"DEBUG: Data file exists: {Path(DATA_FILE).exists()}")

    # Load data
    with st.spinner("Loading price data..."):
        df = load_all_price_data()

    # Single-stock analysis
    # Sidebar controls for Stock Analysis
    st.sidebar.header("📊 Configuration")

    # Stock selector
    stocks = sorted(df['Stock'].unique())
    selected_stock = st.sidebar.selectbox("Select Stock:", stocks)

    # Get stock data
    stock_data = df[df['Stock'] == selected_stock].copy()
    min_date = stock_data['Date'].min()
    max_date = stock_data['Date'].max()

    st.sidebar.write(f"**Data available:** {min_date.date()} to {max_date.date()}")

    # Period selector
    period_days = st.sidebar.radio(
        "Rolling Low Period:",
        options=[30, 90, 180, 270, 365],
        format_func=lambda x: {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[x]
    )

    # Calculate rolling low on FULL dataset FIRST
    # This is the TRUE rolling low for each date - it never changes
    with st.spinner(f"Calculating {period_days}-day rolling low..."):
        stock_data_with_rolling_low = calculate_rolling_low(stock_data.copy(), period_days)

    # Date range selector
    st.sidebar.write("**Date Range Filter:**")
    col1, col2 = st.sidebar.columns(2)

    # Default to 2024-01-01
    default_start = max(min_date.date(), pd.to_datetime('2024-01-01').date())

    with col1:
        start_date = st.date_input(
            "From:",
            value=default_start,
            format="YYYY-MM-DD",
            min_value=min_date.date(),
            max_value=max_date.date()
        )
    with col2:
        end_date = st.date_input(
            "To:",
            value=max_date.date(),
            format="YYYY-MM-DD",
            min_value=min_date.date(),
            max_value=max_date.date()
        )

    # Validate date range
    if start_date > end_date:
        st.sidebar.error("Start date must be before end date")
        return

    # Filter by date range for DISPLAY
    stock_data = stock_data_with_rolling_low[
        (stock_data_with_rolling_low['Date'] >= pd.to_datetime(start_date)) &
        (stock_data_with_rolling_low['Date'] <= pd.to_datetime(end_date))
    ].copy()

    if len(stock_data) == 0:
        st.error("No data available for selected date range")
        return

    # Load H001 results for this stock and period
    period_name = {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[period_days]

    try:
        results = load_results_for_period(period_name)

        if results is not None:
            # Convert support_date to datetime if it's not already
            results['support_date'] = pd.to_datetime(results['support_date'])

            # Filter results by stock AND by selected date range
            results = results[
                (results['stock'] == selected_stock) &
                (results['support_date'] >= pd.to_datetime(start_date)) &
                (results['support_date'] <= pd.to_datetime(end_date))
            ].copy()
    except Exception as e:
        print(f"Error processing H001 results: {str(e)[:100]}")
        results = None

    # Display info
    st.subheader(f"{selected_stock}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Data Points", len(stock_data))
    with col2:
        st.metric("Latest Price", f"{stock_data['Close'].iloc[-1]:.2f} kr")
    with col3:
        st.metric("Period Low", f"{stock_data['Low'].min():.2f} kr")

    # Create interactive chart
    st.subheader("Price History with Rolling Low Support Levels")

    fig = go.Figure()

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=stock_data['Date'],
        open=stock_data['Open'],
        high=stock_data['High'],
        low=stock_data['Low'],
        close=stock_data['Close'],
        name='Price'
    ))

    # Add rolling low line
    rolling_low_data = stock_data[stock_data['rolling_low'].notna()]
    fig.add_trace(go.Scatter(
        x=rolling_low_data['Date'],
        y=rolling_low_data['rolling_low'],
        mode='lines',
        name=f'{period_name} Rolling Low',
        line=dict(color='blue', width=2, dash='dash'),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Rolling Low: %{y:.2f}<extra></extra>'
    ))

    # Highlight where rolling low DECREASED (new lower support found)
    # When rolling_low decreases, it means a new lower price entered the window = support was broken
    stock_data['rolling_low_prev'] = stock_data['rolling_low'].shift()
    breaks = stock_data[stock_data['rolling_low'] < stock_data['rolling_low_prev']].copy()

    if len(breaks) > 0:
        fig.add_trace(go.Scatter(
            x=breaks['Date'],
            y=breaks['rolling_low'],
            mode='markers',
            name='Support Broken',
            marker=dict(color='red', size=10, symbol='circle'),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>New Low: %{y:.2f} kr<extra></extra>'
        ))

        st.write(f"**Supports Broken:** {len(breaks)} dates where rolling low decreased (new support level)")

    # Update layout
    fig.update_layout(
        title=f"{selected_stock} - {period_name} Rolling Low Support Levels",
        yaxis_title="Price (kr)",
        xaxis_title="Date",
        template='plotly_white',
        height=600,
        hovermode='x unified',
        margin=dict(l=0, r=0, t=40, b=0)
    )

    # Display with proper config
    config = {'responsive': True, 'displayModeBar': True, 'displaylogo': False}
    st.plotly_chart(fig, config=config)

    # Support level statistics
    st.subheader("Support Level Statistics")

    # Calculate support break metrics
    breaks, stats = analyze_support_breaks(stock_data)

    if breaks is not None and stats is not None:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Support Breaks", f"{stats['total_breaks']}",
                     help="Number of times the rolling low decreased (support was broken)")
        with col2:
            st.metric("Days Since Last Break", f"{stats['days_since_last_break']}d",
                     help=f"Calendar days since last break on {stats['last_break_date'].strftime('%Y-%m-%d')}")
        with col3:
            st.metric("Stability", f"{stats['stability_pct']:.1f}%",
                     help="% of trading days where support held (didn't break)")
        with col4:
            if stats['trading_days_per_break'] is not None:
                st.metric("Trading Days per Break", f"{stats['trading_days_per_break']:.0f}",
                         help="Average number of trading days between support breaks in the selected period")
            else:
                st.metric("Trading Days per Break", "N/A",
                         help="No breaks to calculate")

        # Additional context row
        st.write("---")
        context_col1, context_col2, context_col3 = st.columns(3)

        with context_col1:
            st.metric("Days Before First Break", f"{stats['days_before_first_break']}d",
                     help=f"Calendar days from start until first break on {stats['first_break_date'].strftime('%Y-%m-%d')}")
        with context_col2:
            if stats['avg_days_between'] is not None:
                st.metric("Avg Days Between Breaks", f"{stats['avg_days_between']:.0f}d",
                         delta=f"Median: {stats['median_days_between']:.0f}d",
                         help="Calendar days between consecutive breaks (volatility measure)")
            else:
                st.metric("Avg Days Between Breaks", "N/A",
                         help="Need at least 2 breaks to calculate")
        with context_col3:
            st.metric("Avg Break Magnitude", f"{stats['avg_drop_pct']:.2f}%",
                     help="Average % drop when support breaks")

        # Show break details
        st.write("---")
        st.write("**Support Break History:**")

        if stats['min_days_between'] is not None:
            detail_col1, detail_col2, detail_col3 = st.columns(3)
            with detail_col1:
                st.metric("Shortest Duration", f"{stats['min_days_between']:.0f} days",
                         help="Shortest calendar days between consecutive breaks")
            with detail_col2:
                st.metric("Longest Duration", f"{stats['max_days_between']:.0f} days",
                         help="Longest calendar days between consecutive breaks")
            with detail_col3:
                st.metric("Biggest Break", f"{stats['max_drop_pct']:.2f}%",
                         help="Largest % drop when support broke")

        # Show detailed break table
        st.write("---")
        st.write("**Detailed Break Events:**")
        breaks_display = breaks[['Date', 'prev_support', 'new_support', 'drop_pct', 'days_since_last_break']].copy()
        breaks_display.columns = ['Date', 'Previous Support', 'New Support', 'Drop %', 'Calendar Days Since Last']
        breaks_display['Date'] = breaks_display['Date'].dt.strftime('%Y-%m-%d')
        st.dataframe(breaks_display, width='stretch', hide_index=True)

    else:
        st.info(f"No support breaks detected in the selected date range for {period_name} {selected_stock}")

    # Show data table at the bottom
    st.subheader("Price Data Table")
    display_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'rolling_low']
    table_data = stock_data[display_cols].copy()
    table_data['Date'] = table_data['Date'].dt.strftime('%Y-%m-%d')
    table_data['rolling_low'] = table_data['rolling_low'].round(2)

    st.dataframe(
        table_data.rename(columns={'rolling_low': f'{period_name} Rolling Low'}),
        width='stretch',
        hide_index=True
    )


if __name__ == '__main__':
    main()
