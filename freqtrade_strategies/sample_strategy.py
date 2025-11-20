"""
Sample FreqTrade Strategy for TradeAgent

This is an example RSI-based strategy following FreqTrade's IStrategy interface.
It demonstrates how to create FreqTrade-compatible strategies for use with
TradeAgent's FreqTradeBotAdapter.

Strategy Logic:
- Entry: RSI < 30 (oversold)
- Exit: RSI > 70 (overbought)
- Stop Loss: 2%
- Take Profit: 4%

This strategy is provided as a starting point and should be thoroughly
backtested before use with real capital.
"""

import pandas as pd
from pandas import DataFrame
from typing import Optional

# Check if FreqTrade is available
try:
    from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
    import freqtrade.vendor.qtpylib.indicators as qtpylib
    from freqtrade.persistence import Trade
    FREQTRADE_AVAILABLE = True
except ImportError:
    # Fallback if FreqTrade not installed
    FREQTRADE_AVAILABLE = False
    print("FreqTrade not installed. Install with: pip install freqtrade ccxt")

    # Create dummy base class for development without FreqTrade
    class IStrategy:
        """Dummy IStrategy for development"""
        minimal_roi = {}
        stoploss = -0.10
        timeframe = '5m'

    class DecimalParameter:
        """Dummy DecimalParameter"""
        def __init__(self, default, low, high, decimals=3, space='buy', optimize=True, load=True):
            self.value = default

    class IntParameter:
        """Dummy IntParameter"""
        def __init__(self, default, low, high, space='buy', optimize=True, load=True):
            self.value = default


