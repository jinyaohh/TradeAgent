"""
Configuration Management System for TradeAgent

This module handles loading and validating configuration from multiple sources:
- Environment variables (.env)
- YAML configuration files
- Default values

Usage:
    from config.config_loader import Config
    config = Config()
    print(config.trading.mode)
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


@dataclass
class TradingConfig:
    """Trading-specific configuration"""
    mode: str = "paper"  # paper, live
    crypto_enabled: bool = True
    stocks_enabled: bool = True
    initial_capital: float = 10000.0


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_risk_per_trade: float = 0.02  # 2%
    max_portfolio_risk: float = 0.10  # 10%
    max_positions: int = 5
    daily_loss_limit: float = 0.05  # 5%
    max_drawdown: float = 0.15  # 15%
    position_size_method: str = "risk_pct"  # risk_pct, fixed_pct, kelly
    min_position_size: float = 100.0


@dataclass
class ExchangeConfig:
    """Exchange/Broker configuration"""
    # Binance
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet: bool = True

    # Alpaca
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None
    alpaca_paper: bool = True
    alpaca_base_url: str = "https://paper-api.alpaca.markets"


@dataclass
class NotificationConfig:
    """Notification configuration"""
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    email_enabled: bool = False
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    email_password: Optional[str] = None

    webhook_enabled: bool = False
    webhook_url: Optional[str] = None


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///tradeagent.db"


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    port: int = 8501
    host: str = "localhost"


@dataclass
class SystemConfig:
    """System-level configuration"""
    environment: str = "development"  # development, staging, production
    log_level: str = "INFO"
    timezone: str = "America/New_York"
    debug_mode: bool = False
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds


class Config:
    """
    Main configuration class that loads and validates all configuration.

    Configuration priority (highest to lowest):
    1. Environment variables
    2. YAML configuration files
    3. Default values
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_dir: Path to configuration directory. If None, uses default.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent

        self.config_dir = Path(config_dir)

        # Load configuration from files and environment
        self._load_config()

    def _load_config(self):
        """Load configuration from all sources"""
        # Load YAML files
        yaml_config = self._load_yaml_configs()

        # Initialize configuration objects with defaults, then override
        self.system = self._load_system_config(yaml_config)
        self.trading = self._load_trading_config(yaml_config)
        self.risk = self._load_risk_config(yaml_config)
        self.exchanges = self._load_exchange_config(yaml_config)
        self.notifications = self._load_notification_config(yaml_config)
        self.database = self._load_database_config(yaml_config)
        self.dashboard = self._load_dashboard_config(yaml_config)

        # Validate configuration
        self._validate_config()

    def _load_yaml_configs(self) -> Dict[str, Any]:
        """Load all YAML configuration files"""
        yaml_files = ['config.yaml', 'exchanges.yaml', 'risk.yaml', 'strategies.yaml']
        merged_config = {}

        for yaml_file in yaml_files:
            file_path = self.config_dir / yaml_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        config_data = yaml.safe_load(f) or {}
                        merged_config.update(config_data)
                except Exception as e:
                    print(f"Warning: Failed to load {yaml_file}: {e}")

        return merged_config

    def _load_system_config(self, yaml_config: Dict) -> SystemConfig:
        """Load system configuration"""
        system_data = yaml_config.get('system', {})

        return SystemConfig(
            environment=os.getenv('ENVIRONMENT', system_data.get('environment', 'development')),
            log_level=os.getenv('LOG_LEVEL', system_data.get('log_level', 'INFO')),
            timezone=os.getenv('TZ', system_data.get('timezone', 'America/New_York')),
            debug_mode=os.getenv('DEBUG_MODE', str(system_data.get('debug_mode', False))).lower() == 'true',
            cache_enabled=os.getenv('CACHE_ENABLED', str(system_data.get('cache_enabled', True))).lower() == 'true',
            cache_ttl=int(os.getenv('CACHE_TTL', system_data.get('cache_ttl', 300)))
        )

    def _load_trading_config(self, yaml_config: Dict) -> TradingConfig:
        """Load trading configuration"""
        trading_data = yaml_config.get('trading', {})

        return TradingConfig(
            mode=os.getenv('TRADING_MODE', trading_data.get('mode', 'paper')),
            crypto_enabled=os.getenv('CRYPTO_ENABLED', str(trading_data.get('crypto_enabled', True))).lower() == 'true',
            stocks_enabled=os.getenv('STOCKS_ENABLED', str(trading_data.get('stocks_enabled', True))).lower() == 'true',
            initial_capital=float(os.getenv('INITIAL_CAPITAL', trading_data.get('initial_capital', 10000.0)))
        )

    def _load_risk_config(self, yaml_config: Dict) -> RiskConfig:
        """Load risk management configuration"""
        risk_data = yaml_config.get('risk', {})

        return RiskConfig(
            max_risk_per_trade=float(os.getenv('MAX_RISK_PER_TRADE', risk_data.get('max_risk_per_trade', 0.02))),
            max_portfolio_risk=float(os.getenv('MAX_PORTFOLIO_RISK', risk_data.get('max_portfolio_risk', 0.10))),
            max_positions=int(os.getenv('MAX_POSITIONS', risk_data.get('max_positions', 5))),
            daily_loss_limit=float(os.getenv('DAILY_LOSS_LIMIT', risk_data.get('daily_loss_limit', 0.05))),
            max_drawdown=float(os.getenv('MAX_DRAWDOWN', risk_data.get('max_drawdown', 0.15))),
            position_size_method=os.getenv('POSITION_SIZE_METHOD', risk_data.get('position_size_method', 'risk_pct')),
            min_position_size=float(os.getenv('MIN_POSITION_SIZE', risk_data.get('min_position_size', 100.0)))
        )

    def _load_exchange_config(self, yaml_config: Dict) -> ExchangeConfig:
        """Load exchange configuration"""
        exchange_data = yaml_config.get('exchanges', {})

        return ExchangeConfig(
            # Binance
            binance_api_key=os.getenv('BINANCE_API_KEY'),
            binance_api_secret=os.getenv('BINANCE_API_SECRET'),
            binance_testnet=os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',

            # Alpaca
            alpaca_api_key=os.getenv('ALPACA_API_KEY'),
            alpaca_api_secret=os.getenv('ALPACA_API_SECRET'),
            alpaca_paper=os.getenv('ALPACA_PAPER', 'true').lower() == 'true',
            alpaca_base_url=os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        )

    def _load_notification_config(self, yaml_config: Dict) -> NotificationConfig:
        """Load notification configuration"""
        notif_data = yaml_config.get('notifications', {})

        return NotificationConfig(
            telegram_enabled=os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true',
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),

            email_enabled=os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            email_smtp_host=os.getenv('EMAIL_SMTP_HOST'),
            email_smtp_port=int(os.getenv('EMAIL_SMTP_PORT', 587)),
            email_from=os.getenv('EMAIL_FROM'),
            email_to=os.getenv('EMAIL_TO'),
            email_password=os.getenv('EMAIL_PASSWORD'),

            webhook_enabled=os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true',
            webhook_url=os.getenv('WEBHOOK_URL')
        )

    def _load_database_config(self, yaml_config: Dict) -> DatabaseConfig:
        """Load database configuration"""
        db_data = yaml_config.get('database', {})

        return DatabaseConfig(
            url=os.getenv('DATABASE_URL', db_data.get('url', 'sqlite:///tradeagent.db'))
        )

    def _load_dashboard_config(self, yaml_config: Dict) -> DashboardConfig:
        """Load dashboard configuration"""
        dashboard_data = yaml_config.get('dashboard', {})

        return DashboardConfig(
            port=int(os.getenv('DASHBOARD_PORT', dashboard_data.get('port', 8501))),
            host=os.getenv('DASHBOARD_HOST', dashboard_data.get('host', 'localhost'))
        )

    def _validate_config(self):
        """Validate configuration values"""
        errors = []

        # Validate trading mode
        if self.trading.mode not in ['paper', 'live']:
            errors.append(f"Invalid trading mode: {self.trading.mode}. Must be 'paper' or 'live'")

        # Validate risk parameters
        if not 0 < self.risk.max_risk_per_trade <= 0.10:
            errors.append(f"max_risk_per_trade must be between 0 and 0.10, got {self.risk.max_risk_per_trade}")

        if not 0 < self.risk.max_portfolio_risk <= 0.50:
            errors.append(f"max_portfolio_risk must be between 0 and 0.50, got {self.risk.max_portfolio_risk}")

        if self.risk.max_positions < 1:
            errors.append(f"max_positions must be at least 1, got {self.risk.max_positions}")

        # Validate API keys if in live mode
        if self.trading.mode == 'live':
            if self.trading.crypto_enabled:
                if not self.exchanges.binance_api_key or not self.exchanges.binance_api_secret:
                    errors.append("Binance API keys required for live crypto trading")

            if self.trading.stocks_enabled:
                if not self.exchanges.alpaca_api_key or not self.exchanges.alpaca_api_secret:
                    errors.append("Alpaca API keys required for live stock trading")

        # Raise exception if there are validation errors
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

    def is_live_mode(self) -> bool:
        """Check if trading in live mode"""
        return self.trading.mode == 'live'

    def is_paper_mode(self) -> bool:
        """Check if trading in paper mode"""
        return self.trading.mode == 'paper'

    def get_active_exchanges(self) -> list:
        """Get list of active exchanges"""
        exchanges = []
        if self.trading.crypto_enabled:
            exchanges.append('binance')
        if self.trading.stocks_enabled:
            exchanges.append('alpaca')
        return exchanges

    def __repr__(self) -> str:
        """String representation of configuration"""
        return (
            f"TradeAgentConfig(\n"
            f"  mode={self.trading.mode},\n"
            f"  crypto={self.trading.crypto_enabled},\n"
            f"  stocks={self.trading.stocks_enabled},\n"
            f"  max_risk={self.risk.max_risk_per_trade},\n"
            f"  max_positions={self.risk.max_positions}\n"
            f")"
        )


# Global configuration instance
_config_instance = None


def get_config(reload: bool = False) -> Config:
    """
    Get the global configuration instance (singleton pattern).

    Args:
        reload: If True, reload configuration from files

    Returns:
        Config instance
    """
    global _config_instance

    if _config_instance is None or reload:
        _config_instance = Config()

    return _config_instance


if __name__ == "__main__":
    # Test configuration loading
    config = Config()
    print(config)
    print(f"\nActive exchanges: {config.get_active_exchanges()}")
    print(f"Is paper mode: {config.is_paper_mode()}")
