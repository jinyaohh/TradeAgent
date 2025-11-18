"""
Integration Test for Trading Engine

Tests the complete trading system end-to-end:
- Trading engine initialization
- Crypto and stock bot execution
- Risk management integration
- Notification system
- Portfolio management
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.trading_engine import TradingEngine, EngineState
from monitoring.logger import get_logger

logger = get_logger(__name__)


def test_engine_initialization():
    """Test 1: Engine initialization"""
    print("\n" + "="*60)
    print("TEST 1: Trading Engine Initialization")
    print("="*60)

    config = {
        'initial_capital': 10000.0,
        'mode': 'paper',
        'crypto_enabled': True,
        'stock_enabled': True,
        'monitor_interval': 10,
        'crypto_interval': 15,
        'stock_interval': 15,
        'notifications': {
            'console_enabled': True,
            'telegram_enabled': False,
            'email_enabled': False
        },
        'risk': {
            'max_risk_per_trade': 0.02,
            'max_open_positions': 5,
            'max_position_size_pct': 0.20,
            'max_daily_loss_pct': 0.05,
            'max_drawdown_pct': 0.15,
            'min_cash_reserve_pct': 0.10
        },
        'crypto': {
            'exchange': 'binance',
            'symbols': ['BTC/USDT', 'ETH/USDT'],
            'strategy': 'rsi',
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        },
        'stock': {
            'broker': 'alpaca',
            'symbols': ['AAPL', 'GOOGL'],
            'strategy': 'rsi',
            'rsi_period': 14,
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'stop_loss_pct': 0.015,
            'take_profit_pct': 0.03
        }
    }

    try:
        engine = TradingEngine(config)
        assert engine.state == EngineState.STOPPED, "Engine should start in STOPPED state"

        # Initialize
        result = engine.initialize()
        assert result == True, "Engine initialization should succeed"
        assert engine.portfolio_manager is not None, "Portfolio manager should be initialized"
        assert engine.risk_monitor is not None, "Risk monitor should be initialized"
        assert engine.notification_manager is not None, "Notification manager should be initialized"
        assert engine.crypto_bot is not None, "Crypto bot should be initialized"
        assert engine.stock_bot is not None, "Stock bot should be initialized"

        print("✅ TEST 1 PASSED: Engine initialized successfully")
        return engine

    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        raise


def test_engine_start_stop(engine):
    """Test 2: Engine start and stop"""
    print("\n" + "="*60)
    print("TEST 2: Engine Start/Stop")
    print("="*60)

    try:
        # Start engine
        result = engine.start()
        assert result == True, "Engine should start successfully"
        assert engine.state == EngineState.RUNNING, "Engine should be in RUNNING state"

        # Check threads
        time.sleep(2)  # Give threads time to start
        assert engine.monitor_thread is not None, "Monitor thread should exist"
        assert engine.monitor_thread.is_alive(), "Monitor thread should be running"

        if engine.config.get('crypto_enabled'):
            assert engine.crypto_thread is not None, "Crypto thread should exist"
            assert engine.crypto_thread.is_alive(), "Crypto thread should be running"

        if engine.config.get('stock_enabled'):
            assert engine.stock_thread is not None, "Stock thread should exist"
            assert engine.stock_thread.is_alive(), "Stock thread should be running"

        print("✅ Engine started successfully with all threads running")

        # Let it run for a bit
        print("\nRunning engine for 20 seconds...")
        time.sleep(20)

        # Stop engine
        print("\nStopping engine...")
        result = engine.stop()
        assert result == True, "Engine should stop successfully"
        assert engine.state == EngineState.STOPPED, "Engine should be in STOPPED state"

        print("✅ TEST 2 PASSED: Engine started and stopped successfully")
        return True

    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        engine.stop()
        raise


def test_engine_pause_resume(engine):
    """Test 3: Engine pause and resume"""
    print("\n" + "="*60)
    print("TEST 3: Engine Pause/Resume")
    print("="*60)

    try:
        # Start engine
        engine.start()
        time.sleep(3)

        # Pause
        result = engine.pause()
        assert result == True, "Engine should pause successfully"
        assert engine.state == EngineState.PAUSED, "Engine should be in PAUSED state"
        print("✅ Engine paused")

        time.sleep(3)

        # Resume
        result = engine.resume()
        assert result == True, "Engine should resume successfully"
        assert engine.state == EngineState.RUNNING, "Engine should be in RUNNING state"
        print("✅ Engine resumed")

        time.sleep(3)

        # Stop
        engine.stop()

        print("✅ TEST 3 PASSED: Pause/resume works correctly")
        return True

    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        engine.stop()
        raise


def test_portfolio_integration(engine):
    """Test 4: Portfolio management integration"""
    print("\n" + "="*60)
    print("TEST 4: Portfolio Management Integration")
    print("="*60)

    try:
        # Start engine
        engine.start()

        # Let bots run and potentially open positions
        print("\nRunning for 30 seconds to allow trading activity...")
        time.sleep(30)

        # Check portfolio state
        status = engine.get_status()
        print(f"\n📊 Portfolio Status:")
        print(f"   Portfolio Value: ${status['portfolio_value']:,.2f}")
        print(f"   Total P&L: ${status['total_pnl']:,.2f}")
        print(f"   Open Positions: {status['open_positions']}")
        print(f"   Total Trades: {status['total_trades']}")

        # Get detailed portfolio metrics
        if engine.portfolio_manager:
            metrics = engine.portfolio_manager.get_portfolio_metrics()
            print(f"\n📈 Detailed Metrics:")
            print(f"   Cash: ${metrics['cash']:,.2f}")
            print(f"   Invested: ${metrics['total_invested']:,.2f}")
            print(f"   Winning Trades: {metrics['winning_trades']}")
            print(f"   Losing Trades: {metrics['losing_trades']}")
            if metrics['num_closed_trades'] > 0:
                print(f"   Win Rate: {metrics['winning_trades'] / metrics['num_closed_trades'] * 100:.1f}%")

        # Stop engine
        engine.stop()

        print("\n✅ TEST 4 PASSED: Portfolio integration working")
        return True

    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        engine.stop()
        raise


def test_risk_management(engine):
    """Test 5: Risk management integration"""
    print("\n" + "="*60)
    print("TEST 5: Risk Management Integration")
    print("="*60)

    try:
        # Start engine
        engine.start()

        # Let it run
        print("\nRunning for 25 seconds...")
        time.sleep(25)

        # Check risk metrics
        if engine.risk_monitor:
            risk_level, alerts = engine.risk_monitor.check_all_risks()
            print(f"\n⚠️  Risk Status:")
            print(f"   Risk Level: {risk_level.value.upper()}")
            print(f"   Active Alerts: {len(alerts)}")

            if alerts:
                print("\n   Alerts:")
                for alert in alerts:
                    print(f"   - {alert['message']}")
            else:
                print("   No risk alerts ✅")

            # Get detailed risk report
            report = engine.risk_monitor.get_risk_report()
            print(f"\n📊 Risk Report:")
            print(f"   Overall Risk Level: {report['overall_risk_level'].upper()}")
            print(f"   Trading Allowed: {report['trading_allowed']}")
            print(f"   Current Positions: {report['position_limits']['current_positions']}")
            print(f"   Max Positions: {report['position_limits']['max_positions']}")
            if report['risk_metrics']:
                print(f"   Risk Metrics Available: {len(report['risk_metrics'])} metrics")

        # Stop engine
        engine.stop()

        print("\n✅ TEST 5 PASSED: Risk management working correctly")
        return True

    except Exception as e:
        print(f"❌ TEST 5 FAILED: {e}")
        engine.stop()
        raise


def test_bot_execution():
    """Test 6: Individual bot execution"""
    print("\n" + "="*60)
    print("TEST 6: Bot Execution")
    print("="*60)

    try:
        from shared.risk_management.portfolio_manager import PortfolioManager
        from shared.risk_management.risk_monitor import RiskMonitor
        from monitoring.notifications import NotificationManager
        from core.crypto_bot import CryptoBot
        from core.stock_bot import StockBot

        # Create components
        portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
        risk_monitor = RiskMonitor(portfolio, {})
        notifier = NotificationManager({'console_enabled': True})

        # Test crypto bot
        print("\n🪙 Testing Crypto Bot...")
        crypto_config = {
            'symbols': ['BTC/USDT'],
            'strategy': 'rsi',
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        }
        crypto_bot = CryptoBot(portfolio, risk_monitor, notifier, crypto_config)

        # Execute a few cycles
        for i in range(3):
            print(f"  Cycle {i+1}...")
            crypto_bot.execute_cycle()
            time.sleep(2)

        print("✅ Crypto bot executed successfully")

        # Test stock bot
        print("\n📈 Testing Stock Bot...")
        stock_config = {
            'symbols': ['AAPL'],
            'strategy': 'rsi',
            'rsi_period': 14,
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'stop_loss_pct': 0.015,
            'take_profit_pct': 0.03
        }
        stock_bot = StockBot(portfolio, risk_monitor, notifier, stock_config)

        # Execute a few cycles
        for i in range(3):
            print(f"  Cycle {i+1}...")
            stock_bot.execute_cycle()
            time.sleep(2)

        print("✅ Stock bot executed successfully")

        # Print final portfolio state
        print("\n📊 Final Portfolio State:")
        portfolio.print_summary()

        print("\n✅ TEST 6 PASSED: Both bots executed successfully")
        return True

    except Exception as e:
        print(f"❌ TEST 6 FAILED: {e}")
        raise


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("TRADEAGENT INTEGRATION TEST SUITE")
    print("="*70)
    print(f"Testing complete trading system integration...")
    print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []
    start_time = time.time()

    try:
        # Test 1: Initialization
        engine = test_engine_initialization()
        results.append(("Initialization", True))

        # Test 2: Start/Stop
        test_engine_start_stop(engine)
        results.append(("Start/Stop", True))

        # Test 3: Pause/Resume
        test_engine_pause_resume(engine)
        results.append(("Pause/Resume", True))

        # Test 4: Portfolio Integration
        test_portfolio_integration(engine)
        results.append(("Portfolio Integration", True))

        # Test 5: Risk Management
        test_risk_management(engine)
        results.append(("Risk Management", True))

        # Test 6: Bot Execution
        test_bot_execution()
        results.append(("Bot Execution", True))

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        results.append(("Test Suite", False))

    # Print summary
    elapsed = time.time() - start_time
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Duration: {elapsed:.1f} seconds")
    print(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
