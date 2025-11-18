"""
Trading Engine

Main orchestrator that coordinates all trading components:
- Crypto trading bot
- Stock trading bot
- Risk management
- Portfolio management
- Notifications
"""

import threading
import time
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
import signal
import sys

from shared.risk_management.portfolio_manager import PortfolioManager
from shared.risk_management.risk_monitor import RiskMonitor
from monitoring.notifications import NotificationManager
from monitoring.logger import get_logger
from core.crypto_bot import CryptoBot
from core.stock_bot import StockBot

logger = get_logger(__name__)


class EngineState(Enum):
    """Trading engine states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class TradingEngine:
    """
    Main trading engine orchestrator

    Coordinates all trading components and manages system lifecycle.
    """

    def __init__(self, config: Dict):
        """
        Initialize trading engine

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.state = EngineState.STOPPED
        self.start_time = None
        self.shutdown_requested = False

        # Core components
        self.portfolio_manager: Optional[PortfolioManager] = None
        self.risk_monitor: Optional[RiskMonitor] = None
        self.notification_manager: Optional[NotificationManager] = None

        # Trading bots (will be initialized later)
        self.crypto_bot = None
        self.stock_bot = None

        # Worker threads
        self.monitor_thread: Optional[threading.Thread] = None
        self.crypto_thread: Optional[threading.Thread] = None
        self.stock_thread: Optional[threading.Thread] = None

        # Stats
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'uptime_seconds': 0
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Trading Engine initialized")

    def initialize(self):
        """Initialize all components"""
        try:
            self.state = EngineState.STARTING
            logger.info("Initializing trading engine components...")

            # 1. Initialize portfolio manager
            initial_capital = self.config.get('initial_capital', 10000.0)
            mode = self.config.get('mode', 'paper')

            self.portfolio_manager = PortfolioManager(
                initial_capital=initial_capital,
                mode=mode
            )
            logger.info(f"Portfolio Manager initialized: ${initial_capital:,.2f} ({mode} mode)")

            # 2. Initialize risk monitor
            self.risk_monitor = RiskMonitor(
                self.portfolio_manager,
                self.config.get('risk', {})
            )
            logger.info("Risk Monitor initialized")

            # 3. Initialize notification manager
            self.notification_manager = NotificationManager(
                self.config.get('notifications', {})
            )
            logger.info("Notification Manager initialized")

            # 4. Initialize trading bots
            if self.config.get('crypto_enabled', True):
                self.crypto_bot = CryptoBot(
                    self.portfolio_manager,
                    self.risk_monitor,
                    self.notification_manager,
                    self.config.get('crypto', {})
                )
                logger.info("Crypto Bot initialized")

            if self.config.get('stock_enabled', True):
                self.stock_bot = StockBot(
                    self.portfolio_manager,
                    self.risk_monitor,
                    self.notification_manager,
                    self.config.get('stock', {})
                )
                logger.info("Stock Bot initialized")

            # Send startup notification
            self.notification_manager.notify(
                title="🚀 Trading Engine Started",
                message=f"Mode: {mode}\nInitial Capital: ${initial_capital:,.2f}\n"
                       f"Crypto Bot: {'Enabled' if self.config.get('crypto_enabled', True) else 'Disabled'}\n"
                       f"Stock Bot: {'Enabled' if self.config.get('stock_enabled', True) else 'Disabled'}"
            )

            logger.info("All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            self.state = EngineState.ERROR
            return False

    def start(self):
        """Start the trading engine"""
        try:
            if self.state == EngineState.RUNNING:
                logger.warning("Engine is already running")
                return False

            # Initialize if not already done
            if self.portfolio_manager is None:
                if not self.initialize():
                    return False

            self.state = EngineState.RUNNING
            self.start_time = datetime.now()
            self.shutdown_requested = False

            logger.info("="*60)
            logger.info("STARTING TRADING ENGINE")
            logger.info("="*60)

            # Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="MonitorThread",
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("Monitor thread started")

            # Start crypto bot if enabled
            if self.config.get('crypto_enabled', True):
                self.crypto_thread = threading.Thread(
                    target=self._crypto_bot_loop,
                    name="CryptoThread",
                    daemon=True
                )
                self.crypto_thread.start()
                logger.info("Crypto bot thread started")

            # Start stock bot if enabled
            if self.config.get('stock_enabled', True):
                self.stock_thread = threading.Thread(
                    target=self._stock_bot_loop,
                    name="StockThread",
                    daemon=True
                )
                self.stock_thread.start()
                logger.info("Stock bot thread started")

            logger.info("Trading Engine is now RUNNING")
            logger.info("Press Ctrl+C to stop gracefully")

            return True

        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            self.state = EngineState.ERROR
            return False

    def stop(self):
        """Stop the trading engine"""
        try:
            if self.state == EngineState.STOPPED:
                logger.warning("Engine is already stopped")
                return True

            logger.info("="*60)
            logger.info("STOPPING TRADING ENGINE")
            logger.info("="*60)

            self.state = EngineState.STOPPING
            self.shutdown_requested = True

            # Wait for threads to finish
            threads_to_wait = [
                ("Monitor", self.monitor_thread),
                ("Crypto Bot", self.crypto_thread),
                ("Stock Bot", self.stock_thread)
            ]

            for name, thread in threads_to_wait:
                if thread and thread.is_alive():
                    logger.info(f"Waiting for {name} thread to stop...")
                    thread.join(timeout=5.0)
                    if thread.is_alive():
                        logger.warning(f"{name} thread did not stop gracefully")

            # Calculate final stats
            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
                self.stats['uptime_seconds'] = uptime

            # Send shutdown notification
            if self.notification_manager:
                self.notification_manager.notify(
                    title="🛑 Trading Engine Stopped",
                    message=f"Uptime: {self.stats['uptime_seconds']/3600:.1f} hours\n"
                           f"Total Trades: {self.stats['total_trades']}\n"
                           f"Total P&L: ${self.stats['total_pnl']:.2f}"
                )

            self.state = EngineState.STOPPED
            logger.info("Trading Engine stopped successfully")
            logger.info("="*60)

            return True

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.state = EngineState.ERROR
            return False

    def pause(self):
        """Pause trading (emergency controls)"""
        if self.state != EngineState.RUNNING:
            logger.warning("Cannot pause: engine not running")
            return False

        self.state = EngineState.PAUSED
        logger.warning("Trading PAUSED by user")

        if self.notification_manager:
            self.notification_manager.notify(
                title="⏸️ Trading Paused",
                message="Trading has been paused manually"
            )

        return True

    def resume(self):
        """Resume trading after pause"""
        if self.state != EngineState.PAUSED:
            logger.warning("Cannot resume: engine not paused")
            return False

        self.state = EngineState.RUNNING
        logger.info("Trading RESUMED")

        if self.notification_manager:
            self.notification_manager.notify(
                title="▶️ Trading Resumed",
                message="Trading has been resumed"
            )

        return True

    def get_status(self) -> Dict:
        """Get current engine status"""
        status = {
            'state': self.state.value,
            'uptime_seconds': 0,
            'portfolio_value': 0.0,
            'total_pnl': 0.0,
            'open_positions': 0,
            'total_trades': self.stats['total_trades'],
            'crypto_bot_running': self.crypto_thread and self.crypto_thread.is_alive() if self.crypto_thread else False,
            'stock_bot_running': self.stock_thread and self.stock_thread.is_alive() if self.stock_thread else False,
            'monitor_running': self.monitor_thread and self.monitor_thread.is_alive() if self.monitor_thread else False
        }

        if self.start_time:
            status['uptime_seconds'] = (datetime.now() - self.start_time).total_seconds()

        if self.portfolio_manager:
            metrics = self.portfolio_manager.get_portfolio_metrics()
            status['portfolio_value'] = metrics['total_value']
            status['total_pnl'] = metrics['total_pnl']
            status['open_positions'] = metrics['num_positions']

        return status

    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Monitor loop started")

        while not self.shutdown_requested and self.state in [EngineState.RUNNING, EngineState.PAUSED]:
            try:
                # Check risk limits every 60 seconds
                if self.state == EngineState.RUNNING:
                    # Perform risk checks
                    if self.risk_monitor:
                        risk_level, alerts = self.risk_monitor.check_all_risks()

                        # Log risk level changes
                        if risk_level.value != 'low':
                            logger.warning(f"Risk level: {risk_level.value.upper()}")

                    # Update stats
                    if self.portfolio_manager:
                        metrics = self.portfolio_manager.get_portfolio_metrics()
                        self.stats['total_pnl'] = metrics['total_pnl']
                        self.stats['total_trades'] = metrics['num_closed_trades']
                        self.stats['winning_trades'] = metrics['winning_trades']
                        self.stats['losing_trades'] = metrics['losing_trades']

                # Sleep for monitoring interval
                time.sleep(self.config.get('monitor_interval', 60))

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)

        logger.info("Monitor loop stopped")

    def _crypto_bot_loop(self):
        """Crypto trading bot loop"""
        logger.info("Crypto bot loop started")

        while not self.shutdown_requested and self.state in [EngineState.RUNNING, EngineState.PAUSED]:
            try:
                if self.state == EngineState.RUNNING and self.crypto_bot:
                    # Execute crypto bot trading cycle
                    self.crypto_bot.execute_cycle()

                # Sleep for bot interval
                time.sleep(self.config.get('crypto_interval', 300))  # 5 minutes default

            except Exception as e:
                logger.error(f"Error in crypto bot loop: {e}")
                time.sleep(30)

        logger.info("Crypto bot loop stopped")

    def _stock_bot_loop(self):
        """Stock trading bot loop"""
        logger.info("Stock bot loop started")

        while not self.shutdown_requested and self.state in [EngineState.RUNNING, EngineState.PAUSED]:
            try:
                if self.state == EngineState.RUNNING and self.stock_bot:
                    # Execute stock bot trading cycle
                    self.stock_bot.execute_cycle()

                # Sleep for bot interval
                time.sleep(self.config.get('stock_interval', 300))  # 5 minutes default

            except Exception as e:
                logger.error(f"Error in stock bot loop: {e}")
                time.sleep(30)

        logger.info("Stock bot loop stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}, shutting down gracefully...")

        self.shutdown_requested = True
        self.stop()
        sys.exit(0)

    def run_forever(self):
        """Run the engine until stopped"""
        if not self.start():
            logger.error("Failed to start engine")
            return False

        try:
            # Keep main thread alive
            while not self.shutdown_requested:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

        return True


if __name__ == "__main__":
    # Test the trading engine
    print("="*60)
    print("Testing Trading Engine")
    print("="*60)

    # Test configuration
    config = {
        'initial_capital': 10000.0,
        'mode': 'paper',
        'crypto_enabled': True,
        'stock_enabled': True,
        'monitor_interval': 10,  # 10 seconds for testing
        'crypto_interval': 30,
        'stock_interval': 30,
        'notifications': {
            'console_enabled': True,
            'telegram_enabled': False
        },
        'risk': {
            'max_open_positions': 5,
            'max_position_size_pct': 0.20
        }
    }

    # Create and start engine
    engine = TradingEngine(config)

    try:
        print("\nStarting engine (will run for 30 seconds)...")
        engine.start()

        # Run for 30 seconds
        time.sleep(30)

        # Test pause
        print("\nPausing engine...")
        engine.pause()
        time.sleep(5)

        # Test resume
        print("\nResuming engine...")
        engine.resume()
        time.sleep(5)

        # Get status
        print("\nEngine Status:")
        status = engine.get_status()
        for key, value in status.items():
            print(f"  {key}: {value}")

    finally:
        print("\nStopping engine...")
        engine.stop()

    print("\n✓ Trading engine test complete!")
    print("="*60)
