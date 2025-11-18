"""
RSI Strategy for Stock Trading

Similar to the crypto RSI strategy but adapted for stock market characteristics:
- Lower volatility expectations
- Market hours awareness
- Different risk parameters
- Gap handling
"""

import pandas as pd
from cryptobot.strategies.base_strategy import BaseStrategy
from shared.indicators.technical import rsi, sma, ema, atr


class StockRsiStrategy(BaseStrategy):
    """
    RSI-based mean reversion strategy optimized for stock trading.

    Differences from crypto RSI strategy:
    - Tighter stop loss (1.5% vs 2%)
    - Lower take profit (3% vs 4%)
    - More conservative entry (RSI < 25 vs 30)
    - Considers market gaps
    """

    def __init__(self, config=None):
        """Initialize stock RSI strategy"""
        default_config = {
            'timeframe': '1Day',  # Daily bars for stocks
            'stoploss': -0.015,    # 1.5% stop loss (tighter for stocks)
            'rsi_period': 14,
            'rsi_oversold': 25,    # More extreme for stocks
            'rsi_overbought': 75,  # More extreme for stocks
            'take_profit': 0.03,   # 3% take profit
            'volume_confirmation': True,
            'volume_multiplier': 1.5,  # Require higher volume
            'gap_filter': True,    # Filter out large gap days
            'max_gap_pct': 0.03,   # Skip if gap > 3%
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        self.rsi_period = self.config['rsi_period']
        self.rsi_oversold = self.config['rsi_oversold']
        self.rsi_overbought = self.config['rsi_overbought']
        self.take_profit = self.config['take_profit']
        self.volume_confirmation = self.config['volume_confirmation']
        self.volume_multiplier = self.config['volume_multiplier']
        self.gap_filter = self.config['gap_filter']
        self.max_gap_pct = self.config['max_gap_pct']

    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Add indicators for stock RSI strategy"""
        # RSI
        dataframe['rsi'] = rsi(dataframe['close'], self.rsi_period)

        # Volume indicators
        dataframe['volume_sma'] = sma(dataframe['volume'], 20)

        # Moving averages for context
        dataframe['sma_20'] = sma(dataframe['close'], 20)
        dataframe['sma_50'] = sma(dataframe['close'], 50)
        dataframe['ema_20'] = ema(dataframe['close'], 20)

        # ATR for volatility
        dataframe['atr'] = atr(dataframe['high'], dataframe['low'], dataframe['close'], 14)

        # Gap detection (stock-specific)
        dataframe['gap'] = (dataframe['open'] - dataframe['close'].shift(1)) / dataframe['close'].shift(1)

        return dataframe

    def entry_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Generate buy signal for stocks

        Conditions:
        - RSI < oversold threshold (25)
        - Volume confirmation
        - No large gap down
        - Price near or above SMA 50 (trend filter)
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

        # Gap filter - avoid buying after large gap down
        if self.gap_filter and pd.notna(row['gap']):
            if row['gap'] < -self.max_gap_pct:  # Large gap down
                return False

        # Don't buy if too far below moving average (falling knife)
        if pd.notna(row['sma_50']):
            if row['close'] < row['sma_50'] * 0.95:  # More than 5% below 50 SMA
                return False

        return True

    def exit_signal(self, dataframe: pd.DataFrame, index: int) -> bool:
        """
        Generate sell signal

        Exit when:
        - RSI > overbought (75)
        - Take profit hit
        - Stop loss hit
        """
        row = dataframe.iloc[index]

        # RSI overbought
        if row['rsi'] > self.rsi_overbought:
            return True

        return False

    def confirm_trade(self, dataframe: pd.DataFrame, index: int, side: str) -> bool:
        """Additional confirmation for stock trades"""
        row = dataframe.iloc[index]

        # Make sure RSI and volume are valid
        if pd.isna(row['rsi']) or pd.isna(row['volume']):
            return False

        # For buy signals, ensure we're not at extreme lows (potential delisting risk)
        if side == 'buy':
            # Avoid penny stocks or extremely low prices
            if row['close'] < 5.0:  # Don't trade stocks below $5
                return False

            # Check volatility isn't too high
            if pd.notna(row['atr']):
                atr_pct = row['atr'] / row['close']
                if atr_pct > 0.05:  # Skip if daily ATR > 5%
                    return False

        return True

    def should_exit_roi(self, current_profit: float, trade_duration: int = 0) -> bool:
        """Check if take profit reached"""
        if current_profit >= self.take_profit:
            return True
        return False


if __name__ == "__main__":
    # Test stock RSI strategy
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from stockbot.data.mock_stock_data import MockStockDataGenerator

    print("Testing Stock RSI Strategy...")

    # Generate stock data
    generator = MockStockDataGenerator()
    df = generator.generate_stock_bars(periods=252, timeframe='1Day')  # 1 year daily

    # Test strategy
    strategy = StockRsiStrategy()
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
        buy_cols = ['close', 'rsi', 'volume', 'sma_50', 'gap']
        print(df_analyzed[df_analyzed['buy_signal']][buy_cols].head(3))

    print("\n✓ Stock RSI Strategy ready!")
