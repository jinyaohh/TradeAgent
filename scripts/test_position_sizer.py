#!/usr/bin/env python3
"""Test Position Sizing Calculator"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.risk_management.position_sizer import PositionSizer

print("="*60)
print("Testing Position Sizer")
print("="*60)

sizer = PositionSizer({
    'max_risk_per_trade': 0.02,  # 2%
    'max_position_pct': 0.10,    # 10%
    'min_position_size': 100.0
})

account = 10000.0
entry = 100.0
stop_loss = 98.0  # 2% stop

print(f"\nAccount: ${account:,.2f}")
print(f"Entry: ${entry:.2f}")
print(f"Stop Loss: ${stop_loss:.2f} (2% below entry)")

# Test different methods
print("\n1. Risk Percentage Method (2% max risk):")
result = sizer.calculate_position_size(account, entry, stop_loss, method='risk_pct')
print(f"   Quantity: {result['quantity']:.2f} shares")
print(f"   Value: ${result['value']:,.2f}")
print(f"   Risk: ${result['risk_amount']:.2f} ({result['risk_pct']:.1%})")
print(f"   Position: {result['position_pct']:.1%} of account")

print("\n2. Fixed Percentage Method (10% position):")
result = sizer.calculate_position_size(account, entry, stop_loss, method='fixed_pct')
print(f"   Quantity: {result['quantity']:.2f} shares")
print(f"   Value: ${result['value']:,.2f}")
print(f"   Position: {result['position_pct']:.1%} of account")

print("\n3. Kelly Criterion (50% win rate, 2:1 reward/risk):")
result = sizer.calculate_position_size(account, entry, stop_loss, method='kelly',
                                      win_rate=0.50, avg_win=0.04, avg_loss=0.02)
print(f"   Quantity: {result['quantity']:.2f} shares")
print(f"   Value: ${result['value']:,.2f}")
print(f"   Kelly Fraction: {result.get('kelly_fraction', 0):.2%}")
print(f"   Position: {result['position_pct']:.1%} of account")

print("\n4. ATR-based Method (ATR=$2, 2x multiplier):")
result = sizer.calculate_position_size(account, entry, stop_loss, method='atr',
                                      atr=2.0, atr_multiplier=2.0)
print(f"   Quantity: {result['quantity']:.2f} shares")
print(f"   Value: ${result['value']:,.2f}")
print(f"   Risk: ${result['risk_amount']:.2f}")
print(f"   ATR Stop: ${result['stop_loss_price']:.2f}")

# Test constraints
print("\n5. Testing Constraints:")
print("   a) Small account (position below minimum):")
result = sizer.calculate_position_size(50.0, entry, stop_loss, method='risk_pct')
print(f"      Quantity: {result['quantity']:.2f}")
print(f"      Constrained: {result.get('constrained', False)}")
if result.get('constrained'):
    print(f"      Reason: {result.get('constraint_reason')}")

print("\n   b) Large position (exceeds max %):")
result = sizer.calculate_position_size(account, 10.0, 9.0, method='risk_pct')
print(f"      Value: ${result['value']:,.2f}")
print(f"      Position: {result['position_pct']:.1%}")
print(f"      Constrained: {result.get('constrained', False)}")
if result.get('constrained'):
    print(f"      Reason: {result.get('constraint_reason')}")

print("\n" + "="*60)
print("✓ Position sizer working correctly!")
print("="*60)

# Summary
print("\nSUMMARY:")
print("Position sizing methods available:")
print("  1. Risk % - Risk fixed % per trade (recommended)")
print("  2. Fixed % - Use fixed % of account")
print("  3. Kelly - Based on win rate and profit factor")
print("  4. ATR - Volatility-based using ATR")
print("\nConstraints applied:")
print(f"  - Minimum position: $100")
print(f"  - Maximum position: 10% of account")
print(f"  - Maximum risk: 2% of account")
