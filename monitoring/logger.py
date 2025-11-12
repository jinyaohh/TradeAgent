"""
Centralized Logging System for TradeAgent

Provides structured logging with:
- Console output with colors
- Rotating file logs
- Separate error logs
- Trade-specific logging
- JSON structured logging (optional)

Usage:
    from monitoring.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Starting trading bot")
"""

import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
import colorlog


class TradeFormatter(logging.Formatter):
    """Custom formatter for trade-related logs"""

    def format(self, record):
        # Add custom fields if they exist
        if hasattr(record, 'trade_id'):
            record.msg = f"[Trade:{record.trade_id}] {record.msg}"
        if hasattr(record, 'symbol'):
            record.msg = f"[{record.symbol}] {record.msg}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add custom fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'lineno', 'module', 'msecs', 'message',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value

        return json.dumps(log_data)


class LoggerManager:
    """Manages logger configuration and setup"""

    _instance = None
    _loggers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # Get log level from environment
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

        # Setup root logger
        self._setup_root_logger()

    def _setup_root_logger(self):
        """Configure the root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))

        # Remove existing handlers
        root_logger.handlers.clear()

    def _get_console_handler(self) -> logging.Handler:
        """Create console handler with colored output"""
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.log_level))

        # Color formatter
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s %(levelname)-8s%(reset)s '
            '%(blue)s[%(name)s]%(reset)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )

        console_handler.setFormatter(color_formatter)
        return console_handler

    def _get_file_handler(self, filename: str, max_bytes: int = 10485760,
                         backup_count: int = 30) -> logging.Handler:
        """
        Create rotating file handler

        Args:
            filename: Name of log file
            max_bytes: Maximum file size before rotation (default 10MB)
            backup_count: Number of backup files to keep (default 30)
        """
        filepath = self.log_dir / filename
        file_handler = RotatingFileHandler(
            filepath,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.log_level))

        # Standard formatter for files
        file_formatter = TradeFormatter(
            '%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        return file_handler

    def _get_error_file_handler(self) -> logging.Handler:
        """Create handler for error logs only"""
        filepath = self.log_dir / 'error.log'
        error_handler = RotatingFileHandler(
            filepath,
            maxBytes=10485760,  # 10MB
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)

        error_formatter = TradeFormatter(
            '%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s\n'
            'File: %(pathname)s:%(lineno)d\n'
            'Function: %(funcName)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        return error_handler

    def _get_trade_file_handler(self) -> logging.Handler:
        """Create handler specifically for trade logs"""
        filepath = self.log_dir / 'trades.log'
        trade_handler = TimedRotatingFileHandler(
            filepath,
            when='midnight',
            interval=1,
            backupCount=365,  # Keep 1 year of trade logs
            encoding='utf-8'
        )
        trade_handler.setLevel(logging.INFO)

        # Use JSON formatter for trade logs for easy parsing
        trade_handler.setFormatter(JSONFormatter())
        return trade_handler

    def _get_json_file_handler(self) -> logging.Handler:
        """Create handler for JSON structured logs"""
        filepath = self.log_dir / 'app.json.log'
        json_handler = RotatingFileHandler(
            filepath,
            maxBytes=10485760,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        json_handler.setLevel(getattr(logging, self.log_level))
        json_handler.setFormatter(JSONFormatter())
        return json_handler

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.log_level))
        logger.propagate = False  # Don't propagate to root

        # Add handlers
        logger.addHandler(self._get_console_handler())
        logger.addHandler(self._get_file_handler('app.log'))
        logger.addHandler(self._get_error_file_handler())

        # Add JSON handler if enabled
        if os.getenv('JSON_LOGGING', 'false').lower() == 'true':
            logger.addHandler(self._get_json_file_handler())

        self._loggers[name] = logger
        return logger

    def get_trade_logger(self) -> logging.Logger:
        """Get logger specifically for trade logs"""
        if 'trade' in self._loggers:
            return self._loggers['trade']

        logger = logging.getLogger('trade')
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # Only add trade-specific handler
        logger.addHandler(self._get_trade_file_handler())

        self._loggers['trade'] = logger
        return logger


# Global logger manager instance
_logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (use __name__ from calling module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return _logger_manager.get_logger(name)


def get_trade_logger() -> logging.Logger:
    """
    Get the trade logger for logging trade-specific events

    Returns:
        Trade logger instance

    Example:
        >>> trade_logger = get_trade_logger()
        >>> trade_logger.info("Trade executed", extra={
        ...     'trade_id': '123',
        ...     'symbol': 'BTC/USDT',
        ...     'side': 'buy',
        ...     'price': 50000,
        ...     'quantity': 0.1
        ... })
    """
    return _logger_manager.get_trade_logger()


def log_trade(symbol: str, side: str, quantity: float, price: float,
              trade_id: Optional[str] = None, **kwargs):
    """
    Convenience function to log a trade

    Args:
        symbol: Trading symbol
        side: Trade side (buy/sell)
        quantity: Trade quantity
        price: Trade price
        trade_id: Optional trade ID
        **kwargs: Additional trade details
    """
    trade_logger = get_trade_logger()

    trade_data = {
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'price': price,
        'value': quantity * price,
        'timestamp': datetime.utcnow().isoformat()
    }

    if trade_id:
        trade_data['trade_id'] = trade_id

    trade_data.update(kwargs)

    trade_logger.info(f"Trade executed: {side.upper()} {quantity} {symbol} @ {price}",
                     extra=trade_data)


def log_error_with_context(logger: logging.Logger, message: str, **context):
    """
    Log an error with additional context

    Args:
        logger: Logger instance
        message: Error message
        **context: Additional context to log
    """
    logger.error(message, extra=context, exc_info=True)


class LogContext:
    """Context manager for adding context to log messages"""

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self):
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        self.old_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# Example usage
if __name__ == "__main__":
    # Test logging
    logger = get_logger(__name__)

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Test trade logging
    log_trade(
        symbol='BTC/USDT',
        side='buy',
        quantity=0.1,
        price=50000,
        trade_id='test-123',
        strategy='rsi_strategy',
        reason='oversold'
    )

    # Test context logging
    with LogContext(logger, symbol='ETH/USDT', strategy='ma_crossover'):
        logger.info("Entry signal detected")
        logger.info("Order placed")

    logger.info("Logging test completed")
