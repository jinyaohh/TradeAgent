#!/usr/bin/env python3
"""Test Emergency Controls and Kill Switch"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.risk_management.portfolio_manager import PortfolioManager
from shared.risk_management.emergency_controls import EmergencyControls, TradingState

print("="*60)
print("Testing Emergency Controls and Kill Switch")
print("="*60)

# Create portfolio and controls
portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
controls = EmergencyControls({
    'max_daily_loss_pct': 0.05,
    'max_drawdown_pct': 0.15,
    'max_rapid_loss_pct': 0.03,
    'max_rapid_loss_minutes': 60
})

# Show initial configuration
controls.print_status()

# Open test positions
print("Opening test positions...")
portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.1, 'long')  # $5,000
portfolio.open_position('ETH/USDT', 'crypto', 3000.0, 1.0, 'long')   # $3,000
portfolio.open_position('AAPL', 'stock', 150.0, 10, 'long')          # $1,500
print(f"  Total positions: {len(portfolio.positions)}")
print(f"  Portfolio value: ${portfolio.get_total_value():,.2f}")

# Test 1: Normal state
print("\n" + "="*60)
print("TEST 1: Normal Trading State")
print("="*60)

print(f"\nCurrent state: {controls.state.value}")
print(f"Trading allowed: {controls.is_trading_allowed()}")

if controls.is_trading_allowed():
    print("  ✓ System allows trading")
else:
    print("  ✗ System blocks trading")

# Test 2: Pause and resume
print("\n" + "="*60)
print("TEST 2: Pause and Resume")
print("="*60)

print("\n2a) Pausing trading...")
success = controls.pause_trading("Manual pause for testing")
print(f"  Pause successful: {success}")
print(f"  State: {controls.state.value}")
print(f"  Trading allowed: {controls.is_trading_allowed()}")

print("\n2b) Resuming trading...")
success = controls.resume_trading("Test complete")
print(f"  Resume successful: {success}")
print(f"  State: {controls.state.value}")
print(f"  Trading allowed: {controls.is_trading_allowed()}")

# Test 3: Kill switch
print("\n" + "="*60)
print("TEST 3: Emergency Kill Switch")
print("="*60)

print("\n3a) Activating kill switch...")
controls.activate_kill_switch("Testing emergency stop functionality")

controls.print_status()

print(f"\nState: {controls.state.value}")
print(f"Trading allowed: {controls.is_trading_allowed()}")

print("\n3b) Try to trade during emergency stop...")
if not controls.is_trading_allowed():
    print("  ✓ Trading correctly blocked")

print("\n3c) Try to pause during emergency (should fail)...")
success = controls.pause_trading("Should not work")
print(f"  Pause successful: {success}")
if not success:
    print("  ✓ Correctly prevented pause during emergency")

print("\n3d) Deactivating kill switch...")
controls.deactivate_kill_switch("Emergency resolved, manual override")
controls.print_status()

# Test 4: Circuit breakers
print("\n" + "="*60)
print("TEST 4: Circuit Breakers")
print("="*60)

# Simulate large loss
print("\n4a) Simulating large portfolio loss (10%)...")
portfolio.update_prices({
    'BTC/USDT': 45000.0,  # -10% loss
    'ETH/USDT': 2700.0,   # -10% loss
    'AAPL': 135.0         # -10% loss
})

print(f"  Portfolio value: ${portfolio.get_total_value():,.2f}")
print(f"  Total loss: ${portfolio.get_total_pnl():,.2f}")
print(f"  Loss %: {(portfolio.get_total_value() / 10000 - 1):.2%}")

print("\n4b) Checking circuit breakers...")
triggered = controls.check_circuit_breakers(portfolio)
print(f"  Circuit breaker triggered: {triggered}")
print(f"  Current state: {controls.state.value}")

if triggered:
    controls.print_status()

# Test 5: Emergency liquidation
print("\n" + "="*60)
print("TEST 5: Emergency Liquidation")
print("="*60)

# Create fresh portfolio for liquidation test
liq_portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
liq_controls = EmergencyControls()

# Open positions
liq_portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.08, 'long')  # $4,000
liq_portfolio.open_position('ETH/USDT', 'crypto', 3000.0, 1.5, 'long')    # $4,500
liq_portfolio.open_position('AAPL', 'stock', 150.0, 5, 'long')            # $750

print(f"\nBefore liquidation:")
print(f"  Open positions: {len(liq_portfolio.positions)}")
print(f"  Portfolio value: ${liq_portfolio.get_total_value():,.2f}")

# Create some losers
liq_portfolio.update_prices({
    'BTC/USDT': 48000.0,  # -4% loss
    'ETH/USDT': 2850.0,   # -5% loss
    'AAPL': 152.0         # +1.3% profit
})

print(f"\nAfter price updates:")
for pos in liq_portfolio.positions.values():
    status = "LOSS" if pos.unrealized_pnl < 0 else "PROFIT"
    print(f"  {pos.symbol:12} ${pos.unrealized_pnl:>8,.2f} ({pos.unrealized_pnl_pct:>6.2%}) {status}")

print("\n5a) Emergency liquidation (losers only)...")
liq_controls.activate_kill_switch("Catastrophic loss detected")
closed_count = liq_controls.emergency_liquidate_positions(
    liq_portfolio,
    close_all=False,
    close_losers_only=True
)

print(f"\nAfter liquidation:")
print(f"  Positions closed: {closed_count}")
print(f"  Positions remaining: {len(liq_portfolio.positions)}")
print(f"  Cash: ${liq_portfolio.cash:,.2f}")

if liq_portfolio.positions:
    print(f"\n  Remaining positions:")
    for pos in liq_portfolio.positions.values():
        print(f"    {pos.symbol}: ${pos.unrealized_pnl:,.2f} ({pos.unrealized_pnl_pct:.2%})")

# Test 6: Rapid loss detection
print("\n" + "="*60)
print("TEST 6: Rapid Loss Detection")
print("="*60)

rapid_portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
rapid_controls = EmergencyControls()

rapid_portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.15, 'long')

print("\n6a) Tracking normal market movements...")
# Simulate gradual tracking
for i, price in enumerate([50000, 49800, 49600, 49400, 49200]):
    rapid_portfolio.update_prices({'BTC/USDT': price})
    rapid_controls._track_portfolio_value(rapid_portfolio.get_total_value())
    if i == 0:
        print(f"  Initial value: ${rapid_portfolio.get_total_value():,.2f}")

print(f"  Final value: ${rapid_portfolio.get_total_value():,.2f}")

rapid_loss = rapid_controls._calculate_rapid_loss()
print(f"  Rapid loss: {rapid_loss:.2%}")

print("\n6b) Checking circuit breakers...")
triggered = rapid_controls.check_circuit_breakers(rapid_portfolio)
print(f"  Circuit breaker triggered: {triggered}")

# Test 7: State transitions
print("\n" + "="*60)
print("TEST 7: State Transitions")
print("="*60)

state_portfolio = PortfolioManager(initial_capital=10000.0)
state_controls = EmergencyControls()

transitions = [
    ("Initial state", lambda: None, TradingState.ACTIVE),
    ("Pause", lambda: state_controls.pause_trading("Test"), TradingState.PAUSED),
    ("Resume", lambda: state_controls.resume_trading("Test"), TradingState.ACTIVE),
    ("Kill switch", lambda: state_controls.activate_kill_switch("Test"), TradingState.EMERGENCY_STOP),
    ("Deactivate", lambda: state_controls.deactivate_kill_switch("Test"), TradingState.ACTIVE),
]

print("\nTesting state transitions:")
for name, action, expected_state in transitions:
    if action:
        action()
    actual_state = state_controls.state
    match = "✓" if actual_state == expected_state else "✗"
    print(f"  {match} {name:20} -> {actual_state.value:20} (expected: {expected_state.value})")

# Test 8: Event history
print("\n" + "="*60)
print("TEST 8: Event History")
print("="*60)

print(f"\nTotal events recorded: {len(state_controls.events)}")
print("\nRecent events:")
for event in state_controls.get_recent_events(5):
    print(f"  [{event.severity:8}] {event.timestamp.strftime('%H:%M:%S')} - {event.message}")

# Final status
print("\n" + "="*60)
print("FINAL STATUS")
print("="*60)

controls.print_status()

print("\n" + "="*60)
print("✓ Emergency controls tests completed!")
print("="*60)

# Summary
print("\nSUMMARY:")
print("Emergency Controls provide:")
print("  ✓ Kill switch for immediate trading halt")
print("  ✓ Pause/resume for temporary stops")
print("  ✓ Circuit breakers (daily loss, drawdown, rapid loss)")
print("  ✓ Emergency position liquidation")
print("  ✓ State management with transitions")
print("  ✓ Event logging and audit trail")
print("  ✓ Rapid loss detection")
print("  ✓ Multiple severity levels")
