"""
FreqTrade Strategies for TradeAgent

This directory contains FreqTrade-compatible strategies (IStrategy interface).

These strategies can be used with the FreqTradeBotAdapter to leverage
FreqTrade's battle-tested trading engine while maintaining integration
with TradeAgent's portfolio management and risk monitoring.

Directory Structure:
- sample_strategy.py - Example RSI strategy following FreqTrade's IStrategy
- __init__.py - This file

Usage:
1. Install FreqTrade: pip install freqtrade ccxt
2. Set crypto_bot_type: 'freqtrade' in config/trading.yaml
3. Set freqtrade_strategy: 'SampleStrategy' to use strategies from this directory

Creating New Strategies:
- Inherit from freqtrade.strategy.IStrategy
- Implement populate_indicators()
- Implement populate_entry_trend()
- Implement populate_exit_trend()
- See FreqTrade docs: https://www.freqtrade.io/en/stable/strategy-customization/

Note: Strategies here follow FreqTrade conventions and can be used directly
with FreqTrade CLI or via TradeAgent's FreqTradeBotAdapter.
"""

__version__ = '1.0.0'
