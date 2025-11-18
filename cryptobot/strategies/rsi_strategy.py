"""
RSI Mean Reversion Strategy

A simple but effective strategy that buys when RSI indicates oversold
conditions and sells when overbought.

Strategy Logic:
- Entry: RSI < 30 (oversold) + volume confirmation
- Exit: RSI > 70 (overbought) OR take profit OR stop loss
- Stop Loss: 2%
- Take Profit: 4%
"""

import pandas as pd
from .base_strategy import BaseStrategy
from shared.indicators.technical import rsi, sma, ema


class RsiStrategy(BaseStrategy):
    """
    RSI-based mean reversion strategy for crypto trading.

    This strategy assumes that extreme RSI values indicate temporary
    price dislocations that will revert to the mean.
    """

    def __init__(self, config=None):
        """
        Initialize RSI strategy

        Args:
            config: Strategy configuration
        """
        # Default configuration
        default_config = {
            'timeframe': '1h',
            'stoploss': -0.02,  # 2% stop loss
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'take_profit': 0.04,  # 4% take profit target
            'volume_confirmation': True,
            'volume_multiplier': 1.2,  # Volume must be 1.2x average
            'trend_filter': False,  # Optional: only trade with trend
            'trend_sma_period': 200,
        }

        # Merge with user config
        if config:
            default_config.update(config)

        super().__init__(default_config)

        # Extract strategy parameters
        self.rsi_period = self.config['rsi_period']
        self.rsi_oversold = self.config['rsi_oversold']
        self.rsi_overbought = self.config['rsi_overbought']
        self.take_profit = self.config['take_profit']
        self.volume_confirmation = self.config['volume_confirmation']
        self.volume_multiplier = self.config['volume_multiplier']
        self.trend_filter = self.config['trend_filter']
        self.trend_sma_period = self.config['trend_sma_period']

    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Add RSI and supporting indicators

        Args:
            dataframe: OHLCV dataframe

        Returns:
            Dataframe with indicators
        """
        # RSI - primary indicator
        dataframe['rsi'] = rsi(dataframe['close'], self.rsi_period)

        # Volume indicators (for confirmation)
        dataframe['volume_sma'] = sma(dataframe['volume'], 20)

        # Trend filter (optional)
        if self.trend_filter:
            dataframe[f'sma_{self.trend_sma_period}'] = sma(
                dataframe['close'],
                self.trend_sma_period
            )

        # Short-term moving average for additional context
        dataframe['ema_20'] = ema(dataframe['close'], 20)

        return dataframe

    def entry_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Generate buy signal when RSI indicates oversold

        Conditions:
        - RSI < oversold threshold
        - Volume confirmation (optional)
        - Price above trend SMA (optional)

        Args:
            dataframe: Dataframe with indicators
            index: Current candle index

        Returns:
            True if should buy
        """
        row = dataframe.iloc[index]

        # RSI oversold check
        if row['rsi'] >= self.rsi_oversold:
            return False

        # Volume confirmation
        if self.volume_confirmation:
            if pd.notna(row['volume_sma']):
                if row['volume'] < row['volume_sma'] * self.volume_multiplier:
                    return False

        # Trend filter (only buy if price above long-term trend)
        if self.trend_filter:
            sma_col = f'sma_{self.trend_sma_period}'
            if sma_col in row and pd.notna(row[sma_col]):
                if row['close'] < row[sma_col]:
                    return False

        return True

    def exit_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Generate sell signal when RSI indicates overbought

        Conditions:
        - RSI > overbought threshold

        Args:
            dataframe: Dataframe with indicators
            index: Current candle index

        Returns:
            True if should sell
        """
        row = dataframe.iloc[index]

        # RSI overbought check
        if row['rsi'] > self.rsi_overbought:
            return True

        return False

    def confirm_trade(self, dataframe: pd.DataFrame, index: int, side: str) -> bool:
        """
        Additional trade confirmation

        Args:
            dataframe: Dataframe with indicators
            index: Current candle index
            side: 'buy' or 'sell'

        Returns:
            True to confirm trade
        """
        row = dataframe.iloc[index]

        # Make sure RSI is not NaN
        if pd.isna(row['rsi']):
            return False

        # For buy signals, make sure we're not buying at a local high
        if side == 'buy':
            # Check if price is not too far above EMA
            if pd.notna(row['ema_20']):
                if row['close'] > row['ema_20'] * 1.05:  # More than 5% above EMA
                    return False

        return True

    def should_exit_roi(self, current_profit: float, trade_duration: int = 0) -> bool:
        """
        Check if take profit target is reached

        Args:
            current_profit: Current profit percentage
            trade_duration: Not used in this strategy

        Returns:
            True if should exit
        """
        if current_profit >= self.take_profit:
            return True
        return False


if __name__ == "__main__":
    # Test RSI strategy
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from cryptobot.data.mock_data import MockDataGenerator

    print("Testing RSI Strategy...")

    # Generate data with some volatility for more signals
    generator = MockDataGenerator()
    df = generator.generate_ohlcv(periods=500, volatility=0.03)

    # Test strategy
    strategy = RsiStrategy()
    df_analyzed = strategy.analyze(df)

    print(f"\nStrategy: {strategy}")
    print(f"Configuration:")
    print(f"  RSI Period: {strategy.rsi_period}")
    print(f"  RSI Oversold: {strategy.rsi_oversold}")
    print(f"  RSI Overbought: {strategy.rsi_overbought}")
    print(f"  Stop Loss: {strategy.stoploss:.1%}")
    print(f"  Take Profit: {strategy.take_profit:.1%}")

    print(f"\nSignals Generated:")
    print(f"  Buy signals: {df_analyzed['buy_signal'].sum()}")
    print(f"  Sell signals: {df_analyzed['sell_signal'].sum()}")

    if df_analyzed['buy_signal'].sum() > 0:
        print("\nFirst 3 buy signals:")
        print(df_analyzed[df_analyzed['buy_signal']][['close', 'rsi', 'volume']].head(3))

    print("\n✓ RSI Strategy ready for backtesting!")
