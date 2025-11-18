#!/usr/bin/env python3
"""
Test Backtesting Engine with RSI Strategy
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptobot.data.mock_data import MockDataGenerator
from cryptobot.strategies.rsi_strategy import RsiStrategy
from backtest.simple_backtest import SimpleBacktest

print("="*60)
print("BACKTESTING RSI STRATEGY")
print("="*60)

# Generate realistic data (1000 candles, ~1.5 months of hourly data)
print("\n1. Generating test data...")
generator = MockDataGenerator(seed=42)
df = generator.generate_ohlcv(periods=1000, volatility=0.03, trend=0.0001)
print(f"✓ Generated {len(df)} hourly candles")
print(f"  Start: {df.index[0]}")
print(f"  End: {df.index[-1]}")
print(f"  Price range: ${df['close'].min():,.2f} - ${df['close'].max():,.2f}")

# Create RSI strategy
print("\n2. Initializing RSI strategy...")
strategy = RsiStrategy()
print(f"✓ Strategy: {strategy.name}")
print(f"  RSI Oversold: {strategy.rsi_oversold}")
print(f"  RSI Overbought: {strategy.rsi_overbought}")
print(f"  Stop Loss: {strategy.stoploss:.1%}")
print(f"  Take Profit: {strategy.take_profit:.1%}")

# Run backtest
print("\n3. Running backtest...")
backtest = SimpleBacktest(
    strategy=strategy,
    initial_capital=10000.0,
    fee_pct=0.001,  # 0.1% trading fee
    position_size_pct=1.0  # Use 100% of capital
)

results = backtest.run(df)

# Print detailed results
backtest.print_results(results)

# Show sample trades
print("\nSample Trades (first 5):")
trades_df = backtest.get_trades_df()
if len(trades_df) > 0:
    print(trades_df[['entry_time', 'entry_price', 'exit_price', 'profit_pct', 'exit_reason']].head().to_string())

# Equity curve
print("\nEquity Curve (last 10 points):")
equity_curve = backtest.get_equity_curve()
print(equity_curve[['equity', 'cash']].tail(10).to_string())

print("\n" + "="*60)
print("✓ Backtest completed successfully!")
print("="*60)

# Interpretation
print("\nINTERPRETATION:")
if results['total_return'] > 0:
    print(f"✓ Strategy is PROFITABLE with {results['total_return']:.2%} return")
else:
    print(f"✗ Strategy LOST {results['total_return']:.2%}")

if results['win_rate'] > 0.5:
    print(f"✓ Good win rate: {results['win_rate']:.1%}")
elif results['win_rate'] > 0.4:
    print(f"⚠ Moderate win rate: {results['win_rate']:.1%}")
else:
    print(f"✗ Low win rate: {results['win_rate']:.1%}")

if results['profit_factor'] > 1.5:
    print(f"✓ Strong profit factor: {results['profit_factor']:.2f}")
elif results['profit_factor'] > 1.0:
    print(f"⚠ Modest profit factor: {results['profit_factor']:.2f}")
else:
    print(f"✗ Weak profit factor: {results['profit_factor']:.2f}")

print("\nReady for live paper trading!")
