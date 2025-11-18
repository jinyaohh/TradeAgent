"""
Advanced Backtesting Engine

Provides sophisticated backtesting capabilities including:
- Walk-forward analysis
- Out-of-sample testing
- Multiple strategy comparison
- Realistic execution simulation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from shared.risk_management.portfolio_manager import PortfolioManager
from shared.risk_management.risk_monitor import RiskMonitor
from monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtest"""
    initial_capital: float = 10000.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    commission: float = 0.001  # 0.1% per trade
    slippage: float = 0.0005   # 0.05% slippage

    # Walk-forward settings
    in_sample_period: int = 252  # 1 year for stocks, adjust for crypto
    out_sample_period: int = 63  # 3 months
    walk_forward: bool = False

    # Risk settings
    max_risk_per_trade: float = 0.02
    max_open_positions: int = 10
    max_position_size_pct: float = 0.10

    # Execution settings
    fill_on: str = 'close'  # close, open, or limit
    allow_fractional: bool = True


@dataclass
class Trade:
    """Represents a completed trade"""
    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    quantity: float
    side: str  # long or short
    pnl: float
    pnl_pct: float
    commission: float
    slippage: float
    strategy: str
    entry_reason: str = ""
    exit_reason: str = ""
    duration_bars: int = 0
    mae: float = 0.0  # Maximum Adverse Excursion
    mfe: float = 0.0  # Maximum Favorable Excursion


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    config: BacktestConfig
    strategy_name: str
    start_date: datetime
    end_date: datetime

    # Equity curve
    equity_curve: pd.Series = field(default_factory=pd.Series)

    # Trades
    trades: List[Trade] = field(default_factory=list)

    # Performance metrics (calculated later)
    metrics: Dict = field(default_factory=dict)

    # Additional data
    daily_returns: pd.Series = field(default_factory=pd.Series)
    drawdown_curve: pd.Series = field(default_factory=pd.Series)
    positions_over_time: pd.Series = field(default_factory=pd.Series)


