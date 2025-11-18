"""
Alpaca Broker Connector

Connects to Alpaca for stock trading.
Supports both paper trading and live trading.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from exchanges.base_connector import (
    BaseExchangeConnector, Order, OrderSide, OrderType, OrderStatus
)
from monitoring.logger import get_logger

logger = get_logger(__name__)

# Optional alpaca-trade-api import
try:
    import alpaca_trade_api as tradeapi
    HAS_ALPACA = True
except ImportError:
    HAS_ALPACA = False
    logger.warning("alpaca-trade-api not installed - Alpaca connector will use mock mode")


class AlpacaConnector(BaseExchangeConnector):
    """
    Alpaca broker connector

    Features:
    - Stock trading (US markets)
    - Paper trading support (free!)
    - Real-time and historical data
    - Fractional shares
    - Extended hours trading

    Note: Requires alpaca-trade-api library (pip install alpaca-trade-api)

    Get free paper trading account: https://alpaca.markets/
    """

    def __init__(self, config: Dict, paper_trading: bool = True):
        """
        Initialize Alpaca connector

        Args:
            config: Configuration with:
                - api_key: Alpaca API key
                - api_secret: Alpaca API secret
                - base_url: API endpoint (paper or live)
        """
        super().__init__(config, paper_trading)

        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')

        # Default to paper trading URL
        if paper_trading:
            self.base_url = config.get('base_url', 'https://paper-api.alpaca.markets')
        else:
            self.base_url = config.get('base_url', 'https://api.alpaca.markets')

        self.api = None
        self.use_mock = False

        if self.use_mock or not HAS_ALPACA:
            logger.warning("alpaca-trade-api not available - using mock connector")
            self.use_mock = True
            from exchanges.base_connector import MockExchangeConnector
            self.mock_connector = MockExchangeConnector(config, paper_trading)

    def connect(self) -> bool:
        """Connect to Alpaca"""
        try:
            if self.use_mock or not HAS_ALPACA:
                if not hasattr(self, 'mock_connector'):
                    from exchanges.base_connector import MockExchangeConnector
                    self.mock_connector = MockExchangeConnector(self.config, self.paper_trading)
                    self.use_mock = True
                logger.warning("Using mock connector (alpaca-trade-api not available or connection failed)")
                return self.mock_connector.connect()

            # Initialize API
            self.api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.api_secret,
                base_url=self.base_url,
                api_version='v2'
            )

            # Test connection by getting account
            account = self.api.get_account()

            if self.paper_trading:
                logger.info("Connected to Alpaca PAPER TRADING")
            else:
                logger.warning("⚠️  Connected to Alpaca LIVE - REAL MONEY AT RISK")

            logger.info(f"Account: ${float(account.portfolio_value):,.2f} portfolio value")
            logger.info(f"Buying power: ${float(account.buying_power):,.2f}")

            self.connected = True
            return True

        except Exception as e:
            logger.warning(f"Failed to connect to Alpaca: {e}")
            logger.warning("Falling back to mock connector")

            # Fall back to mock connector
            if not hasattr(self, 'mock_connector'):
                from exchanges.base_connector import MockExchangeConnector
                self.mock_connector = MockExchangeConnector(self.config, self.paper_trading)

            self.use_mock = True
            return self.mock_connector.connect()

    def disconnect(self):
        """Disconnect from Alpaca"""
        if self.use_mock:
            if hasattr(self, 'mock_connector'):
                self.mock_connector.disconnect()
        else:
            self.api = None

        self.connected = False
        logger.info("Disconnected from Alpaca")

    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            if self.use_mock or not HAS_ALPACA:
                return self.mock_connector.get_account_balance()

            if not self.connected:
                logger.error("Not connected to broker")
                return {}

            account = self.api.get_account()

            return {
                'USD': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity)
            }

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}

    def get_positions(self) -> List[Dict]:
        """Get open positions"""
        try:
            if self.use_mock or not HAS_ALPACA:
                return self.mock_connector.get_positions()

            if not self.connected:
                logger.error("Not connected to broker")
                return []

            positions = self.api.list_positions()

            result = []
            for pos in positions:
                result.append({
                    'symbol': pos.symbol,
                    'quantity': float(pos.qty),
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'current_price': float(pos.current_price),
                    'average_entry_price': float(pos.avg_entry_price),
                    'side': pos.side
                })

            return result

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        try:
            if self.use_mock or not HAS_ALPACA:
                return self.mock_connector.get_current_price(symbol)

            if not self.connected:
                logger.error("Not connected to broker")
                return None

            # Get latest trade
            trade = self.api.get_latest_trade(symbol)
            return float(trade.price)

        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None

    def get_historical_data(self,
                           symbol: str,
                           timeframe: str = '1Hour',
                           limit: int = 500) -> pd.DataFrame:
        """Get historical bar data"""
        try:
            if self.use_mock or not HAS_ALPACA:
                # Convert Alpaca timeframe to mock format
                timeframe_conversion = {
                    '1Min': '1m', '5Min': '5m', '15Min': '15m',
                    '1Hour': '1h', '1Day': '1d'
                }
                mock_timeframe = timeframe_conversion.get(timeframe, '1h')
                return self.mock_connector.get_historical_data(symbol, mock_timeframe, limit)

            if not self.connected:
                logger.error("Not connected to broker")
                return pd.DataFrame()

            # Map timeframe to Alpaca format
            timeframe_map = {
                '1m': '1Min', '5m': '5Min', '15m': '15Min',
                '1h': '1Hour', '1Hour': '1Hour',
                '1d': '1Day', '1Day': '1Day'
            }

            alpaca_timeframe = timeframe_map.get(timeframe, '1Hour')

            # Calculate start date (Alpaca requires start/end, not limit)
            if 'Min' in alpaca_timeframe:
                minutes = int(alpaca_timeframe.replace('Min', ''))
                delta = timedelta(minutes=minutes * limit)
            elif 'Hour' in alpaca_timeframe:
                delta = timedelta(hours=limit)
            else:
                delta = timedelta(days=limit)

            start = datetime.now() - delta
            end = datetime.now()

            # Fetch bars
            bars = self.api.get_bars(
                symbol,
                alpaca_timeframe,
                start=start.isoformat(),
                end=end.isoformat()
            ).df

            # Rename columns to match our format
            bars = bars.rename(columns={'timestamp': 'timestamp'})
            bars.index.name = 'timestamp'

            return bars

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
            if self.use_mock or not HAS_ALPACA:
                return self.mock_connector.place_order(
                    symbol, side, order_type, quantity, price, stop_loss, take_profit
                )

            if not self.connected:
                logger.error("Not connected to broker")
                return None

            # Validate order
            is_valid, reason = self.validate_order(symbol, side, quantity, price)
            if not is_valid:
                logger.error(f"Order validation failed: {reason}")
                return None

            # Convert order type
            alpaca_type = 'market' if order_type == OrderType.MARKET else 'limit'

            # Build order params
            order_params = {
                'symbol': symbol,
                'qty': quantity,
                'side': side.value,
                'type': alpaca_type,
                'time_in_force': 'gtc',  # Good til cancelled
            }

            if price is not None:
                order_params['limit_price'] = price

            # Add stop loss and take profit
            if stop_loss:
                order_params['order_class'] = 'bracket'
                order_params['stop_loss'] = {'stop_price': stop_loss}

            if take_profit:
                if 'order_class' not in order_params:
                    order_params['order_class'] = 'bracket'
                order_params['take_profit'] = {'limit_price': take_profit}

            if self.paper_trading:
                logger.info(f"[PAPER] Placing order: {side.value} {quantity} {symbol} @ "
                           f"{price or 'MARKET'}")

            # Place order
            alpaca_order = self.api.submit_order(**order_params)

            # Convert to our Order object
            order = self._convert_alpaca_order(alpaca_order)

            logger.info(f"Order placed: {order}")

            return order

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            if self.use_mock or not HAS_ALPACA:
                return self.mock_connector.cancel_order(order_id)

            if not self.connected:
                logger.error("Not connected to broker")
                return False

            self.api.cancel_order(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        try:
            if self.use_mock or not HAS_ALPACA:
                return self.mock_connector.get_order_status(order_id)

            if not self.connected:
                logger.error("Not connected to broker")
                return None

            alpaca_order = self.api.get_order(order_id)
            return self._convert_alpaca_order(alpaca_order)

        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return None

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        try:
            if self.use_mock or not HAS_ALPACA:
                return self.mock_connector.get_open_orders(symbol)

            if not self.connected:
                logger.error("Not connected to broker")
                return []

            alpaca_orders = self.api.list_orders(status='open', symbols=symbol if symbol else None)
            return [self._convert_alpaca_order(o) for o in alpaca_orders]

        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    def _convert_alpaca_order(self, alpaca_order) -> Order:
        """Convert Alpaca order to our Order object"""

        # Map Alpaca status to our OrderStatus
        status_map = {
            'new': OrderStatus.OPEN,
            'partially_filled': OrderStatus.PARTIALLY_FILLED,
            'filled': OrderStatus.FILLED,
            'done_for_day': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELLED,
            'expired': OrderStatus.EXPIRED,
            'replaced': OrderStatus.CANCELLED,
            'pending_cancel': OrderStatus.PENDING,
            'pending_replace': OrderStatus.PENDING,
            'accepted': OrderStatus.OPEN,
            'pending_new': OrderStatus.PENDING,
            'accepted_for_bidding': OrderStatus.PENDING,
            'stopped': OrderStatus.CANCELLED,
            'rejected': OrderStatus.REJECTED,
            'suspended': OrderStatus.PENDING,
            'calculated': OrderStatus.PENDING
        }

        status = status_map.get(alpaca_order.status, OrderStatus.PENDING)

        # Map order type
        type_map = {
            'market': OrderType.MARKET,
            'limit': OrderType.LIMIT,
            'stop': OrderType.STOP,
            'stop_limit': OrderType.STOP_LIMIT
        }

        order_type = type_map.get(alpaca_order.type, OrderType.MARKET)

        # Map side
        side = OrderSide.BUY if alpaca_order.side == 'buy' else OrderSide.SELL

        return Order(
            order_id=str(alpaca_order.id),
            symbol=alpaca_order.symbol,
            side=side,
            order_type=order_type,
            quantity=float(alpaca_order.qty) if alpaca_order.qty else 0.0,
            price=float(alpaca_order.limit_price) if alpaca_order.limit_price else None,
            status=status,
            filled_quantity=float(alpaca_order.filled_qty) if alpaca_order.filled_qty else 0.0,
            average_price=float(alpaca_order.filled_avg_price) if alpaca_order.filled_avg_price else None,
            timestamp=alpaca_order.created_at
        )

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            if self.use_mock or not HAS_ALPACA:
                # Simple market hours check for mock mode
                now = datetime.now()
                if now.weekday() >= 5:  # Weekend
                    return False
                hour = now.hour
                return 9 <= hour < 16

            if not self.connected:
                return False

            clock = self.api.get_clock()
            return clock.is_open

        except Exception as e:
            logger.error(f"Failed to check if market is open: {e}")
            return False


if __name__ == "__main__":
    # Test Alpaca connector (with mock if alpaca-trade-api not available)
    print("="*60)
    print("Testing Alpaca Connector")
    print("="*60)

    config = {
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'initial_balance': 10000.0  # For mock mode
    }

    connector = AlpacaConnector(config, paper_trading=True)

    if connector.connect():
        print("\n✓ Connected successfully")

        # Get balance
        balance = connector.get_account_balance()
        print(f"\nBalance: {balance}")

        # Check if market is open
        is_open = connector.is_market_open()
        print(f"\nMarket open: {is_open}")

        # Get current price
        price = connector.get_current_price('AAPL')
        print(f"AAPL Price: ${price:.2f}" if price else "Price unavailable")

        # Get historical data
        df = connector.get_historical_data('AAPL', '1Hour', 10)
        if not df.empty:
            print(f"\nHistorical Data (last 3 bars):")
            print(df.tail(3))

        # Disconnect
        connector.disconnect()
        print("\n✓ Alpaca connector test complete!")
    else:
        print("\n❌ Connection failed")
