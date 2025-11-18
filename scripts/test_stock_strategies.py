#!/usr/bin/env python3
"""
Test Stock Trading Strategies

Tests both RSI and MA Crossover strategies on stock data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stockbot.data.mock_stock_data import MockStockDataGenerator
from stockbot.strategies.stock_rsi_strategy import StockRsiStrategy
from stockbot.strategies.ma_crossover_strategy import MaCrossoverStrategy
from backtest.simple_backtest import SimpleBacktest

print("="*70)
print("TESTING STOCK TRADING STRATEGIES")
print("="*70)

# Generate stock data (1 year of daily bars)
print("\n1. Generating stock market data...")
generator = MockStockDataGenerator(seed=42)
df = generator.generate_stock_bars(
    symbol='TEST',
    periods=252,  # ~1 trading year
    timeframe='1Day',
    initial_price=150.0,
    volatility=0.02  # Typical stock volatility
)
print(f"✓ Generated {len(df)} trading days")
print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

# Test 1: RSI Strategy
print("\n" + "="*70)
print("TEST 1: RSI MEAN REVERSION STRATEGY")
print("="*70)

print("\n2. Initializing RSI strategy...")
rsi_strategy = StockRsiStrategy()
print(f"✓ Strategy: {rsi_strategy.name}")
print(f"  RSI Oversold: {rsi_strategy.rsi_oversold}")
print(f"  RSI Overbought: {rsi_strategy.rsi_overbought}")
print(f"  Stop Loss: {rsi_strategy.stoploss:.1%}")
print(f"  Take Profit: {rsi_strategy.take_profit:.1%}")

print("\n3. Running RSI backtest...")
rsi_backtest = SimpleBacktest(
    strategy=rsi_strategy,
    initial_capital=10000.0,
    fee_pct=0.0,  # Commission-free
    position_size_pct=1.0
)

rsi_results = rsi_backtest.run(df)
rsi_backtest.print_results(rsi_results)

# Test 2: MA Crossover Strategy
print("\n" + "="*70)
print("TEST 2: MOVING AVERAGE CROSSOVER STRATEGY")
print("="*70)

print("\n4. Initializing MA Crossover strategy...")
ma_strategy = MaCrossoverStrategy()
print(f"✓ Strategy: {ma_strategy.name}")
print(f"  Fast MA: {ma_strategy.fast_period}-day {ma_strategy.ma_type}")
print(f"  Slow MA: {ma_strategy.slow_period}-day {ma_strategy.ma_type}")
print(f"  Stop Loss: {ma_strategy.stoploss:.1%}")
print(f"  Take Profit: {ma_strategy.take_profit:.1%}")

print("\n5. Running MA Crossover backtest...")
ma_backtest = SimpleBacktest(
    strategy=ma_strategy,
    initial_capital=10000.0,
    fee_pct=0.0,
    position_size_pct=1.0
)

ma_results = ma_backtest.run(df)
ma_backtest.print_results(ma_results)

# Comparison
print("\n" + "="*70)
print("STRATEGY COMPARISON")
print("="*70)

print(f"\n{'Metric':<20} {'RSI Strategy':<20} {'MA Crossover':<20}")
print("-"*70)
print(f"{'Total Return':<20} {rsi_results['total_return']:>18.2%} {ma_results['total_return']:>18.2%}")
print(f"{'Total Trades':<20} {rsi_results['total_trades']:>18} {ma_results['total_trades']:>18}")
print(f"{'Win Rate':<20} {rsi_results['win_rate']:>18.1%} {ma_results['win_rate']:>18.1%}")
print(f"{'Avg Profit':<20} {rsi_results['avg_profit']:>18.2%} {ma_results['avg_profit']:>18.2%}")
print(f"{'Profit Factor':<20} {rsi_results['profit_factor']:>18.2f} {ma_results['profit_factor']:>18.2f}")
print(f"{'Max Drawdown':<20} {rsi_results['max_drawdown']:>18.2%} {ma_results['max_drawdown']:>18.2%}")

# Determine winner
print("\n" + "="*70)
print("CONCLUSION")
print("="*70)

if rsi_results['total_return'] > ma_results['total_return']:
    winner = "RSI Strategy"
    winner_return = rsi_results['total_return']
else:
    winner = "MA Crossover Strategy"
    winner_return = ma_results['total_return']

print(f"\n🏆 Best performer: {winner}")
print(f"   Return: {winner_return:.2%}")

print("\nNote: These results are on simulated data.")
print("Real performance requires:")
print("  - Extended backtesting (3-5 years)")
print("  - Multiple market conditions")
print("  - Paper trading validation")
print("  - Parameter optimization")

print("\n✓ Stock strategy testing complete!")
print("="*70)
