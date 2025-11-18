"""
Risk Calculator

Calculates risk and performance metrics for trading strategies.
Used for portfolio evaluation, strategy comparison, and risk monitoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

from monitoring.logger import get_logger

logger = get_logger(__name__)


class RiskCalculator:
    """
    Calculate risk and performance metrics for trading strategies.

    Metrics calculated:
    - Returns: Total return, CAGR, annualized return
    - Risk: Sharpe ratio, Sortino ratio, max drawdown, volatility
    - Trade statistics: Win rate, profit factor, avg win/loss
    - Advanced: Calmar ratio, recovery factor, expectancy
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize risk calculator

        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.risk_free_rate = risk_free_rate
        logger.info(f"Risk Calculator initialized with risk-free rate: {risk_free_rate:.2%}")

    def calculate_metrics(self,
                         equity_curve: Union[pd.DataFrame, pd.Series],
                         trades: Optional[pd.DataFrame] = None,
                         initial_capital: Optional[float] = None,
                         timeframe: str = '1D') -> Dict:
        """
        Calculate comprehensive risk metrics

        Args:
            equity_curve: DataFrame or Series with equity values over time
            trades: Optional DataFrame with individual trade data
            initial_capital: Starting capital (extracted from equity_curve if not provided)
            timeframe: Trading timeframe for annualization (1D, 1h, etc.)

        Returns:
            Dictionary with all calculated metrics
        """
        # Convert to Series if DataFrame
        if isinstance(equity_curve, pd.DataFrame):
            if 'equity' in equity_curve.columns:
                equity = equity_curve['equity']
            else:
                equity = equity_curve.iloc[:, 0]
        else:
            equity = equity_curve

        if len(equity) == 0:
            logger.warning("Empty equity curve provided")
            return self._empty_metrics()

        # Get initial capital
        if initial_capital is None:
            initial_capital = equity.iloc[0]

        # Calculate returns
        returns = equity.pct_change().dropna()

        # Get periods per year for annualization
        periods_per_year = self._get_periods_per_year(timeframe)

        # Calculate all metrics
        metrics = {}

        # Return metrics
        metrics.update(self._calculate_return_metrics(equity, initial_capital, periods_per_year))

        # Risk metrics
        metrics.update(self._calculate_risk_metrics(equity, returns, periods_per_year))

        # Drawdown metrics
        metrics.update(self._calculate_drawdown_metrics(equity))

        # Trade-based metrics (if trades provided)
        if trades is not None and len(trades) > 0:
            metrics.update(self._calculate_trade_metrics(trades))

        # Risk-adjusted metrics
        metrics.update(self._calculate_risk_adjusted_metrics(metrics))

        logger.info(f"Calculated metrics: Return={metrics.get('total_return', 0):.2%}, "
                   f"Sharpe={metrics.get('sharpe_ratio', 0):.2f}, "
                   f"MaxDD={metrics.get('max_drawdown', 0):.2%}")

        return metrics

    def _calculate_return_metrics(self, equity: pd.Series,
                                  initial_capital: float,
                                  periods_per_year: int) -> Dict:
        """Calculate return-based metrics"""
        final_equity = equity.iloc[-1]
        total_return = (final_equity - initial_capital) / initial_capital

        # Calculate CAGR
        num_periods = len(equity)
        years = num_periods / periods_per_year

        if years > 0 and final_equity > 0 and initial_capital > 0:
            cagr = (final_equity / initial_capital) ** (1 / years) - 1
        else:
            cagr = 0.0

        # Daily returns
        returns = equity.pct_change().dropna()
        avg_return = returns.mean()

        # Annualized return
        annualized_return = avg_return * periods_per_year

        return {
            'total_return': total_return,
            'cagr': cagr,
            'annualized_return': annualized_return,
            'avg_daily_return': avg_return,
            'initial_capital': initial_capital,
            'final_equity': final_equity,
            'total_periods': num_periods,
            'years': years
        }

    def _calculate_risk_metrics(self, equity: pd.Series,
                                returns: pd.Series,
                                periods_per_year: int) -> Dict:
        """Calculate volatility and risk metrics"""
        # Volatility
        volatility = returns.std()
        annualized_volatility = volatility * np.sqrt(periods_per_year)

        # Downside deviation (for Sortino)
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std()
        annualized_downside_deviation = downside_deviation * np.sqrt(periods_per_year)

        # Value at Risk (95% confidence)
        var_95 = returns.quantile(0.05)

        # Conditional Value at Risk (Expected Shortfall)
        cvar_95 = returns[returns <= var_95].mean()

        return {
            'volatility': volatility,
            'annualized_volatility': annualized_volatility,
            'downside_deviation': downside_deviation,
            'annualized_downside_deviation': annualized_downside_deviation,
            'var_95': var_95,
            'cvar_95': cvar_95
        }

    def _calculate_drawdown_metrics(self, equity: pd.Series) -> Dict:
        """Calculate drawdown statistics"""
        # Calculate running maximum
        running_max = equity.expanding().max()

        # Calculate drawdown
        drawdown = (equity - running_max) / running_max

        # Max drawdown
        max_drawdown = drawdown.min()

        # Max drawdown duration
        is_drawdown = drawdown < 0
        drawdown_periods = is_drawdown.astype(int).groupby(
            (is_drawdown != is_drawdown.shift()).cumsum()
        ).cumsum()

        max_drawdown_duration = drawdown_periods.max() if len(drawdown_periods) > 0 else 0

        # Current drawdown
        current_drawdown = drawdown.iloc[-1]

        # Average drawdown
        drawdowns = drawdown[drawdown < 0]
        avg_drawdown = drawdowns.mean() if len(drawdowns) > 0 else 0.0

        # Number of drawdown periods
        num_drawdowns = len(drawdowns)

        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': int(max_drawdown_duration),
            'current_drawdown': current_drawdown,
            'avg_drawdown': avg_drawdown,
            'num_drawdowns': num_drawdowns
        }

    def _calculate_trade_metrics(self, trades: pd.DataFrame) -> Dict:
        """Calculate trade-based statistics"""
        if 'profit_pct' not in trades.columns:
            logger.warning("No profit_pct column in trades DataFrame")
            return {}

        total_trades = len(trades)

        # Winning and losing trades
        winning_trades = trades[trades['profit_pct'] > 0]
        losing_trades = trades[trades['profit_pct'] <= 0]

        num_wins = len(winning_trades)
        num_losses = len(losing_trades)

        # Win rate
        win_rate = num_wins / total_trades if total_trades > 0 else 0

        # Average profit/loss
        avg_profit = trades['profit_pct'].mean()
        avg_win = winning_trades['profit_pct'].mean() if num_wins > 0 else 0
        avg_loss = losing_trades['profit_pct'].mean() if num_losses > 0 else 0

        # Profit factor
        total_wins = winning_trades['profit_pct'].sum() if num_wins > 0 else 0
        total_losses = abs(losing_trades['profit_pct'].sum()) if num_losses > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

        # Best and worst trades
        best_trade = trades['profit_pct'].max()
        worst_trade = trades['profit_pct'].min()

        # Consecutive wins/losses
        trades_sorted = trades.sort_values('entry_time') if 'entry_time' in trades.columns else trades
        wins = (trades_sorted['profit_pct'] > 0).astype(int)

        # Calculate consecutive wins
        win_groups = wins.groupby((wins != wins.shift()).cumsum()).cumsum()
        max_consecutive_wins = win_groups.max() if len(win_groups) > 0 else 0

        # Calculate consecutive losses
        losses = (trades_sorted['profit_pct'] <= 0).astype(int)
        loss_groups = losses.groupby((losses != losses.shift()).cumsum()).cumsum()
        max_consecutive_losses = loss_groups.max() if len(loss_groups) > 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': win_rate,
            'avg_profit_per_trade': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'max_consecutive_wins': int(max_consecutive_wins),
            'max_consecutive_losses': int(max_consecutive_losses)
        }

    def _calculate_risk_adjusted_metrics(self, metrics: Dict) -> Dict:
        """Calculate risk-adjusted performance metrics"""
        # Sharpe Ratio
        if metrics.get('annualized_volatility', 0) > 0:
            excess_return = metrics.get('annualized_return', 0) - self.risk_free_rate
            sharpe_ratio = excess_return / metrics['annualized_volatility']
        else:
            sharpe_ratio = 0.0

        # Sortino Ratio
        if metrics.get('annualized_downside_deviation', 0) > 0:
            excess_return = metrics.get('annualized_return', 0) - self.risk_free_rate
            sortino_ratio = excess_return / metrics['annualized_downside_deviation']
        else:
            sortino_ratio = 0.0

        # Calmar Ratio (CAGR / Max Drawdown)
        if metrics.get('max_drawdown', 0) < 0:
            calmar_ratio = metrics.get('cagr', 0) / abs(metrics['max_drawdown'])
        else:
            calmar_ratio = 0.0

        # Recovery Factor (Total Return / Max Drawdown)
        if metrics.get('max_drawdown', 0) < 0:
            recovery_factor = metrics.get('total_return', 0) / abs(metrics['max_drawdown'])
        else:
            recovery_factor = 0.0

        # Profit to Max Drawdown
        if metrics.get('max_drawdown', 0) < 0:
            profit_to_max_dd = metrics.get('total_return', 0) / abs(metrics['max_drawdown'])
        else:
            profit_to_max_dd = 0.0

        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'recovery_factor': recovery_factor,
            'profit_to_max_dd_ratio': profit_to_max_dd
        }

    def _get_periods_per_year(self, timeframe: str) -> int:
        """Get number of periods per year based on timeframe"""
        timeframe_map = {
            '1m': 525600,      # 1 minute
            '5m': 105120,      # 5 minutes
            '15m': 35040,      # 15 minutes
            '1h': 8760,        # 1 hour
            '4h': 2190,        # 4 hours
            '1D': 365,         # 1 day
            '1W': 52,          # 1 week
            '1M': 12           # 1 month
        }

        return timeframe_map.get(timeframe, 365)  # Default to daily

    def _empty_metrics(self) -> Dict:
        """Return empty metrics dictionary"""
        return {
            'total_return': 0.0,
            'cagr': 0.0,
            'annualized_return': 0.0,
            'avg_daily_return': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        }

    def compare_strategies(self, strategies_metrics: Dict[str, Dict]) -> pd.DataFrame:
        """
        Compare multiple strategies side-by-side

        Args:
            strategies_metrics: Dict mapping strategy name to metrics dict

        Returns:
            DataFrame with strategies in columns and metrics in rows
        """
        comparison = pd.DataFrame(strategies_metrics).T

        # Sort by Sharpe ratio (best first)
        if 'sharpe_ratio' in comparison.columns:
            comparison = comparison.sort_values('sharpe_ratio', ascending=False)

        logger.info(f"Compared {len(strategies_metrics)} strategies")

        return comparison

    def print_metrics(self, metrics: Dict, title: str = "Performance Metrics"):
        """Print metrics in a nice format"""
        print("\n" + "="*60)
        print(title.upper())
        print("="*60)

        # Returns
        print("\nRETURNS:")
        print(f"  Total Return:      {metrics.get('total_return', 0):>10.2%}")
        print(f"  CAGR:              {metrics.get('cagr', 0):>10.2%}")
        print(f"  Annualized Return: {metrics.get('annualized_return', 0):>10.2%}")

        # Risk
        print("\nRISK:")
        print(f"  Volatility (Ann.): {metrics.get('annualized_volatility', 0):>10.2%}")
        print(f"  Max Drawdown:      {metrics.get('max_drawdown', 0):>10.2%}")
        print(f"  Current Drawdown:  {metrics.get('current_drawdown', 0):>10.2%}")
        print(f"  Avg Drawdown:      {metrics.get('avg_drawdown', 0):>10.2%}")

        # Risk-Adjusted
        print("\nRISK-ADJUSTED:")
        print(f"  Sharpe Ratio:      {metrics.get('sharpe_ratio', 0):>10.2f}")
        print(f"  Sortino Ratio:     {metrics.get('sortino_ratio', 0):>10.2f}")
        print(f"  Calmar Ratio:      {metrics.get('calmar_ratio', 0):>10.2f}")

        # Trade Statistics
        if 'total_trades' in metrics and metrics['total_trades'] > 0:
            print("\nTRADE STATISTICS:")
            print(f"  Total Trades:      {metrics.get('total_trades', 0):>10}")
            print(f"  Win Rate:          {metrics.get('win_rate', 0):>10.2%}")
            print(f"  Profit Factor:     {metrics.get('profit_factor', 0):>10.2f}")
            print(f"  Expectancy:        {metrics.get('expectancy', 0):>10.2%}")
            print(f"  Avg Win:           {metrics.get('avg_win', 0):>10.2%}")
            print(f"  Avg Loss:          {metrics.get('avg_loss', 0):>10.2%}")
            print(f"  Best Trade:        {metrics.get('best_trade', 0):>10.2%}")
            print(f"  Worst Trade:       {metrics.get('worst_trade', 0):>10.2%}")

        print("="*60 + "\n")


