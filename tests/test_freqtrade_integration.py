"""
Tests for FreqTrade Integration

Tests the FreqTrade bot adapter and integration with TradeAgent's
portfolio management and risk monitoring systems.

Run with: pytest tests/test_freqtrade_integration.py
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
import pandas as pd

# Check if FreqTrade is available
try:
    from core.freqtrade_bot import FreqTradeBotAdapter, FREQTRADE_AVAILABLE
except ImportError:
    FREQTRADE_AVAILABLE = False
    FreqTradeBotAdapter = None

from shared.risk_management.portfolio_manager import PortfolioManager
from shared.risk_management.risk_monitor import RiskMonitor
from monitoring.notifications import NotificationManager


class TestFreqTradeIntegration:
    """Test FreqTrade integration with TradeAgent"""

    @pytest.fixture
    def portfolio(self):
        """Create portfolio manager for testing"""
        return PortfolioManager(initial_capital=10000.0, mode='paper')

    @pytest.fixture
    def risk_monitor(self, portfolio):
        """Create risk monitor for testing"""
        config = {
            'max_open_positions': 5,
            'max_position_size_pct': 0.20
        }
        return RiskMonitor(portfolio, config)

    @pytest.fixture
    def notifier(self):
        """Create notification manager for testing"""
        return NotificationManager({'console_enabled': False})

    @pytest.fixture
    def config(self):
        """Create bot configuration for testing"""
        return {
            'exchange': 'binance',
            'symbols': ['BTC/USDT', 'ETH/USDT'],
            'freqtrade_strategy': 'SampleStrategy',
            'freqtrade_strategy_path': 'freqtrade_strategies',
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        }

    @pytest.mark.skipif(not FREQTRADE_AVAILABLE,
                       reason="FreqTrade not installed")
    def test_freqtrade_bot_initialization(self, portfolio, risk_monitor, notifier, config):
        """Test FreqTrade bot adapter initialization"""
        try:
            bot = FreqTradeBotAdapter(portfolio, risk_monitor, notifier, config)

            assert bot is not None
            assert bot.portfolio == portfolio
            assert bot.risk_monitor == risk_monitor
            assert bot.notifier == notifier
            assert bot.symbols == config['symbols']

        except ImportError as e:
            # Expected if FreqTrade not installed
            assert "FreqTrade is not installed" in str(e)

    @pytest.mark.skipif(not FREQTRADE_AVAILABLE,
                       reason="FreqTrade not installed")
    def test_execute_cycle_no_errors(self, portfolio, risk_monitor, notifier, config):
        """Test that execute_cycle runs without errors"""
        try:
            bot = FreqTradeBotAdapter(portfolio, risk_monitor, notifier, config)

            # Mock _get_market_data to return None (no data available)
            bot._get_market_data = Mock(return_value=None)

            # Should not raise any exceptions
            bot.execute_cycle()

        except ImportError:
            pytest.skip("FreqTrade not installed")

    @pytest.mark.skipif(not FREQTRADE_AVAILABLE,
                       reason="FreqTrade not installed")
    def test_freqtrade_config_building(self, portfolio, risk_monitor, notifier, config):
        """Test that FreqTrade configuration is built correctly"""
        try:
            bot = FreqTradeBotAdapter(portfolio, risk_monitor, notifier, config)

            ft_config = bot._build_freqtrade_config()

            assert ft_config is not None
            assert ft_config['dry_run'] == True  # Paper trading
            assert ft_config['stake_currency'] == 'USDT'
            assert ft_config['pair_whitelist'] == config['symbols']
            assert ft_config['exchange']['name'] == config['exchange']

        except ImportError:
            pytest.skip("FreqTrade not installed")

    def test_freqtrade_not_installed_error(self, portfolio, risk_monitor, notifier, config):
        """Test that appropriate error is raised when FreqTrade not installed"""
        if FREQTRADE_AVAILABLE:
            pytest.skip("FreqTrade is installed, cannot test error case")

        with pytest.raises(ImportError) as exc_info:
            # This should fail if FreqTrade not installed
            from core.freqtrade_bot import FreqTradeBotAdapter
            bot = FreqTradeBotAdapter(portfolio, risk_monitor, notifier, config)

        assert "FreqTrade" in str(exc_info.value) or "freqtrade" in str(exc_info.value)


class TestTradingEngineFreqTradeSupport:
    """Test TradingEngine support for FreqTrade bot selection"""

    def test_trading_engine_imports_freqtrade_adapter(self):
        """Test that TradingEngine can import FreqTrade adapter"""
        from core.trading_engine import FREQTRADE_ADAPTER_AVAILABLE

        # Should be True if freqtrade installed, False otherwise
        assert isinstance(FREQTRADE_ADAPTER_AVAILABLE, bool)

    def test_config_crypto_bot_type_custom(self):
        """Test TradingEngine with custom crypto bot"""
        from core.trading_engine import TradingEngine

        config = {
            'initial_capital': 10000.0,
            'mode': 'paper',
            'crypto_enabled': True,
            'crypto_bot_type': 'custom',
            'crypto': {
                'exchange': 'binance',
                'symbols': ['BTC/USDT'],
                'strategy': 'rsi'
            },
            'stock_enabled': False,
            'notifications': {'console_enabled': False}
        }

        engine = TradingEngine(config)
        success = engine.initialize()

        assert success == True
        assert engine.crypto_bot is not None
        assert engine.crypto_bot.__class__.__name__ == 'CryptoBot'

    @pytest.mark.skipif(not FREQTRADE_AVAILABLE,
                       reason="FreqTrade not installed")
    def test_config_crypto_bot_type_freqtrade(self):
        """Test TradingEngine with FreqTrade bot"""
        from core.trading_engine import TradingEngine

        config = {
            'initial_capital': 10000.0,
            'mode': 'paper',
            'crypto_enabled': True,
            'crypto_bot_type': 'freqtrade',
            'crypto': {
                'exchange': 'binance',
                'symbols': ['BTC/USDT'],
                'freqtrade_strategy': 'SampleStrategy',
                'freqtrade_strategy_path': 'freqtrade_strategies'
            },
            'stock_enabled': False,
            'notifications': {'console_enabled': False}
        }

        try:
            engine = TradingEngine(config)
            success = engine.initialize()

            assert success == True
            assert engine.crypto_bot is not None
            assert engine.crypto_bot.__class__.__name__ == 'FreqTradeBotAdapter'

        except ImportError:
            pytest.skip("FreqTrade not fully configured")

    def test_config_invalid_crypto_bot_type(self):
        """Test that invalid crypto_bot_type raises error"""
        from core.trading_engine import TradingEngine

        config = {
            'initial_capital': 10000.0,
            'mode': 'paper',
            'crypto_enabled': True,
            'crypto_bot_type': 'invalid_type',  # Invalid
            'crypto': {
                'exchange': 'binance',
                'symbols': ['BTC/USDT']
            },
            'stock_enabled': False,
            'notifications': {'console_enabled': False}
        }

        engine = TradingEngine(config)

        with pytest.raises(ValueError) as exc_info:
            engine.initialize()

        assert "crypto_bot_type" in str(exc_info.value).lower()


class TestFreqTradeStrategy:
    """Test FreqTrade strategy compatibility"""

    @pytest.mark.skipif(not FREQTRADE_AVAILABLE,
                       reason="FreqTrade not installed")
    def test_sample_strategy_import(self):
        """Test that SampleStrategy can be imported"""
        try:
            from freqtrade_strategies.sample_strategy import SampleStrategy

            strategy = SampleStrategy()
            assert strategy is not None
            assert hasattr(strategy, 'populate_indicators')
            assert hasattr(strategy, 'populate_entry_trend')
            assert hasattr(strategy, 'populate_exit_trend')

        except ImportError:
            pytest.skip("FreqTrade strategies not available")

    @pytest.mark.skipif(not FREQTRADE_AVAILABLE,
                       reason="FreqTrade not installed")
    def test_sample_strategy_indicators(self):
        """Test that SampleStrategy can populate indicators"""
        try:
            from freqtrade_strategies.sample_strategy import SampleStrategy
            import numpy as np

            strategy = SampleStrategy()

            # Create sample OHLCV data
            df = pd.DataFrame({
                'open': np.random.randn(100).cumsum() + 100,
                'high': np.random.randn(100).cumsum() + 102,
                'low': np.random.randn(100).cumsum() + 98,
                'close': np.random.randn(100).cumsum() + 100,
                'volume': np.random.randint(1000, 10000, 100),
            })

            # Populate indicators
            df = strategy.populate_indicators(df, {'pair': 'BTC/USDT'})

            # Check that indicators were added
            assert 'rsi' in df.columns
            assert 'volume_mean' in df.columns
            assert 'ema_20' in df.columns

        except ImportError:
            pytest.skip("FreqTrade strategies not available")


def test_freqtrade_config_file_exists():
    """Test that FreqTrade config file exists"""
    import os
    config_path = 'freqtrade_config/config.json'
    assert os.path.exists(config_path), f"FreqTrade config not found at {config_path}"


def test_freqtrade_strategies_directory_exists():
    """Test that FreqTrade strategies directory exists"""
    import os
    strategies_path = 'freqtrade_strategies'
    assert os.path.exists(strategies_path), f"FreqTrade strategies dir not found"


if __name__ == '__main__':
    # Run tests
    print("="*60)
    print("Running FreqTrade Integration Tests")
    print("="*60)

    if not FREQTRADE_AVAILABLE:
        print("\n⚠️  FreqTrade not installed - some tests will be skipped")
        print("Install with: pip install freqtrade ccxt\n")

    pytest.main([__file__, '-v'])
