"""
Mock Stock Data Generator

Generates realistic stock price data for testing strategies
without requiring live market data or API access.

Stock data characteristics:
- Lower volatility than crypto (typically 1-3% daily moves)
- Market hours only (9:30 AM - 4:00 PM ET)
- Gaps between trading days
- Different behavior than crypto
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Optional


class MockStockDataGenerator:
    """Generate realistic mock stock price data"""

    def __init__(self, seed: Optional[int] = 42):
        """
        Initialize mock stock data generator

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)

    def generate_stock_bars(self,
                           symbol: str = 'AAPL',
                           start_date: Optional[datetime] = None,
                           periods: int = 252,  # ~1 trading year
                           timeframe: str = '1Day',
                           initial_price: float = 150.0,
                           trend: float = 0.0002,  # Small upward bias
                           volatility: float = 0.02) -> pd.DataFrame:
        """
        Generate mock stock OHLCV data

        Args:
            symbol: Stock ticker
            start_date: Start date
            periods: Number of bars
            timeframe: Timeframe (1Min, 5Min, 1Hour, 1Day)
            initial_price: Starting price
            trend: Trend factor (stocks typically have small positive bias)
            volatility: Volatility factor (stocks less volatile than crypto)

        Returns:
            DataFrame with OHLCV data
        """
        # Calculate time delta based on timeframe
        timeframe_minutes = self._parse_timeframe(timeframe)

        # Generate trading timestamps (skip weekends and after-hours)
        if start_date is None:
            start_date = datetime.now() - timedelta(days=periods * 1.4)  # Account for weekends

        timestamps = self._generate_trading_timestamps(start_date, periods, timeframe_minutes)

        # Generate price series (lower volatility than crypto)
        returns = np.random.normal(trend, volatility, len(timestamps))
        price_series = initial_price * np.exp(np.cumsum(returns))

        # Generate OHLCV data
        data = []
        for i, timestamp in enumerate(timestamps):
            close = price_series[i]

            # Generate realistic OHLC
            daily_range = close * volatility * np.random.uniform(0.5, 2.0)
            high = close + daily_range * np.random.uniform(0.3, 0.7)
            low = close - daily_range * np.random.uniform(0.3, 0.7)

            # Open is previous close with a gap
            if i == 0:
                open_price = initial_price
            else:
                gap = (close - price_series[i-1]) * np.random.uniform(0.2, 0.5)
                open_price = price_series[i-1] + gap

            # Ensure OHLC relationships are valid
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            # Generate volume (stocks have more consistent volume)
            base_volume = 1000000  # 1M shares
            price_move = abs(close - open_price) / open_price
            volume = base_volume * (1 + price_move * 5) * np.random.uniform(0.7, 1.3)

            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': int(volume)
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    def _generate_trading_timestamps(self, start_date: datetime,
                                     periods: int, timeframe_minutes: int) -> list:
        """
        Generate timestamps that respect market hours

        Only generates timestamps during market hours (9:30 AM - 4:00 PM ET)
        and excludes weekends.
        """
        timestamps = []
        current = start_date

        # Market hours
        market_open = time(9, 30)   # 9:30 AM
        market_close = time(16, 0)  # 4:00 PM

        while len(timestamps) < periods:
            # Skip weekends
            if current.weekday() >= 5:  # Saturday = 5, Sunday = 6
                current += timedelta(days=1)
                current = current.replace(hour=9, minute=30, second=0)
                continue

            # For intraday, check market hours
            if timeframe_minutes < 1440:  # Less than 1 day
                current_time = current.time()
                if current_time < market_open:
                    current = current.replace(hour=9, minute=30, second=0)
                elif current_time >= market_close:
                    # Move to next day
                    current += timedelta(days=1)
                    current = current.replace(hour=9, minute=30, second=0)
                    continue

            timestamps.append(current)
            current += timedelta(minutes=timeframe_minutes)

        return timestamps

    def generate_tech_stock(self, periods: int = 252) -> pd.DataFrame:
        """Generate data resembling a tech stock (higher volatility)"""
        return self.generate_stock_bars(
            symbol='TECH',
            periods=periods,
            initial_price=300.0,
            trend=0.0005,
            volatility=0.025  # Higher volatility
        )

    def generate_blue_chip(self, periods: int = 252) -> pd.DataFrame:
        """Generate data resembling a blue chip stock (lower volatility)"""
        return self.generate_stock_bars(
            symbol='BLUE',
            periods=periods,
            initial_price=100.0,
            trend=0.0001,
            volatility=0.015  # Lower volatility
        )

    def generate_penny_stock(self, periods: int = 252) -> pd.DataFrame:
        """Generate data resembling a penny stock (high volatility)"""
        return self.generate_stock_bars(
            symbol='PENNY',
            periods=periods,
            initial_price=3.5,
            trend=0.0,
            volatility=0.05  # Very high volatility
        )

    def _parse_timeframe(self, timeframe: str) -> int:
        """
        Convert timeframe string to minutes

        Args:
            timeframe: Timeframe string (1Min, 5Min, 1Hour, 1Day)

        Returns:
            Number of minutes
        """
        # Handle Alpaca-style timeframes
        timeframe_lower = timeframe.lower()

        if 'min' in timeframe_lower:
            return int(timeframe_lower.replace('min', ''))
        elif 'hour' in timeframe_lower:
            value = int(timeframe_lower.replace('hour', ''))
            return value * 60
        elif 'day' in timeframe_lower:
            value = int(timeframe_lower.replace('day', ''))
            return value * 60 * 24
        elif timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 60 * 24
        else:
            raise ValueError(f"Unknown timeframe: {timeframe}")


# Convenience functions
def get_sample_stock_data(symbol: str = 'AAPL',
                         periods: int = 252,
                         timeframe: str = '1Day') -> pd.DataFrame:
    """
    Get sample stock data for testing

    Args:
        symbol: Stock ticker
        periods: Number of bars
        timeframe: Timeframe

    Returns:
        DataFrame with OHLCV data
    """
    generator = MockStockDataGenerator()
    return generator.generate_stock_bars(symbol=symbol, periods=periods, timeframe=timeframe)


if __name__ == "__main__":
    # Test stock data generation
    print("="*60)
    print("Testing Mock Stock Data Generator")
    print("="*60)

    generator = MockStockDataGenerator()

    # Generate different types of stock data
    print("\n1. Tech Stock (daily bars):")
    df_tech = generator.generate_tech_stock(periods=10)
    print(df_tech)

    print("\n2. Blue Chip Stock:")
    df_blue = generator.generate_blue_chip(periods=10)
    print(df_blue[['open', 'high', 'low', 'close', 'volume']])

    print("\n3. Sample with intraday data (1Hour):")
    df_intraday = generator.generate_stock_bars(periods=20, timeframe='1Hour')
    print(df_intraday[['open', 'high', 'low', 'close']].head(10))

    print("\n✓ Stock data generation successful!")
    print(f"Note: All timestamps respect market hours (9:30 AM - 4:00 PM)")
    print(f"Weekends are automatically excluded")