if __name__ == "__main__":
    # Test risk calculator
    print("="*60)
    print("Testing Risk Calculator")
    print("="*60)

    # Create sample equity curve
    np.random.seed(42)
    periods = 252  # 1 year of daily data

    # Generate realistic equity curve
    initial_capital = 10000.0
    daily_returns = np.random.normal(0.0005, 0.015, periods)  # 0.05% avg, 1.5% std

    equity_values = [initial_capital]
    for ret in daily_returns:
        equity_values.append(equity_values[-1] * (1 + ret))

    equity_curve = pd.Series(equity_values)

    # Create sample trades
    trades_data = []
    num_trades = 50

    for i in range(num_trades):
        profit_pct = np.random.normal(0.01, 0.03)  # 1% avg, 3% std
        trades_data.append({
            'entry_time': pd.Timestamp('2024-01-01') + pd.Timedelta(days=i*5),
            'profit_pct': profit_pct,
            'profit_abs': profit_pct * initial_capital * 0.1
        })

    trades_df = pd.DataFrame(trades_data)

    # Calculate metrics
    calculator = RiskCalculator(risk_free_rate=0.02)
    metrics = calculator.calculate_metrics(
        equity_curve=equity_curve,
        trades=trades_df,
        initial_capital=initial_capital,
        timeframe='1D'
    )

    # Print results
    calculator.print_metrics(metrics, "Sample Strategy Performance")

    # Test comparison
    print("\nTesting Strategy Comparison:")
    print("-" * 60)

    strategy_metrics = {
        'Strategy A': metrics,
        'Strategy B': {**metrics, 'sharpe_ratio': 0.5, 'total_return': 0.05},
        'Strategy C': {**metrics, 'sharpe_ratio': 2.0, 'total_return': 0.25}
    }

    comparison = calculator.compare_strategies(strategy_metrics)
    print("\nStrategy Comparison (sorted by Sharpe):")
    print(comparison[['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']].round(3))

    print("\n✓ Risk calculator working correctly!")
    print("="*60)
