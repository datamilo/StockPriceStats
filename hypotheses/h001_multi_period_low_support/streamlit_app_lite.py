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


def analyze_consecutive_breaks(breaks_df, max_gap_days=30):
    """
    Identify clusters of consecutive breaks

    A cluster is a group of breaks where each break happens within max_gap_days
    of the previous break.

    Returns:
    - clusters: List of cluster dictionaries
    - cluster_stats: Summary statistics about clusters
    """
    if breaks_df is None or len(breaks_df) == 0:
        return [], {}

    breaks_df = breaks_df.sort_values('Date').reset_index(drop=True)

    # Identify cluster boundaries
    # A new cluster starts when gap from previous break > max_gap_days
    breaks_df['days_from_prev'] = breaks_df['Date'].diff().dt.days
    breaks_df['new_cluster'] = (breaks_df['days_from_prev'].isna()) | (breaks_df['days_from_prev'] > max_gap_days)
    breaks_df['cluster_id'] = breaks_df['new_cluster'].cumsum()

    # Analyze each cluster
    clusters = []
    for cluster_id, cluster_df in breaks_df.groupby('cluster_id'):
        cluster_df = cluster_df.sort_values('Date')

        cluster_info = {
            'cluster_id': int(cluster_id),
            'num_breaks': len(cluster_df),
            'start_date': cluster_df['Date'].min(),
            'end_date': cluster_df['Date'].max(),
            'duration_days': int((cluster_df['Date'].max() - cluster_df['Date'].min()).days),
            'avg_gap_days': float(cluster_df['days_from_prev'].mean()) if len(cluster_df) > 1 else None,
            'max_gap_days': float(cluster_df['days_from_prev'].max()) if len(cluster_df) > 1 else None,
            'min_gap_days': float(cluster_df['days_from_prev'].min()) if len(cluster_df) > 1 else None,
            'total_drop_pct': float(cluster_df['drop_pct'].sum()),
            'avg_drop_pct': float(cluster_df['drop_pct'].mean()),
            'breaks': cluster_df[['Date', 'prev_support', 'new_support', 'drop_pct', 'days_from_prev']].copy()
        }
        clusters.append(cluster_info)

    # Calculate cluster statistics
    cluster_sizes = [c['num_breaks'] for c in clusters]
    cluster_stats = {
        'total_clusters': len(clusters),
        'total_breaks': len(breaks_df),
        'single_break_clusters': sum(1 for s in cluster_sizes if s == 1),
        'multi_break_clusters': sum(1 for s in cluster_sizes if s > 1),
        'avg_breaks_per_cluster': float(np.mean(cluster_sizes)),
        'max_breaks_in_cluster': int(max(cluster_sizes)),
        'avg_cluster_duration': float(np.mean([c['duration_days'] for c in clusters if c['num_breaks'] > 1])) if any(c['num_breaks'] > 1 for c in clusters) else None,
    }

    return clusters, cluster_stats


