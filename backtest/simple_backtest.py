"""
Simple Backtesting Engine

Tests trading strategies on historical data to evaluate performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    size: float = 1.0  # Position size
    side: str = 'long'  # long or short
    profit_pct: float = 0.0
    profit_abs: float = 0.0
    exit_reason: str = ''  # signal, stoploss, roi, etc.

    def close(self, exit_time: datetime, exit_price: float, reason: str = 'signal'):
        """Close the trade"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = reason

        # Calculate profit
        self.profit_pct = (exit_price - self.entry_price) / self.entry_price
        self.profit_abs = (exit_price - self.entry_price) * self.size

    def is_open(self) -> bool:
        """Check if trade is still open"""
        return self.exit_time is None


class SimpleBacktest:
    """
    Simple backtesting engine for strategy evaluation.

    Features:
    - Long-only trading
    - Fixed position sizing
    - Stop loss and take profit
    - Trading fees
    - Performance metrics
    """

    def __init__(self,
                 strategy,
                 initial_capital: float = 10000.0,
                 fee_pct: float = 0.001,  # 0.1% per trade
                 position_size_pct: float = 1.0):  # Use 100% of capital
        """
        Initialize backtest

        Args:
            strategy: Strategy instance to test
            initial_capital: Starting capital in USD
            fee_pct: Trading fee percentage (0.001 = 0.1%)
            position_size_pct: Percentage of capital to use per trade
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.fee_pct = fee_pct
        self.position_size_pct = position_size_pct

        # State
        self.capital = initial_capital
        self.trades: List[Trade] = []
        self.current_trade: Optional[Trade] = None
        self.equity_curve = []

    def run(self, dataframe: pd.DataFrame) -> Dict:
        """
        Run backtest on historical data

        Args:
            dataframe: OHLCV dataframe

        Returns:
            Dictionary with results
        """
        logger.info(f"Starting backtest with {len(dataframe)} candles")
        logger.info(f"Initial capital: ${self.initial_capital:,.2f}")

        # Add indicators to dataframe
        df = self.strategy.populate_indicators(dataframe.copy())

        # Initialize tracking
        self.capital = self.initial_capital
        self.trades = []
        self.current_trade = None
        self.equity_curve = []

        # Iterate through candles
        for i in range(len(df)):
            if i < 1:  # Skip first candle (need previous data)
                continue

            timestamp = df.index[i]
            row = df.iloc[i]

            # Update equity
            if self.current_trade:
                unrealized_pnl = (row['close'] - self.current_trade.entry_price) * self.current_trade.size
                current_equity = self.capital + unrealized_pnl
            else:
                current_equity = self.capital

            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': current_equity,
                'cash': self.capital
            })

            # Check for exit if in position
            if self.current_trade:
                exit_reason = None
                exit_price = None

                # Check stop loss
                current_profit_pct = (row['close'] - self.current_trade.entry_price) / self.current_trade.entry_price
                if self.strategy.should_exit_stoploss(current_profit_pct):
                    exit_reason = 'stoploss'
                    exit_price = row['close']

                # Check take profit
                elif hasattr(self.strategy, 'should_exit_roi') and self.strategy.should_exit_roi(current_profit_pct):
                    exit_reason = 'take_profit'
                    exit_price = row['close']

                # Check strategy exit signal
                elif self.strategy.exit_signal(df, i):
                    if self.strategy.confirm_trade(df, i, 'sell'):
                        exit_reason = 'signal'
                        exit_price = row['close']

                # Execute exit
                if exit_reason:
                    self._exit_trade(timestamp, exit_price, exit_reason)

            # Check for entry if not in position
            else:
                if self.strategy.entry_signal(df, i):
                    if self.strategy.confirm_trade(df, i, 'buy'):
                        self._enter_trade(timestamp, row['close'])

        # Close any open trade at the end
        if self.current_trade:
            last_row = df.iloc[-1]
            self._exit_trade(df.index[-1], last_row['close'], 'end_of_data')

        # Calculate performance metrics
        results = self._calculate_metrics()

        logger.info(f"Backtest complete: {len(self.trades)} trades")
        logger.info(f"Final equity: ${results['final_equity']:,.2f}")
        logger.info(f"Total return: {results['total_return']:.2%}")

        return results

    def _enter_trade(self, timestamp: datetime, price: float):
        """Enter a new trade"""
        # Calculate position size
        capital_to_use = self.capital * self.position_size_pct
        fee = capital_to_use * self.fee_pct
        position_size = (capital_to_use - fee) / price

        # Create trade
        self.current_trade = Trade(
            entry_time=timestamp,
            entry_price=price,
            size=position_size
        )

        # Deduct from capital
        self.capital -= (capital_to_use)

        logger.debug(f"ENTER: {timestamp} @ ${price:,.2f}, size={position_size:.6f}, fee=${fee:.2f}")

    def _exit_trade(self, timestamp: datetime, price: float, reason: str):
        """Exit current trade"""
        if not self.current_trade:
            return

        # Close trade
        self.current_trade.close(timestamp, price, reason)

        # Calculate proceeds
        proceeds = self.current_trade.size * price
        fee = proceeds * self.fee_pct
        net_proceeds = proceeds - fee

        # Add to capital
        self.capital += net_proceeds

        logger.debug(f"EXIT: {timestamp} @ ${price:,.2f}, "
                    f"profit={self.current_trade.profit_pct:.2%}, reason={reason}")

        # Store trade
        self.trades.append(self.current_trade)
        self.current_trade = None

    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'final_equity': self.capital,
                'total_return': 0.0,
                'win_rate': 0.0,
                'avg_profit': 0.0,
                'max_drawdown': 0.0
            }

        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.profit_pct > 0]
        losing_trades = [t for t in self.trades if t.profit_pct <= 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        # Profit metrics
        total_profit_pct = sum(t.profit_pct for t in self.trades)
        avg_profit_pct = total_profit_pct / total_trades if total_trades > 0 else 0

        avg_win = np.mean([t.profit_pct for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_pct for t in losing_trades]) if losing_trades else 0

        # Max drawdown
        equity_df = pd.DataFrame(self.equity_curve)
        if len(equity_df) > 0:
            equity_df['cummax'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
            max_drawdown = equity_df['drawdown'].min()
        else:
            max_drawdown = 0.0

        # Returns
        final_equity = self.capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_profit': avg_profit_pct,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_return': total_return,
            'final_equity': final_equity,
            'initial_capital': self.initial_capital,
            'max_drawdown': max_drawdown,
            'profit_factor': abs(sum(t.profit_abs for t in winning_trades) / sum(t.profit_abs for t in losing_trades)) if losing_trades else 0,
        }

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame"""
        if not self.trades:
            return pd.DataFrame()

        trades_data = [asdict(t) for t in self.trades]
        return pd.DataFrame(trades_data)

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return pd.DataFrame(self.equity_curve).set_index('timestamp')

    def print_results(self, results: Dict):
        """Print backtest results in a nice format"""
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)

        print(f"\nCapital:")
        print(f"  Initial: ${results['initial_capital']:,.2f}")
        print(f"  Final:   ${results['final_equity']:,.2f}")
        print(f"  Return:  {results['total_return']:.2%}")

        print(f"\nTrades:")
        print(f"  Total:   {results['total_trades']}")
        print(f"  Winners: {results['winning_trades']} ({results['win_rate']:.1%})")
        print(f"  Losers:  {results['losing_trades']}")

        print(f"\nPerformance:")
        print(f"  Avg Profit:   {results['avg_profit']:.2%}")
        print(f"  Avg Win:      {results['avg_win']:.2%}")
        print(f"  Avg Loss:     {results['avg_loss']:.2%}")
        print(f"  Profit Factor: {results['profit_factor']:.2f}")
        print(f"  Max Drawdown: {results['max_drawdown']:.2%}")

        print("="*60)


if __name__ == "__main__":
    # Test backtest engine
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from cryptobot.data.mock_data import MockDataGenerator
    from cryptobot.strategies.rsi_strategy import RsiStrategy

    print("Testing Backtest Engine...")

    # Generate data
    generator = MockDataGenerator()
    df = generator.generate_ohlcv(periods=1000, volatility=0.03)

    # Create strategy
    strategy = RsiStrategy()

    # Run backtest
    backtest = SimpleBacktest(strategy, initial_capital=10000.0)
    results = backtest.run(df)

    # Print results
    backtest.print_results(results)

    print("\n✓ Backtest engine working!")
