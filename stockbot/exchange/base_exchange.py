"""
Base Exchange Interface for Stock Trading

Defines the standard interface that all stock broker implementations must follow.
Similar to crypto exchange but adapted for stock-specific features.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from enum import Enum


class OrderType(Enum):
    """Order types for stock trading"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


class TimeInForce(Enum):
    """Time in force options"""
    DAY = "day"          # Good for day
    GTC = "gtc"          # Good til canceled
    IOC = "ioc"          # Immediate or cancel
    FOK = "fok"          # Fill or kill


class BaseStockExchange(ABC):
    """
    Abstract base class for stock broker implementations.

    All stock broker connectors must inherit from this class and implement
    the required methods.
    """

    def __init__(self, config: Dict):
        """
        Initialize exchange

        Args:
            config: Exchange configuration dictionary
        """
        self.config = config
        self.exchange_id = config.get('exchange_id', 'unknown')
        self.name = self.__class__.__name__

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker and verify credentials

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def fetch_quote(self, symbol: str) -> Dict:
        """
        Fetch current quote (bid/ask/last) for a symbol

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dictionary with quote data:
            {
                'symbol': str,
                'bid': float,
                'ask': float,
                'last': float,
                'bid_size': int,
                'ask_size': int,
                'timestamp': datetime
            }
        """
        pass

    @abstractmethod
    def fetch_bars(self, symbol: str, timeframe: str = '1Hour',
                   start: Optional[str] = None, end: Optional[str] = None,
                   limit: int = 100) -> pd.DataFrame:
        """
        Fetch historical bar (OHLCV) data

        Args:
            symbol: Stock ticker symbol
            timeframe: Bar timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            limit: Maximum number of bars

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass

    @abstractmethod
    def create_order(self, symbol: str, qty: float, side: str,
                    order_type: str = 'market', limit_price: Optional[float] = None,
                    stop_price: Optional[float] = None,
                    time_in_force: str = 'day') -> Dict:
        """
        Create an order

        Args:
            symbol: Stock ticker symbol
            qty: Number of shares
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop', 'stop_limit'
            limit_price: Price for limit orders
            stop_price: Price for stop orders
            time_in_force: 'day', 'gtc', 'ioc', 'fok'

        Returns:
            Order dictionary with id, status, etc.
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successfully canceled
        """
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Dict:
        """
        Get order details

        Args:
            order_id: Order ID

        Returns:
            Order dictionary
        """
        pass

    @abstractmethod
    def get_account(self) -> Dict:
        """
        Get account information

        Returns:
            Dictionary with account details:
            {
                'cash': float,
                'buying_power': float,
                'portfolio_value': float,
                'equity': float
            }
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """
        Get all current positions

        Returns:
            List of position dictionaries
        """
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get position for a specific symbol

        Args:
            symbol: Stock ticker symbol

        Returns:
            Position dictionary or None if no position
        """
        pass

    @abstractmethod
    def close_position(self, symbol: str) -> bool:
        """
        Close a position (market order for full quantity)

        Args:
            symbol: Stock ticker symbol

        Returns:
            True if successfully closed
        """
        pass

    # Helper methods

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate stock symbol format

        Args:
            symbol: Stock ticker

        Returns:
            True if valid
        """
        # Basic validation - all caps, alphanumeric
        return symbol.isalpha() and symbol.isupper() and len(symbol) <= 5

    def calculate_shares(self, capital: float, price: float) -> int:
        """
        Calculate number of shares that can be bought

        Args:
            capital: Available capital
            price: Stock price

        Returns:
            Number of whole shares
        """
        return int(capital / price)

    def get_commission(self, qty: float, price: float) -> float:
        """
        Calculate commission (if any)

        Args:
            qty: Number of shares
            price: Price per share

        Returns:
            Commission amount
        """
        # Most modern brokers are commission-free
        return self.config.get('fees', {}).get('commission', 0.0)

    def __repr__(self) -> str:
        return f"{self.name}(exchange_id='{self.exchange_id}')"
