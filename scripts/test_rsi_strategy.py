#!/usr/bin/env python3
"""Test RSI Strategy"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptobot.data.mock_data import MockDataGenerator
from cryptobot.strategies.rsi_strategy import RsiStrategy

print("="*60)
print("Testing RSI Strategy")
print("="*60)

# Generate data with some volatility
print("\n1. Generating volatile mock data...")
generator = MockDataGenerator()
df = generator.generate_ohlcv(periods=500, volatility=0.03)
print(f"✓ Generated {len(df)} candles")

# Test strategy
print("\n2. Initializing RSI strategy...")
strategy = RsiStrategy()
print(f"✓ Strategy: {strategy}")
print(f"\nConfiguration:")
print(f"  RSI Period: {strategy.rsi_period}")
print(f"  RSI Oversold: {strategy.rsi_oversold}")
print(f"  RSI Overbought: {strategy.rsi_overbought}")
print(f"  Stop Loss: {strategy.stoploss:.1%}")
print(f"  Take Profit: {strategy.take_profit:.1%}")

# Analyze
print("\n3. Analyzing data and generating signals...")
df_analyzed = strategy.analyze(df)

buy_count = df_analyzed['buy_signal'].sum()
sell_count = df_analyzed['sell_signal'].sum()

print(f"✓ Buy signals: {buy_count}")
print(f"✓ Sell signals: {sell_count}")

# Show examples
if buy_count > 0:
    print("\n4. Buy signal examples (first 5):")
    buy_signals = df_analyzed[df_analyzed['buy_signal']][['close', 'rsi', 'volume', 'ema_20']]
    print(buy_signals.head().to_string())

if sell_count > 0:
    print("\n5. Sell signal examples (first 5):")
    sell_signals = df_analyzed[df_analyzed['sell_signal']][['close', 'rsi', 'volume', 'ema_20']]
    print(sell_signals.head().to_string())

print("\n" + "="*60)
print("✓ RSI Strategy test completed!")
print("Ready for backtesting!")
print("="*60)
