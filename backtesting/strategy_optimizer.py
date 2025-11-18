"""
Strategy Optimizer

Optimizes strategy parameters using various methods:
- Grid search
- Random search
- Walk-forward optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable, Optional
from itertools import product
import time

from backtesting.backtest_engine import BacktestEngine, BacktestConfig
from backtesting.performance_analyzer import PerformanceAnalyzer
from monitoring.logger import get_logger

logger = get_logger(__name__)


class StrategyOptimizer:
    """
    Optimize strategy parameters

    Methods:
    - Grid search: Test all combinations of parameters
    - Random search: Random sampling of parameter space
    - Walk-forward: Optimize on training, validate on test
    """

    def __init__(self,
                 backtest_config: BacktestConfig,
                 optimization_metric: str = 'sharpe_ratio'):
        """
        Initialize optimizer

        Args:
            backtest_config: Configuration for backtests
            optimization_metric: Metric to optimize (sharpe_ratio, cagr, profit_factor, etc.)
        """
        self.config = backtest_config
        self.optimization_metric = optimization_metric
        self.analyzer = PerformanceAnalyzer()

        self.results = []  # Store all optimization results

        logger.info(f"Optimizer initialized: metric={optimization_metric}")

    def grid_search(self,
                   data: pd.DataFrame,
                   strategy_class,
                   param_grid: Dict[str, List]) -> Tuple[Dict, pd.DataFrame]:
        """
        Grid search over parameter combinations

        Args:
            data: Historical data for backtesting
            strategy_class: Strategy class to optimize
            param_grid: Dictionary of {param_name: [values]}

        Returns:
            Tuple of (best_params, results_df)
        """
        logger.info("="*60)
        logger.info("GRID SEARCH OPTIMIZATION")
        logger.info("="*60)
        logger.info(f"Strategy: {strategy_class.__name__}")
        logger.info(f"Optimization Metric: {self.optimization_metric}")
        logger.info(f"Parameter Grid:")
        for param, values in param_grid.items():
            logger.info(f"  {param}: {values}")

        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        total_combinations = len(combinations)
        logger.info(f"\nTotal combinations to test: {total_combinations}")

        # Test each combination
        results = []
        start_time = time.time()

        for i, combination in enumerate(combinations, 1):
            # Create parameter dict
            params = dict(zip(param_names, combination))

            logger.debug(f"\nTesting combination {i}/{total_combinations}: {params}")

            try:
                # Create strategy with these parameters
                strategy = strategy_class(params)

                # Run backtest
                engine = BacktestEngine(self.config)
                backtest_result = engine.run_backtest(data, strategy)

                # Analyze performance
                metrics = self.analyzer.analyze(backtest_result)

                # Store result
                result_row = {
                    'combination': i,
                    **params,
                    **metrics
                }
                results.append(result_row)

                # Log progress
                if i % max(1, total_combinations // 10) == 0:
                    logger.info(f"Progress: {i}/{total_combinations} ({i/total_combinations*100:.1f}%)")

            except Exception as e:
                logger.error(f"Error testing {params}: {e}")
                # Add failed result
                result_row = {
                    'combination': i,
                    **params,
                    self.optimization_metric: -999,  # Flag as failed
                    'error': str(e)
                }
                results.append(result_row)

        elapsed = time.time() - start_time

        # Create results dataframe
        results_df = pd.DataFrame(results)

        # Find best parameters
        if self.optimization_metric in results_df.columns:
            best_idx = results_df[self.optimization_metric].idxmax()
            best_params = results_df.loc[best_idx, param_names].to_dict()
            best_score = results_df.loc[best_idx, self.optimization_metric]
        else:
            logger.error(f"Metric '{self.optimization_metric}' not found in results")
            best_params = {param: values[0] for param, values in param_grid.items()}
            best_score = 0

        logger.info("\n" + "="*60)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Time elapsed: {elapsed:.1f} seconds")
        logger.info(f"Best {self.optimization_metric}: {best_score:.4f}")
        logger.info(f"Best parameters: {best_params}")

        self.results.append({
            'method': 'grid_search',
            'best_params': best_params,
            'best_score': best_score,
            'results_df': results_df
        })

        return best_params, results_df

    def random_search(self,
                     data: pd.DataFrame,
                     strategy_class,
                     param_distributions: Dict[str, Tuple],
                     n_iter: int = 50) -> Tuple[Dict, pd.DataFrame]:
        """
        Random search over parameter space

        Args:
            data: Historical data
            strategy_class: Strategy class
            param_distributions: Dict of {param: (min, max)} for uniform sampling
            n_iter: Number of random combinations to test

        Returns:
            Tuple of (best_params, results_df)
        """
        logger.info("="*60)
        logger.info("RANDOM SEARCH OPTIMIZATION")
        logger.info("="*60)
        logger.info(f"Strategy: {strategy_class.__name__}")
        logger.info(f"Optimization Metric: {self.optimization_metric}")
        logger.info(f"Iterations: {n_iter}")
        logger.info(f"Parameter Distributions:")
        for param, (min_val, max_val) in param_distributions.items():
            logger.info(f"  {param}: [{min_val}, {max_val}]")

        results = []
        start_time = time.time()

        for i in range(n_iter):
            # Sample random parameters
            params = {}
            for param, (min_val, max_val) in param_distributions.items():
                # Handle int vs float
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[param] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param] = np.random.uniform(min_val, max_val)

            logger.debug(f"\nIteration {i+1}/{n_iter}: {params}")

            try:
                # Create strategy
                strategy = strategy_class(params)

                # Run backtest
                engine = BacktestEngine(self.config)
                backtest_result = engine.run_backtest(data, strategy)

                # Analyze
                metrics = self.analyzer.analyze(backtest_result)

                # Store result
                result_row = {
                    'iteration': i + 1,
                    **params,
                    **metrics
                }
                results.append(result_row)

                if (i + 1) % max(1, n_iter // 10) == 0:
                    logger.info(f"Progress: {i+1}/{n_iter} ({(i+1)/n_iter*100:.1f}%)")

            except Exception as e:
                logger.error(f"Error in iteration {i+1}: {e}")
                result_row = {
                    'iteration': i + 1,
                    **params,
                    self.optimization_metric: -999
                }
                results.append(result_row)

        elapsed = time.time() - start_time

        # Results dataframe
        results_df = pd.DataFrame(results)

        # Find best
        best_idx = results_df[self.optimization_metric].idxmax()
        param_names = list(param_distributions.keys())
        best_params = results_df.loc[best_idx, param_names].to_dict()
        best_score = results_df.loc[best_idx, self.optimization_metric]

        logger.info("\n" + "="*60)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Time elapsed: {elapsed:.1f} seconds")
        logger.info(f"Best {self.optimization_metric}: {best_score:.4f}")
        logger.info(f"Best parameters: {best_params}")

        self.results.append({
            'method': 'random_search',
            'best_params': best_params,
            'best_score': best_score,
            'results_df': results_df
        })

        return best_params, results_df

    def walk_forward_optimize(self,
                             data: pd.DataFrame,
                             strategy_class,
                             param_grid: Dict[str, List],
                             in_sample_pct: float = 0.7) -> List[Dict]:
        """
        Walk-forward optimization

        Args:
            data: Historical data
            strategy_class: Strategy class
            param_grid: Parameter grid for optimization
            in_sample_pct: Percentage of data for in-sample optimization

        Returns:
            List of results for each window
        """
        logger.info("="*60)
        logger.info("WALK-FORWARD OPTIMIZATION")
        logger.info("="*60)

        split_idx = int(len(data) * in_sample_pct)

        in_sample_data = data.iloc[:split_idx]
        out_sample_data = data.iloc[split_idx:]

        logger.info(f"In-sample period: {in_sample_data.index[0]} to {in_sample_data.index[-1]}")
        logger.info(f"Out-sample period: {out_sample_data.index[0]} to {out_sample_data.index[-1]}")

        # Optimize on in-sample
        logger.info("\n" + "-"*60)
        logger.info("PHASE 1: In-Sample Optimization")
        logger.info("-"*60)

        best_params, in_sample_results = self.grid_search(
            in_sample_data,
            strategy_class,
            param_grid
        )

        # Test on out-sample
        logger.info("\n" + "-"*60)
        logger.info("PHASE 2: Out-Sample Validation")
        logger.info("-"*60)
        logger.info(f"Testing with optimized parameters: {best_params}")

        strategy = strategy_class(best_params)
        engine = BacktestEngine(self.config)
        out_sample_result = engine.run_backtest(out_sample_data, strategy)
        out_metrics = self.analyzer.analyze(out_sample_result)

        logger.info("\n" + "="*60)
        logger.info("WALK-FORWARD RESULTS")
        logger.info("="*60)
        logger.info(f"In-sample {self.optimization_metric}: "
                   f"{in_sample_results.loc[in_sample_results[self.optimization_metric].idxmax(), self.optimization_metric]:.4f}")
        logger.info(f"Out-sample {self.optimization_metric}: {out_metrics[self.optimization_metric]:.4f}")

        # Calculate overfitting ratio
        in_sample_score = in_sample_results[self.optimization_metric].max()
        out_sample_score = out_metrics[self.optimization_metric]
        overfit_ratio = out_sample_score / in_sample_score if in_sample_score != 0 else 0

        logger.info(f"Overfitting Ratio: {overfit_ratio:.2f} "
                   f"({'GOOD' if overfit_ratio > 0.7 else 'WARNING: Possible overfitting'})")

        return [{
            'best_params': best_params,
            'in_sample_score': in_sample_score,
            'out_sample_score': out_sample_score,
            'overfit_ratio': overfit_ratio,
            'in_sample_results': in_sample_results,
            'out_sample_metrics': out_metrics
        }]

    def get_parameter_importance(self, results_df: pd.DataFrame, param_names: List[str]) -> pd.DataFrame:
        """
        Analyze which parameters have the most impact

        Args:
            results_df: Results from grid/random search
            param_names: List of parameter names

        Returns:
            DataFrame with parameter importance scores
        """
        importance_data = []

        for param in param_names:
            # Group by parameter value and get mean/std of metric
            grouped = results_df.groupby(param)[self.optimization_metric].agg(['mean', 'std', 'min', 'max'])

            importance = {
                'parameter': param,
                'range': grouped['max'] - grouped['min'],
                'mean_impact': grouped['mean'].std(),
                'best_value': results_df.loc[results_df[self.optimization_metric].idxmax(), param]
            }
            importance_data.append(importance)

        importance_df = pd.DataFrame(importance_data)
        importance_df = importance_df.sort_values('range', ascending=False)

        return importance_df


if __name__ == "__main__":
    # Test optimizer
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from cryptobot.strategies.rsi_strategy import RsiStrategy
    from cryptobot.data.mock_data import MockDataGenerator

    print("="*60)
    print("Testing Strategy Optimizer")
    print("="*60)

    # Generate data
    generator = MockDataGenerator()
    data = generator.generate_ohlcv(periods=500, volatility=0.02)

    # Create config
    config = BacktestConfig(
        initial_capital=10000.0,
        commission=0.001
    )

    # Create optimizer
    optimizer = StrategyOptimizer(config, optimization_metric='sharpe_ratio')

    # Define parameter grid (small for testing)
    param_grid = {
        'rsi_period': [10, 14, 20],
        'rsi_oversold': [25, 30, 35],
        'rsi_overbought': [65, 70, 75]
    }

    # Run grid search
    best_params, results_df = optimizer.grid_search(data, RsiStrategy, param_grid)

    print(f"\nTop 5 combinations:")
    print(results_df.nlargest(5, 'sharpe_ratio')[['rsi_period', 'rsi_oversold', 'rsi_overbought', 'sharpe_ratio', 'total_return']])

    # Parameter importance
    importance = optimizer.get_parameter_importance(results_df, list(param_grid.keys()))
    print(f"\nParameter Importance:")
    print(importance)

    print("\n✓ Optimizer test complete!")
