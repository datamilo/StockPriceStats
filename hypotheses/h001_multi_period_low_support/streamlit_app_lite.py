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
import plotly.express as px
from pathlib import Path
import warnings

# Suppress Plotly's deprecation warnings about keyword arguments
warnings.filterwarnings('ignore', message='The keyword arguments have been deprecated')

# Configuration - paths relative to this script file
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_FILE = SCRIPT_DIR / '../../price_data_filtered.parquet'

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


@st.cache_data(show_spinner="Calculating statistics for all stocks... (this runs once, then cached)")
def calculate_all_stocks_statistics(period_days):
    """Calculate statistics for all stocks - cached for performance"""
    df = load_all_price_data()
    all_stocks_stats = []

    for stock in sorted(df['Stock'].unique()):
        stock_data = df[df['Stock'] == stock].copy()

        if len(stock_data) < period_days:
            continue

        stock_data_with_low = calculate_rolling_low(stock_data, period_days)
        breaks, stats = analyze_support_breaks(stock_data_with_low)

        if stats is not None and stats['total_breaks'] > 0:
            all_stocks_stats.append({
                'Stock': stock,
                'Total Breaks': stats['total_breaks'],
                'Avg Days Between': round(stats['avg_days_between'], 1) if stats['avg_days_between'] else None,
                'Median Days Between': round(stats['median_days_between'], 1) if stats['median_days_between'] else None,
                'Trading Days per Break': round(stats['trading_days_per_break'], 1) if stats['trading_days_per_break'] else None,
                'Stability %': round(stats['stability_pct'], 1),
                'Avg Break %': round(stats['avg_drop_pct'], 2),
                'Max Break %': round(stats['max_drop_pct'], 2),
                'Days Since Last': stats['days_since_last_break']
            })

    return pd.DataFrame(all_stocks_stats) if all_stocks_stats else None


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

    # Page selector
    st.sidebar.header("📄 Page")
    page = st.sidebar.radio(
        "View:",
        ["Single Stock Analysis", "📊 Top Lists"],
        help="Switch between detailed analysis and multi-stock rankings"
    )

    # Configuration section
    st.sidebar.header("📊 Configuration")

    # Period selector (shared by both pages)
    period_days = st.sidebar.radio(
        "Rolling Low Period:",
        options=[30, 90, 180, 270, 365],
        format_func=lambda x: {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[x]
    )
    period_name = {30: "1-Month", 90: "3-Month", 180: "6-Month", 270: "9-Month", 365: "1-Year"}[period_days]

    # ============================================================================
    # PAGE: TOP LISTS
    # ============================================================================
    if page == "📊 Top Lists":
        st.header(f"📊 Top Lists - {period_name} Rolling Low")
        st.info("Rankings based on pure historical support level behavior - calculated once and cached for speed")

        # Calculate all stock statistics (cached)
        df_all_stocks = calculate_all_stocks_statistics(period_days)

        if df_all_stocks is not None and len(df_all_stocks) > 0:
            # Create tabs
            tab1, tab2, tab3 = st.tabs([
                "🔒 Most Stable",
                "⏱️ Longest Between Breaks",
                "📉 Smallest Breaks"
            ])

            with tab1:
                st.subheader("Most Stable Support Levels")
                st.write("**Stocks with highest stability % (fewest breaks relative to trading days)**")

                stable_df = df_all_stocks.sort_values('Stability %', ascending=False)
                st.dataframe(stable_df, width='stretch', hide_index=True)

                fig = px.bar(
                    stable_df.head(15),
                    x='Stock',
                    y='Stability %',
                    title=f'Top 15 Most Stable - {period_name}',
                    color='Stability %',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("Longest Time Between Support Breaks")
                st.write("**Stocks where support levels last the longest before breaking**")

                time_df = df_all_stocks[df_all_stocks['Avg Days Between'].notna()].sort_values('Avg Days Between', ascending=False)
                st.dataframe(time_df, width='stretch', hide_index=True)

                fig = px.bar(
                    time_df.head(15),
                    x='Stock',
                    y='Avg Days Between',
                    title=f'Top 15 Longest Duration - {period_name}',
                    color='Avg Days Between',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(xaxis_tickangle=-45, height=500, yaxis_title='Calendar Days')
                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                st.subheader("Smallest Support Breaks")
                st.write("**Stocks with smallest average % drops when support breaks**")

                break_df = df_all_stocks.sort_values('Avg Break %', ascending=True)
                st.dataframe(break_df, width='stretch', hide_index=True)

                fig = px.bar(
                    break_df.head(15),
                    x='Stock',
                    y='Avg Break %',
                    title=f'Top 15 Smallest Breaks - {period_name}',
                    color='Avg Break %',
                    color_continuous_scale='RdYlGn_r'
                )
                fig.update_layout(xaxis_tickangle=-45, height=500, yaxis_title='Average Break %')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No statistics available for this period")
        return

    # ============================================================================
    # PAGE: SINGLE STOCK ANALYSIS
    # ============================================================================
    # Stock selector
    stocks = sorted(df['Stock'].unique())
    selected_stock = st.sidebar.selectbox("Select Stock:", stocks)

    # Get stock data
    stock_data = df[df['Stock'] == selected_stock].copy()
    min_date = stock_data['Date'].min()
    max_date = stock_data['Date'].max()

    st.sidebar.write(f"**Data available:** {min_date.date()} to {max_date.date()}")

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
