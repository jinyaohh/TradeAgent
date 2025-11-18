"""
Base Strategy Class for Crypto Trading

Defines the interface and common functionality that all trading strategies must implement.
Inspired by FreqTrade's strategy architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import pandas as pd
from datetime import datetime
from enum import Enum

from monitoring.logger import get_logger

logger = get_logger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    All strategies must implement:
    - populate_indicators(): Add technical indicators to dataframe
    - entry_signal(): Determine if should enter position
    - exit_signal(): Determine if should exit position
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize strategy

        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.name = self.__class__.__name__

        # Strategy parameters (can be overridden)
        self.timeframe = self.config.get('timeframe', '1h')
        self.minimal_roi = self.config.get('minimal_roi', {})
        self.stoploss = self.config.get('stoploss', -0.02)  # Default -2%
        self.trailing_stop = self.config.get('trailing_stop', False)
        self.trailing_stop_positive = self.config.get('trailing_stop_positive', 0.01)

        # Risk management
        self.max_open_trades = self.config.get('max_open_trades', 5)

        logger.info(f"Strategy '{self.name}' initialized with timeframe {self.timeframe}")

    @abstractmethod
    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataframe.

        This method is called once when the strategy loads data and calculates
        all necessary technical indicators.

        Args:
            dataframe: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicator columns

        Example:
            def populate_indicators(self, dataframe):
                dataframe['rsi'] = rsi(dataframe['close'], 14)
                dataframe['sma'] = sma(dataframe['close'], 20)
                return dataframe
        """
        pass

    @abstractmethod
    def entry_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Determine if should enter a buy position.

        This method is called for each candle to check if entry conditions are met.

        Args:
            dataframe: DataFrame with OHLCV and indicators
            index: Index of current candle to check

        Returns:
            True if should enter position, False otherwise

        Example:
            def entry_signal(self, dataframe, index):
                row = dataframe.iloc[index]
                return row['rsi'] < 30  # Buy when oversold
        """
        pass

    @abstractmethod
    def exit_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Determine if should exit current position.

        This method is called for each candle when in a position.

        Args:
            dataframe: DataFrame with OHLCV and indicators
            index: Index of current candle to check

        Returns:
            True if should exit position, False otherwise

        Example:
            def exit_signal(self, dataframe, index):
                row = dataframe.iloc[index]
                return row['rsi'] > 70  # Sell when overbought
        """
        pass

    def confirm_trade(self, dataframe: pd.DataFrame, index: int, side: str) -> bool:
        """
        Optional: Additional confirmation before placing trade.

        Can be used for volume confirmation, trend filters, etc.

        Args:
            dataframe: DataFrame with OHLCV and indicators
            index: Index of current candle
            side: 'buy' or 'sell'

        Returns:
            True if trade is confirmed, False to cancel
        """
        return True  # Default: confirm all trades

    def custom_stoploss(self, current_time: datetime, current_rate: float,
                       current_profit: float, **kwargs) -> Optional[float]:
        """
        Optional: Custom stop loss logic.

        Can implement trailing stops, time-based stops, etc.

        Args:
            current_time: Current time
            current_rate: Current price
            current_profit: Current profit/loss percentage
            **kwargs: Additional context (trade_duration, etc.)

        Returns:
            Stop loss percentage (e.g., -0.02 for -2%), or None for default
        """
        return None  # Use default stop loss

    def get_signal(self, dataframe: pd.DataFrame, index: int,
                  in_position: bool = False) -> SignalType:
        """
        Get trading signal for current candle.

        Args:
            dataframe: DataFrame with OHLCV and indicators
            index: Current candle index
            in_position: Whether currently in a position

        Returns:
            SignalType (BUY, SELL, or HOLD)
        """
        try:
            if not in_position:
                # Check for entry signal
                if self.entry_signal(dataframe, index):
                    if self.confirm_trade(dataframe, index, 'buy'):
                        return SignalType.BUY
            else:
                # Check for exit signal
                if self.exit_signal(dataframe, index):
                    if self.confirm_trade(dataframe, index, 'sell'):
                        return SignalType.SELL

            return SignalType.HOLD

        except Exception as e:
            logger.error(f"Error getting signal: {e}", exc_info=True)
            return SignalType.HOLD

    def analyze(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze dataframe and add buy/sell signals.

        Args:
            dataframe: DataFrame with OHLCV data

        Returns:
            DataFrame with indicators and signals
        """
        # Add indicators
        dataframe = self.populate_indicators(dataframe)

        # Add signal columns
        dataframe['buy_signal'] = False
        dataframe['sell_signal'] = False

        # Generate signals for each candle
        for i in range(len(dataframe)):
            if i < 1:  # Skip first candle (need previous data)
                continue

            # Check entry signal
            if self.entry_signal(dataframe, i):
                if self.confirm_trade(dataframe, i, 'buy'):
                    dataframe.loc[dataframe.index[i], 'buy_signal'] = True

            # Check exit signal (assuming in position)
            if self.exit_signal(dataframe, i):
                if self.confirm_trade(dataframe, i, 'sell'):
                    dataframe.loc[dataframe.index[i], 'sell_signal'] = True

        return dataframe

    def get_roi(self, current_profit: float, trade_duration: int) -> Optional[float]:
        """
        Get minimal ROI for current trade duration.

        Args:
            current_profit: Current profit percentage
            trade_duration: Minutes in trade

        Returns:
            Minimal ROI threshold, or None
        """
        if not self.minimal_roi:
            return None

        # Find applicable ROI tier
        for duration_minutes, roi_threshold in sorted(self.minimal_roi.items(), reverse=True):
            if trade_duration >= duration_minutes:
                return roi_threshold

        return None

    def should_exit_roi(self, current_profit: float, trade_duration: int) -> bool:
        """
        Check if should exit based on ROI.

        Args:
            current_profit: Current profit percentage
            trade_duration: Minutes in trade

        Returns:
            True if should exit based on ROI
        """
        roi = self.get_roi(current_profit, trade_duration)
        if roi is not None and current_profit >= roi:
            logger.info(f"ROI target reached: {current_profit:.2%} >= {roi:.2%}")
            return True
        return False

    def should_exit_stoploss(self, current_profit: float) -> bool:
        """
        Check if should exit based on stop loss.

        Args:
            current_profit: Current profit percentage

        Returns:
            True if stop loss hit
        """
        if current_profit <= self.stoploss:
            logger.info(f"Stop loss hit: {current_profit:.2%} <= {self.stoploss:.2%}")
            return True
        return False

    def __repr__(self) -> str:
        return (f"{self.name}(timeframe='{self.timeframe}', "
                f"stoploss={self.stoploss:.2%})")


class SimpleStrategy(BaseStrategy):
    """
    Example simple strategy implementation.

    This demonstrates how to create a basic strategy.
    """

    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Add simple indicators"""
        from shared.indicators.technical import sma, rsi

        dataframe['sma_20'] = sma(dataframe['close'], 20)
        dataframe['rsi'] = rsi(dataframe['close'], 14)

        return dataframe

    def entry_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """Buy when RSI < 30 and price > SMA"""
        row = dataframe.iloc[index]
        return (row['rsi'] < 30 and
                row['close'] > row['sma_20'])

    def exit_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """Sell when RSI > 70"""
        row = dataframe.iloc[index]
        return row['rsi'] > 70


if __name__ == "__main__":
    # Test strategy
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from cryptobot.data.mock_data import get_sample_data

    print("Testing Base Strategy...")

    # Create sample data
    df = get_sample_data(periods=100, timeframe='1h')

    # Test simple strategy
    strategy = SimpleStrategy()
    df_analyzed = strategy.analyze(df)

    print(f"\nStrategy: {strategy}")
    print(f"Buy signals: {df_analyzed['buy_signal'].sum()}")
    print(f"Sell signals: {df_analyzed['sell_signal'].sum()}")

    print("\nBuy signal candles:")
    print(df_analyzed[df_analyzed['buy_signal']][['close', 'rsi', 'sma_20']].head())

    print("\n✓ Base strategy working correctly!")
