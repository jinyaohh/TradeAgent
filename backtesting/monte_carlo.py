"""
Monte Carlo Simulation

Tests strategy robustness through randomization:
- Trade sequence randomization
- Return randomization
- Bootstrap simulation
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional

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


class MonteCarloSimulator:
    """
    Monte Carlo simulation for strategy robustness testing

    Methods:
    - Trade sequence randomization
    - Return randomization (parametric)
    - Bootstrap simulation (non-parametric)
    """

    def __init__(self, n_simulations: int = 1000):
        """
        Initialize Monte Carlo simulator

        Args:
            n_simulations: Number of simulation runs
        """
        self.n_simulations = n_simulations
        self.analyzer = PerformanceAnalyzer()

        logger.info(f"Monte Carlo Simulator initialized: {n_simulations} simulations")

    def simulate_trade_sequence(self,
                                trades: List,
                                initial_capital: float = 10000.0) -> pd.DataFrame:
        """
        Randomize trade sequence to test order dependency

        Args:
            trades: List of Trade objects from backtest
            initial_capital: Starting capital

        Returns:
            DataFrame with simulation results
        """
        logger.info("="*60)
        logger.info("MONTE CARLO: Trade Sequence Randomization")
        logger.info("="*60)
        logger.info(f"Number of trades: {len(trades)}")
        logger.info(f"Simulations: {self.n_simulations}")

        if not trades:
            logger.warning("No trades to simulate")
            return pd.DataFrame()

        results = []

        for sim in range(self.n_simulations):
            # Randomly shuffle trades
            shuffled_trades = np.random.permutation(trades)

            # Calculate equity curve
            equity = initial_capital
            equity_curve = [equity]

            for trade in shuffled_trades:
                equity += trade.pnl
                equity_curve.append(equity)

            # Calculate metrics
            equity_series = pd.Series(equity_curve)
            returns = equity_series.pct_change().fillna(0)

            final_equity = equity_curve[-1]
            total_return = (final_equity / initial_capital) - 1

            # Drawdown
            cummax = equity_series.expanding().max()
            drawdown = ((equity_series - cummax) / cummax).min()

            # Sharpe (simplified)
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0

            results.append({
                'simulation': sim + 1,
                'final_equity': final_equity,
                'total_return': total_return,
                'max_drawdown': abs(drawdown),
                'sharpe_ratio': sharpe
            })

            if (sim + 1) % (self.n_simulations // 10) == 0:
                logger.debug(f"Progress: {sim+1}/{self.n_simulations}")

        results_df = pd.DataFrame(results)

        # Calculate statistics
        logger.info("\nSimulation Statistics:")
        logger.info(f"Mean Return: {results_df['total_return'].mean():.2%}")
        logger.info(f"Median Return: {results_df['total_return'].median():.2%}")
        logger.info(f"Std Return: {results_df['total_return'].std():.2%}")
        logger.info(f"5th Percentile: {results_df['total_return'].quantile(0.05):.2%}")
        logger.info(f"95th Percentile: {results_df['total_return'].quantile(0.95):.2%}")
        logger.info(f"Probability of Profit: {(results_df['total_return'] > 0).mean():.1%}")

        return results_df

    def simulate_returns(self,
                        equity_curve: pd.Series,
                        method: str = 'parametric') -> pd.DataFrame:
        """
        Simulate returns using parametric or bootstrap methods

        Args:
            equity_curve: Historical equity curve
            method: 'parametric' (normal dist) or 'bootstrap' (resample)

        Returns:
            DataFrame with simulation results
        """
        logger.info("="*60)
        logger.info(f"MONTE CARLO: Return Simulation ({method})")
        logger.info("="*60)

        # Calculate historical returns
        returns = equity_curve.pct_change().dropna()

        if len(returns) == 0:
            logger.warning("No returns to simulate")
            return pd.DataFrame()

        initial_capital = equity_curve.iloc[0]
        n_periods = len(returns)

        results = []

        for sim in range(self.n_simulations):
            if method == 'parametric':
                # Sample from normal distribution with historical mean/std
                sim_returns = np.random.normal(
                    returns.mean(),
                    returns.std(),
                    n_periods
                )
            elif method == 'bootstrap':
                # Resample actual returns with replacement
                sim_returns = np.random.choice(returns.values, n_periods, replace=True)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Build equity curve
            equity = initial_capital * (1 + pd.Series(sim_returns)).cumprod()

            # Calculate metrics
            final_equity = equity.iloc[-1]
            total_return = (final_equity / initial_capital) - 1

            cummax = equity.expanding().max()
            drawdown = ((equity - cummax) / cummax).min()

            sharpe = sim_returns.mean() / sim_returns.std() * np.sqrt(252) if sim_returns.std() > 0 else 0

            results.append({
                'simulation': sim + 1,
                'final_equity': final_equity,
                'total_return': total_return,
                'max_drawdown': abs(drawdown),
                'sharpe_ratio': sharpe
            })

        results_df = pd.DataFrame(results)

        logger.info("\nSimulation Statistics:")
        logger.info(f"Mean Return: {results_df['total_return'].mean():.2%}")
        logger.info(f"Median Return: {results_df['total_return'].median():.2%}")
        logger.info(f"5th Percentile: {results_df['total_return'].quantile(0.05):.2%}")
        logger.info(f"95th Percentile: {results_df['total_return'].quantile(0.95):.2%}")
        logger.info(f"Probability of Profit: {(results_df['total_return'] > 0).mean():.1%}")

        return results_df

    def calculate_risk_metrics(self, results_df: pd.DataFrame) -> Dict:
        """
        Calculate risk metrics from Monte Carlo results

        Args:
            results_df: Simulation results

        Returns:
            Dictionary with risk metrics
        """
        metrics = {
            # Return metrics
            'mean_return': results_df['total_return'].mean(),
            'median_return': results_df['total_return'].median(),
            'std_return': results_df['total_return'].std(),
            'min_return': results_df['total_return'].min(),
            'max_return': results_df['total_return'].max(),

            # Percentiles
            'percentile_5': results_df['total_return'].quantile(0.05),
            'percentile_25': results_df['total_return'].quantile(0.25),
            'percentile_75': results_df['total_return'].quantile(0.75),
            'percentile_95': results_df['total_return'].quantile(0.95),

            # Risk metrics
            'probability_of_profit': (results_df['total_return'] > 0).mean(),
            'probability_of_loss': (results_df['total_return'] < 0).mean(),
            'mean_max_drawdown': results_df['max_drawdown'].mean(),
            'worst_drawdown': results_df['max_drawdown'].max(),

            # Sharpe
            'mean_sharpe': results_df['sharpe_ratio'].mean(),
            'median_sharpe': results_df['sharpe_ratio'].median(),
        }

        return metrics

    def print_monte_carlo_report(self, results_df: pd.DataFrame, metrics: Optional[Dict] = None):
        """
        Print Monte Carlo analysis report

        Args:
            results_df: Simulation results
            metrics: Pre-calculated metrics (optional)
        """
        if metrics is None:
            metrics = self.calculate_risk_metrics(results_df)

        print("\n" + "="*70)
        print("MONTE CARLO SIMULATION REPORT")
        print("="*70)
        print(f"Number of Simulations: {len(results_df)}")

        print("\n📊 RETURN DISTRIBUTION")
        print("-" * 70)
        print(f"Mean Return:           {metrics['mean_return']:>12.2%}")
        print(f"Median Return:         {metrics['median_return']:>12.2%}")
        print(f"Std Deviation:         {metrics['std_return']:>12.2%}")
        print(f"Min Return:            {metrics['min_return']:>12.2%}")
        print(f"Max Return:            {metrics['max_return']:>12.2%}")

        print("\n📉 PERCENTILES")
        print("-" * 70)
        print(f"5th Percentile:        {metrics['percentile_5']:>12.2%}")
        print(f"25th Percentile:       {metrics['percentile_25']:>12.2%}")
        print(f"75th Percentile:       {metrics['percentile_75']:>12.2%}")
        print(f"95th Percentile:       {metrics['percentile_95']:>12.2%}")

        print("\n⚠️  RISK METRICS")
        print("-" * 70)
        print(f"Probability of Profit: {metrics['probability_of_profit']:>12.1%}")
        print(f"Probability of Loss:   {metrics['probability_of_loss']:>12.1%}")
        print(f"Mean Max Drawdown:     {metrics['mean_max_drawdown']:>12.2%}")
        print(f"Worst Drawdown:        {metrics['worst_drawdown']:>12.2%}")

        print("\n⚖️  SHARPE RATIO")
        print("-" * 70)
        print(f"Mean Sharpe:           {metrics['mean_sharpe']:>12.2f}")
        print(f"Median Sharpe:         {metrics['median_sharpe']:>12.2f}")

        print("\n" + "="*70)

    def plot_distribution(self, results_df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Plot Monte Carlo results distribution

        Args:
            results_df: Simulation results
            save_path: Path to save plot (optional)
        """
        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available - cannot plot")
            return None

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Return distribution
        axes[0, 0].hist(results_df['total_return'] * 100, bins=50, edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(results_df['total_return'].mean() * 100, color='red', linestyle='--', label='Mean')
        axes[0, 0].axvline(results_df['total_return'].median() * 100, color='green', linestyle='--', label='Median')
        axes[0, 0].set_xlabel('Total Return (%)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Return Distribution')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)

        # Drawdown distribution
        axes[0, 1].hist(results_df['max_drawdown'] * 100, bins=50, edgecolor='black', alpha=0.7, color='orange')
        axes[0, 1].axvline(results_df['max_drawdown'].mean() * 100, color='red', linestyle='--', label='Mean')
        axes[0, 1].set_xlabel('Max Drawdown (%)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Drawdown Distribution')
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)

        # Sharpe distribution
        axes[1, 0].hist(results_df['sharpe_ratio'], bins=50, edgecolor='black', alpha=0.7, color='green')
        axes[1, 0].axvline(results_df['sharpe_ratio'].mean(), color='red', linestyle='--', label='Mean')
        axes[1, 0].set_xlabel('Sharpe Ratio')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Sharpe Ratio Distribution')
        axes[1, 0].legend()
        axes[1, 0].grid(alpha=0.3)

        # Cumulative distribution
        sorted_returns = np.sort(results_df['total_return'])
        cumulative = np.arange(1, len(sorted_returns) + 1) / len(sorted_returns)
        axes[1, 1].plot(sorted_returns * 100, cumulative * 100, linewidth=2)
        axes[1, 1].axvline(0, color='red', linestyle='--', alpha=0.5)
        axes[1, 1].set_xlabel('Total Return (%)')
        axes[1, 1].set_ylabel('Cumulative Probability (%)')
        axes[1, 1].set_title('Cumulative Distribution Function')
        axes[1, 1].grid(alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig


if __name__ == "__main__":
    # Test Monte Carlo simulator
    print("="*60)
    print("Testing Monte Carlo Simulator")
    print("="*60)

    # Create sample trades
    from backtesting.backtest_engine import Trade
    from datetime import datetime

    trades = []
    for i in range(50):
        trade = Trade(
            symbol='TEST',
            entry_date=datetime.now(),
            exit_date=datetime.now(),
            entry_price=100.0,
            exit_price=100.0 + np.random.normal(2, 5),
            quantity=10,
            side='long',
            pnl=np.random.normal(20, 50),
            pnl_pct=np.random.normal(0.02, 0.05),
            commission=1.0,
            slippage=0.1,
            strategy='Test'
        )
        trades.append(trade)

    # Run simulation
    simulator = MonteCarloSimulator(n_simulations=1000)

    results_df = simulator.simulate_trade_sequence(trades)

    metrics = simulator.calculate_risk_metrics(results_df)
    simulator.print_monte_carlo_report(results_df, metrics)

    print("\n✓ Monte Carlo simulator test complete!")
