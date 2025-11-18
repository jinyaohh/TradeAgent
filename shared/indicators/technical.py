"""
Technical Indicators for Trading Strategies

Implements common technical indicators without external dependencies.
Based on standard formulas.
"""

import pandas as pd
import numpy as np
from typing import Optional


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average

    Args:
        series: Price series
        period: Number of periods

    Returns:
        SMA series
    """
    return series.rolling(window=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average

    Args:
        series: Price series
        period: Number of periods

    Returns:
        EMA series
    """
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index

    Args:
        series: Price series
        period: RSI period (default 14)

    Returns:
        RSI series (0-100)
    """
    # Calculate price changes
    delta = series.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)

    # Calculate average gains and losses
    avg_gains = gains.ewm(span=period, adjust=False).mean()
    avg_losses = losses.ewm(span=period, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi_values = 100 - (100 / (1 + rs))

    return rsi_values


def macd(series: pd.Series,
         fast_period: int = 12,
         slow_period: int = 26,
         signal_period: int = 9) -> tuple:
    """
    Moving Average Convergence Divergence

    Args:
        series: Price series
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line period

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    # Calculate MACD line
    fast_ema = ema(series, fast_period)
    slow_ema = ema(series, slow_period)
    macd_line = fast_ema - slow_ema

    # Calculate signal line
    signal_line = ema(macd_line, signal_period)

    # Calculate histogram
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series,
                   period: int = 20,
                   std_dev: float = 2.0) -> tuple:
    """
    Bollinger Bands

    Args:
        series: Price series
        period: Moving average period
        std_dev: Number of standard deviations

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle_band = sma(series, period)
    rolling_std = series.rolling(window=period).std()

    upper_band = middle_band + (rolling_std * std_dev)
    lower_band = middle_band - (rolling_std * std_dev)

    return upper_band, middle_band, lower_band


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average True Range

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period

    Returns:
        ATR series
    """
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    true_range = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)

    # Calculate ATR using EMA
    atr_values = true_range.ewm(span=period, adjust=False).mean()

    return atr_values


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
              k_period: int = 14, d_period: int = 3) -> tuple:
    """
    Stochastic Oscillator

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        k_period: %K period
        d_period: %D period

    Returns:
        Tuple of (%K, %D)
    """
    # Calculate %K
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)

    # Calculate %D (SMA of %K)
    d_percent = k_percent.rolling(window=d_period).mean()

    return k_percent, d_percent


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average Directional Index (trend strength indicator)

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ADX period

    Returns:
        ADX series (0-100, higher = stronger trend)
    """
    # Calculate +DM and -DM
    plus_dm = high.diff()
    minus_dm = -low.diff()

    # Zero out opposite movements
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    plus_dm[(minus_dm > plus_dm)] = 0
    minus_dm[(plus_dm > minus_dm)] = 0

    # Calculate ATR
    atr_values = atr(high, low, close, period)

    # Calculate +DI and -DI
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr_values)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr_values)

    # Calculate DX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

    # Calculate ADX
    adx_values = dx.ewm(span=period, adjust=False).mean()

    return adx_values


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume

    Args:
        close: Close prices
        volume: Volume

    Returns:
        OBV series
    """
    obv_values = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv_values


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all common technical indicators to a dataframe

    Args:
        df: DataFrame with OHLCV data

    Returns:
        DataFrame with added indicator columns
    """
    # Make a copy to avoid modifying original
    df = df.copy()

    # Moving Averages
    df['sma_20'] = sma(df['close'], 20)
    df['sma_50'] = sma(df['close'], 50)
    df['sma_200'] = sma(df['close'], 200)
    df['ema_12'] = ema(df['close'], 12)
    df['ema_26'] = ema(df['close'], 26)

    # RSI
    df['rsi'] = rsi(df['close'], 14)

    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = macd(df['close'])

    # Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = bollinger_bands(df['close'])

    # ATR
    df['atr'] = atr(df['high'], df['low'], df['close'])

    # Stochastic
    df['stoch_k'], df['stoch_d'] = stochastic(df['high'], df['low'], df['close'])

    # ADX (trend strength)
    df['adx'] = adx(df['high'], df['low'], df['close'])

    # OBV
    df['obv'] = obv(df['close'], df['volume'])

    return df


if __name__ == "__main__":
    # Test indicators with mock data
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from cryptobot.data.mock_data import get_sample_data

    print("Testing Technical Indicators...")

    # Generate sample data
    df = get_sample_data(periods=100, timeframe='1h')

    # Add all indicators
    df_with_indicators = add_all_indicators(df)

    print("\nDataFrame with indicators:")
    print(df_with_indicators[['close', 'rsi', 'macd', 'sma_20', 'bb_upper', 'bb_lower']].tail())

    print("\n✓ Technical indicators working correctly!")