@st.cache_data
def load_top_lists_for_period(period_name):
    """Load pre-calculated top lists from parquet files"""
    top_lists_dir = SCRIPT_DIR / 'top_lists'
    file_name = f'{period_name.lower().replace("-", "_")}_top_lists.parquet'
    file_path = top_lists_dir / file_name

    if not file_path.exists():
        return None

    try:
        df = pd.read_parquet(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading top lists: {e}")
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
        st.info("📈 Rankings based on pure historical support level behavior - pre-calculated for instant loading")

        # Load pre-calculated statistics
        df_all_stocks = load_top_lists_for_period(period_name)

        if df_all_stocks is not None and len(df_all_stocks) > 0:
            # Add data quality filter
            if 'Years of Data' in df_all_stocks.columns:
                st.sidebar.markdown("---")
                st.sidebar.subheader("Data Quality Filter")
                min_years = st.sidebar.slider(
                    "Minimum years of historical data",
                    min_value=0.0,
                    max_value=float(df_all_stocks['Years of Data'].max()),
                    value=5.0,
                    step=0.5,
                    help="Filter out stocks with limited historical data to ensure fair comparisons"
                )

                # Apply filter
                df_filtered = df_all_stocks[df_all_stocks['Years of Data'] >= min_years].copy()
                stocks_filtered_count = len(df_all_stocks) - len(df_filtered)

                if stocks_filtered_count > 0:
                    st.info(f"ℹ️ Showing {len(df_filtered)} stocks with ≥{min_years} years of data (filtered out {stocks_filtered_count} stocks with limited data)")

                df_all_stocks = df_filtered
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

                # Hide Median Days Between column (not useful - almost all stocks have same value)
                display_cols = [col for col in stable_df.columns if col != 'Median Days Between']
                st.dataframe(stable_df[display_cols], width='stretch', hide_index=True)

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

                # Hide Median Days Between column (not useful - almost all stocks have same value)
                display_cols = [col for col in time_df.columns if col != 'Median Days Between']
                st.dataframe(time_df[display_cols], width='stretch', hide_index=True)

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

                # Hide Median Days Between column (not useful - almost all stocks have same value)
                display_cols = [col for col in break_df.columns if col != 'Median Days Between']
                st.dataframe(break_df[display_cols], width='stretch', hide_index=True)

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
        margin=dict(l=0, r=0, t=80, b=0),
        xaxis=dict(rangeslider=dict(visible=False)),
        dragmode='pan'  # Pan mode for easier navigation
    )

    # Add range selector buttons for quick time period selection with automatic y-axis scaling
    # Position buttons on the right side to avoid overlapping with chart title
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]),
            bgcolor="lightgray",
            activecolor="gray",
            x=1.0,  # Position on the right
            y=1.0,
            xanchor='right',
            yanchor='bottom'
        )
    )

    # Display chart
    config = {'responsive': True, 'displayModeBar': True, 'displaylogo': False}
    st.plotly_chart(fig, config=config, use_container_width=True)

    st.info("💡 **Tip:** Use the **quick selection buttons** (1m, 3m, 6m, 1y, All) above the chart for zoom with automatic y-axis scaling, or adjust the **date range filter** in the sidebar for custom periods.")

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

        # Consecutive break analysis
        st.write("---")
        st.subheader("📊 Consecutive Break Analysis")
        st.write("**Clustering of support breaks - when multiple breaks happen within a short period**")

        # Max gap selector
        max_gap = st.slider(
            "Maximum days between consecutive breaks:",
            min_value=1,
            max_value=90,
            value=30,
            step=1,
            help="Breaks within this many days are considered consecutive (part of the same cluster)"
        )

        # Analyze consecutive breaks
        clusters, cluster_stats = analyze_consecutive_breaks(breaks, max_gap)

        if cluster_stats and cluster_stats['total_clusters'] > 0:
            # Display cluster statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Clusters", cluster_stats['total_clusters'],
                         help="Number of separate break clusters identified")
            with col2:
                st.metric("Multi-Break Clusters", cluster_stats['multi_break_clusters'],
                         help="Clusters with 2+ consecutive breaks")
            with col3:
                st.metric("Max Consecutive", cluster_stats['max_breaks_in_cluster'],
                         help="Largest number of breaks in a single cluster")
            with col4:
                st.metric("Avg Cluster Size", f"{cluster_stats['avg_breaks_per_cluster']:.1f}",
                         help="Average number of breaks per cluster")

            # Cluster size distribution chart
            cluster_sizes = [c['num_breaks'] for c in clusters]
            size_counts = pd.Series(cluster_sizes).value_counts().sort_index()

            fig_dist = px.bar(
                x=size_counts.index,
                y=size_counts.values,
                labels={'x': 'Number of Consecutive Breaks', 'y': 'Number of Clusters'},
                title=f'Distribution of Consecutive Break Clusters (max {max_gap}d gap)',
                color=size_counts.values,
                color_continuous_scale='Reds'
            )
            fig_dist.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_dist, use_container_width=True)

            # Show all clusters in detail
            if len(clusters) > 0:
                st.write("**All Break Clusters:**")

                for cluster in sorted(clusters, key=lambda x: x['cluster_id']):
                    # Use different emoji for single vs multi-break clusters
                    emoji = "🔴" if cluster['num_breaks'] > 1 else "🟡"
                    break_label = "break" if cluster['num_breaks'] == 1 else "breaks"

                    with st.expander(
                        f"{emoji} Cluster #{cluster['cluster_id']}: {cluster['num_breaks']} {break_label} "
                        f"({cluster['start_date'].strftime('%Y-%m-%d')} to {cluster['end_date'].strftime('%Y-%m-%d')})"
                    ):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Duration", f"{cluster['duration_days']} days")
                        with col_b:
                            if cluster['avg_gap_days'] is not None:
                                st.metric("Avg Gap", f"{cluster['avg_gap_days']:.1f} days")
                        with col_c:
                            st.metric("Total Drop", f"{cluster['total_drop_pct']:.2f}%")

                        # Show individual breaks in cluster
                        cluster_breaks = cluster['breaks'].copy()
                        cluster_breaks['Date'] = cluster_breaks['Date'].dt.strftime('%Y-%m-%d')
                        cluster_breaks.columns = ['Date', 'Previous Support', 'New Support', 'Drop %', 'Days From Previous']
                        st.dataframe(cluster_breaks, width='stretch', hide_index=True)

                # Summary stats for multi-break clusters only
                multi_break_clusters = [c for c in clusters if c['num_breaks'] > 1]
                if len(multi_break_clusters) > 0:
                    st.write("---")
                    st.write("**Multi-Break Cluster Summary:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_duration = np.mean([c['duration_days'] for c in multi_break_clusters])
                        st.metric("Avg Cluster Duration", f"{avg_duration:.1f} days",
                                 help="Average time from first to last break in multi-break clusters")
                    with col2:
                        avg_gaps = [c['avg_gap_days'] for c in multi_break_clusters if c['avg_gap_days'] is not None]
                        if avg_gaps:
                            st.metric("Avg Gap Between Breaks", f"{np.mean(avg_gaps):.1f} days",
                                     help="Average days between consecutive breaks within clusters")
                    with col3:
                        min_gaps = [c['min_gap_days'] for c in multi_break_clusters if c['min_gap_days'] is not None]
                        if min_gaps:
                            st.metric("Shortest Gap Ever", f"{min(min_gaps):.0f} days",
                                     help="Shortest time between two consecutive breaks")

            else:
                st.info(f"No clusters found.")

        else:
            st.info("Not enough breaks to analyze consecutive patterns")

    else:
        st.info(f"No support breaks detected in the selected date range for {period_name} {selected_stock}")


if __name__ == '__main__':
    main()
