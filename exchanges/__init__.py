"""
Exchange Connectors Module

Provides unified interface for connecting to exchanges and brokers.

Available Connectors:
- BinanceConnector: Binance exchange (crypto)
- AlpacaConnector: Alpaca broker (stocks)
- MockExchangeConnector: Mock connector for testing

Usage:
    from exchanges import BinanceConnector, AlpacaConnector

    # Binance (crypto)
    binance = BinanceConnector(config, paper_trading=True)
    binance.connect()
    price = binance.get_current_price('BTC/USDT')

    # Alpaca (stocks)
    alpaca = AlpacaConnector(config, paper_trading=True)
    alpaca.connect()
    price = alpaca.get_current_price('AAPL')
"""

from exchanges.base_connector import (
    BaseExchangeConnector,
    MockExchangeConnector,
    Order,
    OrderSide,
    OrderType,
    OrderStatus
)
from exchanges.binance_connector import BinanceConnector
from exchanges.alpaca_connector import AlpacaConnector

__all__ = [
    'BaseExchangeConnector',
    'MockExchangeConnector',
    'BinanceConnector',
    'AlpacaConnector',
    'Order',
    'OrderSide',
    'OrderType',
    'OrderStatus',
]
