"""
Stock Trading Bot

Executes stock trading strategies using the strategy framework.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd

from stockbot.data.mock_stock_data import MockStockDataGenerator
from stockbot.strategies.stock_rsi_strategy import StockRsiStrategy
from stockbot.strategies.ma_crossover_strategy import MaCrossoverStrategy
from shared.risk_management.portfolio_manager import PortfolioManager
from shared.risk_management.risk_monitor import RiskMonitor
from monitoring.notifications import NotificationManager
from monitoring.logger import get_logger

logger = get_logger(__name__)


class StockBot:
    """
    Stock trading bot

    Executes trading strategies on stock assets
    """

    def __init__(self,
                 portfolio_manager: PortfolioManager,
                 risk_monitor: RiskMonitor,
                 notification_manager: NotificationManager,
                 config: Dict):
        """
        Initialize stock bot

        Args:
            portfolio_manager: Portfolio manager instance
            risk_monitor: Risk monitor instance
            notification_manager: Notification manager instance
            config: Configuration dictionary
        """
        self.portfolio = portfolio_manager
        self.risk_monitor = risk_monitor
        self.notifier = notification_manager
        self.config = config

        # Initialize data generator (using mock data for now)
        self.data_generator = MockStockDataGenerator()

        # Initialize strategy
        strategy_name = config.get('strategy', 'rsi')
        if strategy_name == 'rsi':
            strategy_config = {
                'rsi_period': config.get('rsi_period', 14),
                'rsi_oversold': config.get('rsi_oversold', 25),
                'rsi_overbought': config.get('rsi_overbought', 75),
                'stoploss': -config.get('stop_loss_pct', 0.015),  # Note: negative for stoploss
                'take_profit': config.get('take_profit_pct', 0.03)
            }
            self.strategy = StockRsiStrategy(strategy_config)
        elif strategy_name == 'ma_crossover':
            self.strategy = MaCrossoverStrategy()
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        # Trading symbols
        self.symbols = config.get('symbols', ['AAPL', 'GOOGL', 'MSFT'])

        # Execution state
        self.last_check = {}  # Track last check time per symbol

        logger.info(f"Stock Bot initialized: strategy={strategy_name}, symbols={self.symbols}")

    def execute_cycle(self):
        """Execute one trading cycle"""
        try:
            logger.debug("Stock bot: Starting execution cycle")

            # Check market hours
            if not self._is_market_open():
                logger.debug("Stock bot: Market is closed")
                return

            # Check each symbol
            for symbol in self.symbols:
                try:
                    self._check_symbol(symbol)
                except Exception as e:
                    logger.error(f"Error checking {symbol}: {e}")

            logger.debug("Stock bot: Execution cycle complete")

        except Exception as e:
            logger.error(f"Stock bot execution error: {e}")

    def _is_market_open(self) -> bool:
        """Check if stock market is open"""
        now = datetime.now()

        # Weekend check
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # Market hours check (9:30 AM - 4:00 PM ET)
        # Simplified - not accounting for timezone
        hour = now.hour
        if hour < 9 or hour >= 16:
            return False
        if hour == 9 and now.minute < 30:
            return False

        return True

    def _check_symbol(self, symbol: str):
        """Check a single symbol for trading opportunities"""

        # Get market data
        df = self._get_market_data(symbol)

        if df is None or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return

        # Populate indicators
        df = self.strategy.populate_indicators(df)

        # Get current price
        current_price = df['close'].iloc[-1]
        current_index = len(df) - 1

        # Check if we have open position
        existing_positions = self.portfolio.get_positions_by_symbol(symbol)

        if existing_positions:
            # We have an open position - check exit
            for position in existing_positions:
                self._check_exit(position, df, current_index, current_price)
        else:
            # No position - check entry
            self._check_entry(symbol, df, current_index, current_price)

    def _check_entry(self, symbol: str, df: pd.DataFrame,
                    index: int, current_price: float):
        """Check for entry signal"""

        # Check entry signal
        if not self.strategy.entry_signal(df, index):
            return

        logger.info(f"Entry signal for {symbol} at ${current_price:,.2f}")

        # Calculate position size using risk management
        stop_loss_price = current_price * (1 - self.config.get('stop_loss_pct', 0.015))

        position_size = self.risk_monitor.calculate_position_size(
            entry_price=current_price,
            stop_loss_price=stop_loss_price,
            symbol=symbol,
            asset_type='stock',
            method='risk_pct'
        )

        # Check if position is allowed
        can_open, reason, violations = self.risk_monitor.can_open_position(
            symbol=symbol,
            position_value=position_size['value'],
            asset_type='stock'
        )

        if not can_open:
            logger.warning(f"Position blocked for {symbol}: {reason}")
            return

        # Calculate stop loss and take profit
        stop_loss = current_price * (1 - self.config.get('stop_loss_pct', 0.015))
        take_profit = current_price * (1 + self.config.get('take_profit_pct', 0.03))

        try:
            # Open position
            position = self.portfolio.open_position(
                symbol=symbol,
                asset_type='stock',
                entry_price=current_price,
                quantity=position_size['quantity'],
                side='long',
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy_name=self.strategy.__class__.__name__
            )

            logger.info(f"✅ Opened {symbol}: {position.quantity:.2f} shares @ ${current_price:,.2f}")

            # Send notification
            self.notifier.trade_executed(
                symbol=symbol,
                side='buy',
                quantity=position.quantity,
                price=current_price,
                strategy=self.strategy.__class__.__name__
            )

        except Exception as e:
            logger.error(f"Failed to open position for {symbol}: {e}")

    def _check_exit(self, position, df: pd.DataFrame,
                   index: int, current_price: float):
        """Check for exit signal"""

        # Update position price
        position.update_price(current_price)

        exit_reason = None

        # Check exit signal from strategy
        if self.strategy.exit_signal(df, index):
            exit_reason = 'strategy_signal'

        # Check stop loss
        elif position.stop_loss and current_price <= position.stop_loss:
            exit_reason = 'stop_loss'

        # Check take profit
        elif position.take_profit and current_price >= position.take_profit:
            exit_reason = 'take_profit'

        if exit_reason:
            try:
                # Close position
                self.portfolio.close_position(
                    position.position_id,
                    current_price,
                    reason=exit_reason
                )

                logger.info(f"✅ Closed {position.symbol}: "
                          f"P&L ${position.realized_pnl:.2f} ({position.realized_pnl_pct:.2%}), "
                          f"reason={exit_reason}")

                # Send notification
                self.notifier.position_closed(
                    symbol=position.symbol,
                    pnl=position.realized_pnl,
                    pnl_pct=position.realized_pnl_pct,
                    reason=exit_reason
                )

            except Exception as e:
                logger.error(f"Failed to close position {position.symbol}: {e}")

    def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get market data for symbol"""
        try:
            # Using mock data for now
            # In production, this would fetch from broker
            df = self.data_generator.generate_stock_bars(
                symbol=symbol,
                periods=500,
                timeframe='1Day'
            )

            return df

        except Exception as e:
            logger.error(f"Failed to get data for {symbol}: {e}")
            return None


if __name__ == "__main__":
    # Test stock bot
    from shared.risk_management.risk_monitor import RiskMonitor

    print("="*60)
    print("Testing Stock Bot")
    print("="*60)

    # Create components
    portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
    monitor = RiskMonitor(portfolio, {})
    notifier = NotificationManager({'console_enabled': True})

    # Create bot
    config = {
        'strategy': 'rsi',
        'symbols': ['AAPL', 'GOOGL', 'MSFT'],
        'rsi_period': 14,
        'rsi_oversold': 25,
        'rsi_overbought': 75,
        'stop_loss_pct': 0.015,
        'take_profit_pct': 0.03
    }

    bot = StockBot(portfolio, monitor, notifier, config)

    # Run a few cycles
    print("\nRunning 3 execution cycles...")
    for i in range(3):
        print(f"\nCycle {i+1}:")
        bot.execute_cycle()
        portfolio.print_summary()
        time.sleep(2)

    print("\n✓ Stock bot test complete!")
    print("="*60)