class BacktestEngine:
    """
    Advanced backtesting engine

    Features:
    - Realistic execution (commission, slippage)
    - Walk-forward analysis
    - Multiple symbol support
    - Risk management integration
    - Detailed trade tracking
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize backtest engine

        Args:
            config: Backtesting configuration
        """
        self.config = config
        self.results = []

        logger.info(f"Backtest Engine initialized: capital=${config.initial_capital:,.2f}, "
                   f"commission={config.commission:.3%}, slippage={config.slippage:.3%}")

    def run_backtest(self,
                     data: pd.DataFrame,
                     strategy,
                     symbols: Optional[List[str]] = None) -> BacktestResult:
        """
        Run backtest on historical data

        Args:
            data: Historical OHLCV data (can be single or multi-symbol)
            strategy: Strategy instance with analyze() method
            symbols: List of symbols (for multi-symbol backtest)

        Returns:
            BacktestResult with trades and metrics
        """
        logger.info("="*60)
        logger.info("STARTING BACKTEST")
        logger.info("="*60)
        logger.info(f"Strategy: {strategy.__class__.__name__}")
        logger.info(f"Initial Capital: ${self.config.initial_capital:,.2f}")
        logger.info(f"Data Period: {data.index[0]} to {data.index[-1]}")
        logger.info(f"Total Bars: {len(data)}")

        # Initialize portfolio for backtest
        portfolio = PortfolioManager(
            initial_capital=self.config.initial_capital,
            mode='backtest'
        )

        # Initialize risk monitor
        risk_config = {
            'max_risk_per_trade': self.config.max_risk_per_trade,
            'max_open_positions': self.config.max_open_positions,
            'max_position_size_pct': self.config.max_position_size_pct
        }
        risk_monitor = RiskMonitor(portfolio, risk_config)

        # Prepare data
        if symbols is None:
            # Single symbol backtest
            symbols = ['SINGLE']
            data_dict = {'SINGLE': data}
        else:
            # Multi-symbol backtest (data should have MultiIndex)
            data_dict = {symbol: data.xs(symbol, level='symbol')
                        for symbol in symbols}

        # Run analysis on each symbol's data
        analyzed_data = {}
        for symbol, df in data_dict.items():
            analyzed_data[symbol] = strategy.analyze(df.copy())

        # Initialize tracking
        equity_curve = [self.config.initial_capital]
        equity_dates = [data.index[0]]
        trades = []

        # Simulate bar-by-bar execution
        for i in range(len(data)):
            current_date = data.index[i]

            # Update all open positions with current prices
            for symbol in symbols:
                if i >= len(analyzed_data[symbol]):
                    continue

                current_price = analyzed_data[symbol].iloc[i]['close']

                # Update positions
                open_positions = portfolio.get_positions_by_symbol(symbol)
                for position in open_positions:
                    position.update_price(current_price)

            # Check exits first
            for symbol in symbols:
                if i >= len(analyzed_data[symbol]):
                    continue

                df = analyzed_data[symbol]
                current_bar = df.iloc[i]
                current_price = current_bar['close']

                open_positions = portfolio.get_positions_by_symbol(symbol)
                for position in open_positions:
                    should_exit = False
                    exit_reason = ""

                    # Check strategy exit signal
                    if 'sell_signal' in df.columns and current_bar['sell_signal']:
                        should_exit = True
                        exit_reason = "strategy_signal"

                    # Check stop loss
                    elif position.stop_loss and current_price <= position.stop_loss:
                        should_exit = True
                        exit_reason = "stop_loss"
                        # Apply slippage (worse price)
                        current_price = current_price * (1 - self.config.slippage)

                    # Check take profit
                    elif position.take_profit and current_price >= position.take_profit:
                        should_exit = True
                        exit_reason = "take_profit"
                        # Apply slippage (worse price)
                        current_price = current_price * (1 - self.config.slippage)

                    if should_exit:
                        # Calculate commission
                        exit_value = position.quantity * current_price
                        commission = exit_value * self.config.commission

                        # Close position
                        portfolio.close_position(
                            position.position_id,
                            current_price,
                            reason=exit_reason
                        )

                        # Record trade
                        trade = Trade(
                            symbol=symbol,
                            entry_date=position.entry_time,
                            exit_date=current_date,
                            entry_price=position.entry_price,
                            exit_price=current_price,
                            quantity=position.quantity,
                            side=position.side,
                            pnl=position.realized_pnl - commission,
                            pnl_pct=position.realized_pnl_pct,
                            commission=commission,
                            slippage=abs(current_price - current_bar['close']),
                            strategy=strategy.__class__.__name__,
                            exit_reason=exit_reason,
                            duration_bars=i - position.entry_time.toordinal() if hasattr(position.entry_time, 'toordinal') else 0
                        )
                        trades.append(trade)

                        logger.debug(f"Exit {symbol}: {exit_reason}, P&L: ${trade.pnl:.2f}")

            # Check entries
            for symbol in symbols:
                if i >= len(analyzed_data[symbol]):
                    continue

                df = analyzed_data[symbol]
                current_bar = df.iloc[i]
                current_price = current_bar['close']

                # Check if we have buy signal
                if 'buy_signal' in df.columns and current_bar['buy_signal']:
                    # Check if we already have position
                    existing = portfolio.get_positions_by_symbol(symbol)
                    if existing:
                        continue

                    # Calculate position size
                    # Use ATR or fixed stop loss for position sizing
                    stop_loss_pct = getattr(strategy, 'stoploss', -0.02)
                    stop_loss_price = current_price * (1 + stop_loss_pct)

                    position_info = risk_monitor.calculate_position_size(
                        entry_price=current_price,
                        stop_loss_price=stop_loss_price,
                        symbol=symbol,
                        asset_type='stock',
                        method='risk_pct'
                    )

                    # Check if position allowed
                    can_open, reason, violations = risk_monitor.can_open_position(
                        symbol=symbol,
                        position_value=position_info['value'],
                        asset_type='stock'
                    )

                    if not can_open:
                        logger.debug(f"Position blocked for {symbol}: {reason}")
                        continue

                    # Apply slippage (worse entry price)
                    entry_price = current_price * (1 + self.config.slippage)

                    # Calculate commission
                    entry_value = position_info['quantity'] * entry_price
                    commission = entry_value * self.config.commission

                    # Check if we have enough cash
                    if portfolio.cash < entry_value + commission:
                        logger.debug(f"Insufficient cash for {symbol}")
                        continue

                    # Calculate stops
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit_pct = getattr(strategy, 'take_profit', 0.04)
                    take_profit = entry_price * (1 + take_profit_pct)

                    # Open position
                    try:
                        position = portfolio.open_position(
                            symbol=symbol,
                            asset_type='stock',
                            entry_price=entry_price,
                            quantity=position_info['quantity'],
                            side='long',
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            strategy_name=strategy.__class__.__name__
                        )

                        logger.debug(f"Entry {symbol}: qty={position.quantity:.2f}, "
                                   f"price=${entry_price:.2f}")

                    except Exception as e:
                        logger.error(f"Failed to open position: {e}")

            # Record equity
            equity = portfolio.get_total_value()
            equity_curve.append(equity)
            equity_dates.append(current_date)

        # Close any remaining positions at end
        for symbol in symbols:
            open_positions = portfolio.get_positions_by_symbol(symbol)
            if open_positions and len(analyzed_data[symbol]) > 0:
                final_price = analyzed_data[symbol].iloc[-1]['close']
                for position in open_positions:
                    portfolio.close_position(
                        position.position_id,
                        final_price,
                        reason="backtest_end"
                    )

                    exit_value = position.quantity * final_price
                    commission = exit_value * self.config.commission

                    trade = Trade(
                        symbol=symbol,
                        entry_date=position.entry_time,
                        exit_date=data.index[-1],
                        entry_price=position.entry_price,
                        exit_price=final_price,
                        quantity=position.quantity,
                        side=position.side,
                        pnl=position.realized_pnl - commission,
                        pnl_pct=position.realized_pnl_pct,
                        commission=commission,
                        slippage=0.0,
                        strategy=strategy.__class__.__name__,
                        exit_reason="backtest_end"
                    )
                    trades.append(trade)

        # Create result
        result = BacktestResult(
            config=self.config,
            strategy_name=strategy.__class__.__name__,
            start_date=data.index[0],
            end_date=data.index[-1],
            equity_curve=pd.Series(equity_curve, index=equity_dates),
            trades=trades
        )

        # Calculate daily returns
        result.daily_returns = result.equity_curve.pct_change().fillna(0)

        # Calculate drawdown
        cummax = result.equity_curve.expanding().max()
        result.drawdown_curve = (result.equity_curve - cummax) / cummax

        logger.info("="*60)
        logger.info("BACKTEST COMPLETE")
        logger.info("="*60)
        logger.info(f"Total Trades: {len(trades)}")
        logger.info(f"Final Equity: ${equity_curve[-1]:,.2f}")
        logger.info(f"Total Return: {(equity_curve[-1]/self.config.initial_capital - 1):.2%}")

        self.results.append(result)
        return result

    def run_walk_forward(self,
                        data: pd.DataFrame,
                        strategy_class,
                        optimize_func=None) -> List[BacktestResult]:
        """
        Run walk-forward analysis

        Args:
            data: Historical data
            strategy_class: Strategy class (not instance)
            optimize_func: Function to optimize strategy parameters

        Returns:
            List of BacktestResult for each walk period
        """
        logger.info("="*60)
        logger.info("WALK-FORWARD ANALYSIS")
        logger.info("="*60)

        in_sample = self.config.in_sample_period
        out_sample = self.config.out_sample_period

        results = []
        start_idx = 0

        while start_idx + in_sample + out_sample <= len(data):
            # Split data
            in_sample_data = data.iloc[start_idx:start_idx + in_sample]
            out_sample_data = data.iloc[start_idx + in_sample:start_idx + in_sample + out_sample]

            logger.info(f"\nWalk Period {len(results) + 1}:")
            logger.info(f"  In-sample: {in_sample_data.index[0]} to {in_sample_data.index[-1]}")
            logger.info(f"  Out-sample: {out_sample_data.index[0]} to {out_sample_data.index[-1]}")

            # Optimize on in-sample (if optimizer provided)
            if optimize_func:
                best_params = optimize_func(in_sample_data)
                strategy = strategy_class(best_params)
                logger.info(f"  Optimized params: {best_params}")
            else:
                strategy = strategy_class()

            # Test on out-of-sample
            result = self.run_backtest(out_sample_data, strategy)
            results.append(result)

            # Move to next period
            start_idx += out_sample

        logger.info(f"\nWalk-forward complete: {len(results)} periods tested")
        return results


