"""
Example script for technical analysis on price data
This script demonstrates basic usage of the installed libraries
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
import pandas_ta as pta

# Set plotting style
sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)

def load_data(use_filtered=True):
    """
    Load the parquet file

    Args:
        use_filtered: If True, load filtered data (only stocks with options).
                     If False, load all stock data.
    """
    if use_filtered:
        filename = 'price_data_filtered.parquet'
    else:
        filename = 'price_data_all.parquet'

    df = pd.read_parquet(filename)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_stock_data(df, stock_name):
    """Get data for a specific stock"""
    stock_df = df[df['name'] == stock_name].copy()
    stock_df = stock_df.sort_values('date').reset_index(drop=True)
    return stock_df

def add_technical_indicators(df):
    """
    Add common technical indicators to the dataframe
    Requires columns: close, high, low, volume
    """
    # Make sure we have the required columns
    if not all(col in df.columns for col in ['close', 'high', 'low']):
        print("Missing required columns (close, high, low)")
        return df

    # Simple Moving Averages
    df['SMA_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['SMA_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
    df['SMA_200'] = SMAIndicator(close=df['close'], window=200).sma_indicator()

    # Exponential Moving Averages
    df['EMA_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()
    df['EMA_26'] = EMAIndicator(close=df['close'], window=26).ema_indicator()

    # MACD
    macd = MACD(close=df['close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_diff'] = macd.macd_diff()

    # RSI
    df['RSI'] = RSIIndicator(close=df['close'], window=14).rsi()

    # Bollinger Bands
    bb = BollingerBands(close=df['close'], window=20, window_dev=2)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_middle'] = bb.bollinger_mavg()
    df['BB_lower'] = bb.bollinger_lband()

    # Average True Range (if volume exists)
    if 'volume' in df.columns and df['volume'].notna().sum() > 0:
        df['ATR'] = AverageTrueRange(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=14
        ).average_true_range()

    # Stochastic Oscillator
    stoch = StochasticOscillator(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        window=14,
        smooth_window=3
    )
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()

    return df

def plot_price_with_indicators(df, stock_name):
    """Plot price chart with technical indicators"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

    # Price and Moving Averages
    axes[0].plot(df['date'], df['close'], label='Close Price', linewidth=2)
    axes[0].plot(df['date'], df['SMA_20'], label='SMA 20', alpha=0.7)
    axes[0].plot(df['date'], df['SMA_50'], label='SMA 50', alpha=0.7)
    axes[0].plot(df['date'], df['SMA_200'], label='SMA 200', alpha=0.7)
    axes[0].set_title(f'{stock_name} - Price and Moving Averages')
    axes[0].set_ylabel('Price')
    axes[0].legend()
    axes[0].grid(True)

    # Bollinger Bands
    axes[1].plot(df['date'], df['close'], label='Close Price', linewidth=2)
    axes[1].plot(df['date'], df['BB_upper'], label='BB Upper', alpha=0.5, linestyle='--')
    axes[1].plot(df['date'], df['BB_middle'], label='BB Middle', alpha=0.5)
    axes[1].plot(df['date'], df['BB_lower'], label='BB Lower', alpha=0.5, linestyle='--')
    axes[1].fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.2)
    axes[1].set_title('Bollinger Bands')
    axes[1].set_ylabel('Price')
    axes[1].legend()
    axes[1].grid(True)

    # RSI
    axes[2].plot(df['date'], df['RSI'], label='RSI', color='purple', linewidth=2)
    axes[2].axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Overbought (70)')
    axes[2].axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Oversold (30)')
    axes[2].set_title('Relative Strength Index (RSI)')
    axes[2].set_ylabel('RSI')
    axes[2].set_ylim(0, 100)
    axes[2].legend()
    axes[2].grid(True)

    # MACD
    axes[3].plot(df['date'], df['MACD'], label='MACD', linewidth=2)
    axes[3].plot(df['date'], df['MACD_signal'], label='Signal', linewidth=2)
    axes[3].bar(df['date'], df['MACD_diff'], label='MACD Diff', alpha=0.3)
    axes[3].axhline(y=0, color='black', linestyle='-', alpha=0.3)
    axes[3].set_title('MACD')
    axes[3].set_ylabel('MACD')
    axes[3].set_xlabel('Date')
    axes[3].legend()
    axes[3].grid(True)

    plt.tight_layout()
    plt.savefig(f'{stock_name.replace(" ", "_")}_technical_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Chart saved as {stock_name.replace(' ', '_')}_technical_analysis.png")

def main():
    """Main function to run the analysis"""
    # Load data (using filtered data by default - only stocks with options)
    print("Loading filtered data (stocks with options)...")
    df = load_data(use_filtered=True)  # Set to False to use all stocks

    # Show available stocks
    print(f"\nTotal rows: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\nNumber of unique stocks: {df['name'].nunique()}")
    print("\nFirst 10 stocks:")
    print(df['name'].value_counts().head(10))

    # Example: Analyze a specific stock (change this to your preferred stock)
    # Get the first stock with sufficient data
    stock_counts = df.groupby('name').size().sort_values(ascending=False)
    example_stock = stock_counts.index[0]

    print(f"\n{'='*60}")
    print(f"Example Analysis for: {example_stock}")
    print(f"{'='*60}")

    # Get stock data
    stock_df = get_stock_data(df, example_stock)
    print(f"\nData points: {len(stock_df)}")
    print(f"Date range: {stock_df['date'].min()} to {stock_df['date'].max()}")

    # Add technical indicators
    print("\nCalculating technical indicators...")
    stock_df = add_technical_indicators(stock_df)

    # Display latest values
    print("\nLatest technical indicators:")
    latest = stock_df.iloc[-1]
    print(f"Date: {latest['date']}")
    print(f"Close: {latest['close']:.2f}")
    print(f"SMA 20: {latest['SMA_20']:.2f}")
    print(f"SMA 50: {latest['SMA_50']:.2f}")
    print(f"RSI: {latest['RSI']:.2f}")
    print(f"MACD: {latest['MACD']:.4f}")

    # Plot
    print("\nGenerating charts...")
    plot_price_with_indicators(stock_df, example_stock)

    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)
    print("\nTo analyze a different stock, modify the 'example_stock' variable")
    print("or use: get_stock_data(df, 'STOCK_NAME')")

if __name__ == "__main__":
    main()
