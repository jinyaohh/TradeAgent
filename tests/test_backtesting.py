"""
Comprehensive Backtesting System Test

Tests all backtesting components:
- Backtest Engine
- Performance Analyzer
- Strategy Optimizer
- Monte Carlo Simulator
- Report Generator
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime

from backtesting.backtest_engine import BacktestEngine, BacktestConfig
from backtesting.performance_analyzer import PerformanceAnalyzer
from backtesting.strategy_optimizer import StrategyOptimizer
from backtesting.monte_carlo import MonteCarloSimulator
from backtesting.report_generator import ReportGenerator

from cryptobot.strategies.rsi_strategy import RsiStrategy
from cryptobot.data.mock_data import MockDataGenerator
from monitoring.logger import get_logger

logger = get_logger(__name__)


def test_backtest_engine():
    """Test 1: Backtest Engine"""
    print("\n" + "="*70)
    print("TEST 1: Backtest Engine")
    print("="*70)

    try:
        # Generate data
        generator = MockDataGenerator()
        data = generator.generate_ohlcv(periods=500, volatility=0.02)

        # Create config
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001,
            slippage=0.0005
        )

        # Create engine
        engine = BacktestEngine(config)

        # Create strategy
        strategy = RsiStrategy()

        # Run backtest
        result = engine.run_backtest(data, strategy)

        # Validate results
        assert result is not None, "Backtest should return results"
        assert len(result.equity_curve) > 0, "Equity curve should not be empty"
        assert result.equity_curve.iloc[-1] > 0, "Final equity should be positive"

        print(f"\n✅ TEST 1 PASSED")
        print(f"   Total Trades: {len(result.trades)}")
        print(f"   Final Equity: ${result.equity_curve.iloc[-1]:,.2f}")
        return result

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        raise


def test_performance_analyzer(backtest_result):
    """Test 2: Performance Analyzer"""
    print("\n" + "="*70)
    print("TEST 2: Performance Analyzer")
    print("="*70)

    try:
        analyzer = PerformanceAnalyzer()

        # Analyze results
        metrics = analyzer.analyze(backtest_result)

        # Validate metrics
        assert 'total_return' in metrics, "Should have total_return metric"
        assert 'sharpe_ratio' in metrics, "Should have sharpe_ratio metric"
        assert 'max_drawdown' in metrics, "Should have max_drawdown metric"
        assert 'win_rate' in metrics, "Should have win_rate metric"

        # Print report
        analyzer.print_performance_report(metrics, detailed=False)

        print(f"\n✅ TEST 2 PASSED")
        print(f"   Metrics calculated: {len(metrics)}")
        return metrics

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        raise


def test_strategy_optimizer():
    """Test 3: Strategy Optimizer"""
    print("\n" + "="*70)
    print("TEST 3: Strategy Optimizer (Grid Search)")
    print("="*70)

    try:
        # Generate data
        generator = MockDataGenerator()
        data = generator.generate_ohlcv(periods=300, volatility=0.02)

        # Create config
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001
        )

        # Create optimizer
        optimizer = StrategyOptimizer(config, optimization_metric='sharpe_ratio')

        # Define parameter grid (small for testing)
        param_grid = {
            'rsi_period': [10, 14],
            'rsi_oversold': [25, 30],
            'rsi_overbought': [70, 75]
        }

        # Run optimization
        best_params, results_df = optimizer.grid_search(data, RsiStrategy, param_grid)

        # Validate
        assert best_params is not None, "Should find best parameters"
        assert len(results_df) == 8, "Should test 8 combinations (2x2x2)"
        assert 'sharpe_ratio' in results_df.columns, "Should have sharpe_ratio column"

        print(f"\n✅ TEST 3 PASSED")
        print(f"   Best parameters: {best_params}")
        print(f"   Best Sharpe: {results_df['sharpe_ratio'].max():.2f}")

        return best_params

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        raise


def test_monte_carlo(backtest_result):
    """Test 4: Monte Carlo Simulator"""
    print("\n" + "="*70)
    print("TEST 4: Monte Carlo Simulator")
    print("="*70)

    try:
        if not backtest_result.trades:
            print("⚠️  TEST 4 SKIPPED: No trades to simulate")
            return None

        # Create simulator
        simulator = MonteCarloSimulator(n_simulations=100)  # Reduced for testing

        # Run simulation
        results_df = simulator.simulate_trade_sequence(
            backtest_result.trades,
            initial_capital=backtest_result.config.initial_capital
        )

        # Validate
        assert len(results_df) == 100, "Should have 100 simulations"
        assert 'total_return' in results_df.columns, "Should have total_return column"
        assert 'max_drawdown' in results_df.columns, "Should have max_drawdown column"

        # Calculate metrics
        metrics = simulator.calculate_risk_metrics(results_df)

        print(f"\n✅ TEST 4 PASSED")
        print(f"   Simulations: {len(results_df)}")
        print(f"   Mean Return: {metrics['mean_return']:.2%}")
        print(f"   Probability of Profit: {metrics['probability_of_profit']:.1%}")

        return results_df

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        raise


def test_report_generator(backtest_result):
    """Test 5: Report Generator"""
    print("\n" + "="*70)
    print("TEST 5: Report Generator")
    print("="*70)

    try:
        generator = ReportGenerator()

        # Generate text report
        report = generator.generate_full_report(backtest_result)

        # Validate
        assert len(report) > 0, "Report should not be empty"
        assert "RETURNS" in report, "Report should have RETURNS section"
        assert "TRADE STATISTICS" in report, "Report should have TRADE STATISTICS section"

        # Test comparison (with single strategy)
        comparison_df = generator.compare_strategies([
            ("RSI Strategy", backtest_result)
        ])

        assert len(comparison_df) == 1, "Should have 1 strategy"
        assert 'Total Return' in comparison_df.columns, "Should have Total Return"

        print(f"\n✅ TEST 5 PASSED")
        print(f"   Report length: {len(report)} characters")

        return report

    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        raise


def test_walk_forward():
    """Test 6: Walk-Forward Analysis"""
    print("\n" + "="*70)
    print("TEST 6: Walk-Forward Analysis")
    print("="*70)

    try:
        # Generate data
        generator = MockDataGenerator()
        data = generator.generate_ohlcv(periods=300, volatility=0.02)

        # Create config with walk-forward enabled
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001,
            walk_forward=True,
            in_sample_period=200,
            out_sample_period=50
        )

        # Create optimizer
        optimizer = StrategyOptimizer(config, optimization_metric='sharpe_ratio')

        # Simple param grid
        param_grid = {
            'rsi_period': [10, 14],
            'rsi_oversold': [30]
        }

        # Run walk-forward optimization
        results = optimizer.walk_forward_optimize(
            data,
            RsiStrategy,
            param_grid,
            in_sample_pct=0.7
        )

        # Validate
        assert len(results) > 0, "Should have walk-forward results"
        assert 'best_params' in results[0], "Should have best_params"
        assert 'overfit_ratio' in results[0], "Should have overfit_ratio"

        print(f"\n✅ TEST 6 PASSED")
        print(f"   Overfit Ratio: {results[0]['overfit_ratio']:.2f}")

        return results

    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        raise


def run_all_tests():
    """Run all backtesting system tests"""
    print("\n" + "="*70)
    print("BACKTESTING SYSTEM TEST SUITE")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results_summary = []
    test_start = datetime.now()

    try:
        # Test 1: Backtest Engine
        backtest_result = test_backtest_engine()
        results_summary.append(("Backtest Engine", True))

        # Test 2: Performance Analyzer
        metrics = test_performance_analyzer(backtest_result)
        results_summary.append(("Performance Analyzer", True))

        # Test 3: Strategy Optimizer
        best_params = test_strategy_optimizer()
        results_summary.append(("Strategy Optimizer", True))

        # Test 4: Monte Carlo
        mc_results = test_monte_carlo(backtest_result)
        results_summary.append(("Monte Carlo Simulator", True))

        # Test 5: Report Generator
        report = test_report_generator(backtest_result)
        results_summary.append(("Report Generator", True))

        # Test 6: Walk-Forward
        wf_results = test_walk_forward()
        results_summary.append(("Walk-Forward Analysis", True))

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        results_summary.append(("Test Suite", False))

    # Print summary
    elapsed = (datetime.now() - test_start).total_seconds()
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results_summary if result)
    total = len(results_summary)

    for test_name, result in results_summary:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Duration: {elapsed:.1f} seconds")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Backtesting system is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
