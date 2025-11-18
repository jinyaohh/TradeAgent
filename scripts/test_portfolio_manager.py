#!/usr/bin/env python3
"""Test Portfolio Manager"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime, timedelta
from shared.risk_management.portfolio_manager import PortfolioManager, AssetType, Position

print("="*60)
print("Testing Portfolio Manager")
print("="*60)

# Test 1: Basic portfolio operations
print("\n" + "="*60)
print("TEST 1: Basic Portfolio Operations")
print("="*60)

portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')

print(f"\nInitial State:")
print(f"  Initial Capital: ${portfolio.initial_capital:,.2f}")
print(f"  Cash: ${portfolio.cash:,.2f}")
print(f"  Total Value: ${portfolio.get_total_value():,.2f}")

# Open positions
print("\n1a) Opening crypto position (BTC)...")
btc_pos = portfolio.open_position(
    symbol='BTC/USDT',
    asset_type='crypto',
    entry_price=50000.0,
    quantity=0.1,
    side='long',
    stop_loss=48000.0,
    take_profit=55000.0,
    strategy_name='RSI Strategy',
    notes='Oversold bounce'
)
print(f"   Position ID: {btc_pos.position_id}")
print(f"   Cost: ${btc_pos.quantity * btc_pos.entry_price:,.2f}")
print(f"   Remaining cash: ${portfolio.cash:,.2f}")

print("\n1b) Opening stock position (AAPL)...")
aapl_pos = portfolio.open_position(
    symbol='AAPL',
    asset_type='stock',
    entry_price=150.0,
    quantity=10,
    side='long',
    stop_loss=145.0,
    take_profit=160.0,
    strategy_name='MA Crossover'
)
print(f"   Position ID: {aapl_pos.position_id}")
print(f"   Cost: ${aapl_pos.quantity * aapl_pos.entry_price:,.2f}")
print(f"   Remaining cash: ${portfolio.cash:,.2f}")

print("\n1c) Opening another crypto position (ETH)...")
eth_pos = portfolio.open_position(
    symbol='ETH/USDT',
    asset_type='crypto',
    entry_price=3000.0,
    quantity=1.0,
    side='long',
    strategy_name='Momentum'
)
print(f"   Position ID: {eth_pos.position_id}")
print(f"   Remaining cash: ${portfolio.cash:,.2f}")

# Test 2: Price updates and P&L
print("\n" + "="*60)
print("TEST 2: Price Updates and P&L Calculation")
print("="*60)

print("\nUpdating prices (simulating market movement)...")
portfolio.update_prices({
    'BTC/USDT': 52000.0,  # +4% profit
    'AAPL': 148.0,        # -1.33% loss
    'ETH/USDT': 3100.0    # +3.33% profit
})

print("\nPosition P&L:")
for pos_id, pos in portfolio.positions.items():
    print(f"  {pos.symbol:12} ${pos.unrealized_pnl:>8,.2f} ({pos.unrealized_pnl_pct:>6.2%})")

print(f"\nTotal Unrealized P&L: ${portfolio.get_unrealized_pnl():,.2f}")
print(f"Total Value: ${portfolio.get_total_value():,.2f}")

# Test 3: Closing positions
print("\n" + "="*60)
print("TEST 3: Closing Positions")
print("="*60)

print("\n3a) Closing BTC position at profit...")
closed_btc = portfolio.close_position(btc_pos.position_id, 52000.0, reason='take_profit')
print(f"   Realized P&L: ${closed_btc.realized_pnl:,.2f} ({closed_btc.realized_pnl_pct:.2%})")
print(f"   Cash after close: ${portfolio.cash:,.2f}")

print("\n3b) Closing AAPL position at loss...")
closed_aapl = portfolio.close_position(aapl_pos.position_id, 148.0, reason='stop_loss')
print(f"   Realized P&L: ${closed_aapl.realized_pnl:,.2f} ({closed_aapl.realized_pnl_pct:.2%})")
print(f"   Cash after close: ${portfolio.cash:,.2f}")

# Test 4: Portfolio metrics
print("\n" + "="*60)
print("TEST 4: Portfolio Metrics")
print("="*60)

portfolio.print_summary()

# Test 5: Query positions
print("\n" + "="*60)
print("TEST 5: Query Positions")
print("="*60)

print("\n5a) Get all crypto positions:")
crypto_positions = portfolio.get_positions_by_asset_type('crypto')
print(f"   Found {len(crypto_positions)} crypto position(s)")
for pos in crypto_positions:
    print(f"   - {pos.symbol}: {pos.quantity} @ ${pos.entry_price:,.2f}")

print("\n5b) Get all stock positions:")
stock_positions = portfolio.get_positions_by_asset_type('stock')
print(f"   Found {len(stock_positions)} stock position(s)")

print("\n5c) Get positions for ETH/USDT:")
eth_positions = portfolio.get_positions_by_symbol('ETH/USDT')
print(f"   Found {len(eth_positions)} ETH position(s)")

# Test 6: DataFrame export
print("\n" + "="*60)
print("TEST 6: DataFrame Export")
print("="*60)

print("\n6a) Open Positions DataFrame:")
open_df = portfolio.get_positions_df()
if not open_df.empty:
    cols = ['symbol', 'asset_type', 'quantity', 'entry_price',
            'current_price', 'unrealized_pnl', 'unrealized_pnl_pct']
    print(open_df[cols].to_string(index=False))
else:
    print("   No open positions")

print("\n6b) Closed Positions DataFrame:")
closed_df = portfolio.get_closed_positions_df()
if not closed_df.empty:
    cols = ['symbol', 'asset_type', 'entry_price', 'exit_price',
            'realized_pnl', 'realized_pnl_pct', 'exit_reason']
    print(closed_df[cols].to_string(index=False))
else:
    print("   No closed positions")

# Test 7: Edge cases
print("\n" + "="*60)
print("TEST 7: Edge Cases")
print("="*60)

print("\n7a) Try to open position with insufficient cash...")
try:
    portfolio.open_position(
        symbol='TSLA',
        asset_type='stock',
        entry_price=1000.0,
        quantity=100,  # Would cost $100,000
        side='long'
    )
    print("   ERROR: Should have raised exception!")
except ValueError as e:
    print(f"   ✓ Correctly rejected: {e}")

print("\n7b) Try to close non-existent position...")
try:
    portfolio.close_position('fake_position_id', 100.0)
    print("   ERROR: Should have raised exception!")
except ValueError as e:
    print(f"   ✓ Correctly rejected: {e}")

print("\n7c) Empty portfolio metrics:")
empty_portfolio = PortfolioManager(initial_capital=5000.0)
empty_metrics = empty_portfolio.get_portfolio_metrics()
print(f"   Total Value: ${empty_metrics['total_value']:,.2f}")
print(f"   Num Positions: {empty_metrics['num_positions']}")
print(f"   Win Rate: {empty_metrics['win_rate']:.1%}")

# Test 8: Complex scenario
print("\n" + "="*60)
print("TEST 8: Complex Multi-Asset Trading Scenario")
print("="*60)

# Create new portfolio
complex_portfolio = PortfolioManager(initial_capital=50000.0, mode='paper')

# Open multiple positions
positions = [
    ('BTC/USDT', 'crypto', 50000.0, 0.3),
    ('ETH/USDT', 'crypto', 3000.0, 2.0),
    ('AAPL', 'stock', 150.0, 50),
    ('GOOGL', 'stock', 140.0, 20),
    ('MSFT', 'stock', 380.0, 10),
]

print("\nOpening 5 positions across crypto and stocks...")
opened = []
for symbol, asset_type, price, qty in positions:
    try:
        pos = complex_portfolio.open_position(
            symbol=symbol,
            asset_type=asset_type,
            entry_price=price,
            quantity=qty,
            side='long'
        )
        opened.append(pos)
        print(f"  ✓ {symbol:12} {qty:>6.2f} @ ${price:>8,.2f} = ${qty*price:>10,.2f}")
    except ValueError as e:
        print(f"  ✗ {symbol:12} Failed: {e}")

# Simulate price changes
print("\nSimulating market movements...")
price_updates = {
    'BTC/USDT': 53000.0,   # +6%
    'ETH/USDT': 2900.0,    # -3.33%
    'AAPL': 155.0,         # +3.33%
    'GOOGL': 145.0,        # +3.57%
    'MSFT': 375.0,         # -1.32%
}
complex_portfolio.update_prices(price_updates)

# Show detailed summary
complex_portfolio.print_summary()

# Close some winners
print("\nClosing profitable positions...")
for pos in list(complex_portfolio.positions.values()):
    if pos.unrealized_pnl > 0:
        complex_portfolio.close_position(
            pos.position_id,
            pos.current_price,
            reason='profit_target'
        )
        print(f"  ✓ Closed {pos.symbol}: ${pos.realized_pnl:,.2f} profit")

# Final summary
print("\nFinal Portfolio State:")
complex_portfolio.print_summary()

print("\n" + "="*60)
print("✓ Portfolio manager tests completed!")
print("="*60)

# Summary
print("\nSUMMARY:")
print("Portfolio Manager provides:")
print("  ✓ Multi-asset position tracking (crypto, stocks, etc.)")
print("  ✓ Real-time P&L calculation (realized & unrealized)")
print("  ✓ Portfolio-level metrics and allocation")
print("  ✓ Position lifecycle management (open/update/close)")
print("  ✓ DataFrame export for analysis")
print("  ✓ Query positions by symbol/asset type")
print("  ✓ Comprehensive error handling")
print("  ✓ Cash and risk management")
