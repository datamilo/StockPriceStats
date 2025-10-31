"""
Lightweight Streamlit App for H001 Support Level Analysis
Focuses on single stock investigation with date range filtering

This version is designed to:
- Load minimal data (single stock + date range)
- Not crash with large datasets
- Show price history + rolling low + support markers
- Allow interactive exploration
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
st.set_page_config(page_title="Support Level Test", layout="wide")
st.title("Support Level Test")

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

def calculate_stock_success_rates(period_name):
    """Calculate success rates for all stocks in a given period"""
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

        # Count successes and failures
        successful = (stock_results['success'] == True).sum()
        failed = (stock_results['success'] == False).sum()
        total = successful + failed

        if total > 0:
            success_rate = (successful / total) * 100

            # Calculate average days to break for failed supports
            failed_results = stock_results[
                (stock_results['success'] == False) &
                (stock_results['days_to_break'].notna())
            ]
            avg_days_to_break = failed_results['days_to_break'].mean()

            stock_stats.append({
                'Stock': stock,
                'Total Supports': total,
                'Successful': successful,
                'Failed': failed,
                'Success Rate %': round(success_rate, 1),
                'Avg Days to Break': round(avg_days_to_break, 1) if pd.notna(avg_days_to_break) else 0
            })

    if stock_stats:
        df_stats = pd.DataFrame(stock_stats)
        df_stats = df_stats.sort_values('Success Rate %', ascending=False)
        return df_stats

    return None


def calculate_stock_resilience(period_name):
    """Calculate average days to break support for all stocks in a given period

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

    # Calculate resilience (days to break) per stock
    stock_stats = []

    for stock in immediate_supports['stock'].unique():
        stock_results = immediate_supports[immediate_supports['stock'] == stock]

        # Get failed supports with days to break
        failed_results = stock_results[
            (stock_results['success'] == False) &
            (stock_results['days_to_break'].notna())
        ]

        if len(failed_results) > 0:
            avg_days_to_break = failed_results['days_to_break'].mean()
            total_failures = len(failed_results)

            stock_stats.append({
                'Stock': stock,
                'Avg Days to Break': round(avg_days_to_break, 1),
                'Failed Supports': total_failures,
                'Resilience Score': round(avg_days_to_break * (total_failures / len(stock_results)), 1)
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

    # Create tabs for different views
    tab1, tab2 = st.tabs(["📈 Stock Analysis", "🏆 Top Performers"])

    with tab1:
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
        st.subheader("Support Level Performance Statistics")

        if results is not None and len(results) > 0:
            # Get unique support levels identified (wait_days == 0)
            immediate_supports = results[results['wait_days'] == 0].copy()
            unique_supports = immediate_supports[['support_date', 'support_level']].drop_duplicates()

            # Determine success for each unique support
            support_success = {}
            for _, row in immediate_supports.iterrows():
                date = row['support_date']
                level = row['support_level']
                success = row['success']
                key = (date, level)
                if key not in support_success:
                    support_success[key] = []
                if pd.notna(success):
                    support_success[key].append(success)

            # Calculate statistics
            successful = sum(1 for v in support_success.values() if any(v))
            failed = sum(1 for v in support_success.values() if not any(v) and len(v) > 0)
            total_supports = successful + failed

            success_rate = (successful / total_supports * 100) if total_supports > 0 else 0

            # Calculate average days to break for failed supports
            failed_results = immediate_supports[
                (immediate_supports['success'] == False) &
                (immediate_supports['days_to_break'].notna())
            ]
            avg_days_to_break = failed_results['days_to_break'].mean() if len(failed_results) > 0 else 0

            # Calculate rolling low change frequency
            rolling_low_changes = (stock_data['rolling_low'] != stock_data['rolling_low'].shift()).sum()
            total_days = len(stock_data[stock_data['rolling_low'].notna()])
            change_frequency = (rolling_low_changes / total_days * 100) if total_days > 0 else 0

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Support Levels", f"{total_supports:,}")
            with col2:
                st.metric("Success Rate", f"{success_rate:.1f}%",
                         delta=f"{successful} ✓ / {failed} ✗")
            with col3:
                st.metric("Avg Days to Break (Calendar)", f"{avg_days_to_break:.1f}d" if avg_days_to_break > 0 else "N/A")
            with col4:
                st.metric("Rolling Low Changes", f"{change_frequency:.1f}%")

            # Additional breakdown
            st.write("---")
            breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)

            with breakdown_col1:
                st.metric("Successful Supports", f"{successful}",
                         f"{(successful/total_supports*100):.1f}% of total")
            with breakdown_col2:
                st.metric("Failed Supports", f"{failed}",
                         f"{(failed/total_supports*100):.1f}% of total")
            with breakdown_col3:
                st.metric("Tested Supports", f"{len(immediate_supports):,}",
                         "individual tests")

        else:
            st.warning(f"No H001 analysis results available for {period_name} {selected_stock} in this date range")

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

    with tab2:
        st.subheader("📊 Top Performers Analysis")
        st.write("Comprehensive metrics across all trading scenarios")
        st.write("---")

        # Period selector
        period_selector = st.radio(
            "Select Time Period:",
            options=[30, 90, 180, 270, 365],
            format_func=lambda x: {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[x],
            key="top_performers_period"
        )

        period_name_tp = {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[period_selector]

        # Create sub-tabs within Top Performers
        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
            "📈 Success Metrics",
            "⏱️ Resilience Metrics",
            "🛡️ Risk Metrics",
            "🎯 Strategy Metrics",
            "🗓️ Temporal Patterns"
        ])

        # ===== SUB-TAB 1: Success Metrics =====
        with sub_tab1:
            st.write("**Success Rate & Support Frequency**")
            st.write("---")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Success Rate** - % of supports that held")
                with st.spinner(f"Calculating success rates for {period_name_tp}..."):
                    data = calculate_stock_success_rates(period_name_tp)

                if data is not None and len(data) > 0:
                    top_5 = data.head(5)
                    cols = st.columns(5)
                    for idx, (_, row) in enumerate(top_5.iterrows()):
                        with cols[idx]:
                            st.metric(row['Stock'], f"{row['Success Rate %']:.1f}%",
                                     f"{int(row['Successful'])}/{int(row['Total Supports'])}")

                    st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Average Success Rate", f"{data['Success Rate %'].mean():.1f}%")
                    with stats_col2:
                        st.metric("Best Stock", f"{data.iloc[0]['Stock']} ({data.iloc[0]['Success Rate %']:.1f}%)")
                else:
                    st.warning("No data available")

            with col2:
                st.write("**Support Frequency** - How often new supports are identified")
                with st.spinner(f"Calculating support frequency for {period_name_tp}..."):
                    data = calculate_support_frequency(period_name_tp)

                if data is not None and len(data) > 0:
                    top_5 = data.head(5)
                    cols = st.columns(5)
                    for idx, (_, row) in enumerate(top_5.iterrows()):
                        with cols[idx]:
                            st.metric(row['Stock'], f"{row['Supports/Year']:.1f}/yr",
                                     f"{int(row['Total Supports'])} total")

                    st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Average Frequency", f"{data['Supports/Year'].mean():.1f}/yr")
                    with stats_col2:
                        st.metric("Most Frequent Stock", f"{data.iloc[0]['Stock']} ({data.iloc[0]['Supports/Year']:.1f}/yr)")
                else:
                    st.warning("No data available")

        # ===== SUB-TAB 2: Resilience Metrics =====
        with sub_tab2:
            st.write("**Days to Break & Support Consistency**")
            st.write("---")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Days to Break Support** - How long before support breaks (calendar days)")
                with st.spinner(f"Calculating resilience for {period_name_tp}..."):
                    data = calculate_stock_resilience(period_name_tp)

                if data is not None and len(data) > 0:
                    top_5 = data.head(5)
                    cols = st.columns(5)
                    for idx, (_, row) in enumerate(top_5.iterrows()):
                        with cols[idx]:
                            st.metric(row['Stock'], f"{row['Avg Days to Break']:.1f}d",
                                     f"{int(row['Failed Supports'])} breaks")

                    st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Average Days", f"{data['Avg Days to Break'].mean():.1f}d")
                    with stats_col2:
                        st.metric("Most Resilient", f"{data.iloc[0]['Stock']} ({data.iloc[0]['Avg Days to Break']:.1f}d)")
                else:
                    st.warning("No data available")

            with col2:
                st.write("**Support Consistency** - Predictability of breaks (lower = more predictable)")
                with st.spinner(f"Calculating consistency for {period_name_tp}..."):
                    data = calculate_support_consistency(period_name_tp)

                if data is not None and len(data) > 0:
                    top_5 = data.head(5)
                    cols = st.columns(5)
                    for idx, (_, row) in enumerate(top_5.iterrows()):
                        with cols[idx]:
                            st.metric(row['Stock'], f"{row['Stddev Days']:.1f}d",
                                     f"μ={row['Mean Days']:.1f}d")

                    st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Average Stddev", f"{data['Stddev Days'].mean():.1f}d")
                    with stats_col2:
                        st.metric("Most Consistent", f"{data.iloc[0]['Stock']} ({data.iloc[0]['Stddev Days']:.1f}d)")
                else:
                    st.warning("No data available")

        # ===== SUB-TAB 3: Risk Metrics =====
        with sub_tab3:
            st.write("**Downside Risk when Support Breaks**")
            st.write("---")

            with st.spinner(f"Calculating downside risk for {period_name_tp}..."):
                data = calculate_downside_risk(period_name_tp)

            if data is not None and len(data) > 0:
                top_5 = data.head(5)
                cols = st.columns(5)
                for idx, (_, row) in enumerate(top_5.iterrows()):
                    with cols[idx]:
                        # Downside risk shows as negative (red, pointing down) for higher values = worse
                        st.metric(row['Stock'], f"{row['Avg Downside %']:.2f}%",
                                 f"{row['Max Downside %']:.2f}%")

                st.subheader("All Stocks")
                st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                stats_col1, stats_col2, stats_col3 = st.columns(3)
                with stats_col1:
                    st.metric("Average Downside", f"{data['Avg Downside %'].mean():.2f}%")
                with stats_col2:
                    st.metric("Lowest Risk Stock", f"{data.iloc[0]['Stock']} ({data.iloc[0]['Avg Downside %']:.2f}%)")
                with stats_col3:
                    st.metric("Highest Risk Stock", f"{data.iloc[-1]['Stock']} ({data.iloc[-1]['Avg Downside %']:.2f}%)")
            else:
                st.warning("No downside risk data available (missing break_pct in analysis results)")

        # ===== SUB-TAB 4: Strategy Metrics =====
        with sub_tab4:
            st.write("**Optimal Strategies for Put Option Writing**")
            st.write("---")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Best Option Expiry Period** - Which expiry works best")
                with st.spinner(f"Analyzing expiry effectiveness for {period_name_tp}..."):
                    data = calculate_expiry_effectiveness(period_name_tp)

                if data is not None and len(data) > 0:
                    top_5 = data.head(5)
                    cols = st.columns(5)
                    for idx, (_, row) in enumerate(top_5.iterrows()):
                        with cols[idx]:
                            st.metric(row['Stock'], f"{row['Best Expiry']}",
                                     f"{row['Best Rate %']:.1f}%")

                    st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Average Best Rate", f"{data['Best Rate %'].mean():.1f}%")
                    with stats_col2:
                        st.metric("Most Optimal Stock", f"{data.iloc[0]['Stock']} ({data.iloc[0]['Best Rate %']:.1f}%)")
                else:
                    st.warning("No expiry data available")

            with col2:
                st.write("**Wait Time Effectiveness** - Does waiting improve success?")
                with st.spinner(f"Analyzing wait time effectiveness for {period_name_tp}..."):
                    data = calculate_wait_time_effectiveness(period_name_tp)

                if data is not None and len(data) > 0:
                    top_5 = data.head(5)
                    cols = st.columns(5)
                    for idx, (_, row) in enumerate(top_5.iterrows()):
                        with cols[idx]:
                            # Show improvement as delta: positive is good (green ↑), negative is bad (red ↓)
                            improvement = row['Improvement %']
                            delta_display = f"+{improvement:.1f}%" if improvement >= 0 else f"{improvement:.1f}%"
                            st.metric(row['Stock'], delta_display,
                                     f"{row['Immediate %']:.1f}% → {row['After Wait %']:.1f}%")

                    st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Average Improvement", f"{data['Improvement %'].mean():.1f}%")
                    with stats_col2:
                        improving = len(data[data['Improvement %'] > 0])
                        st.metric("Stocks Improving with Wait", f"{improving}/{len(data)}")
                else:
                    st.warning("No wait time data available")

        # ===== SUB-TAB 5: Temporal Patterns =====
        with sub_tab5:
            st.write("**Seasonal Patterns - Best & Worst Months**")
            st.write("---")

            with st.spinner(f"Analyzing temporal patterns for {period_name_tp}..."):
                data = calculate_temporal_patterns(period_name_tp)

            if data is not None and len(data) > 0:
                top_5 = data.head(5)
                cols = st.columns(5)
                for idx, (_, row) in enumerate(top_5.iterrows()):
                    with cols[idx]:
                        st.metric(row['Stock'], f"{row['Best Month']}",
                                 f"Best: {row['Best Rate %']:.1f}% | Worst: {row['Worst Rate %']:.1f}%")

                st.subheader("All Stocks")
                st.dataframe(data.reset_index(drop=True), width='stretch', hide_index=True)

                stats_col1, stats_col2, stats_col3 = st.columns(3)
                with stats_col1:
                    st.metric("Average Best Rate", f"{data['Best Rate %'].mean():.1f}%")
                with stats_col2:
                    st.metric("Average Worst Rate", f"{data['Worst Rate %'].mean():.1f}%")
                with stats_col3:
                    avg_spread = data['Best Rate %'].mean() - data['Worst Rate %'].mean()
                    st.metric("Average Seasonal Spread", f"{avg_spread:.1f}%")
            else:
                st.warning("No temporal pattern data available")

if __name__ == '__main__':
    main()
