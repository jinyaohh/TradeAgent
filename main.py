#!/usr/bin/env python3
"""
TradeAgent - Main Entry Point

Command-line interface for controlling the trading system.

Usage:
    python main.py start [--config CONFIG_FILE]
    python main.py stop
    python main.py status
    python main.py pause
    python main.py resume
    python main.py dashboard
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path
import yaml
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.trading_engine import TradingEngine
from monitoring.logger import get_logger

logger = get_logger(__name__)


class TradeAgentCLI:
    """Command-line interface for TradeAgent"""

    def __init__(self):
        self.config_file = Path("config/trading.yaml")
        self.state_file = Path(".tradeagent_state.json")

    def load_config(self, config_path: str = None) -> dict:
        """Load configuration from YAML file"""
        if config_path:
            self.config_file = Path(config_path)

        if not self.config_file.exists():
            logger.error(f"Config file not found: {self.config_file}")
            return self._get_default_config()

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration"""
        return {
            'initial_capital': 10000.0,
            'mode': 'paper',
            'crypto_enabled': True,
            'stock_enabled': True,
            'monitor_interval': 60,
            'crypto_interval': 300,
            'stock_interval': 300,
            'notifications': {
                'console_enabled': True,
                'telegram_enabled': False
            },
            'risk': {
                'max_open_positions': 10,
                'max_position_size_pct': 0.20,
                'max_daily_loss_pct': 0.05,
                'max_drawdown_pct': 0.20,
                'min_cash_reserve_pct': 0.15
            }
        }

    def save_state(self, state: dict):
        """Save engine state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def load_state(self) -> dict:
        """Load engine state from file"""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}

    def cmd_start(self, args):
        """Start the trading engine"""
        print("="*60)
        print("TRADEAGENT - STARTING")
        print("="*60)

        # Load configuration
        config = self.load_config(args.config)

        # Display configuration
        print("\nConfiguration:")
        print(f"  Mode: {config.get('mode', 'paper').upper()}")
        print(f"  Initial Capital: ${config.get('initial_capital', 10000):,.2f}")
        print(f"  Crypto Bot: {'Enabled' if config.get('crypto_enabled') else 'Disabled'}")
        print(f"  Stock Bot: {'Enabled' if config.get('stock_enabled') else 'Disabled'}")

        # Warning for live mode
        if config.get('mode') == 'live':
            print("\n⚠️  WARNING: LIVE TRADING MODE ⚠️")
            print("You are about to start trading with REAL MONEY!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return

        print("\nStarting trading engine...")

        try:
            # Create and start engine
            engine = TradingEngine(config)

            # Save initial state
            self.save_state({
                'state': 'starting',
                'start_time': datetime.now().isoformat(),
                'config': config
            })

            # Run forever (until Ctrl+C)
            engine.run_forever()

        except KeyboardInterrupt:
            print("\n\nShutdown requested by user")
        except Exception as e:
            logger.error(f"Engine error: {e}")
            print(f"\n❌ Error: {e}")
        finally:
            self.save_state({'state': 'stopped', 'stop_time': datetime.now().isoformat()})

    def cmd_stop(self, args):
        """Stop the trading engine"""
        print("Stopping trading engine...")
        print("⚠️  This feature requires engine to be running as a service")
        print("For now, use Ctrl+C in the running terminal to stop")

    def cmd_status(self, args):
        """Show engine status"""
        print("="*60)
        print("TRADEAGENT - STATUS")
        print("="*60)

        # Load state
        state = self.load_state()

        if not state:
            print("\nStatus: STOPPED")
            print("No active trading session found")
            return

        print(f"\nLast Known State: {state.get('state', 'unknown').upper()}")

        if 'start_time' in state:
            start_time = datetime.fromisoformat(state['start_time'])
            uptime = datetime.now() - start_time
            print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Uptime: {uptime}")

        if 'config' in state:
            config = state['config']
            print(f"\nConfiguration:")
            print(f"  Mode: {config.get('mode', 'unknown')}")
            print(f"  Capital: ${config.get('initial_capital', 0):,.2f}")

        print("\n💡 For real-time status, use the dashboard:")
        print("   streamlit run dashboard/app.py")

    def cmd_pause(self, args):
        """Pause trading"""
        print("Pausing trading...")
        print("⚠️  This feature requires engine to be running as a service")
        print("Use the dashboard emergency controls to pause trading")

    def cmd_resume(self, args):
        """Resume trading"""
        print("Resuming trading...")
        print("⚠️  This feature requires engine to be running as a service")
        print("Use the dashboard emergency controls to resume trading")

    def cmd_dashboard(self, args):
        """Launch the dashboard"""
        print("="*60)
        print("LAUNCHING DASHBOARD")
        print("="*60)

        dashboard_path = Path(__file__).parent / "dashboard" / "app.py"

        if not dashboard_path.exists():
            print(f"❌ Dashboard not found at {dashboard_path}")
            return

        print("\n📊 Starting Streamlit dashboard...")
        print("The dashboard will open in your default browser")
        print("Press Ctrl+C to stop the dashboard\n")

        try:
            subprocess.run([
                sys.executable, "-m", "streamlit", "run",
                str(dashboard_path),
                "--server.headless", "true"
            ])
        except KeyboardInterrupt:
            print("\n\nDashboard stopped")
        except Exception as e:
            print(f"❌ Failed to start dashboard: {e}")

    def cmd_config(self, args):
        """Show current configuration"""
        print("="*60)
        print("CURRENT CONFIGURATION")
        print("="*60)

        config = self.load_config(args.config)

        print("\n" + yaml.dump(config, default_flow_style=False))

    def cmd_help(self, args):
        """Show help"""
        print("""
TradeAgent - Automated Trading System

COMMANDS:
  start       Start the trading engine
  stop        Stop the trading engine
  status      Show current status
  pause       Pause trading
  resume      Resume trading
  dashboard   Launch the monitoring dashboard
  config      Show current configuration
  help        Show this help message

USAGE:
  python main.py start [--config CONFIG_FILE]
  python main.py stop
  python main.py status
  python main.py dashboard

EXAMPLES:
  # Start with default configuration
  python main.py start

  # Start with custom configuration
  python main.py start --config config/my_config.yaml

  # Check status
  python main.py status

  # Launch dashboard
  python main.py dashboard

For more information, see README.md
""")


def main():
    """Main entry point"""
    cli = TradeAgentCLI()

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="TradeAgent - Automated Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['start', 'stop', 'status', 'pause', 'resume', 'dashboard', 'config', 'help'],
        default='help',
        help='Command to execute'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )

    args = parser.parse_args()

    # Execute command
    commands = {
        'start': cli.cmd_start,
        'stop': cli.cmd_stop,
        'status': cli.cmd_status,
        'pause': cli.cmd_pause,
        'resume': cli.cmd_resume,
        'dashboard': cli.cmd_dashboard,
        'config': cli.cmd_config,
        'help': cli.cmd_help
    }

    command_func = commands.get(args.command, cli.cmd_help)
    command_func(args)


if __name__ == "__main__":
    main()
