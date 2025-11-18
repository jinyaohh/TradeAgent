#!/usr/bin/env python3
"""Test Limits Enforcer"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.risk_management.portfolio_manager import PortfolioManager, AssetType
from shared.risk_management.limits_enforcer import LimitsEnforcer, LimitType

print("="*60)
print("Testing Limits Enforcer")
print("="*60)

# Create portfolio and enforcer with strict limits
portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
enforcer = LimitsEnforcer({
    'max_open_positions': 3,
    'max_position_size_pct': 0.25,     # 25% max per position
    'max_single_asset_pct': 0.30,      # 30% max in single asset
    'max_crypto_pct': 0.50,            # 50% max in crypto
    'max_stock_pct': 0.70,             # 70% max in stocks
    'max_daily_loss_pct': 0.05,        # 5% max daily loss
    'max_drawdown_pct': 0.15,          # 15% max drawdown
    'min_cash_reserve_pct': 0.20       # 20% min cash
})

# Display configuration
enforcer.print_limits()

# Test 1: Normal trade (should pass)
print("="*60)
print("TEST 1: Normal Trade (Should Pass)")
print("="*60)

print("\nAttempting to open BTC position ($2,000)...")
allowed, violations = enforcer.check_trade(portfolio, 'BTC/USDT', 2000.0, 'crypto')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
print(f"  Violations: {len(violations)}")

if allowed:
    pos = portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.04, 'long')
    print(f"  Position opened: {pos.position_id}")

# Test 2: Position size too large (should fail)
print("\n" + "="*60)
print("TEST 2: Position Size Too Large (Should Fail)")
print("="*60)

print("\nAttempting to open large ETH position ($3,000 = 30%)...")
allowed, violations = enforcer.check_trade(portfolio, 'ETH/USDT', 3000.0, 'crypto')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
print(f"  Violations: {len(violations)}")
for v in violations:
    print(f"    - {v}")

# Test 3: Acceptable positions
print("\n" + "="*60)
print("TEST 3: Open More Positions (Fill to Max)")
print("="*60)

print("\nOpening AAPL position ($1,500)...")
allowed, violations = enforcer.check_trade(portfolio, 'AAPL', 1500.0, 'stock')
if allowed:
    portfolio.open_position('AAPL', 'stock', 150.0, 10, 'long')
    print("  ✓ AAPL position opened")

print("\nOpening GOOGL position ($700)...")
allowed, violations = enforcer.check_trade(portfolio, 'GOOGL', 700.0, 'stock')
if allowed:
    portfolio.open_position('GOOGL', 'stock', 140.0, 5, 'long')
    print("  ✓ GOOGL position opened")

portfolio.print_summary()

# Test 4: Max positions reached (should fail)
print("\n" + "="*60)
print("TEST 4: Max Positions Reached (Should Fail)")
print("="*60)

print("\nAttempting to open 4th position (MSFT)...")
allowed, violations = enforcer.check_trade(portfolio, 'MSFT', 1000.0, 'stock')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
print(f"  Violations: {len(violations)}")
for v in violations:
    print(f"    - {v}")

# Test 5: Concentration limits
print("\n" + "="*60)
print("TEST 5: Concentration Limits")
print("="*60)

# Close one position to make room
print("\nClosing GOOGL to make room...")
googl_positions = portfolio.get_positions_by_symbol('GOOGL')
if googl_positions:
    portfolio.close_position(googl_positions[0].position_id, 145.0, 'manual')

print("\n5a) Try to add more BTC (would exceed single asset limit)...")
allowed, violations = enforcer.check_trade(portfolio, 'BTC/USDT', 2000.0, 'crypto')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
for v in violations:
    print(f"    - {v}")

print("\n5b) Try to add too much crypto (would exceed crypto limit)...")
allowed, violations = enforcer.check_trade(portfolio, 'SOL/USDT', 3500.0, 'crypto')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
for v in violations:
    print(f"    - {v}")

# Test 6: Cash reserve limit
print("\n" + "="*60)
print("TEST 6: Cash Reserve Limit")
print("="*60)

print(f"\nCurrent cash: ${portfolio.cash:,.2f}")
print(f"Min required (20%): ${portfolio.get_total_value() * 0.20:,.2f}")

print("\nTrying to use too much cash (would go below 20% reserve)...")
max_allowed_spend = portfolio.cash - (portfolio.get_total_value() * 0.20)
print(f"  Max allowed spend: ${max_allowed_spend:,.2f}")

allowed, violations = enforcer.check_trade(portfolio, 'NVDA', max_allowed_spend + 500, 'stock')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
for v in violations:
    print(f"    - {v}")

# Test 7: Daily loss limit
print("\n" + "="*60)
print("TEST 7: Daily Loss Limit")
print("="*60)

print("\nSimulating losses to trigger daily loss limit...")

# Update prices to create losses
portfolio.update_prices({
    'BTC/USDT': 47500.0,  # -5% loss
    'AAPL': 142.5,        # -5% loss
})

print(f"Current portfolio value: ${portfolio.get_total_value():,.2f}")
print(f"Daily start value: ${enforcer.daily_start_value:,.2f}")
daily_pnl_pct = (portfolio.get_total_value() - enforcer.daily_start_value) / enforcer.daily_start_value
print(f"Daily P&L: {daily_pnl_pct:.2%}")

print("\nTrying to open new position after daily loss limit...")
allowed, violations = enforcer.check_trade(portfolio, 'AMD', 500.0, 'stock')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
for v in violations:
    print(f"    - {v}")

# Test 8: Portfolio health check
print("\n" + "="*60)
print("TEST 8: Portfolio Health Check")
print("="*60)

health, violations = enforcer.check_portfolio_health(portfolio)
print(f"\nHealth Status: {health.upper()}")
print(f"Violations: {len(violations)}")
for v in violations:
    print(f"  - {v}")

# Test 9: Get available position size
print("\n" + "="*60)
print("TEST 9: Get Available Position Size")
print("="*60)

# Reset to healthy state
healthy_portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
healthy_enforcer = LimitsEnforcer({
    'max_position_size_pct': 0.25,
    'max_single_asset_pct': 0.30,
    'max_crypto_pct': 0.50,
    'min_cash_reserve_pct': 0.20
})

print(f"\nPortfolio value: ${healthy_portfolio.get_total_value():,.2f}")
print("\nMaximum allowed position sizes:")

for symbol, asset_type in [('BTC/USDT', 'crypto'), ('AAPL', 'stock'), ('ETH/USDT', 'crypto')]:
    max_size = healthy_enforcer.get_available_position_size(healthy_portfolio, symbol, asset_type)
    print(f"  {symbol:12} ({asset_type:6}): ${max_size:>8,.2f}")

# Open a crypto position
healthy_portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.04, 'long')

print("\nAfter opening BTC position ($2,000):")
for symbol, asset_type in [('BTC/USDT', 'crypto'), ('AAPL', 'stock'), ('ETH/USDT', 'crypto')]:
    max_size = healthy_enforcer.get_available_position_size(healthy_portfolio, symbol, asset_type)
    print(f"  {symbol:12} ({asset_type:6}): ${max_size:>8,.2f}")

# Test 10: Drawdown limit
print("\n" + "="*60)
print("TEST 10: Maximum Drawdown Limit")
print("="*60)

# Create portfolio with positions
dd_portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
dd_enforcer = LimitsEnforcer({'max_drawdown_pct': 0.15})

# Open position
dd_portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.1, 'long')

# Set peak
dd_enforcer.peak_portfolio_value = dd_portfolio.get_total_value()
print(f"\nPeak portfolio value: ${dd_enforcer.peak_portfolio_value:,.2f}")

# Simulate large drawdown
dd_portfolio.update_prices({'BTC/USDT': 42500.0})  # -15% loss
current_value = dd_portfolio.get_total_value()
drawdown = (current_value - dd_enforcer.peak_portfolio_value) / dd_enforcer.peak_portfolio_value

print(f"Current portfolio value: ${current_value:,.2f}")
print(f"Drawdown: {drawdown:.2%}")

print("\nTrying to trade with max drawdown exceeded...")
allowed, violations = dd_enforcer.check_trade(dd_portfolio, 'ETH/USDT', 500.0, 'crypto')
print(f"  Result: {'✓ ALLOWED' if allowed else '✗ BLOCKED'}")
for v in violations:
    print(f"    - {v}")

print("\n" + "="*60)
print("✓ Limits enforcer tests completed!")
print("="*60)

# Summary
print("\nSUMMARY:")
print("Limits Enforcer provides:")
print("  ✓ Position count limits (max positions)")
print("  ✓ Position size limits (% of portfolio)")
print("  ✓ Concentration limits (single asset, asset class)")
print("  ✓ Daily loss limits (% of portfolio)")
print("  ✓ Drawdown limits (% from peak)")
print("  ✓ Cash reserve requirements")
print("  ✓ Available position size calculator")
print("  ✓ Portfolio health monitoring")
print("  ✓ Multiple severity levels (warning, error, critical)")
