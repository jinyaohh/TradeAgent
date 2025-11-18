"""
Backtesting Module

Advanced backtesting capabilities for strategy validation.

Components:
- BacktestEngine: Core backtesting with walk-forward analysis
- PerformanceAnalyzer: Comprehensive metrics calculation
- StrategyOptimizer: Parameter optimization (grid/random search)
- MonteCarloSimulator: Robustness testing
"""

from backtesting.backtest_engine import BacktestEngine, BacktestConfig, BacktestResult, Trade
from backtesting.performance_analyzer import PerformanceAnalyzer
from backtesting.strategy_optimizer import StrategyOptimizer
from backtesting.monte_carlo import MonteCarloSimulator

__all__ = [
    'BacktestEngine',
    'BacktestConfig',
    'BacktestResult',
    'Trade',
    'PerformanceAnalyzer',
    'StrategyOptimizer',
    'MonteCarloSimulator',
]
