"""
Performance Analyzer

Calculates comprehensive performance metrics from backtest results.
Includes standard metrics plus advanced statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from monitoring.logger import get_logger

logger = get_logger(__name__)


class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for backtests

    Calculates:
    - Returns metrics (CAGR, total return, annual volatility)
    - Risk metrics (Sharpe, Sortino, Calmar, max drawdown)
    - Trade statistics (win rate, profit factor, expectancy)
    - Advanced metrics (Omega ratio, tail ratio, recovery factor)
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance analyzer

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculations
        """
        self.risk_free_rate = risk_free_rate

    def analyze(self, backtest_result) -> Dict:
        """
        Perform comprehensive analysis on backtest result

        Args:
            backtest_result: BacktestResult object

        Returns:
            Dictionary with all performance metrics
        """
        logger.info(f"Analyzing performance for {backtest_result.strategy_name}")

        metrics = {}

        # Returns metrics
        metrics.update(self._calculate_returns_metrics(backtest_result))

        # Risk metrics
        metrics.update(self._calculate_risk_metrics(backtest_result))

        # Trade statistics
        metrics.update(self._calculate_trade_statistics(backtest_result))

        # Drawdown analysis
        metrics.update(self._calculate_drawdown_metrics(backtest_result))

        # Advanced metrics
        metrics.update(self._calculate_advanced_metrics(backtest_result))

        return metrics

    def _calculate_returns_metrics(self, result) -> Dict:
        """Calculate return-based metrics"""
        equity_curve = result.equity_curve
        initial_capital = result.config.initial_capital
        daily_returns = result.daily_returns

        # Total return
        total_return = (equity_curve.iloc[-1] / initial_capital) - 1

        # CAGR
        days = (result.end_date - result.start_date).days
        years = days / 365.25
        cagr = (equity_curve.iloc[-1] / initial_capital) ** (1 / years) - 1 if years > 0 else 0

        # Annualized volatility
        annual_vol = daily_returns.std() * np.sqrt(252)

        # Best/worst day
        best_day = daily_returns.max()
        worst_day = daily_returns.min()

        # Best/worst month
        monthly_returns = equity_curve.resample('M').last().pct_change().dropna()
        best_month = monthly_returns.max() if len(monthly_returns) > 0 else 0
        worst_month = monthly_returns.min() if len(monthly_returns) > 0 else 0

        return {
            'total_return': total_return,
            'cagr': cagr,
            'annual_volatility': annual_vol,
            'best_day': best_day,
            'worst_day': worst_day,
            'best_month': best_month,
            'worst_month': worst_month,
            'days_traded': days,
            'years_traded': years
        }

    def _calculate_risk_metrics(self, result) -> Dict:
        """Calculate risk-adjusted metrics"""
        daily_returns = result.daily_returns
        equity_curve = result.equity_curve

        # Sharpe Ratio (annualized)
        excess_returns = daily_returns - (self.risk_free_rate / 252)
        sharpe = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)
                 if excess_returns.std() > 0 else 0)

        # Sortino Ratio (annualized, using downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino = (daily_returns.mean() / downside_std * np.sqrt(252)
                  if downside_std > 0 else 0)

        # Calmar Ratio (CAGR / Max Drawdown)
        max_dd = abs(result.drawdown_curve.min())
        days = (result.end_date - result.start_date).days
        years = days / 365.25
        cagr = ((equity_curve.iloc[-1] / result.config.initial_capital) ** (1 / years) - 1
               if years > 0 else 0)
        calmar = cagr / max_dd if max_dd > 0 else 0

        # Value at Risk (VaR) - 95% confidence
        var_95 = np.percentile(daily_returns, 5)

        # Conditional VaR (CVaR) - expected loss beyond VaR
        cvar_95 = daily_returns[daily_returns <= var_95].mean() if len(daily_returns[daily_returns <= var_95]) > 0 else 0

        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'var_95': var_95,
            'cvar_95': cvar_95
        }

    def _calculate_trade_statistics(self, result) -> Dict:
        """Calculate trade-level statistics"""
        trades = result.trades

        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'expectancy': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_trade_duration': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }

        # Basic counts
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]

        num_wins = len(winning_trades)
        num_losses = len(losing_trades)

        # Win rate
        win_rate = num_wins / total_trades if total_trades > 0 else 0

        # Profit factor (gross profit / gross loss)
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Expectancy (average $ per trade)
        expectancy = np.mean([t.pnl for t in trades])

        # Average win/loss
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0

        # Largest win/loss
        largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0

        # Average trade duration
        avg_duration = np.mean([t.duration_bars for t in trades if t.duration_bars > 0])

        # Consecutive wins/losses
        max_consec_wins = 0
        max_consec_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consec_wins = max(max_consec_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consec_losses = max(max_consec_losses, current_losses)

        # Average P&L percentage
        avg_pnl_pct = np.mean([t.pnl_pct for t in trades])

        # Total commissions and slippage
        total_commission = sum(t.commission for t in trades)
        total_slippage = sum(t.slippage * t.quantity for t in trades)

        return {
            'total_trades': total_trades,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_duration': avg_duration,
            'max_consecutive_wins': max_consec_wins,
            'max_consecutive_losses': max_consec_losses,
            'avg_pnl_pct': avg_pnl_pct,
            'total_commission': total_commission,
            'total_slippage': total_slippage
        }

    def _calculate_drawdown_metrics(self, result) -> Dict:
        """Calculate drawdown-related metrics"""
        drawdown_curve = result.drawdown_curve
        equity_curve = result.equity_curve

        # Maximum drawdown
        max_drawdown = abs(drawdown_curve.min())

        # Maximum drawdown duration (in days)
        # Find periods underwater (below previous high)
        underwater = drawdown_curve < 0
        if underwater.any():
            # Find continuous underwater periods
            changes = underwater.astype(int).diff()
            starts = drawdown_curve.index[changes == 1]
            ends = drawdown_curve.index[changes == -1]

            # Handle if still underwater at end
            if len(starts) > len(ends):
                ends = ends.append(pd.Index([drawdown_curve.index[-1]]))

            if len(starts) > 0 and len(ends) > 0:
                durations = [(end - start).days for start, end in zip(starts, ends)]
                max_dd_duration = max(durations) if durations else 0
                avg_dd_duration = np.mean(durations) if durations else 0
            else:
                max_dd_duration = 0
                avg_dd_duration = 0
        else:
            max_dd_duration = 0
            avg_dd_duration = 0

        # Recovery factor (net profit / max drawdown)
        net_profit = equity_curve.iloc[-1] - result.config.initial_capital
        recovery_factor = net_profit / (max_drawdown * result.config.initial_capital) if max_drawdown > 0 else 0

        # Average drawdown
        avg_drawdown = abs(drawdown_curve[drawdown_curve < 0].mean()) if (drawdown_curve < 0).any() else 0

        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_duration_days': max_dd_duration,
            'avg_drawdown_duration_days': avg_dd_duration,
            'recovery_factor': recovery_factor,
            'avg_drawdown': avg_drawdown
        }

    def _calculate_advanced_metrics(self, result) -> Dict:
        """Calculate advanced statistical metrics"""
        daily_returns = result.daily_returns
        equity_curve = result.equity_curve

        # Skewness (asymmetry of return distribution)
        skewness = daily_returns.skew()

        # Kurtosis (tail heaviness)
        kurtosis = daily_returns.kurtosis()

        # Omega Ratio (probability-weighted ratio of gains vs losses)
        # Using 0 as threshold
        gains = daily_returns[daily_returns > 0]
        losses = daily_returns[daily_returns < 0]
        omega = (gains.sum() / abs(losses.sum())) if len(losses) > 0 and losses.sum() != 0 else 0

        # Tail Ratio (95th percentile / 5th percentile)
        percentile_95 = np.percentile(daily_returns, 95)
        percentile_5 = np.percentile(daily_returns, 5)
        tail_ratio = abs(percentile_95 / percentile_5) if percentile_5 != 0 else 0

        # Stability (std of monthly returns)
        monthly_returns = equity_curve.resample('M').last().pct_change().dropna()
        stability = monthly_returns.std() if len(monthly_returns) > 0 else 0

        # Up/down capture (if benchmark provided, otherwise use 0)
        # This would require benchmark data - placeholder for now
        up_capture = 0
        down_capture = 0

        return {
            'skewness': skewness,
            'kurtosis': kurtosis,
            'omega_ratio': omega,
            'tail_ratio': tail_ratio,
            'stability': stability,
            'up_capture': up_capture,
            'down_capture': down_capture
        }

    def print_performance_report(self, metrics: Dict, detailed: bool = True):
        """
        Print formatted performance report

        Args:
            metrics: Dictionary of calculated metrics
            detailed: If True, print all metrics; if False, summary only
        """
        print("\n" + "="*70)
        print("PERFORMANCE REPORT")
        print("="*70)

        # Returns
        print("\n📈 RETURNS")
        print("-" * 70)
        print(f"Total Return:        {metrics['total_return']:>12.2%}")
        print(f"CAGR:                {metrics['cagr']:>12.2%}")
        print(f"Annual Volatility:   {metrics['annual_volatility']:>12.2%}")
        print(f"Best Day:            {metrics['best_day']:>12.2%}")
        print(f"Worst Day:           {metrics['worst_day']:>12.2%}")

        # Risk-Adjusted
        print("\n⚖️  RISK-ADJUSTED METRICS")
        print("-" * 70)
        print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:>12.2f}")
        print(f"Sortino Ratio:       {metrics['sortino_ratio']:>12.2f}")
        print(f"Calmar Ratio:        {metrics['calmar_ratio']:>12.2f}")

        # Drawdown
        print("\n📉 DRAWDOWN")
        print("-" * 70)
        print(f"Max Drawdown:        {metrics['max_drawdown']:>12.2%}")
        print(f"Max DD Duration:     {metrics['max_drawdown_duration_days']:>12.0f} days")
        print(f"Recovery Factor:     {metrics['recovery_factor']:>12.2f}")

        # Trade Statistics
        print("\n💼 TRADE STATISTICS")
        print("-" * 70)
        print(f"Total Trades:        {metrics['total_trades']:>12.0f}")
        print(f"Win Rate:            {metrics['win_rate']:>12.2%}")
        print(f"Profit Factor:       {metrics['profit_factor']:>12.2f}")
        print(f"Expectancy:          ${metrics['expectancy']:>11.2f}")
        print(f"Avg Win:             ${metrics['avg_win']:>11.2f}")
        print(f"Avg Loss:            ${metrics['avg_loss']:>11.2f}")
        print(f"Largest Win:         ${metrics['largest_win']:>11.2f}")
        print(f"Largest Loss:        ${metrics['largest_loss']:>11.2f}")

        if detailed:
            # Advanced metrics
            print("\n🔬 ADVANCED METRICS")
            print("-" * 70)
            print(f"Omega Ratio:         {metrics['omega_ratio']:>12.2f}")
            print(f"Tail Ratio:          {metrics['tail_ratio']:>12.2f}")
            print(f"Skewness:            {metrics['skewness']:>12.2f}")
            print(f"Kurtosis:            {metrics['kurtosis']:>12.2f}")
            print(f"VaR (95%):           {metrics['var_95']:>12.2%}")
            print(f"CVaR (95%):          {metrics['cvar_95']:>12.2%}")

            # Streak info
            print("\n🔥 STREAKS")
            print("-" * 70)
            print(f"Max Consecutive Wins:   {metrics['max_consecutive_wins']:>9.0f}")
            print(f"Max Consecutive Losses: {metrics['max_consecutive_losses']:>9.0f}")

        print("\n" + "="*70)

    def compare_strategies(self, results_list: List, metric_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compare multiple strategy results

        Args:
            results_list: List of (strategy_name, backtest_result) tuples
            metric_names: Specific metrics to compare (None = key metrics)

        Returns:
            DataFrame with strategies as rows, metrics as columns
        """
        if metric_names is None:
            metric_names = [
                'total_return', 'cagr', 'sharpe_ratio', 'sortino_ratio',
                'max_drawdown', 'win_rate', 'profit_factor', 'total_trades'
            ]

        comparison_data = []

        for name, result in results_list:
            metrics = self.analyze(result)
            row = {'strategy': name}
            for metric in metric_names:
                row[metric] = metrics.get(metric, 0)
            comparison_data.append(row)

        df = pd.DataFrame(comparison_data)
        df = df.set_index('strategy')

        return df


if __name__ == "__main__":
    # Test performance analyzer
    print("="*60)
    print("Testing Performance Analyzer")
    print("="*60)

    # Create mock backtest result for testing
    from backtesting.backtest_engine import BacktestResult, BacktestConfig, Trade
    from datetime import timedelta

    config = BacktestConfig(initial_capital=10000.0)

    # Create sample equity curve
    dates = pd.date_range('2024-01-01', periods=252, freq='D')
    # Simulate equity curve with some volatility
    returns = np.random.normal(0.001, 0.015, 252)
    equity = 10000 * (1 + returns).cumprod()

    result = BacktestResult(
        config=config,
        strategy_name="TestStrategy",
        start_date=dates[0],
        end_date=dates[-1],
        equity_curve=pd.Series(equity, index=dates),
        trades=[],
    )

    # Calculate metrics
    result.daily_returns = result.equity_curve.pct_change().fillna(0)
    cummax = result.equity_curve.expanding().max()
    result.drawdown_curve = (result.equity_curve - cummax) / cummax

    # Analyze
    analyzer = PerformanceAnalyzer()
    metrics = analyzer.analyze(result)

    # Print report
    analyzer.print_performance_report(metrics)

    print("\n✓ Performance analyzer test complete!")
