"""
Binance Exchange Connector

Connects to Binance exchange for crypto trading.
Supports both paper trading (testnet) and live trading.
"""

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from exchanges.base_connector import (
    BaseExchangeConnector, Order, OrderSide, OrderType, OrderStatus
)
from monitoring.logger import get_logger

logger = get_logger(__name__)

# Optional ccxt import
try:
    import ccxt
    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False
    logger.warning("ccxt not installed - Binance connector will use mock mode")


class BinanceConnector(BaseExchangeConnector):
    """
    Binance exchange connector

    Features:
    - Spot trading
    - Real-time prices
    - Historical data
    - Order management
    - WebSocket support (future)

    Note: Requires ccxt library (pip install ccxt)
    """

    def __init__(self, config: Dict, paper_trading: bool = True):
        """
        Initialize Binance connector

        Args:
            config: Configuration with:
                - api_key: Binance API key
                - api_secret: Binance API secret
                - testnet: Use testnet if True
        """
        super().__init__(config, paper_trading)

        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.testnet = config.get('testnet', True)

        self.exchange = None
        self.use_mock = False

        if self.use_mock or not HAS_CCXT:
            logger.warning("ccxt not available - using mock connector")
            self.use_mock = True
            from exchanges.base_connector import MockExchangeConnector
            self.mock_connector = MockExchangeConnector(config, paper_trading)

    def connect(self) -> bool:
        """Connect to Binance"""
        try:
            if self.use_mock or not HAS_CCXT:
                if not hasattr(self, 'mock_connector'):
                    from exchanges.base_connector import MockExchangeConnector
                    self.mock_connector = MockExchangeConnector(self.config, self.paper_trading)
                    self.use_mock = True
                logger.warning("Using mock connector (ccxt not available or connection failed)")
                return self.mock_connector.connect()

            # Initialize exchange
            self.exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })

            if self.testnet:
                # Use testnet endpoints
                self.exchange.set_sandbox_mode(True)
                logger.info("Connected to Binance TESTNET")
            else:
                logger.warning("⚠️  Connected to Binance LIVE - REAL MONEY AT RISK")

            # Test connection
            self.exchange.load_markets()

            self.connected = True
            logger.info(f"Binance connector ready: {len(self.exchange.markets)} markets available")

            return True

        except Exception as e:
            logger.warning(f"Failed to connect to Binance: {e}")
            logger.warning("Falling back to mock connector")

            # Fall back to mock connector
            if not hasattr(self, 'mock_connector'):
                from exchanges.base_connector import MockExchangeConnector
                self.mock_connector = MockExchangeConnector(self.config, self.paper_trading)

            self.use_mock = True
            return self.mock_connector.connect()

    def disconnect(self):
        """Disconnect from Binance"""
        if self.use_mock:
            if hasattr(self, 'mock_connector'):
                self.mock_connector.disconnect()
        elif self.exchange and hasattr(self.exchange, 'close'):
            self.exchange.close()

        self.connected = False
        logger.info("Disconnected from Binance")

    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            if self.use_mock or not HAS_CCXT:
                return self.mock_connector.get_account_balance()

            if not self.connected:
                logger.error("Not connected to exchange")
                return {}

            balance = self.exchange.fetch_balance()

            # Return free (available) balances
            result = {}
            for asset, amount in balance['free'].items():
                if amount > 0:
                    result[asset] = amount

            return result

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}

    def get_positions(self) -> List[Dict]:
        """
        Get open positions

        Note: Spot trading doesn't have positions like futures
        Returns balances with positive amounts
        """
        balance = self.get_account_balance()
        positions = []

        for asset, amount in balance.items():
            if asset != 'USDT' and amount > 0:
                positions.append({
                    'asset': asset,
                    'amount': amount,
                    'symbol': f"{asset}/USDT"
                })

        return positions

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        try:
            if self.use_mock or not HAS_CCXT:
                return self.mock_connector.get_current_price(symbol)

            if not self.connected:
                logger.error("Not connected to exchange")
                return None

            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']

        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None

    def get_historical_data(self,
                           symbol: str,
                           timeframe: str = '1h',
                           limit: int = 500) -> pd.DataFrame:
        """Get historical OHLCV data"""
        try:
            if self.use_mock or not HAS_CCXT:
                return self.mock_connector.get_historical_data(symbol, timeframe, limit)

            if not self.connected:
                logger.error("Not connected to exchange")
                return pd.DataFrame()

            # Fetch OHLCV
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return pd.DataFrame()

    def place_order(self,
                   symbol: str,
                   side: OrderSide,
                   order_type: OrderType,
                   quantity: float,
                   price: Optional[float] = None,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None) -> Optional[Order]:
        """Place an order"""
        try:
            if self.use_mock or not HAS_CCXT:
                return self.mock_connector.place_order(
                    symbol, side, order_type, quantity, price, stop_loss, take_profit
                )

            if not self.connected:
                logger.error("Not connected to exchange")
                return None

            # Validate order
            is_valid, reason = self.validate_order(symbol, side, quantity, price)
            if not is_valid:
                logger.error(f"Order validation failed: {reason}")
                return None

            # Convert order type
            ccxt_type = 'market' if order_type == OrderType.MARKET else 'limit'

            # Place order
            if self.paper_trading:
                logger.info(f"[PAPER] Would place order: {side.value} {quantity} {symbol} @ "
                           f"{price or 'MARKET'}")

            ccxt_order = self.exchange.create_order(
                symbol=symbol,
                type=ccxt_type,
                side=side.value,
                amount=quantity,
                price=price
            )

            # Convert to our Order object
            order = self._convert_ccxt_order(ccxt_order)

            logger.info(f"Order placed: {order}")

            # Place stop loss if provided
            if stop_loss and order.status == OrderStatus.FILLED:
                try:
                    sl_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
                    self.exchange.create_order(
                        symbol=symbol,
                        type='stop_loss_limit',
                        side=sl_side.value,
                        amount=quantity,
                        price=stop_loss,
                        params={'stopPrice': stop_loss}
                    )
                    logger.info(f"Stop loss placed at {stop_loss}")
                except Exception as e:
                    logger.error(f"Failed to place stop loss: {e}")

            # Place take profit if provided
            if take_profit and order.status == OrderStatus.FILLED:
                try:
                    tp_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
                    self.exchange.create_order(
                        symbol=symbol,
                        type='take_profit_limit',
                        side=tp_side.value,
                        amount=quantity,
                        price=take_profit,
                        params={'stopPrice': take_profit}
                    )
                    logger.info(f"Take profit placed at {take_profit}")
                except Exception as e:
                    logger.error(f"Failed to place take profit: {e}")

            return order

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None

    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """Cancel an order"""
        try:
            if self.use_mock or not HAS_CCXT:
                return self.mock_connector.cancel_order(order_id)

            if not self.connected:
                logger.error("Not connected to exchange")
                return False

            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Optional[Order]:
        """Get order status"""
        try:
            if self.use_mock or not HAS_CCXT:
                return self.mock_connector.get_order_status(order_id)

            if not self.connected:
                logger.error("Not connected to exchange")
                return None

            ccxt_order = self.exchange.fetch_order(order_id, symbol)
            return self._convert_ccxt_order(ccxt_order)

        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return None

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        try:
            if self.use_mock or not HAS_CCXT:
                return self.mock_connector.get_open_orders(symbol)

            if not self.connected:
                logger.error("Not connected to exchange")
                return []

            ccxt_orders = self.exchange.fetch_open_orders(symbol)
            return [self._convert_ccxt_order(o) for o in ccxt_orders]

        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    def _convert_ccxt_order(self, ccxt_order: Dict) -> Order:
        """Convert ccxt order to our Order object"""

        # Map ccxt status to our OrderStatus
        status_map = {
            'open': OrderStatus.OPEN,
            'closed': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELLED,
            'expired': OrderStatus.EXPIRED,
            'rejected': OrderStatus.REJECTED,
        }

        status = status_map.get(ccxt_order.get('status', '').lower(), OrderStatus.PENDING)

        # Map order type
        type_map = {
            'market': OrderType.MARKET,
            'limit': OrderType.LIMIT,
            'stop_loss': OrderType.STOP,
            'stop_loss_limit': OrderType.STOP_LIMIT,
        }

        order_type = type_map.get(ccxt_order.get('type', '').lower(), OrderType.MARKET)

        # Map side
        side = OrderSide.BUY if ccxt_order.get('side') == 'buy' else OrderSide.SELL

        return Order(
            order_id=str(ccxt_order.get('id', '')),
            symbol=ccxt_order.get('symbol', ''),
            side=side,
            order_type=order_type,
            quantity=ccxt_order.get('amount', 0.0),
            price=ccxt_order.get('price'),
            status=status,
            filled_quantity=ccxt_order.get('filled', 0.0),
            average_price=ccxt_order.get('average'),
            timestamp=datetime.fromtimestamp(ccxt_order.get('timestamp', 0) / 1000)
                     if ccxt_order.get('timestamp') else datetime.now()
        )


if __name__ == "__main__":
    # Test Binance connector (with mock if ccxt not available)
    print("="*60)
    print("Testing Binance Connector")
    print("="*60)

    config = {
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'testnet': True,
        'initial_balance': 10000.0  # For mock mode
    }

    connector = BinanceConnector(config, paper_trading=True)

    if connector.connect():
        print("\n✓ Connected successfully")

        # Get balance
        balance = connector.get_account_balance()
        print(f"\nBalance: {balance}")

        # Get current price
        price = connector.get_current_price('BTC/USDT')
        print(f"BTC/USDT Price: ${price:,.2f}" if price else "Price unavailable")

        # Get historical data
        df = connector.get_historical_data('BTC/USDT', '1h', 10)
        if not df.empty:
            print(f"\nHistorical Data (last 3 bars):")
            print(df.tail(3))

        # Disconnect
        connector.disconnect()
        print("\n✓ Binance connector test complete!")
    else:
        print("\n❌ Connection failed")