class SampleStrategy(IStrategy):
    """
    Sample RSI Strategy for FreqTrade/TradeAgent

    This strategy uses RSI to identify oversold and overbought conditions.

    Entry Signal:
    - RSI crosses below 30 (oversold)
    - Volume confirmation (optional)

    Exit Signal:
    - RSI crosses above 70 (overbought)
    - Or take profit target reached
    - Or stop loss hit

    Compatible with:
    - FreqTrade CLI (direct usage)
    - TradeAgent FreqTradeBotAdapter (via integration)
    """

    # Strategy interface version - required by FreqTrade
    INTERFACE_VERSION = 3

    # Minimal ROI designed for the strategy
    # This can be overridden in the config
    minimal_roi = {
        "0": 0.04,   # 4% profit target
        "30": 0.02,  # After 30 minutes, 2% profit acceptable
        "60": 0.01,  # After 1 hour, 1% profit acceptable
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.02  # 2% stop loss

    # Trailing stop loss
    trailing_stop = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True

    # Optimal timeframe for the strategy
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = True

    # These values can be overridden in the config
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Strategy parameters - can be optimized via hyperopt
    buy_rsi = IntParameter(20, 40, default=30, space="buy", optimize=True)
    sell_rsi = IntParameter(60, 80, default=70, space="sell", optimize=True)

    # Optional: Volume multiplier for confirmation
    volume_check = True
    volume_multiplier = 1.2

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add technical indicators to the dataframe

        This method is called by FreqTrade to calculate all indicators
        needed for the strategy.

        Args:
            dataframe: OHLCV DataFrame
            metadata: Additional information (pair, timeframe, etc.)

        Returns:
            DataFrame with indicators added
        """
        # RSI - primary indicator
        dataframe['rsi'] = self._calculate_rsi(dataframe['close'], 14)

        # Volume indicators
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=20).mean()

        # Additional indicators for context
        # Moving averages
        dataframe['ema_20'] = self._calculate_ema(dataframe['close'], 20)
        dataframe['ema_50'] = self._calculate_ema(dataframe['close'], 50)

        # Bollinger Bands (optional - for additional confirmation)
        # Not used in this basic strategy but useful for enhancement
        bollinger = self._calculate_bollinger_bands(dataframe['close'], 20, 2)
        dataframe['bb_lower'] = bollinger['lower']
        dataframe['bb_middle'] = bollinger['middle']
        dataframe['bb_upper'] = bollinger['upper']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on indicators, populate the 'enter_long' column

        FreqTrade will enter trades when enter_long is True.

        Args:
            dataframe: DataFrame with indicators
            metadata: Additional information

        Returns:
            DataFrame with enter_long column
        """
        conditions = []

        # RSI oversold condition
        conditions.append(dataframe['rsi'] < self.buy_rsi.value)

        # Volume confirmation (optional)
        if self.volume_check:
            conditions.append(
                dataframe['volume'] > dataframe['volume_mean'] * self.volume_multiplier
            )

        # Additional filter: price above short-term EMA
        # This helps avoid buying in strong downtrends
        conditions.append(dataframe['close'] > dataframe['ema_20'])

        # Combine all conditions
        if conditions:
            dataframe.loc[
                pd.concat(conditions, axis=1).all(axis=1),
                'enter_long'
            ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on indicators, populate the 'exit_long' column

        FreqTrade will exit trades when exit_long is True.

        Args:
            dataframe: DataFrame with indicators
            metadata: Additional information

        Returns:
            DataFrame with exit_long column
        """
        conditions = []

        # RSI overbought condition
        conditions.append(dataframe['rsi'] > self.sell_rsi.value)

        # Combine all conditions
        if conditions:
            dataframe.loc[
                pd.concat(conditions, axis=1).all(axis=1),
                'exit_long'
            ] = 1

        return dataframe

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime',
                   current_rate: float, current_profit: float, **kwargs) -> Optional[str]:
        """
        Custom exit signal logic (optional)

        This method is called on every candle and can be used for
        additional exit conditions beyond the standard exit signals.

        Args:
            pair: Trading pair
            trade: Trade object
            current_time: Current datetime
            current_rate: Current price
            current_profit: Current profit (0.02 = 2%)

        Returns:
            Exit reason string if should exit, None otherwise
        """
        # Example: Exit if profit target reached
        if current_profit >= 0.04:  # 4% profit
            return 'take_profit_4pct'

        # Example: Exit on rapid profit to lock in gains
        if current_profit >= 0.02 and trade.calc_profit_ratio(current_rate) > 0.015:
            return 'take_profit_rapid'

        return None

    # Helper methods for indicator calculation
    # (In real usage, FreqTrade provides these via ta-lib or pandas-ta)

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate EMA indicator"""
        return series.ewm(span=period, adjust=False).mean()

    def _calculate_bollinger_bands(self, series: pd.Series, period: int = 20, std: int = 2) -> dict:
        """Calculate Bollinger Bands"""
        middle = series.rolling(window=period).mean()
        std_dev = series.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }


# For testing without FreqTrade
if __name__ == "__main__":
    print("="*60)
    print("Sample FreqTrade Strategy")
    print("="*60)

    if not FREQTRADE_AVAILABLE:
        print("\n❌ FreqTrade not installed!")
        print("Install with: pip install freqtrade ccxt")
        print("\nThis strategy requires FreqTrade to run.")
        print("="*60)
        exit(1)

    # Test strategy initialization
    strategy = SampleStrategy()

    print(f"\nStrategy: {strategy.__class__.__name__}")
    print(f"Timeframe: {strategy.timeframe}")
    print(f"Stop Loss: {strategy.stoploss:.1%}")
    print(f"Minimal ROI: {strategy.minimal_roi}")
    print(f"\nParameters:")
    print(f"  Buy RSI: {strategy.buy_rsi.value}")
    print(f"  Sell RSI: {strategy.sell_rsi.value}")
    print(f"  Volume Check: {strategy.volume_check}")

    # Test with sample data
    import numpy as np
    sample_data = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
    })

    print("\nTesting populate_indicators...")
    df = strategy.populate_indicators(sample_data, {'pair': 'BTC/USDT'})
    print(f"  Indicators added: {[col for col in df.columns if col not in sample_data.columns]}")

    print("\nTesting populate_entry_trend...")
    df = strategy.populate_entry_trend(df, {'pair': 'BTC/USDT'})
    entry_signals = df.get('enter_long', pd.Series([0])).sum()
    print(f"  Entry signals found: {entry_signals}")

    print("\nTesting populate_exit_trend...")
    df = strategy.populate_exit_trend(df, {'pair': 'BTC/USDT'})
    exit_signals = df.get('exit_long', pd.Series([0])).sum()
    print(f"  Exit signals found: {exit_signals}")

    print("\n✓ Strategy test complete!")
    print("="*60)
