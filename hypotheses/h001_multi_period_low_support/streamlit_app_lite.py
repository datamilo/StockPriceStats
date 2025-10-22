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

# Configuration - paths relative to this script file
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'
H001_RESULTS_DIR = SCRIPT_DIR

# Page config
st.set_page_config(page_title="H001 Support Level Analyzer", layout="wide")
st.title("🔍 H001: Support Level Investigation Tool")
st.write("Lightweight explorer for single-stock analysis")

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
    """Load detailed results for a specific period"""
    file = f'{period_name.lower().replace(" ", "_").replace("-", "_")}_detailed_results.parquet'
    filepath = Path(H001_RESULTS_DIR) / file
    if filepath.exists():
        return pd.read_parquet(str(filepath))
    return None

def calculate_rolling_low(stock_data, period_days):
    """Calculate rolling low for given period"""
    stock_data = stock_data.sort_values('Date').reset_index(drop=True)
    rolling_lows = []

    for idx in range(len(stock_data)):
        if idx < period_days - 1:
            rolling_lows.append(None)
        else:
            window_start = idx - period_days + 1
            window_data = stock_data.iloc[window_start:idx+1]
            rolling_lows.append(window_data['Low'].min())

    stock_data['rolling_low'] = rolling_lows
    return stock_data

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

    # Sidebar controls
    st.sidebar.header("📊 Configuration")

    # Stock selector
    stocks = sorted(df['Stock'].unique())
    selected_stock = st.sidebar.selectbox("Select Stock:", stocks)

    # Get stock data
    stock_data = df[df['Stock'] == selected_stock].copy()
    min_date = stock_data['Date'].min()
    max_date = stock_data['Date'].max()

    st.sidebar.write(f"**Data available:** {min_date.date()} to {max_date.date()}")

    # Period selector (BEFORE date range, so we can calculate rolling low on full dataset)
    period_days = st.sidebar.radio(
        "Rolling Low Period:",
        options=[30, 90, 180, 270, 365],
        format_func=lambda x: {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[x]
    )

    # Calculate rolling low on ENTIRE dataset first (before filtering by date)
    stock_data = calculate_rolling_low(stock_data, period_days)

    # Date range selector
    st.sidebar.write("**Date Range Filter:**")
    col1, col2 = st.sidebar.columns(2)

    # Default to last year
    default_start = max(min_date.date(), max_date.date() - timedelta(days=365))

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

    # Filter by date range AFTER calculating rolling low
    stock_data = stock_data[
        (stock_data['Date'] >= pd.to_datetime(start_date)) &
        (stock_data['Date'] <= pd.to_datetime(end_date))
    ].copy()

    if len(stock_data) == 0:
        st.error("No data available for selected date range")
        return

    # Load H001 results for this stock and period
    period_name = {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[period_days]
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

    # Add support level markers if we have results
    if results is not None and len(results) > 0:
        # Filter results for 0 wait days (immediate support identification)
        immediate_supports = results[results['wait_days'] == 0].copy()

        if len(immediate_supports) > 0:
            # Group by support_date and get unique levels
            unique_supports = immediate_supports[['support_date', 'support_level']].drop_duplicates()
            unique_supports = unique_supports.sort_values('support_date')

            # For each support, determine if ANY test was successful (optimistic)
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

            # Determine color: green if any test passed, red if all failed
            successful_supports = []
            failed_supports = []

            for date, level in support_success:
                if any(support_success[(date, level)]):
                    successful_supports.append((date, level))
                else:
                    failed_supports.append((date, level))

            # Add successful supports (green)
            if successful_supports:
                supp_dates, supp_levels = zip(*successful_supports)
                fig.add_trace(go.Scatter(
                    x=supp_dates,
                    y=supp_levels,
                    mode='markers',
                    name='Support (Success)',
                    marker=dict(color='green', size=8, symbol='circle'),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Support: %{y:.2f} ✓<extra></extra>'
                ))

            # Add failed supports (red)
            if failed_supports:
                supp_dates, supp_levels = zip(*failed_supports)
                fig.add_trace(go.Scatter(
                    x=supp_dates,
                    y=supp_levels,
                    mode='markers',
                    name='Support (Failed)',
                    marker=dict(color='red', size=8, symbol='circle'),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Support: %{y:.2f} ✗<extra></extra>'
                ))

            # Show summary
            st.write(f"**Support Levels Found (wait=0):** {len(successful_supports)} successful, {len(failed_supports)} failed")

    # Update layout
    fig.update_layout(
        title=f"{selected_stock} - {period_name} Rolling Low Support Levels",
        yaxis_title="Price (kr)",
        xaxis_title="Date",
        template='plotly_white',
        height=600,
        hovermode='x unified'
    )

    st.plotly_chart(fig, width='stretch')

    # Show data table
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
            st.metric("Avg Days to Break", f"{avg_days_to_break:.1f}d" if avg_days_to_break > 0 else "N/A")
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

if __name__ == '__main__':
    main()
