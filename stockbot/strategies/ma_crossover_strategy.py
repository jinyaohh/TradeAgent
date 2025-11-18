"""
Moving Average Crossover Strategy for Stocks

A classic trend-following strategy that buys when a fast moving average
crosses above a slow moving average, and sells when it crosses below.

This is one of the most popular and reliable strategies for stock trading.
"""

import pandas as pd
from cryptobot.strategies.base_strategy import BaseStrategy
from shared.indicators.technical import sma, ema, atr, adx


class MaCrossoverStrategy(BaseStrategy):
    """
    Moving average crossover strategy for stock trading.

    Entry: Fast MA crosses above Slow MA (golden cross)
    Exit: Fast MA crosses below Slow MA (death cross)

    Works best in trending markets.
    """

    def __init__(self, config=None):
        """Initialize MA crossover strategy"""
        default_config = {
            'timeframe': '1Day',
            'stoploss': -0.02,      # 2% stop loss
            'fast_period': 50,      # 50-day MA
            'slow_period': 200,     # 200-day MA
            'ma_type': 'SMA',       # SMA or EMA
            'take_profit': 0.10,    # 10% take profit (let winners run)
            'volume_confirmation': True,
            'trend_strength_filter': True,  # Use ADX to filter
            'min_adx': 20,          # Minimum trend strength
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        self.fast_period = self.config['fast_period']
        self.slow_period = self.config['slow_period']
        self.ma_type = self.config['ma_type']
        self.take_profit = self.config['take_profit']
        self.volume_confirmation = self.config['volume_confirmation']
        self.trend_strength_filter = self.config['trend_strength_filter']
        self.min_adx = self.config['min_adx']

    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Add moving averages and supporting indicators"""
        # Choose MA type
        ma_func = sma if self.ma_type == 'SMA' else ema

        # Moving averages
        dataframe['ma_fast'] = ma_func(dataframe['close'], self.fast_period)
        dataframe['ma_slow'] = ma_func(dataframe['close'], self.slow_period)

        # Crossover detection
        dataframe['ma_diff'] = dataframe['ma_fast'] - dataframe['ma_slow']
        dataframe['ma_cross_up'] = (
            (dataframe['ma_diff'] > 0) &
            (dataframe['ma_diff'].shift(1) <= 0)
        )
        dataframe['ma_cross_down'] = (
            (dataframe['ma_diff'] < 0) &
            (dataframe['ma_diff'].shift(1) >= 0)
        )

        # Volume
        dataframe['volume_sma'] = sma(dataframe['volume'], 20)

        # Trend strength (ADX)
        if self.trend_strength_filter:
            dataframe['adx'] = adx(dataframe['high'], dataframe['low'],
                                  dataframe['close'], 14)

        # Volatility (ATR)
        dataframe['atr'] = atr(dataframe['high'], dataframe['low'],
                              dataframe['close'], 14)

        return dataframe

    def entry_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Buy when fast MA crosses above slow MA

        Additional filters:
        - Volume above average (confirmation)
        - ADX above minimum (trending market)
        - Price not too far above MA (avoid chasing)
        """
        row = dataframe.iloc[index]

        # Check for golden cross
        if not row['ma_cross_up']:
            return False

        # Make sure both MAs are calculated
        if pd.isna(row['ma_fast']) or pd.isna(row['ma_slow']):
            return False

        # Volume confirmation
        if self.volume_confirmation:
            if pd.notna(row['volume_sma']):
                if row['volume'] < row['volume_sma']:
                    return False

        # Trend strength filter (avoid choppy markets)
        if self.trend_strength_filter:
            if pd.notna(row['adx']):
                if row['adx'] < self.min_adx:
                    return False

        # Don't buy if price has already moved too far above slow MA
        if row['close'] > row['ma_slow'] * 1.10:  # More than 10% above
            return False

        return True

    def exit_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Sell when fast MA crosses below slow MA
        """
        row = dataframe.iloc[index]

        # Check for death cross
        if row['ma_cross_down']:
            return True

        return False

    def confirm_trade(self, dataframe: pd.DataFrame, index: int, side: str) -> bool:
        """Additional trade confirmation"""
        row = dataframe.iloc[index]

        # Ensure valid data
        if pd.isna(row['ma_fast']) or pd.isna(row['ma_slow']):
            return False

        # For buy signals, check price isn't too low
        if side == 'buy':
            if row['close'] < 10.0:  # Avoid low-priced stocks
                return False

        return True

    def should_exit_roi(self, current_profit: float, trade_duration: int = 0) -> bool:
        """
        Check if take profit reached

        For trend-following, we want to let winners run, so higher target
        """
        if current_profit >= self.take_profit:
            return True
        return False


if __name__ == "__main__":
    print("MA Crossover Strategy for Stocks")
    print("Use test script: python scripts/test_stock_strategies.py")
