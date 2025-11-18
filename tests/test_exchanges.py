"""
Comprehensive Exchange Integration Tests

Tests all exchange connector components:
- Base connector framework
- Binance connector (with mock fallback)
- Alpaca connector (with mock fallback)
- Connection manager
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
import time

from exchanges import (
    BinanceConnector,
    AlpacaConnector,
    MockExchangeConnector,
    OrderSide,
    OrderType
)
from exchanges.connection_manager import ConnectionManager
from monitoring.logger import get_logger

logger = get_logger(__name__)


def test_mock_connector():
    """Test 1: Mock Exchange Connector"""
    print("\n" + "="*70)
    print("TEST 1: Mock Exchange Connector")
    print("="*70)

    try:
        config = {'initial_balance': 10000.0}
        connector = MockExchangeConnector(config, paper_trading=True)

        # Connect
        assert connector.connect(), "Connection should succeed"
        assert connector.connected, "Should be connected"

        # Get balance
        balance = connector.get_account_balance()
        assert 'USD' in balance, "Should have USD balance"
        assert balance['USD'] == 10000.0, "Should have correct initial balance"

        # Get current price
        price = connector.get_current_price('BTC/USDT')
        assert price is not None, "Should return price"
        assert price > 0, "Price should be positive"

        # Place buy order
        order = connector.place_order(
            symbol='BTC/USDT',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1
        )
        assert order is not None, "Order should be placed"
        assert order.symbol == 'BTC/USDT', "Order should have correct symbol"

        # Check balance after buy
        balance = connector.get_account_balance()
        assert balance['USD'] < 10000.0, "Cash should decrease after buy"
        assert balance.get('BTC', 0) > 0, "Should have BTC after buy"

        # Place sell order
        order = connector.place_order(
            symbol='BTC/USDT',
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=0.05
        )
        assert order is not None, "Sell order should be placed"

        # Get historical data
        df = connector.get_historical_data('BTC/USDT', '1h', 100)
        assert not df.empty, "Should return historical data"
        assert len(df) == 100, "Should return requested number of bars"

        # Disconnect
        connector.disconnect()
        assert not connector.connected, "Should be disconnected"

        print(f"\n✅ TEST 1 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        raise


def test_binance_connector():
    """Test 2: Binance Connector (with mock fallback)"""
    print("\n" + "="*70)
    print("TEST 2: Binance Connector")
    print("="*70)

    try:
        config = {
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'testnet': True,
            'initial_balance': 10000.0  # For mock mode
        }

        connector = BinanceConnector(config, paper_trading=True)

        # Connect
        success = connector.connect()
        assert success, "Connection should succeed"

        # Get balance
        balance = connector.get_account_balance()
        assert balance is not None, "Should return balance"
        assert isinstance(balance, dict), "Balance should be dictionary"

        # Get current price
        price = connector.get_current_price('BTC/USDT')
        if price:
            assert price > 0, "Price should be positive"
            print(f"  BTC/USDT Price: ${price:,.2f}")

        # Get historical data
        df = connector.get_historical_data('BTC/USDT', '1h', 10)
        assert not df.empty, "Should return historical data"
        print(f"  Historical data: {len(df)} bars")

        # Disconnect
        connector.disconnect()

        print(f"\n✅ TEST 2 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        raise


def test_alpaca_connector():
    """Test 3: Alpaca Connector (with mock fallback)"""
    print("\n" + "="*70)
    print("TEST 3: Alpaca Connector")
    print("="*70)

    try:
        config = {
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'initial_balance': 10000.0  # For mock mode
        }

        connector = AlpacaConnector(config, paper_trading=True)

        # Connect
        success = connector.connect()
        assert success, "Connection should succeed"

        # Get balance
        balance = connector.get_account_balance()
        assert balance is not None, "Should return balance"
        assert isinstance(balance, dict), "Balance should be dictionary"

        # Check if market is open
        is_open = connector.is_market_open()
        print(f"  Market open: {is_open}")

        # Get current price
        price = connector.get_current_price('AAPL')
        if price:
            assert price > 0, "Price should be positive"
            print(f"  AAPL Price: ${price:.2f}")

        # Get historical data
        df = connector.get_historical_data('AAPL', '1Hour', 10)
        assert not df.empty, "Should return historical data"
        print(f"  Historical data: {len(df)} bars")

        # Disconnect
        connector.disconnect()

        print(f"\n✅ TEST 3 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        raise


def test_connection_manager():
    """Test 4: Connection Manager"""
    print("\n" + "="*70)
    print("TEST 4: Connection Manager")
    print("="*70)

    try:
        manager = ConnectionManager({})

        # Add connectors
        success = manager.add_connector(
            'binance',
            'binance',
            {'api_key': 'test', 'api_secret': 'test', 'initial_balance': 10000.0},
            paper_trading=True
        )
        assert success, "Should add Binance connector"

        success = manager.add_connector(
            'alpaca',
            'alpaca',
            {'api_key': 'test', 'api_secret': 'test', 'initial_balance': 10000.0},
            paper_trading=True
        )
        assert success, "Should add Alpaca connector"

        # Connect all
        success = manager.connect_all()
        assert success, "All connectors should connect"

        # Get connector
        binance = manager.get_connector('binance')
        assert binance is not None, "Should get Binance connector"

        alpaca = manager.get_connector('alpaca')
        assert alpaca is not None, "Should get Alpaca connector"

        # Get health status
        health = manager.get_health_status()
        assert 'binance' in health, "Should have Binance health status"
        assert 'alpaca' in health, "Should have Alpaca health status"
        print(f"  Health status: {len(health)} connectors")

        # Get all balances
        balances = manager.get_all_balances()
        assert 'binance' in balances, "Should have Binance balance"
        assert 'alpaca' in balances, "Should have Alpaca balance"
        print(f"  Balances: {len(balances)} connectors")

        # Check connection status
        all_connected = manager.is_all_connected()
        assert all_connected, "All connectors should be connected"

        # Disconnect all
        manager.disconnect_all()

        print(f"\n✅ TEST 4 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        raise


def test_order_validation():
    """Test 5: Order Validation"""
    print("\n" + "="*70)
    print("TEST 5: Order Validation")
    print("="*70)

    try:
        config = {'initial_balance': 1000.0}
        connector = MockExchangeConnector(config, paper_trading=True)
        connector.connect()

        # Test 1: Valid buy order
        is_valid, reason = connector.validate_order('BTC/USDT', OrderSide.BUY, 0.01, 45000.0)
        assert is_valid, f"Valid buy order should pass: {reason}"

        # Test 2: Invalid quantity (zero)
        is_valid, reason = connector.validate_order('BTC/USDT', OrderSide.BUY, 0, 45000.0)
        assert not is_valid, "Zero quantity should fail"

        # Test 3: Invalid quantity (negative)
        is_valid, reason = connector.validate_order('BTC/USDT', OrderSide.BUY, -1, 45000.0)
        assert not is_valid, "Negative quantity should fail"

        # Test 4: Insufficient cash
        is_valid, reason = connector.validate_order('BTC/USDT', OrderSide.BUY, 1.0, 45000.0)
        assert not is_valid, "Insufficient cash should fail"
        print(f"  Correctly rejected order: {reason}")

        # Test 5: Valid sell order (after buying)
        connector.place_order('BTC/USDT', OrderSide.BUY, OrderType.MARKET, 0.01)
        is_valid, reason = connector.validate_order('BTC/USDT', OrderSide.SELL, 0.005, None)
        assert is_valid, "Valid sell order should pass"

        # Test 6: Insufficient asset to sell
        is_valid, reason = connector.validate_order('BTC/USDT', OrderSide.SELL, 1.0, None)
        assert not is_valid, "Insufficient BTC should fail"
        print(f"  Correctly rejected order: {reason}")

        connector.disconnect()

        print(f"\n✅ TEST 5 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        raise


def test_health_monitoring():
    """Test 6: Health Monitoring"""
    print("\n" + "="*70)
    print("TEST 6: Health Monitoring")
    print("="*70)

    try:
        manager = ConnectionManager({})

        # Add connector
        manager.add_connector(
            'binance',
            'binance',
            {'api_key': 'test', 'api_secret': 'test', 'initial_balance': 10000.0},
            paper_trading=True
        )

        # Connect
        manager.connect_all()

        # Start health monitoring
        manager.start_health_monitoring(interval=2)
        print("  Health monitoring started (2s interval)")

        # Wait for a few health checks
        time.sleep(5)

        # Get health status
        health = manager.get_health_status()
        assert 'binance' in health, "Should have health status"
        assert health['binance']['last_check'] is not None, "Should have last check time"
        print(f"  Last check: {health['binance']['last_check']}")

        # Stop monitoring
        manager.stop_health_monitoring()
        print("  Health monitoring stopped")

        # Disconnect
        manager.disconnect_all()

        print(f"\n✅ TEST 6 PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        raise


def run_all_tests():
    """Run all exchange tests"""
    print("\n" + "="*70)
    print("EXCHANGE INTEGRATION TEST SUITE")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results_summary = []
    test_start = datetime.now()

    try:
        # Test 1: Mock Connector
        test_mock_connector()
        results_summary.append(("Mock Connector", True))

        # Test 2: Binance Connector
        test_binance_connector()
        results_summary.append(("Binance Connector", True))

        # Test 3: Alpaca Connector
        test_alpaca_connector()
        results_summary.append(("Alpaca Connector", True))

        # Test 4: Connection Manager
        test_connection_manager()
        results_summary.append(("Connection Manager", True))

        # Test 5: Order Validation
        test_order_validation()
        results_summary.append(("Order Validation", True))

        # Test 6: Health Monitoring
        test_health_monitoring()
        results_summary.append(("Health Monitoring", True))

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        results_summary.append(("Test Suite", False))

    # Print summary
    elapsed = (datetime.now() - test_start).total_seconds()
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results_summary if result)
    total = len(results_summary)

    for test_name, result in results_summary:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Duration: {elapsed:.1f} seconds")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Exchange system is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