if __name__ == "__main__":
    # Test backtest engine
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from cryptobot.strategies.rsi_strategy import RsiStrategy
    from cryptobot.data.mock_data import MockDataGenerator

    print("="*60)
    print("Testing Backtest Engine")
    print("="*60)

    # Generate test data
    generator = MockDataGenerator()
    data = generator.generate_ohlcv(periods=500, volatility=0.02)

    # Create backtest config
    config = BacktestConfig(
        initial_capital=10000.0,
        commission=0.001,
        slippage=0.0005,
        max_risk_per_trade=0.02
    )

    # Create engine
    engine = BacktestEngine(config)

    # Create strategy
    strategy = RsiStrategy()

    # Run backtest
    result = engine.run_backtest(data, strategy)

    print(f"\n{'='*60}")
    print("BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"Strategy: {result.strategy_name}")
    print(f"Period: {result.start_date} to {result.end_date}")
    print(f"Initial Capital: ${config.initial_capital:,.2f}")
    print(f"Final Equity: ${result.equity_curve.iloc[-1]:,.2f}")
    print(f"Total Return: {(result.equity_curve.iloc[-1]/config.initial_capital - 1):.2%}")
    print(f"Total Trades: {len(result.trades)}")

    if result.trades:
        winning = [t for t in result.trades if t.pnl > 0]
        print(f"Winning Trades: {len(winning)}")
        print(f"Win Rate: {len(winning)/len(result.trades):.1%}")
        print(f"Avg P&L: ${np.mean([t.pnl for t in result.trades]):.2f}")

    print("\n✓ Backtest engine test complete!")
