"""
Binance Exchange Implementation

Implements connection to Binance exchange (both live and testnet) using CCXT.
"""

import ccxt
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import time

from .base_exchange import BaseExchange, OrderType, OrderSide, OrderStatus
from monitoring.logger import get_logger

logger = get_logger(__name__)


class BinanceExchange(BaseExchange):
    """
    Binance exchange implementation using CCXT

    Supports both live trading and testnet for paper trading.
    """

    def __init__(self, config: Dict):
        """
        Initialize Binance exchange

        Args:
            config: Configuration dictionary containing:
                - api_key: Binance API key
                - api_secret: Binance API secret
                - testnet: Boolean, True for testnet
                - fees: Trading fees (maker/taker)
        """
        super().__init__(config)

        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.testnet = config.get('testnet', True)

        self.exchange = None
        self._connect()

    def _connect(self) -> bool:
        """Internal method to create CCXT exchange instance"""
        try:
            # Create Binance exchange instance
            exchange_config = {
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # spot trading
                }
            }

            # Add API credentials if provided
            if self.api_key and self.api_secret:
                exchange_config['apiKey'] = self.api_key
                exchange_config['secret'] = self.api_secret

            self.exchange = ccxt.binance(exchange_config)

            # For testnet with API keys, set sandbox mode
            # For read-only (no keys), use production URLs for public data
            if self.testnet and self.api_key and self.api_secret:
                self.exchange.set_sandbox_mode(True)
                logger.info("Binance exchange initialized in TESTNET mode with API keys")
            elif self.api_key and self.api_secret:
                logger.info("Binance exchange initialized in LIVE mode with API keys")
            else:
                # Read-only mode - use production for public data
                logger.info("Binance exchange initialized in READ-ONLY mode (no API keys)")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Binance exchange: {e}")
            return False

    def connect(self) -> bool:
        """
        Connect to Binance and verify credentials

        Returns:
            True if connection successful
        """
        try:
            # Test connection by fetching balance (if we have credentials)
            if self.api_key and self.api_secret:
                balance = self.exchange.fetch_balance()
                logger.info(f"Successfully connected to Binance ({('TESTNET' if self.testnet else 'LIVE')})")
                return True
            else:
                # Read-only mode - just test by loading markets
                markets = self.exchange.load_markets()
                logger.info(f"Connected to Binance in read-only mode. {len(markets)} markets available")
                return True

        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}", exc_info=True)
            return False

    def fetch_ticker(self, symbol: str) -> Dict:
        """
        Fetch current ticker for symbol

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Ticker dictionary
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)

            return {
                'symbol': ticker['symbol'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'timestamp': ticker['timestamp'],
                'datetime': ticker['datetime']
            }

        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise

    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h',
                    since: Optional[int] = None, limit: int = 500) -> pd.DataFrame:
        """
        Fetch OHLCV candlestick data

        Args:
            symbol: Trading pair
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            since: Start timestamp in milliseconds
            limit: Number of candles (max 1000)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Fetch from exchange
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=min(limit, 1000)  # Binance max is 1000
            )

            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            logger.debug(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df

        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            raise

    def create_order(self, symbol: str, order_type: OrderType, side: OrderSide,
                    amount: float, price: Optional[float] = None,
                    params: Optional[Dict] = None) -> Dict:
        """
        Create order on Binance

        Args:
            symbol: Trading pair
            order_type: Order type (market/limit)
            side: Buy or sell
            amount: Amount to trade
            price: Price (for limit orders)
            params: Additional parameters

        Returns:
            Order dictionary
        """
        try:
            # Validate order
            is_valid, error_msg = self.validate_order(symbol, order_type, side, amount, price)
            if not is_valid:
                raise ValueError(f"Invalid order: {error_msg}")

            # Round to exchange precision
            amount = self.amount_to_precision(symbol, amount)
            if price:
                price = self.price_to_precision(symbol, price)

            # Create order via CCXT
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type.value,
                side=side.value,
                amount=amount,
                price=price,
                params=params or {}
            )

            logger.info(f"Order created: {side.value.upper()} {amount} {symbol} @ {price or 'market'}")
            return order

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise

    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an order"""
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order {order_id} canceled for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            raise

    def fetch_order(self, order_id: str, symbol: str) -> Dict:
        """Fetch order details"""
        try:
            return self.exchange.fetch_order(order_id, symbol)

        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            raise

    def fetch_balance(self) -> Dict:
        """Fetch account balance"""
        try:
            balance = self.exchange.fetch_balance()

            return {
                'total': balance['total'],
                'free': balance['free'],
                'used': balance['used'],
                'timestamp': int(time.time() * 1000)
            }

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise

    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Fetch open orders"""
        try:
            return self.exchange.fetch_open_orders(symbol)

        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise

    def fetch_closed_orders(self, symbol: Optional[str] = None,
                           since: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Fetch closed orders"""
        try:
            return self.exchange.fetch_closed_orders(symbol, since, limit)

        except Exception as e:
            logger.error(f"Error fetching closed orders: {e}")
            raise

    def fetch_my_trades(self, symbol: Optional[str] = None,
                       since: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Fetch trade history"""
        try:
            return self.exchange.fetch_my_trades(symbol, since, limit)

        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            raise

    def get_markets(self) -> Dict:
        """Get all available markets"""
        try:
            if not self.exchange.markets:
                self.exchange.load_markets()
            return self.exchange.markets

        except Exception as e:
            logger.error(f"Error loading markets: {e}")
            raise

    def get_trading_fees(self, symbol: str) -> Dict:
        """Get trading fees for symbol"""
        try:
            fees = self.exchange.fetch_trading_fees()
            if symbol in fees:
                return fees[symbol]
            else:
                # Return default fees
                return {
                    'maker': 0.001,  # 0.1%
                    'taker': 0.001   # 0.1%
                }

        except Exception as e:
            logger.warning(f"Could not fetch fees for {symbol}, using defaults: {e}")
            return {
                'maker': 0.001,
                'taker': 0.001
            }


# Factory function for easy creation
def create_binance_exchange(api_key: Optional[str] = None,
                            api_secret: Optional[str] = None,
                            testnet: bool = True) -> BinanceExchange:
    """
    Factory function to create Binance exchange instance

    Args:
        api_key: Binance API key (optional for read-only)
        api_secret: Binance API secret (optional for read-only)
        testnet: Use testnet (default True)

    Returns:
        BinanceExchange instance
    """
    config = {
        'exchange_id': 'binance',
        'api_key': api_key,
        'api_secret': api_secret,
        'testnet': testnet,
        'fees': {
            'maker': 0.001,
            'taker': 0.001
        }
    }

    return BinanceExchange(config)


if __name__ == "__main__":
    # Test exchange connectivity (read-only mode)
    exchange = create_binance_exchange(testnet=True)

    if exchange.connect():
        # Test fetching ticker
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"BTC/USDT Price: ${ticker['last']:,.2f}")

        # Test fetching OHLCV
        df = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=10)
        print(f"\nLast 10 hourly candles:")
        print(df[['open', 'high', 'low', 'close', 'volume']])
