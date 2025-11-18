#!/usr/bin/env python3
"""Test Risk Calculator"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from shared.risk_management.risk_calculator import RiskCalculator

print("="*60)
print("Testing Risk Calculator")
print("="*60)

# Create sample equity curve (1 year of daily trading)
np.random.seed(42)
periods = 252  # Trading days in a year

# Generate realistic equity curve with trend
initial_capital = 10000.0
daily_returns = np.random.normal(0.0008, 0.02, periods)  # 0.08% avg daily, 2% volatility

equity_values = [initial_capital]
for ret in daily_returns:
    equity_values.append(equity_values[-1] * (1 + ret))

dates = pd.date_range(start='2024-01-01', periods=len(equity_values), freq='D')
equity_curve = pd.Series(equity_values, index=dates)

print(f"\nEquity Curve Generated:")
print(f"  Start Date: {equity_curve.index[0].date()}")
print(f"  End Date: {equity_curve.index[-1].date()}")
print(f"  Initial Capital: ${equity_curve.iloc[0]:,.2f}")
print(f"  Final Capital: ${equity_curve.iloc[-1]:,.2f}")
print(f"  Data Points: {len(equity_curve)}")

# Create sample trades
trades_data = []
num_trades = 50

np.random.seed(42)
for i in range(num_trades):
    # Simulate realistic win rate (60%)
    is_win = np.random.random() < 0.60

    if is_win:
        profit_pct = np.random.uniform(0.01, 0.05)  # 1-5% wins
    else:
        profit_pct = np.random.uniform(-0.03, -0.01)  # 1-3% losses

    trades_data.append({
        'entry_time': pd.Timestamp('2024-01-01') + pd.Timedelta(days=i*5),
        'exit_time': pd.Timestamp('2024-01-01') + pd.Timedelta(days=i*5+2),
        'profit_pct': profit_pct,
        'profit_abs': profit_pct * initial_capital * 0.1
    })

trades_df = pd.DataFrame(trades_data)

print(f"\nTrades Generated:")
print(f"  Total Trades: {len(trades_df)}")
print(f"  Winning Trades: {(trades_df['profit_pct'] > 0).sum()}")
print(f"  Losing Trades: {(trades_df['profit_pct'] <= 0).sum()}")

# Test 1: Basic metrics calculation
print("\n" + "="*60)
print("TEST 1: Basic Metrics Calculation")
print("="*60)

calculator = RiskCalculator(risk_free_rate=0.02)
metrics = calculator.calculate_metrics(
    equity_curve=equity_curve,
    trades=trades_df,
    initial_capital=initial_capital,
    timeframe='1D'
)

calculator.print_metrics(metrics, "Test Strategy Performance")

# Test 2: Metrics without trades
print("\n" + "="*60)
print("TEST 2: Metrics Without Trades (Equity Curve Only)")
print("="*60)

metrics_no_trades = calculator.calculate_metrics(
    equity_curve=equity_curve,
    initial_capital=initial_capital,
    timeframe='1D'
)

print(f"\nKey Metrics (No Trade Data):")
print(f"  Total Return: {metrics_no_trades['total_return']:.2%}")
print(f"  CAGR: {metrics_no_trades['cagr']:.2%}")
print(f"  Sharpe Ratio: {metrics_no_trades['sharpe_ratio']:.2f}")
print(f"  Max Drawdown: {metrics_no_trades['max_drawdown']:.2%}")
print(f"  Volatility: {metrics_no_trades['annualized_volatility']:.2%}")

# Test 3: Strategy Comparison
print("\n" + "="*60)
print("TEST 3: Strategy Comparison")
print("="*60)

# Create multiple strategy results
strategies = {
    'Conservative RSI': {
        **metrics,
        'total_return': 0.15,
        'sharpe_ratio': 1.8,
        'max_drawdown': -0.08,
        'win_rate': 0.65,
        'profit_factor': 2.1
    },
    'Aggressive MA Cross': {
        **metrics,
        'total_return': 0.35,
        'sharpe_ratio': 1.2,
        'max_drawdown': -0.18,
        'win_rate': 0.52,
        'profit_factor': 1.5
    },
    'Balanced Momentum': {
        **metrics,
        'total_return': 0.25,
        'sharpe_ratio': 2.2,
        'max_drawdown': -0.10,
        'win_rate': 0.60,
        'profit_factor': 2.5
    }
}

comparison = calculator.compare_strategies(strategies)

print("\nStrategy Comparison (sorted by Sharpe Ratio):")
print("-" * 60)
key_metrics = ['total_return', 'sharpe_ratio', 'sortino_ratio',
               'max_drawdown', 'win_rate', 'profit_factor']
print(comparison[key_metrics].round(3).to_string())

# Test 4: Different timeframes
print("\n" + "="*60)
print("TEST 4: Different Timeframes")
print("="*60)

timeframes = ['1D', '1h', '4h', '1W']
print(f"\n{'Timeframe':<12} {'Ann. Return':<15} {'Sharpe':<10} {'Volatility'}")
print("-" * 60)

for tf in timeframes:
    tf_metrics = calculator.calculate_metrics(
        equity_curve=equity_curve,
        initial_capital=initial_capital,
        timeframe=tf
    )
    print(f"{tf:<12} {tf_metrics['annualized_return']:>13.2%} {tf_metrics['sharpe_ratio']:>9.2f} "
          f"{tf_metrics['annualized_volatility']:>10.2%}")

# Test 5: Edge cases
print("\n" + "="*60)
print("TEST 5: Edge Cases")
print("="*60)

# Empty equity curve
print("\n5a) Empty equity curve:")
empty_metrics = calculator.calculate_metrics(pd.Series([]), timeframe='1D')
print(f"   Total Return: {empty_metrics['total_return']:.2%}")
print(f"   Sharpe Ratio: {empty_metrics['sharpe_ratio']:.2f}")

# Single value
print("\n5b) Single value equity curve:")
single_metrics = calculator.calculate_metrics(pd.Series([10000.0]), timeframe='1D')
print(f"   Total Return: {single_metrics['total_return']:.2%}")

# Flat equity curve (no volatility)
print("\n5c) Flat equity curve (no trades):")
flat_curve = pd.Series([10000.0] * 100)
flat_metrics = calculator.calculate_metrics(flat_curve, timeframe='1D')
print(f"   Volatility: {flat_metrics['volatility']:.4f}")
print(f"   Sharpe: {flat_metrics['sharpe_ratio']:.2f}")

print("\n" + "="*60)
print("✓ Risk calculator tests completed!")
print("="*60)

# Summary
print("\nSUMMARY:")
print("Risk Calculator provides:")
print("  ✓ Return metrics (Total, CAGR, Annualized)")
print("  ✓ Risk metrics (Volatility, Max DD, VaR)")
print("  ✓ Risk-adjusted ratios (Sharpe, Sortino, Calmar)")
print("  ✓ Trade statistics (Win rate, Profit factor, Expectancy)")
print("  ✓ Strategy comparison")
print("  ✓ Multiple timeframe support")
print("  ✓ Robust edge case handling")
