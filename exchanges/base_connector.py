"""
Exchange Connector Framework

Base classes for exchange and broker integrations.
Provides unified interface for different exchanges/brokers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

from monitoring.logger import get_logger

logger = get_logger(__name__)


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Order:
    """Order object"""
    def __init__(self,
                 order_id: str,
                 symbol: str,
                 side: OrderSide,
                 order_type: OrderType,
                 quantity: float,
                 price: Optional[float] = None,
                 status: OrderStatus = OrderStatus.PENDING,
                 filled_quantity: float = 0.0,
                 average_price: Optional[float] = None,
                 timestamp: Optional[datetime] = None):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.status = status
        self.filled_quantity = filled_quantity
        self.average_price = average_price
        self.timestamp = timestamp or datetime.now()

    def __repr__(self):
        return (f"Order({self.symbol} {self.side.value} {self.quantity} @ "
               f"{self.price or 'MARKET'}, status={self.status.value})")


class BaseExchangeConnector(ABC):
    """
    Base class for exchange/broker connectors

    Provides unified interface for:
    - Account information
    - Market data
    - Order execution
    - Position management
    """

    def __init__(self, config: Dict, paper_trading: bool = True):
        """
        Initialize connector

        Args:
            config: Configuration dictionary with API keys
            paper_trading: If True, use paper trading mode
        """
        self.config = config
        self.paper_trading = paper_trading
        self.connected = False

        logger.info(f"Initializing {self.__class__.__name__} "
                   f"(mode: {'paper' if paper_trading else 'LIVE'})")

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to exchange/broker

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from exchange/broker"""
        pass

    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance

        Returns:
            Dictionary of {asset: balance}
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """
        Get open positions

        Returns:
            List of position dictionaries
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for symbol

        Args:
            symbol: Trading symbol

        Returns:
            Current price or None if unavailable
        """
        pass

    @abstractmethod
    def get_historical_data(self,
                           symbol: str,
                           timeframe: str = '1h',
                           limit: int = 500) -> pd.DataFrame:
        """
        Get historical OHLCV data

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Number of bars

        Returns:
            DataFrame with OHLCV data
        """
        pass

    @abstractmethod
    def place_order(self,
                   symbol: str,
                   side: OrderSide,
                   order_type: OrderType,
                   quantity: float,
                   price: Optional[float] = None,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Optional[Order]:
        """
        Place an order

        Args:
            symbol: Trading symbol
            side: Buy or sell
            order_type: Market, limit, etc.
            quantity: Order quantity
            price: Limit price (for limit orders)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)

        Returns:
            Order object if successful, None otherwise
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        Get order status

        Args:
            order_id: Order ID

        Returns:
            Order object with current status
        """
        pass

    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get open orders

        Args:
            symbol: Filter by symbol (optional)

        Returns:
            List of open orders
        """
        pass

    def validate_order(self,
                      symbol: str,
                      side: OrderSide,
                      quantity: float,
                      price: Optional[float] = None) -> Tuple[bool, str]:
        """
        Validate order before placing

        Args:
            symbol: Trading symbol
            side: Buy or sell
            quantity: Order quantity
            price: Order price

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check quantity is positive
        if quantity <= 0:
            return False, "Quantity must be positive"

        # Check price is positive (for limit orders)
        if price is not None and price <= 0:
            return False, "Price must be positive"

        # Check if we have sufficient balance
        balance = self.get_account_balance()

        if side == OrderSide.BUY:
            # Need cash to buy
            cash_needed = quantity * (price or self.get_current_price(symbol) or 0)
            if 'USD' in balance or 'USDT' in balance:
                available_cash = balance.get('USD', balance.get('USDT', 0))
                if cash_needed > available_cash:
                    return False, f"Insufficient cash: need ${cash_needed:.2f}, have ${available_cash:.2f}"

        elif side == OrderSide.SELL:
            # Need asset to sell
            # Extract base asset from symbol (e.g., BTC from BTC/USDT or BTCUSDT)
            base_asset = symbol.split('/')[0] if '/' in symbol else symbol.replace('USDT', '').replace('USD', '')
            available = balance.get(base_asset, 0)
            if quantity > available:
                return False, f"Insufficient {base_asset}: need {quantity}, have {available}"

        return True, "Order is valid"

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


class MockExchangeConnector(BaseExchangeConnector):
    """
    Mock exchange connector for testing

    Simulates exchange behavior without real API calls
    """

    def __init__(self, config: Dict, paper_trading: bool = True):
        super().__init__(config, paper_trading)

        self.balance = {
            'USD': config.get('initial_balance', 10000.0),
            'BTC': 0.0,
            'ETH': 0.0
        }

        self.positions = []
        self.orders = {}
        self.order_counter = 0

        from cryptobot.data.mock_data import MockDataGenerator
        self.data_generator = MockDataGenerator()

    def connect(self) -> bool:
        """Mock connection"""
        logger.info("Mock connector: Connected successfully")
        self.connected = True
        return True

    def disconnect(self):
        """Mock disconnection"""
        logger.info("Mock connector: Disconnected")
        self.connected = False

    def get_account_balance(self) -> Dict[str, float]:
        """Return mock balance"""
        return self.balance.copy()

    def get_positions(self) -> List[Dict]:
        """Return mock positions"""
        return self.positions.copy()

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Return mock price"""
        # Generate realistic price
        if 'BTC' in symbol:
            return 45000.0 + (hash(str(datetime.now().timestamp())) % 5000)
        elif 'ETH' in symbol:
            return 3000.0 + (hash(str(datetime.now().timestamp())) % 500)
        return 100.0

    def get_historical_data(self, symbol: str, timeframe: str = '1h', limit: int = 500) -> pd.DataFrame:
        """Return mock historical data"""
        return self.data_generator.generate_ohlcv(symbol=symbol, periods=limit, timeframe=timeframe)

    def place_order(self,
                   symbol: str,
                   side: OrderSide,
                   order_type: OrderType,
                   quantity: float,
                   price: Optional[float] = None,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Optional[Order]:
        """Place mock order"""

        # Validate order
        is_valid, reason = self.validate_order(symbol, side, quantity, price)
        if not is_valid:
            logger.error(f"Order validation failed: {reason}")
            return None

        # Create order
        self.order_counter += 1
        order_id = f"MOCK_{self.order_counter}"

        current_price = price or self.get_current_price(symbol)

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.FILLED,  # Mock: instantly filled
            filled_quantity=quantity,
            average_price=current_price
        )

        self.orders[order_id] = order

        # Update balances
        base_asset = symbol.split('/')[0] if '/' in symbol else symbol.replace('USDT', '').replace('USD', '')
        quote_asset = 'USD'

        if side == OrderSide.BUY:
            cost = quantity * current_price
            self.balance[quote_asset] -= cost
            self.balance[base_asset] = self.balance.get(base_asset, 0) + quantity
        else:
            proceeds = quantity * current_price
            self.balance[quote_asset] += proceeds
            self.balance[base_asset] -= quantity

        logger.info(f"Mock order placed: {order}")
        return order

    def cancel_order(self, order_id: str) -> bool:
        """Cancel mock order"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            logger.info(f"Mock order cancelled: {order_id}")
            return True
        return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get mock order status"""
        return self.orders.get(order_id)

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get mock open orders"""
        open_orders = [o for o in self.orders.values()
                      if o.status == OrderStatus.OPEN]

        if symbol:
            open_orders = [o for o in open_orders if o.symbol == symbol]

        return open_orders


if __name__ == "__main__":
    # Test mock connector
    print("="*60)
    print("Testing Exchange Connector Framework")
    print("="*60)

    config = {'initial_balance': 10000.0}

    with MockExchangeConnector(config, paper_trading=True) as connector:
        # Get balance
        balance = connector.get_account_balance()
        print(f"\nInitial Balance: {balance}")

        # Get current price
        btc_price = connector.get_current_price('BTC/USDT')
        print(f"BTC Price: ${btc_price:,.2f}")

        # Place buy order
        order = connector.place_order(
            symbol='BTC/USDT',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.1
        )
        print(f"\nOrder placed: {order}")

        # Check balance after
        balance = connector.get_account_balance()
        print(f"Balance after buy: {balance}")

        # Place sell order
        order = connector.place_order(
            symbol='BTC/USDT',
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=0.05
        )
        print(f"\nSell order: {order}")

        # Final balance
        balance = connector.get_account_balance()
        print(f"Final Balance: {balance}")

    print("\n✓ Exchange connector framework test complete!")
