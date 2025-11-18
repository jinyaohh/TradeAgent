#!/usr/bin/env python3
"""
Test script for crypto exchange connectivity
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptobot.exchange.binance_exchange import create_binance_exchange
from monitoring.logger import get_logger

logger = get_logger(__name__)


def test_exchange_connection():
    """Test Binance exchange in read-only mode"""
    print("="*60)
    print("Testing Binance Exchange Connection (Testnet)")
    print("="*60)

    try:
        # Create exchange in testnet mode (no API keys needed for public data)
        exchange = create_binance_exchange(testnet=True)

        # Test connection
        print("\n1. Testing connection...")
        if exchange.connect():
            print("✓ Connected to Binance testnet")
        else:
            print("✗ Failed to connect")
            return False

        # Test fetching ticker
        print("\n2. Testing ticker fetch...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✓ BTC/USDT Price: ${ticker['last']:,.2f}")
        print(f"  Bid: ${ticker['bid']:,.2f}")
        print(f"  Ask: ${ticker['ask']:,.2f}")
        print(f"  Volume: {ticker['volume']:,.2f} BTC")

        # Test fetching OHLCV
        print("\n3. Testing OHLCV fetch...")
        df = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=10)
        print(f"✓ Fetched {len(df)} hourly candles")
        print("\nLast 5 candles:")
        print(df[['open', 'high', 'low', 'close', 'volume']].tail())

        # Test multiple symbols
        print("\n4. Testing multiple symbols...")
        symbols = ['ETH/USDT', 'BNB/USDT', 'SOL/USDT']
        for symbol in symbols:
            ticker = exchange.fetch_ticker(symbol)
            print(f"  {symbol}: ${ticker['last']:,.2f}")

        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_exchange_connection()
    sys.exit(0 if success else 1)
