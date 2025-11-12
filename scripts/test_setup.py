#!/usr/bin/env python3
"""
Test script to verify Phase 1 setup is working correctly

Tests:
1. Configuration loading
2. Logging system
3. Directory structure
4. Import paths
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from config.config_loader import Config, get_config
        print("✓ Config loader imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config_loader: {e}")
        return False

    try:
        from monitoring.logger import get_logger, log_trade
        print("✓ Logger imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import logger: {e}")
        return False

    return True


def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")

    try:
        from config.config_loader import Config

        config = Config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Trading mode: {config.trading.mode}")
        print(f"  - Crypto enabled: {config.trading.crypto_enabled}")
        print(f"  - Stocks enabled: {config.trading.stocks_enabled}")
        print(f"  - Max risk per trade: {config.risk.max_risk_per_trade}")
        print(f"  - Max positions: {config.risk.max_positions}")
        print(f"  - Log level: {config.system.log_level}")

        # Test validation
        assert config.trading.mode in ['paper', 'live'], "Invalid trading mode"
        assert 0 < config.risk.max_risk_per_trade <= 0.10, "Invalid risk per trade"
        print("✓ Configuration validation passed")

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logging():
    """Test logging system"""
    print("\nTesting logging system...")

    try:
        from monitoring.logger import get_logger, get_trade_logger, log_trade

        # Test regular logger
        logger = get_logger(__name__)
        logger.debug("Debug message test")
        logger.info("Info message test")
        logger.warning("Warning message test")
        print("✓ Regular logging working")

        # Test trade logger
        log_trade(
            symbol='TEST/USDT',
            side='buy',
            quantity=1.0,
            price=100.0,
            trade_id='test-001',
            strategy='test_strategy'
        )
        print("✓ Trade logging working")

        # Check log files were created
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            print(f"✓ Log directory created with {len(log_files)} log file(s)")
        else:
            print("⚠ Log directory not found")

        return True

    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_directory_structure():
    """Test that all required directories exist"""
    print("\nTesting directory structure...")

    required_dirs = [
        'config',
        'stockbot',
        'stockbot/exchange',
        'stockbot/strategies',
        'shared',
        'shared/risk_management',
        'shared/portfolio',
        'shared/indicators',
        'shared/notifications',
        'backtest',
        'monitoring',
        'tests',
        'scripts',
        'logs',
        'data'
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - MISSING")
            all_exist = False

    return all_exist


def test_config_files():
    """Test that all config files exist"""
    print("\nTesting configuration files...")

    required_files = [
        'requirements.txt',
        '.gitignore',
        '.env.example',
        'README.md',
        'ARCHITECTURE.md',
        'IMPLEMENTATION_PLAN.md',
        'WORKFLOW.md',
        'TASK_BREAKDOWN.md',
        'config/config.yaml',
        'config/risk.yaml',
        'config/exchanges.yaml',
        'config/strategies.yaml',
        'config/config_loader.py'
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False

    return all_exist


def main():
    """Run all tests"""
    print("="*60)
    print("TradeAgent Phase 1 Setup Test")
    print("="*60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Directory Structure", test_directory_structure()))
    results.append(("Config Files", test_config_files()))
    results.append(("Configuration", test_configuration()))
    results.append(("Logging", test_logging()))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 All tests passed! Phase 1 setup is complete.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Run: pip install -r requirements.txt")
        print("3. Proceed to Phase 2: Crypto Module Integration")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
