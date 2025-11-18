"""
Mock Data Generator for Testing

Generates realistic cryptocurrency price data for testing strategies
without needing a live connection to exchanges.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


class MockDataGenerator:
    """Generate realistic mock cryptocurrency price data"""

    def __init__(self, seed: Optional[int] = 42):
        """
        Initialize mock data generator

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)

    def generate_ohlcv(self,
                      symbol: str = 'BTC/USDT',
                      start_date: Optional[datetime] = None,
                      periods: int = 1000,
                      timeframe: str = '1h',
                      initial_price: float = 50000.0,
                      trend: float = 0.0,
                      volatility: float = 0.02) -> pd.DataFrame:
        """
        Generate mock OHLCV data

        Args:
            symbol: Trading pair symbol
            start_date: Start datetime (defaults to 1000 periods ago)
            periods: Number of candles to generate
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            initial_price: Starting price
            trend: Trend factor (-0.01 to 0.01 for realistic trends)
            volatility: Volatility factor (0.01 to 0.05 for realistic vol)

        Returns:
            DataFrame with OHLCV data
        """
        # Calculate time delta based on timeframe
        timeframe_minutes = self._parse_timeframe(timeframe)

        # Generate timestamps
        if start_date is None:
            start_date = datetime.now() - timedelta(minutes=timeframe_minutes * periods)

        timestamps = [start_date + timedelta(minutes=timeframe_minutes * i)
                     for i in range(periods)]

        # Generate price series using geometric Brownian motion
        returns = np.random.normal(trend, volatility, periods)
        price_series = initial_price * np.exp(np.cumsum(returns))

        # Generate OHLCV data
        data = []
        for i, timestamp in enumerate(timestamps):
            close = price_series[i]

            # Generate realistic OHLC from close price
            hl_range = close * volatility * np.random.uniform(0.5, 2.0)
            high = close + hl_range * np.random.uniform(0, 1)
            low = close - hl_range * np.random.uniform(0, 1)

            # Open is previous close (with some gap)
            if i == 0:
                open_price = initial_price
            else:
                gap = (close - price_series[i-1]) * np.random.uniform(0.3, 0.7)
                open_price = price_series[i-1] + gap

            # Ensure OHLC relationships are valid
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            # Generate volume (correlated with price movement)
            price_change = abs(close - open_price) / open_price
            base_volume = 1000
            volume = base_volume * (1 + price_change * 10) * np.random.uniform(0.5, 1.5)

            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': round(volume, 2)
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def generate_trending_data(self,
                              periods: int = 1000,
                              timeframe: str = '1h',
                              trend_strength: float = 0.001) -> pd.DataFrame:
        """
        Generate data with a clear uptrend

        Args:
            periods: Number of candles
            timeframe: Timeframe
            trend_strength: Strength of trend (0.0005 to 0.002)

        Returns:
            DataFrame with trending OHLCV data
        """
        return self.generate_ohlcv(
            periods=periods,
            timeframe=timeframe,
            trend=trend_strength,
            volatility=0.015
        )

    def generate_ranging_data(self,
                             periods: int = 1000,
                             timeframe: str = '1h') -> pd.DataFrame:
        """
        Generate sideways/ranging market data

        Args:
            periods: Number of candles
            timeframe: Timeframe

        Returns:
            DataFrame with ranging OHLCV data
        """
        return self.generate_ohlcv(
            periods=periods,
            timeframe=timeframe,
            trend=0.0,
            volatility=0.01
        )

    def generate_volatile_data(self,
                              periods: int = 1000,
                              timeframe: str = '1h') -> pd.DataFrame:
        """
        Generate highly volatile market data

        Args:
            periods: Number of candles
            timeframe: Timeframe

        Returns:
            DataFrame with volatile OHLCV data
        """
        return self.generate_ohlcv(
            periods=periods,
            timeframe=timeframe,
            trend=0.0,
            volatility=0.05
        )

    def _parse_timeframe(self, timeframe: str) -> int:
        """
        Convert timeframe string to minutes

        Args:
            timeframe: Timeframe string (1m, 5m, 1h, 1d, etc.)

        Returns:
            Number of minutes
        """
        unit = timeframe[-1]
        value = int(timeframe[:-1])

        if unit == 'm':
            return value
        elif unit == 'h':
            return value * 60
        elif unit == 'd':
            return value * 60 * 24
        elif unit == 'w':
            return value * 60 * 24 * 7
        else:
            raise ValueError(f"Unknown timeframe unit: {unit}")


# Convenience functions
def get_sample_data(periods: int = 1000, timeframe: str = '1h') -> pd.DataFrame:
    """
    Get sample OHLCV data for testing

    Args:
        periods: Number of candles
        timeframe: Timeframe

    Returns:
        DataFrame with OHLCV data
    """
    generator = MockDataGenerator()
    return generator.generate_ohlcv(periods=periods, timeframe=timeframe)


def get_trending_sample() -> pd.DataFrame:
    """Get sample data with uptrend"""
    generator = MockDataGenerator()
    return generator.generate_trending_data()


def get_ranging_sample() -> pd.DataFrame:
    """Get sample ranging/sideways data"""
    generator = MockDataGenerator()
    return generator.generate_ranging_data()


if __name__ == "__main__":
    # Test mock data generation
    print("Generating mock OHLCV data...")

    generator = MockDataGenerator()

    # Generate different types of data
    print("\n1. Normal market data:")
    df_normal = generator.generate_ohlcv(periods=10, timeframe='1h')
    print(df_normal)

    print("\n2. Trending market data:")
    df_trend = generator.generate_trending_data(periods=10)
    print(df_trend[['open', 'high', 'low', 'close', 'volume']])

    print("\n3. Ranging market data:")
    df_range = generator.generate_ranging_data(periods=10)
    print(df_range[['open', 'high', 'low', 'close', 'volume']])

    print("\n✓ Mock data generation successful!")
