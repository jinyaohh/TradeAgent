"""
Base Exchange Interface for Cryptocurrency Trading

Provides abstract base class that all crypto exchange implementations must follow.
Based on FreqTrade's exchange architecture but simplified.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from enum import Enum


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_LIMIT = "stop_loss_limit"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status"""
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class BaseExchange(ABC):
    """
    Abstract base class for cryptocurrency exchanges.

    All exchange implementations must inherit from this class and implement
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
        Connect to the exchange

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> Dict:
        """
        Fetch current ticker data for a symbol

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')

        Returns:
            Dictionary containing ticker data:
            {
                'symbol': str,
                'last': float,
                'bid': float,
                'ask': float,
                'volume': float,
                'timestamp': int
            }
        """
        pass

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h',
                    since: Optional[int] = None, limit: int = 500) -> pd.DataFrame:
        """
        Fetch OHLCV (candlestick) data

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            since: Timestamp in milliseconds to fetch data from
            limit: Maximum number of candles to fetch

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass

    @abstractmethod
    def create_order(self, symbol: str, order_type: OrderType, side: OrderSide,
                    amount: float, price: Optional[float] = None,
                    params: Optional[Dict] = None) -> Dict:
        """
        Create an order on the exchange

        Args:
            symbol: Trading pair symbol
            order_type: Type of order (market, limit, etc.)
            side: Buy or sell
            amount: Amount to trade
            price: Price for limit orders
            params: Additional exchange-specific parameters

        Returns:
            Order dictionary:
            {
                'id': str,
                'symbol': str,
                'type': str,
                'side': str,
                'amount': float,
                'price': float,
                'status': str,
                'timestamp': int
            }
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an open order

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol

        Returns:
            Canceled order dictionary
        """
        pass

    @abstractmethod
    def fetch_order(self, order_id: str, symbol: str) -> Dict:
        """
        Fetch order details

        Args:
            order_id: Order ID
            symbol: Trading pair symbol

        Returns:
            Order dictionary
        """
        pass

    @abstractmethod
    def fetch_balance(self) -> Dict:
        """
        Fetch account balance

        Returns:
            Balance dictionary:
            {
                'total': {'BTC': float, 'USDT': float, ...},
                'free': {'BTC': float, 'USDT': float, ...},
                'used': {'BTC': float, 'USDT': float, ...}
            }
        """
        pass

    @abstractmethod
    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Fetch all open orders

        Args:
            symbol: Optional symbol to filter orders

        Returns:
            List of order dictionaries
        """
        pass

    @abstractmethod
    def fetch_closed_orders(self, symbol: Optional[str] = None,
                           since: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        Fetch closed/filled orders

        Args:
            symbol: Optional symbol to filter orders
            since: Timestamp to fetch from
            limit: Maximum number of orders

        Returns:
            List of order dictionaries
        """
        pass

    @abstractmethod
    def fetch_my_trades(self, symbol: Optional[str] = None,
                       since: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        Fetch user's trade history

        Args:
            symbol: Optional symbol to filter trades
            since: Timestamp to fetch from
            limit: Maximum number of trades

        Returns:
            List of trade dictionaries
        """
        pass

    # Helper methods (implemented in base class)

    def get_fee(self, symbol: str, order_type: OrderType, side: OrderSide,
                amount: float, price: float) -> Dict:
        """
        Calculate trading fee

        Args:
            symbol: Trading pair
            order_type: Order type
            side: Buy or sell
            amount: Trade amount
            price: Trade price

        Returns:
            Fee dictionary with 'cost' and 'currency'
        """
        fees = self.config.get('fees', {})

        if order_type == OrderType.MARKET:
            fee_rate = fees.get('taker', 0.001)  # Default 0.1%
        else:
            fee_rate = fees.get('maker', 0.001)  # Default 0.1%

        cost = amount * price * fee_rate

        # Extract quote currency (e.g., USDT from BTC/USDT)
        quote_currency = symbol.split('/')[1] if '/' in symbol else 'USDT'

        return {
            'cost': cost,
            'currency': quote_currency,
            'rate': fee_rate
        }

    def amount_to_precision(self, symbol: str, amount: float) -> float:
        """
        Round amount to exchange precision

        Args:
            symbol: Trading pair
            amount: Amount to round

        Returns:
            Rounded amount
        """
        # Default to 8 decimal places for crypto
        precision = self.config.get('precision', {}).get(symbol, 8)
        return round(amount, precision)

    def price_to_precision(self, symbol: str, price: float) -> float:
        """
        Round price to exchange precision

        Args:
            symbol: Trading pair
            price: Price to round

        Returns:
            Rounded price
        """
        # Default to 2 decimal places for prices
        precision = self.config.get('price_precision', {}).get(symbol, 2)
        return round(price, precision)

    def validate_order(self, symbol: str, order_type: OrderType, side: OrderSide,
                      amount: float, price: Optional[float] = None) -> Tuple[bool, str]:
        """
        Validate order parameters

        Args:
            symbol: Trading pair
            order_type: Order type
            side: Buy or sell
            amount: Trade amount
            price: Trade price (for limit orders)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check minimum amount
        min_amount = self.config.get('min_amounts', {}).get(symbol, 0)
        if amount < min_amount:
            return False, f"Amount {amount} below minimum {min_amount}"

        # Check maximum amount (optional)
        max_amount = self.config.get('max_amounts', {}).get(symbol, float('inf'))
        if amount > max_amount:
            return False, f"Amount {amount} exceeds maximum {max_amount}"

        # Check price for limit orders
        if order_type == OrderType.LIMIT and price is None:
            return False, "Price required for limit orders"

        # Check price is positive
        if price is not None and price <= 0:
            return False, f"Invalid price: {price}"

        return True, ""

    def __repr__(self) -> str:
        return f"{self.name}(exchange_id='{self.exchange_id}')"
