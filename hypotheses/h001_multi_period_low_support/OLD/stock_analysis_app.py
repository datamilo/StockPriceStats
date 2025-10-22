#!/usr/bin/env python3
"""
Interactive Streamlit dashboard for H001 multi-period low analysis.
Visualizes per-stock success/failure patterns with dynamic filtering.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="H001 Stock Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# LOAD DATA
# ============================================================================

@st.cache_data
def load_detailed_results(period_file):
    """Load detailed results for a specific period."""
    try:
        df = pd.read_parquet(f'{period_file}_detailed_results.parquet')
        df['support_date'] = pd.to_datetime(df['support_date'])
        df['test_date'] = pd.to_datetime(df['test_date'])
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        return df
    except FileNotFoundError:
        st.error(f"File not found: {period_file}_detailed_results.parquet")
        return pd.DataFrame()

@st.cache_data
def load_price_data():
    """Load price data for all stocks."""
    try:
        df = pd.read_parquet('../../price_data_filtered.parquet')
        df['date'] = pd.to_datetime(df['date'])
        # Rename 'name' column to 'stock' for consistency
        df = df.rename(columns={'name': 'stock'})
        return df
    except FileNotFoundError:
        st.error("Price data file not found: ../../price_data_filtered.parquet")
        return pd.DataFrame()

@st.cache_data
def load_all_periods():
    """Load data for all periods."""
    periods_data = {}
    period_files = [
        ('1_month', '1-Month Low'),
        ('3_month', '3-Month Low'),
        ('6_month', '6-Month Low'),
        ('9_month', '9-Month Low'),
        ('1_year', '1-Year Low')
    ]

    for file_prefix, period_name in period_files:
        df = load_detailed_results(file_prefix)
        if not df.empty:
            periods_data[period_name] = df

    return periods_data

# Load data
periods_data = load_all_periods()
price_data = load_price_data()

if not periods_data or price_data.empty:
    st.error("❌ Unable to load required data files")
    st.stop()

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================

st.sidebar.title("🔧 Filters")

# Period selector
period_name = st.sidebar.selectbox(
    "📅 Select Low Period",
    options=list(periods_data.keys()),
    help="Choose the low period to analyze"
)
df_period = periods_data[period_name]

# Stock selector
stocks = sorted(df_period['stock'].unique())
selected_stock = st.sidebar.selectbox(
    "🏢 Select Stock",
    options=stocks,
    help="Choose a stock to analyze"
)
df_stock = df_period[df_period['stock'] == selected_stock].copy()

# Wait days selector
wait_days_options = sorted(df_stock['wait_days'].unique())
selected_wait_days = st.sidebar.multiselect(
    "⏳ Wait Days (Days before writing put)",
    options=wait_days_options,
    default=[0, 90] if 0 in wait_days_options and 90 in wait_days_options else wait_days_options[:2],
    help="Select which wait periods to analyze"
)

# Expiry days selector
expiry_days_options = sorted(df_stock['expiry_days'].unique())
selected_expiry_days = st.sidebar.multiselect(
    "📈 Expiry Days (Put option duration)",
    options=expiry_days_options,
    default=[30] if 30 in expiry_days_options else [expiry_days_options[0]],
    help="Select which expiry periods to analyze"
)

# Filter the data
df_filtered = df_stock[
    (df_stock['wait_days'].isin(selected_wait_days)) &
    (df_stock['expiry_days'].isin(selected_expiry_days))
].copy()

if df_filtered.empty:
    st.warning("❌ No data available for the selected filters")
    st.stop()

# ============================================================================
# DISPLAY TITLE AND KEY METRICS
# ============================================================================

st.title(f"📊 {selected_stock} - {period_name} Analysis")
st.markdown(f"**Period:** {period_name} | **Low Period Days:** {df_period['period_days'].iloc[0]}")

# Get price data for the stock
df_price = price_data[price_data['stock'] == selected_stock].copy()

if df_price.empty:
    st.warning(f"No price data available for {selected_stock}")
    st.stop()

# ============================================================================
# KEY METRICS
# ============================================================================

col1, col2, col3, col4, col5 = st.columns(5)

total_events = len(df_filtered)
successful = (df_filtered['success'] == 'True').sum() if 'success' in df_filtered.columns else (df_filtered['success'] == True).sum()
success_rate = (successful / total_events * 100) if total_events > 0 else 0
avg_support_level = df_filtered['support_level'].mean()
max_drawdown = df_filtered['break_pct'].min() if 'break_pct' in df_filtered.columns else None

with col1:
    st.metric(
        "Total Events",
        f"{total_events:,}",
        help="Total number of support events matching filters"
    )

with col2:
    st.metric(
        "Success Rate",
        f"{success_rate:.1f}%",
        delta=f"{successful}/{total_events}",
        help="Percentage of supports that held"
    )

with col3:
    st.metric(
        "Avg Support Level",
        f"{avg_support_level:.2f} kr",
        help="Average support price level"
    )

with col4:
    st.metric(
        "Min Price",
        f"{df_price['close'].min():.2f} kr",
        help="Lowest price in data"
    )

with col5:
    st.metric(
        "Max Price",
        f"{df_price['close'].max():.2f} kr",
        help="Highest price in data"
    )

# ============================================================================
# DATE RANGE SLIDER
# ============================================================================

st.subheader("📅 Date Range Selector")

min_date = df_price['date'].min()
max_date = df_price['date'].max()

col_range1, col_range2 = st.columns(2)

with col_range1:
    date_from = st.date_input(
        "From",
        value=max(min_date, max_date - timedelta(days=365*2)),  # Default: last 2 years
        min_value=min_date,
        max_value=max_date,
        help="Start date for chart"
    )

with col_range2:
    date_to = st.date_input(
        "To",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        help="End date for chart"
    )

# Convert to datetime for filtering
date_from = pd.to_datetime(date_from)
date_to = pd.to_datetime(date_to)

# Filter price data by date range
df_price_filtered = df_price[(df_price['date'] >= date_from) & (df_price['date'] <= date_to)].copy()

# Also filter support events by date range
df_events_filtered = df_filtered[
    (df_filtered['support_date'] >= date_from) & (df_filtered['support_date'] <= date_to)
].copy()

# ============================================================================
# INTERACTIVE PRICE CHART WITH SUPPORT EVENTS
# ============================================================================

st.subheader("📉 Price Chart with Support Events")

if df_price_filtered.empty:
    st.warning("No price data in selected date range")
else:
    # Create the figure
    fig = go.Figure()

    # Add price line
    fig.add_trace(go.Scatter(
        x=df_price_filtered['date'],
        y=df_price_filtered['close'],
        mode='lines',
        name='Close Price',
        line=dict(color='#34495e', width=2),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Price: %{y:.2f} kr<extra></extra>',
        fill='tozeroy',
        fillcolor='rgba(52, 73, 94, 0.05)'
    ))

    # Add support events with different colors for success/failure
    if not df_events_filtered.empty:
        # Separate successful and failed events
        df_success = df_events_filtered[df_events_filtered['success'] == 'True'] if 'success' in df_events_filtered.columns else df_events_filtered[df_events_filtered['success'] == True]
        df_failure = df_events_filtered[df_events_filtered['success'] != 'True'] if 'success' in df_events_filtered.columns else df_events_filtered[df_events_filtered['success'] != True]

        # Add success markers
        if not df_success.empty:
            fig.add_trace(go.Scatter(
                x=df_success['support_date'],
                y=df_success['support_level'],
                mode='markers',
                name='✅ Success',
                marker=dict(
                    color='#27ae60',
                    size=10,
                    symbol='diamond',
                    line=dict(color='#229954', width=2)
                ),
                customdata=df_success[['wait_days', 'expiry_days', 'min_during_option', 'test_date', 'days_to_break', 'break_pct']],
                hovertemplate=
                    '<b>✅ SUCCESS - Support Held</b><br>' +
                    'Support Date: %{x|%Y-%m-%d}<br>' +
                    'Support Level: %{y:.2f} kr<br>' +
                    'Wait Days: %{customdata[0]}<br>' +
                    'Expiry Days: %{customdata[1]}<br>' +
                    'Min Price During Option: %{customdata[2]:.2f} kr<br>' +
                    'Test End Date: %{customdata[3]|%Y-%m-%d}<br>' +
                    '<extra></extra>',
                showlegend=True
            ))

        # Add failure markers
        if not df_failure.empty:
            fig.add_trace(go.Scatter(
                x=df_failure['support_date'],
                y=df_failure['support_level'],
                mode='markers',
                name='❌ Failure',
                marker=dict(
                    color='#e74c3c',
                    size=10,
                    symbol='x',
                    line=dict(color='#c0392b', width=2)
                ),
                customdata=df_failure[['wait_days', 'expiry_days', 'min_during_option', 'test_date', 'days_to_break', 'break_pct']],
                hovertemplate=
                    '<b>❌ FAILURE - Support Broke</b><br>' +
                    'Support Date: %{x|%Y-%m-%d}<br>' +
                    'Support Level: %{y:.2f} kr<br>' +
                    'Wait Days: %{customdata[0]}<br>' +
                    'Expiry Days: %{customdata[1]}<br>' +
                    'Min Price During Option: %{customdata[2]:.2f} kr<br>' +
                    'Test End Date: %{customdata[3]|%Y-%m-%d}<br>' +
                    'Days to Break: %{customdata[4]:.0f}<br>' +
                    'Decline: %{customdata[5]:.2f}%<br>' +
                    '<extra></extra>',
                showlegend=True
            ))

    # Update layout
    fig.update_layout(
        title=f"{selected_stock} Price Chart ({date_from.date()} to {date_to.date()})",
        xaxis_title="Date",
        yaxis_title="Price (kr)",
        height=600,
        hovermode='x unified',
        template='plotly_white',
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date'
        ),
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#2c3e50',
            borderwidth=1
        ),
        font=dict(size=11)
    )

    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# SUCCESS RATE ANALYSIS BY WAIT DAYS AND EXPIRY DAYS
# ============================================================================

st.subheader("📊 Success Rate Breakdown")

col_breakdown1, col_breakdown2 = st.columns(2)

with col_breakdown1:
    st.markdown("**Success Rate by Wait Days:**")
    success_by_wait = df_filtered.groupby('wait_days').apply(
        lambda x: (
            (x['success'] == 'True').sum() if 'success' in x.columns else (x['success'] == True).sum()
        ) / len(x) * 100
    ).reset_index()
    success_by_wait.columns = ['Wait Days', 'Success Rate (%)']

    # Format as a nice table
    for idx, row in success_by_wait.iterrows():
        st.write(f"**{int(row['Wait Days'])} days:** {row['Success Rate (%)']:.1f}%")

with col_breakdown2:
    st.markdown("**Success Rate by Expiry Days:**")
    success_by_expiry = df_filtered.groupby('expiry_days').apply(
        lambda x: (
            (x['success'] == 'True').sum() if 'success' in x.columns else (x['success'] == True).sum()
        ) / len(x) * 100
    ).reset_index()
    success_by_expiry.columns = ['Expiry Days', 'Success Rate (%)']

    # Format as a nice table
    for idx, row in success_by_expiry.iterrows():
        st.write(f"**{int(row['Expiry Days'])} days:** {row['Success Rate (%)']:.1f}%")

# ============================================================================
# DETAILED EVENT TABLE
# ============================================================================

st.subheader("📋 Detailed Event Data")

# Prepare display columns
display_df = df_events_filtered[[
    'support_date', 'support_level', 'wait_days', 'expiry_days',
    'test_date', 'min_during_option', 'success', 'days_to_break', 'break_pct'
]].copy()

display_df = display_df.rename(columns={
    'support_date': 'Support Date',
    'support_level': 'Support Level (kr)',
    'wait_days': 'Wait Days',
    'expiry_days': 'Expiry Days',
    'test_date': 'Test Date',
    'min_during_option': 'Min Price (kr)',
    'success': 'Result',
    'days_to_break': 'Days to Break',
    'break_pct': 'Decline %'
})

# Format dates
display_df['Support Date'] = display_df['Support Date'].dt.strftime('%Y-%m-%d')
display_df['Test Date'] = display_df['Test Date'].dt.strftime('%Y-%m-%d')

# Format numbers
display_df['Support Level (kr)'] = display_df['Support Level (kr)'].apply(lambda x: f"{x:.2f}")
display_df['Min Price (kr)'] = display_df['Min Price (kr)'].apply(lambda x: f"{x:.2f}")
display_df['Break_pct'] = display_df['Decline %'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
display_df['Days to Break'] = display_df['Days to Break'].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "-")

# Remove old break_pct column and reorder
display_df = display_df[['Support Date', 'Support Level (kr)', 'Wait Days', 'Expiry Days',
                         'Test Date', 'Min Price (kr)', 'Result', 'Days to Break', 'Break_pct']]

# Color the results column
def color_result(val):
    if val == 'True' or val == True:
        return '✅ Success'
    else:
        return '❌ Failure'

display_df['Result'] = display_df['Result'].apply(color_result)
display_df = display_df.rename(columns={'Break_pct': 'Decline %'})

# Display table
st.dataframe(
    display_df.sort_values('Support Date', ascending=False),
    use_container_width=True,
    height=400,
    hide_index=True
)

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

st.subheader("📈 Summary Statistics")

col_stat1, col_stat2, col_stat3 = st.columns(3)

with col_stat1:
    st.write("**Support Level Statistics:**")
    st.write(f"Mean: {df_filtered['support_level'].mean():.2f} kr")
    st.write(f"Median: {df_filtered['support_level'].median():.2f} kr")
    st.write(f"Std Dev: {df_filtered['support_level'].std():.2f} kr")

with col_stat2:
    st.write("**Minimum Price During Option (Failures):**")
    df_failure_events = df_filtered[df_filtered['success'] != 'True'] if 'success' in df_filtered.columns else df_filtered[df_filtered['success'] != True]
    if len(df_failure_events) > 0:
        st.write(f"Mean: {df_failure_events['min_during_option'].mean():.2f} kr")
        st.write(f"Median: {df_failure_events['min_during_option'].median():.2f} kr")
        st.write(f"Min: {df_failure_events['min_during_option'].min():.2f} kr")
    else:
        st.write("No failures to analyze")

with col_stat3:
    st.write("**Data Coverage:**")
    st.write(f"Date range: {df_events_filtered['support_date'].min().date()} to {df_events_filtered['support_date'].max().date()}")
    st.write(f"Days span: {(df_events_filtered['support_date'].max() - df_events_filtered['support_date'].min()).days} days")
    st.write(f"Events in range: {len(df_events_filtered)} / {total_events}")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
**📖 How to use this dashboard:**
1. Select a low period from the sidebar
2. Choose a stock to analyze
3. Select which wait days and expiry days to view
4. Use the date range slider to zoom in on specific time periods
5. Hover over the chart markers to see detailed information about each support event
6. Green diamonds (✅) = support held successfully
7. Red X marks (❌) = support broke and failed the test

**💡 Key metrics:**
- **Success Rate:** % of events where support held during the option period
- **Decline %:** How far below support price the stock fell during failure
- **Days to Break:** How quickly the support broke after being set
""")
