"""
Backtest Report Generator

Creates comprehensive reports and visualizations from backtest results.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

from backtesting.performance_analyzer import PerformanceAnalyzer
from monitoring.logger import get_logger

logger = get_logger(__name__)

# Optional matplotlib import
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available - plotting functions disabled")


class ReportGenerator:
    """
    Generate comprehensive backtest reports

    Features:
    - HTML reports
    - Strategy comparison
    - Visualization generation
    - Export to various formats
    """

    def __init__(self):
        """Initialize report generator"""
        self.analyzer = PerformanceAnalyzer()

    def generate_full_report(self,
                            backtest_result,
                            output_path: Optional[str] = None) -> str:
        """
        Generate comprehensive text report

        Args:
            backtest_result: BacktestResult object
            output_path: Path to save report (optional)

        Returns:
            Report as string
        """
        # Analyze performance
        metrics = self.analyzer.analyze(backtest_result)

        # Build report
        report = []
        report.append("="*80)
        report.append("COMPREHENSIVE BACKTEST REPORT")
        report.append("="*80)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Strategy info
        report.append("\n" + "-"*80)
        report.append("STRATEGY INFORMATION")
        report.append("-"*80)
        report.append(f"Strategy Name:       {backtest_result.strategy_name}")
        report.append(f"Test Period:         {backtest_result.start_date} to {backtest_result.end_date}")
        report.append(f"Duration:            {metrics['days_traded']} days ({metrics['years_traded']:.2f} years)")
        report.append(f"Initial Capital:     ${backtest_result.config.initial_capital:,.2f}")
        report.append(f"Final Equity:        ${backtest_result.equity_curve.iloc[-1]:,.2f}")

        # Returns
        report.append("\n" + "-"*80)
        report.append("RETURNS")
        report.append("-"*80)
        report.append(f"Total Return:        {metrics['total_return']:>12.2%}")
        report.append(f"CAGR:                {metrics['cagr']:>12.2%}")
        report.append(f"Annual Volatility:   {metrics['annual_volatility']:>12.2%}")
        report.append(f"Best Day:            {metrics['best_day']:>12.2%}")
        report.append(f"Worst Day:           {metrics['worst_day']:>12.2%}")
        report.append(f"Best Month:          {metrics['best_month']:>12.2%}")
        report.append(f"Worst Month:         {metrics['worst_month']:>12.2%}")

        # Risk-adjusted metrics
        report.append("\n" + "-"*80)
        report.append("RISK-ADJUSTED PERFORMANCE")
        report.append("-"*80)
        report.append(f"Sharpe Ratio:        {metrics['sharpe_ratio']:>12.2f}")
        report.append(f"Sortino Ratio:       {metrics['sortino_ratio']:>12.2f}")
        report.append(f"Calmar Ratio:        {metrics['calmar_ratio']:>12.2f}")
        report.append(f"Omega Ratio:         {metrics['omega_ratio']:>12.2f}")

        # Drawdown
        report.append("\n" + "-"*80)
        report.append("DRAWDOWN ANALYSIS")
        report.append("-"*80)
        report.append(f"Max Drawdown:        {metrics['max_drawdown']:>12.2%}")
        report.append(f"Max DD Duration:     {metrics['max_drawdown_duration_days']:>12.0f} days")
        report.append(f"Avg Drawdown:        {metrics['avg_drawdown']:>12.2%}")
        report.append(f"Recovery Factor:     {metrics['recovery_factor']:>12.2f}")

        # Trade statistics
        report.append("\n" + "-"*80)
        report.append("TRADE STATISTICS")
        report.append("-"*80)
        report.append(f"Total Trades:        {metrics['total_trades']:>12.0f}")
        report.append(f"Winning Trades:      {metrics['winning_trades']:>12.0f}")
        report.append(f"Losing Trades:       {metrics['losing_trades']:>12.0f}")
        report.append(f"Win Rate:            {metrics['win_rate']:>12.2%}")
        report.append(f"Profit Factor:       {metrics['profit_factor']:>12.2f}")
        report.append(f"Expectancy:          ${metrics['expectancy']:>11.2f}")
        report.append(f"Avg Win:             ${metrics['avg_win']:>11.2f}")
        report.append(f"Avg Loss:            ${metrics['avg_loss']:>11.2f}")
        report.append(f"Avg Win/Loss Ratio:  {abs(metrics['avg_win']/metrics['avg_loss']):.2f}" if metrics['avg_loss'] != 0 else "Avg Win/Loss Ratio:  N/A")
        report.append(f"Largest Win:         ${metrics['largest_win']:>11.2f}")
        report.append(f"Largest Loss:        ${metrics['largest_loss']:>11.2f}")
        report.append(f"Avg Trade Duration:  {metrics['avg_trade_duration']:>12.1f} bars")

        # Streaks
        report.append("\n" + "-"*80)
        report.append("STREAKS")
        report.append("-"*80)
        report.append(f"Max Consecutive Wins:   {metrics['max_consecutive_wins']:>9.0f}")
        report.append(f"Max Consecutive Losses: {metrics['max_consecutive_losses']:>9.0f}")

        # Costs
        report.append("\n" + "-"*80)
        report.append("TRANSACTION COSTS")
        report.append("-"*80)
        report.append(f"Total Commission:    ${metrics['total_commission']:>11.2f}")
        report.append(f"Total Slippage:      ${metrics['total_slippage']:>11.2f}")
        report.append(f"Total Costs:         ${metrics['total_commission'] + metrics['total_slippage']:>11.2f}")

        # Risk metrics
        report.append("\n" + "-"*80)
        report.append("RISK METRICS")
        report.append("-"*80)
        report.append(f"VaR (95%):           {metrics['var_95']:>12.2%}")
        report.append(f"CVaR (95%):          {metrics['cvar_95']:>12.2%}")
        report.append(f"Skewness:            {metrics['skewness']:>12.2f}")
        report.append(f"Kurtosis:            {metrics['kurtosis']:>12.2f}")
        report.append(f"Tail Ratio:          {metrics['tail_ratio']:>12.2f}")

        report.append("\n" + "="*80)

        report_text = "\n".join(report)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_path}")

        return report_text

    def compare_strategies(self,
                          results_list: List[Tuple[str, object]],
                          output_path: Optional[str] = None) -> pd.DataFrame:
        """
        Compare multiple strategy results

        Args:
            results_list: List of (strategy_name, backtest_result) tuples
            output_path: Path to save comparison (optional)

        Returns:
            DataFrame with comparison
        """
        logger.info(f"Comparing {len(results_list)} strategies")

        comparison_data = []

        for name, result in results_list:
            metrics = self.analyzer.analyze(result)

            row = {
                'Strategy': name,
                'Total Return': metrics['total_return'],
                'CAGR': metrics['cagr'],
                'Volatility': metrics['annual_volatility'],
                'Sharpe': metrics['sharpe_ratio'],
                'Sortino': metrics['sortino_ratio'],
                'Max DD': metrics['max_drawdown'],
                'Calmar': metrics['calmar_ratio'],
                'Win Rate': metrics['win_rate'],
                'Profit Factor': metrics['profit_factor'],
                'Total Trades': metrics['total_trades'],
                'Expectancy': metrics['expectancy']
            }
            comparison_data.append(row)

        df = pd.DataFrame(comparison_data)

        if output_path:
            df.to_csv(output_path, index=False)
            logger.info(f"Comparison saved to {output_path}")

        return df

    def plot_equity_curves(self,
                          results_list: List[Tuple[str, object]],
                          save_path: Optional[str] = None):
        """
        Plot equity curves for multiple strategies

        Args:
            results_list: List of (strategy_name, backtest_result) tuples
            save_path: Path to save plot (optional)
        """
        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available - cannot plot")
            return None

        plt.figure(figsize=(14, 8))

        for name, result in results_list:
            # Normalize to percentage returns
            equity = result.equity_curve
            normalized = (equity / equity.iloc[0] - 1) * 100
            plt.plot(normalized.index, normalized, label=name, linewidth=2, alpha=0.8)

        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Return (%)', fontsize=12)
        plt.title('Strategy Comparison - Equity Curves', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(alpha=0.3)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return plt.gcf()

    def plot_backtest_summary(self,
                             backtest_result,
                             save_path: Optional[str] = None):
        """
        Create comprehensive visualization of backtest results

        Args:
            backtest_result: BacktestResult object
            save_path: Path to save plot (optional)
        """
        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available - cannot plot")
            return None

        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # 1. Equity curve
        ax1 = fig.add_subplot(gs[0, :])
        equity = backtest_result.equity_curve
        ax1.plot(equity.index, equity, linewidth=2, color='blue')
        ax1.fill_between(equity.index, backtest_result.config.initial_capital, equity, alpha=0.3)
        ax1.set_ylabel('Equity ($)', fontsize=11)
        ax1.set_title(f'{backtest_result.strategy_name} - Equity Curve', fontsize=13, fontweight='bold')
        ax1.grid(alpha=0.3)
        ax1.axhline(y=backtest_result.config.initial_capital, color='gray', linestyle='--', alpha=0.5)

        # 2. Drawdown
        ax2 = fig.add_subplot(gs[1, :])
        drawdown = backtest_result.drawdown_curve * 100
        ax2.fill_between(drawdown.index, 0, drawdown, color='red', alpha=0.3)
        ax2.plot(drawdown.index, drawdown, color='darkred', linewidth=1)
        ax2.set_ylabel('Drawdown (%)', fontsize=11)
        ax2.set_title('Underwater Plot', fontsize=13, fontweight='bold')
        ax2.grid(alpha=0.3)

        # 3. Monthly returns heatmap
        ax3 = fig.add_subplot(gs[2, 0])
        monthly_returns = equity.resample('M').last().pct_change().dropna() * 100

        if len(monthly_returns) > 0:
            # Create year-month matrix
            monthly_returns.index = pd.to_datetime(monthly_returns.index)
            monthly_data = monthly_returns.groupby([monthly_returns.index.year, monthly_returns.index.month]).mean()

            if len(monthly_data) > 0:
                years = sorted(monthly_data.index.get_level_values(0).unique())
                months = range(1, 13)

                matrix = np.full((len(years), 12), np.nan)
                for i, year in enumerate(years):
                    for j, month in enumerate(months):
                        if (year, month) in monthly_data.index:
                            matrix[i, j] = monthly_data.loc[(year, month)]

                im = ax3.imshow(matrix, aspect='auto', cmap='RdYlGn', vmin=-10, vmax=10)
                ax3.set_xticks(range(12))
                ax3.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], fontsize=9)
                ax3.set_yticks(range(len(years)))
                ax3.set_yticklabels(years, fontsize=9)
                ax3.set_title('Monthly Returns (%)', fontsize=11, fontweight='bold')
                plt.colorbar(im, ax=ax3)

        # 4. Return distribution
        ax4 = fig.add_subplot(gs[2, 1])
        daily_returns = backtest_result.daily_returns * 100
        ax4.hist(daily_returns, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
        ax4.axvline(daily_returns.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {daily_returns.mean():.3f}%')
        ax4.axvline(daily_returns.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {daily_returns.median():.3f}%')
        ax4.set_xlabel('Daily Return (%)', fontsize=10)
        ax4.set_ylabel('Frequency', fontsize=10)
        ax4.set_title('Return Distribution', fontsize=11, fontweight='bold')
        ax4.legend(fontsize=9)
        ax4.grid(alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def export_trades_to_csv(self,
                            backtest_result,
                            output_path: str):
        """
        Export trade history to CSV

        Args:
            backtest_result: BacktestResult object
            output_path: Path to save CSV
        """
        if not backtest_result.trades:
            logger.warning("No trades to export")
            return

        trades_data = []
        for trade in backtest_result.trades:
            trades_data.append({
                'Symbol': trade.symbol,
                'Entry Date': trade.entry_date,
                'Exit Date': trade.exit_date,
                'Entry Price': trade.entry_price,
                'Exit Price': trade.exit_price,
                'Quantity': trade.quantity,
                'Side': trade.side,
                'P&L': trade.pnl,
                'P&L %': trade.pnl_pct,
                'Commission': trade.commission,
                'Slippage': trade.slippage,
                'Strategy': trade.strategy,
                'Exit Reason': trade.exit_reason,
                'Duration (bars)': trade.duration_bars
            })

        df = pd.DataFrame(trades_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Trades exported to {output_path}")

    def export_metrics_to_json(self,
                               backtest_result,
                               output_path: str):
        """
        Export metrics to JSON

        Args:
            backtest_result: BacktestResult object
            output_path: Path to save JSON
        """
        metrics = self.analyzer.analyze(backtest_result)

        # Convert to JSON-serializable format
        json_metrics = {}
        for key, value in metrics.items():
            if isinstance(value, (np.integer, np.floating)):
                json_metrics[key] = float(value)
            elif pd.isna(value):
                json_metrics[key] = None
            else:
                json_metrics[key] = value

        with open(output_path, 'w') as f:
            json.dump(json_metrics, f, indent=2, default=str)

        logger.info(f"Metrics exported to {output_path}")


if __name__ == "__main__":
    # Test report generator
    print("="*60)
    print("Testing Report Generator")
    print("="*60)

    # Create mock result
    from backtesting.backtest_engine import BacktestResult, BacktestConfig

    config = BacktestConfig(initial_capital=10000.0)
    dates = pd.date_range('2024-01-01', periods=252, freq='D')
    returns = np.random.normal(0.001, 0.015, 252)
    equity = 10000 * (1 + returns).cumprod()

    result = BacktestResult(
        config=config,
        strategy_name="TestStrategy",
        start_date=dates[0],
        end_date=dates[-1],
        equity_curve=pd.Series(equity, index=dates),
        trades=[]
    )

    result.daily_returns = result.equity_curve.pct_change().fillna(0)
    cummax = result.equity_curve.expanding().max()
    result.drawdown_curve = (result.equity_curve - cummax) / cummax

    # Generate report
    generator = ReportGenerator()
    report = generator.generate_full_report(result)
    print(report)

    print("\n✓ Report generator test complete!")
