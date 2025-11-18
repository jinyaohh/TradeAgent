"""
Connection Manager

Manages connections to multiple exchanges/brokers.
Provides health monitoring and automatic reconnection.
"""

import time
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from exchanges.base_connector import BaseExchangeConnector
from exchanges.binance_connector import BinanceConnector
from exchanges.alpaca_connector import AlpacaConnector
from monitoring.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages multiple exchange/broker connections

    Features:
    - Multi-connector management
    - Health monitoring
    - Automatic reconnection
    - Unified interface
    """

    def __init__(self, config: Dict):
        """
        Initialize connection manager

        Args:
            config: Configuration dictionary with exchange configs
        """
        self.config = config
        self.connectors: Dict[str, BaseExchangeConnector] = {}
        self.health_status: Dict[str, Dict] = {}

        self.monitor_thread: Optional[threading.Thread] = None
        self.monitoring = False

        logger.info("Connection Manager initialized")

    def add_connector(self, name: str, connector_type: str, config: Dict, paper_trading: bool = True):
        """
        Add a connector

        Args:
            name: Unique name for the connector
            connector_type: 'binance', 'alpaca', etc.
            config: Configuration for the connector
            paper_trading: If True, use paper trading mode
        """
        try:
            if connector_type.lower() == 'binance':
                connector = BinanceConnector(config, paper_trading)
            elif connector_type.lower() == 'alpaca':
                connector = AlpacaConnector(config, paper_trading)
            else:
                logger.error(f"Unknown connector type: {connector_type}")
                return False

            self.connectors[name] = connector
            self.health_status[name] = {
                'connected': False,
                'last_check': None,
                'consecutive_failures': 0,
                'last_error': None
            }

            logger.info(f"Added connector: {name} ({connector_type})")
            return True

        except Exception as e:
            logger.error(f"Failed to add connector {name}: {e}")
            return False

    def connect_all(self) -> bool:
        """
        Connect to all configured exchanges/brokers

        Returns:
            True if all connections successful
        """
        logger.info("Connecting to all exchanges/brokers...")

        all_success = True

        for name, connector in self.connectors.items():
            logger.info(f"Connecting to {name}...")
            try:
                success = connector.connect()
                self.health_status[name]['connected'] = success
                self.health_status[name]['last_check'] = datetime.now()

                if success:
                    logger.info(f"✓ {name} connected")
                else:
                    logger.error(f"✗ {name} connection failed")
                    all_success = False

            except Exception as e:
                logger.error(f"Error connecting to {name}: {e}")
                self.health_status[name]['connected'] = False
                self.health_status[name]['last_error'] = str(e)
                all_success = False

        if all_success:
            logger.info("✓ All connectors connected successfully")
        else:
            logger.warning("⚠️  Some connectors failed to connect")

        return all_success

    def disconnect_all(self):
        """Disconnect from all exchanges/brokers"""
        logger.info("Disconnecting from all exchanges/brokers...")

        for name, connector in self.connectors.items():
            try:
                connector.disconnect()
                self.health_status[name]['connected'] = False
                logger.info(f"✓ {name} disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting from {name}: {e}")

        logger.info("All connectors disconnected")

    def get_connector(self, name: str) -> Optional[BaseExchangeConnector]:
        """
        Get connector by name

        Args:
            name: Connector name

        Returns:
            Connector instance or None if not found
        """
        return self.connectors.get(name)

    def start_health_monitoring(self, interval: int = 60):
        """
        Start health monitoring thread

        Args:
            interval: Check interval in seconds
        """
        if self.monitoring:
            logger.warning("Health monitoring already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()

        logger.info(f"Health monitoring started (interval: {interval}s)")

    def stop_health_monitoring(self):
        """Stop health monitoring thread"""
        self.monitoring = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        logger.info("Health monitoring stopped")

    def _health_monitor_loop(self, interval: int):
        """Health monitoring loop"""
        logger.info("Health monitor loop started")

        while self.monitoring:
            try:
                for name, connector in self.connectors.items():
                    self._check_health(name, connector)

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                time.sleep(interval)

        logger.info("Health monitor loop stopped")

    def _check_health(self, name: str, connector: BaseExchangeConnector):
        """
        Check health of a connector

        Args:
            name: Connector name
            connector: Connector instance
        """
        try:
            # Simple health check: try to get balance
            balance = connector.get_account_balance()

            if balance:
                # Connection is healthy
                self.health_status[name]['connected'] = True
                self.health_status[name]['consecutive_failures'] = 0
                self.health_status[name]['last_error'] = None
                logger.debug(f"Health check OK: {name}")
            else:
                # Connection might be unhealthy
                self.health_status[name]['consecutive_failures'] += 1
                logger.warning(f"Health check warning: {name} returned empty balance")

        except Exception as e:
            # Connection is unhealthy
            self.health_status[name]['connected'] = False
            self.health_status[name]['consecutive_failures'] += 1
            self.health_status[name]['last_error'] = str(e)
            logger.error(f"Health check failed: {name} - {e}")

            # Try to reconnect after 3 consecutive failures
            if self.health_status[name]['consecutive_failures'] >= 3:
                logger.warning(f"Attempting to reconnect {name}...")
                try:
                    connector.disconnect()
                    time.sleep(2)
                    if connector.connect():
                        logger.info(f"✓ {name} reconnected successfully")
                        self.health_status[name]['consecutive_failures'] = 0
                    else:
                        logger.error(f"✗ {name} reconnection failed")
                except Exception as reconnect_error:
                    logger.error(f"Reconnection error for {name}: {reconnect_error}")

        finally:
            self.health_status[name]['last_check'] = datetime.now()

    def get_health_status(self) -> Dict:
        """
        Get health status of all connectors

        Returns:
            Dictionary with health status for each connector
        """
        return self.health_status.copy()

    def print_status(self):
        """Print status of all connectors"""
        print("\n" + "="*70)
        print("CONNECTION MANAGER STATUS")
        print("="*70)

        for name, status in self.health_status.items():
            connected = "✓ CONNECTED" if status['connected'] else "✗ DISCONNECTED"
            print(f"\n{name}: {connected}")

            if status['last_check']:
                print(f"  Last Check: {status['last_check'].strftime('%Y-%m-%d %H:%M:%S')}")

            if status['consecutive_failures'] > 0:
                print(f"  Consecutive Failures: {status['consecutive_failures']}")

            if status['last_error']:
                print(f"  Last Error: {status['last_error']}")

        print("\n" + "="*70)

    def is_all_connected(self) -> bool:
        """Check if all connectors are connected"""
        return all(status['connected'] for status in self.health_status.values())

    def get_all_balances(self) -> Dict[str, Dict]:
        """
        Get balances from all connectors

        Returns:
            Dictionary of {connector_name: balance_dict}
        """
        balances = {}

        for name, connector in self.connectors.items():
            if self.health_status[name]['connected']:
                try:
                    balances[name] = connector.get_account_balance()
                except Exception as e:
                    logger.error(f"Failed to get balance from {name}: {e}")
                    balances[name] = {}
            else:
                balances[name] = {}

        return balances


if __name__ == "__main__":
    # Test connection manager
    print("="*60)
    print("Testing Connection Manager")
    print("="*60)

    # Create manager
    manager = ConnectionManager({})

    # Add connectors
    print("\nAdding connectors...")

    manager.add_connector(
        'binance',
        'binance',
        {'api_key': 'test', 'api_secret': 'test', 'initial_balance': 10000.0},
        paper_trading=True
    )

    manager.add_connector(
        'alpaca',
        'alpaca',
        {'api_key': 'test', 'api_secret': 'test', 'initial_balance': 10000.0},
        paper_trading=True
    )

    # Connect all
    print("\nConnecting to all exchanges...")
    success = manager.connect_all()

    # Print status
    manager.print_status()

    # Get balances
    print("\nBalances:")
    balances = manager.get_all_balances()
    for name, balance in balances.items():
        print(f"  {name}: {balance}")

    # Disconnect all
    print("\nDisconnecting...")
    manager.disconnect_all()

    print("\n✓ Connection manager test complete!")
