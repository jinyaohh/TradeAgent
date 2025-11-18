#!/usr/bin/env python3
"""Test Notification System"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.notifications import NotificationManager, NotificationLevel

print("="*60)
print("Testing Notification System")
print("="*60)

# Create manager (console only for testing)
manager = NotificationManager({
    'console_enabled': True,
    'telegram_enabled': False,
    'email_enabled': False
})

# Test different notification types
print("\n1. Trade Execution:")
manager.trade_executed('BTC/USDT', 'buy', 0.1, 50000.0, 'RSI Strategy')

print("\n2. Position Closed (Profit):")
manager.position_closed('ETH/USDT', 150.50, 0.05, 'take_profit')

print("\n3. Position Closed (Loss):")
manager.position_closed('AAPL', -45.20, -0.03, 'stop_loss')

print("\n4. Risk Limit Breach:")
manager.risk_limit_breach('daily_loss', 0.06, 0.05)

print("\n5. System Error:")
manager.system_error('API Connection', 'Failed to connect to exchange')

print("\n6. Daily Summary:")
manager.daily_summary(10500.0, 250.0, 0.025, 5, 3)

print("\n7. Emergency Stop:")
manager.emergency_stop('Circuit breaker triggered - daily loss limit')

print("\n" + "="*60)
print("✓ Notification system test complete!")
print(f"Total notifications in history: {len(manager.history)}")
print("="*60)
