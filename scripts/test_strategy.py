#!/usr/bin/env python3
"""
Test trading strategy
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptobot.data.mock_data import get_sample_data
from cryptobot.strategies.base_strategy import SimpleStrategy

print("="*60)
print("Testing Trading Strategy")
print("="*60)

# Create sample data
print("\n1. Generating mock data...")
df = get_sample_data(periods=200, timeframe='1h')
print(f"✓ Generated {len(df)} candles")

# Test simple strategy
print("\n2. Initializing strategy...")
strategy = SimpleStrategy()
print(f"✓ Strategy: {strategy}")

# Analyze data
print("\n3. Analyzing data and generating signals...")
df_analyzed = strategy.analyze(df)

buy_count = df_analyzed['buy_signal'].sum()
sell_count = df_analyzed['sell_signal'].sum()

print(f"✓ Buy signals: {buy_count}")
print(f"✓ Sell signals: {sell_count}")

# Show signal details
if buy_count > 0:
    print("\n4. Buy signal examples:")
    buy_signals = df_analyzed[df_analyzed['buy_signal']][['close', 'rsi', 'sma_20']].head(3)
    print(buy_signals.to_string())

if sell_count > 0:
    print("\n5. Sell signal examples:")
    sell_signals = df_analyzed[df_analyzed['sell_signal']][['close', 'rsi', 'sma_20']].head(3)
    print(sell_signals.to_string())

print("\n" + "="*60)
print("✓ Strategy test completed successfully!")
print("="*60)
