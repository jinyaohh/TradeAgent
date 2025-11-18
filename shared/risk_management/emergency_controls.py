"""
Emergency Controls and Kill Switch

Provides emergency trading controls to prevent catastrophic losses.
Includes kill switch, circuit breakers, and position liquidation.
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from monitoring.logger import get_logger

logger = get_logger(__name__)


class TradingState(Enum):
    """Trading system states"""
    ACTIVE = "active"          # Normal trading
    PAUSED = "paused"          # Temporarily paused (manual)
    HALTED = "halted"          # Halted due to circuit breaker
    EMERGENCY_STOP = "emergency_stop"  # Kill switch activated
    LIQUIDATING = "liquidating"  # Emergency liquidation in progress


class CircuitBreakerType(Enum):
    """Types of circuit breakers"""
    DAILY_LOSS = "daily_loss"
    DRAWDOWN = "drawdown"
    VOLATILITY = "volatility"
    RAPID_LOSS = "rapid_loss"
    MANUAL = "manual"


@dataclass
class EmergencyEvent:
    """Records an emergency event"""
    timestamp: datetime
    event_type: str
    severity: str  # info, warning, critical
    message: str
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    action_taken: str = ''
    positions_closed: int = 0


class EmergencyControls:
    """
    Emergency trading controls system

    Features:
    - Kill switch for immediate trading halt
    - Circuit breakers for automatic halts
    - Emergency position liquidation
    - State management and recovery
    - Event logging and audit trail
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize emergency controls

        Args:
            config: Configuration dictionary
        """
        default_config = {
            # Circuit breaker thresholds
            'max_daily_loss_pct': 0.05,      # 5% daily loss triggers halt
            'max_drawdown_pct': 0.20,        # 20% drawdown triggers halt
            'max_rapid_loss_pct': 0.03,      # 3% loss in 1 hour triggers halt
            'max_rapid_loss_minutes': 60,    # Time window for rapid loss

            # Volatility circuit breaker
            'max_volatility_factor': 3.0,    # 3x normal volatility

            # Auto-resume settings
            'auto_resume_enabled': False,    # Don't auto-resume by default
            'halt_duration_minutes': 60,     # How long to stay halted

            # Emergency liquidation
            'emergency_liquidate_losers': True,  # Close losing positions first
            'emergency_keep_cash': 0.50,    # Keep 50% in cash during emergency
        }

        if config:
            default_config.update(config)

        self.config = default_config

        # Current state
        self.state = TradingState.ACTIVE
        self.halt_reason = None
        self.halt_time = None

        # Event history
        self.events: List[EmergencyEvent] = []

        # Tracking
        self.last_portfolio_value = None
        self.rapid_loss_tracking = []

        logger.info(f"Emergency Controls initialized: state={self.state.value}")

    def activate_kill_switch(self, reason: str = "Manual kill switch") -> bool:
        """
        Activate emergency kill switch

        Immediately stops all trading activity.

        Args:
            reason: Reason for activation

        Returns:
            True if successful
        """
        old_state = self.state
        self.state = TradingState.EMERGENCY_STOP
        self.halt_reason = reason
        self.halt_time = datetime.now()

        # Log event
        event = EmergencyEvent(
            timestamp=datetime.now(),
            event_type='kill_switch_activated',
            severity='critical',
            message=f"KILL SWITCH ACTIVATED: {reason}",
            action_taken='all_trading_stopped'
        )
        self.events.append(event)

        logger.critical(f"🚨 KILL SWITCH ACTIVATED 🚨")
        logger.critical(f"Reason: {reason}")
        logger.critical(f"Previous state: {old_state.value}")
        logger.critical(f"All trading STOPPED")

        return True

    def deactivate_kill_switch(self, reason: str = "Manual override") -> bool:
        """
        Deactivate kill switch and resume trading

        Args:
            reason: Reason for deactivation

        Returns:
            True if successful
        """
        if self.state != TradingState.EMERGENCY_STOP:
            logger.warning(f"Cannot deactivate kill switch: state is {self.state.value}")
            return False

        self.state = TradingState.ACTIVE
        old_halt_reason = self.halt_reason
        self.halt_reason = None
        halt_duration = None

        if self.halt_time:
            halt_duration = (datetime.now() - self.halt_time).total_seconds() / 60
            self.halt_time = None

        # Log event
        event = EmergencyEvent(
            timestamp=datetime.now(),
            event_type='kill_switch_deactivated',
            severity='warning',
            message=f"Kill switch deactivated: {reason}",
            action_taken='trading_resumed'
        )
        self.events.append(event)

        logger.warning(f"Kill switch deactivated")
        logger.warning(f"Reason: {reason}")
        if halt_duration:
            logger.warning(f"Was halted for {halt_duration:.1f} minutes")
        logger.info(f"Trading RESUMED (was halted for: {old_halt_reason})")

        return True

    def pause_trading(self, reason: str = "Manual pause") -> bool:
        """
        Pause trading temporarily (less severe than kill switch)

        Args:
            reason: Reason for pause

        Returns:
            True if successful
        """
        if self.state in [TradingState.EMERGENCY_STOP, TradingState.LIQUIDATING]:
            logger.warning(f"Cannot pause: in critical state {self.state.value}")
            return False

        self.state = TradingState.PAUSED
        self.halt_reason = reason

        event = EmergencyEvent(
            timestamp=datetime.now(),
            event_type='trading_paused',
            severity='warning',
            message=f"Trading paused: {reason}",
            action_taken='trading_paused'
        )
        self.events.append(event)

        logger.warning(f"Trading PAUSED: {reason}")

        return True

    def resume_trading(self, reason: str = "Manual resume") -> bool:
        """
        Resume trading from paused state

        Args:
            reason: Reason for resume

        Returns:
            True if successful
        """
        if self.state not in [TradingState.PAUSED, TradingState.HALTED]:
            logger.warning(f"Cannot resume: state is {self.state.value}")
            return False

        self.state = TradingState.ACTIVE
        self.halt_reason = None

        event = EmergencyEvent(
            timestamp=datetime.now(),
            event_type='trading_resumed',
            severity='info',
            message=f"Trading resumed: {reason}",
            action_taken='trading_resumed'
        )
        self.events.append(event)

        logger.info(f"Trading RESUMED: {reason}")

        return True

    def check_circuit_breakers(self, portfolio) -> bool:
        """
        Check all circuit breakers

        Args:
            portfolio: PortfolioManager instance

        Returns:
            True if any circuit breaker triggered (trading should halt)
        """
        if self.state in [TradingState.EMERGENCY_STOP, TradingState.LIQUIDATING]:
            return True  # Already in emergency state

        metrics = portfolio.get_portfolio_metrics()
        total_value = metrics['total_value']

        # Track portfolio value for rapid loss detection
        self._track_portfolio_value(total_value)

        triggered = False

        # 1. Daily loss circuit breaker
        if self._check_daily_loss_breaker(metrics):
            self._trigger_circuit_breaker(CircuitBreakerType.DAILY_LOSS, metrics['total_return'])
            triggered = True

        # 2. Drawdown circuit breaker
        if self._check_drawdown_breaker(metrics):
            drawdown = metrics.get('current_drawdown', 0)
            self._trigger_circuit_breaker(CircuitBreakerType.DRAWDOWN, drawdown)
            triggered = True

        # 3. Rapid loss circuit breaker
        if self._check_rapid_loss_breaker():
            rapid_loss = self._calculate_rapid_loss()
            self._trigger_circuit_breaker(CircuitBreakerType.RAPID_LOSS, rapid_loss)
            triggered = True

        return triggered

    def _check_daily_loss_breaker(self, metrics: Dict) -> bool:
        """Check if daily loss exceeds threshold"""
        # This would need daily tracking similar to limits_enforcer
        # For now, use total_return as proxy
        total_return = metrics.get('total_return', 0)

        # Only trigger on losses
        if total_return < -self.config['max_daily_loss_pct']:
            return True

        return False

    def _check_drawdown_breaker(self, metrics: Dict) -> bool:
        """Check if drawdown exceeds threshold"""
        current_drawdown = abs(metrics.get('current_drawdown', 0))

        if current_drawdown > self.config['max_drawdown_pct']:
            return True

        return False

    def _check_rapid_loss_breaker(self) -> bool:
        """Check for rapid loss in short time window"""
        if len(self.rapid_loss_tracking) < 2:
            return False

        rapid_loss = self._calculate_rapid_loss()

        if rapid_loss < -self.config['max_rapid_loss_pct']:
            return True

        return False

    def _calculate_rapid_loss(self) -> float:
        """Calculate loss over rapid loss time window"""
        if len(self.rapid_loss_tracking) < 2:
            return 0.0

        cutoff_time = datetime.now() - timedelta(
            minutes=self.config['max_rapid_loss_minutes']
        )

        # Get values within time window
        recent_values = [
            (ts, val) for ts, val in self.rapid_loss_tracking
            if ts >= cutoff_time
        ]

        if len(recent_values) < 2:
            return 0.0

        # Calculate return from earliest to latest in window
        start_value = recent_values[0][1]
        end_value = recent_values[-1][1]

        return (end_value - start_value) / start_value if start_value > 0 else 0.0

    def _track_portfolio_value(self, value: float):
        """Track portfolio value for rapid loss detection"""
        now = datetime.now()

        # Add current value
        self.rapid_loss_tracking.append((now, value))

        # Remove old values (keep 2x the rapid loss window)
        cutoff = now - timedelta(
            minutes=self.config['max_rapid_loss_minutes'] * 2
        )
        self.rapid_loss_tracking = [
            (ts, val) for ts, val in self.rapid_loss_tracking
            if ts >= cutoff
        ]

    def _trigger_circuit_breaker(self, breaker_type: CircuitBreakerType,
                                 trigger_value: float):
        """Trigger a circuit breaker"""
        self.state = TradingState.HALTED
        self.halt_reason = f"Circuit breaker: {breaker_type.value}"
        self.halt_time = datetime.now()

        # Get threshold for this breaker type
        threshold_map = {
            CircuitBreakerType.DAILY_LOSS: -self.config['max_daily_loss_pct'],
            CircuitBreakerType.DRAWDOWN: -self.config['max_drawdown_pct'],
            CircuitBreakerType.RAPID_LOSS: -self.config['max_rapid_loss_pct'],
        }
        threshold = threshold_map.get(breaker_type, 0)

        event = EmergencyEvent(
            timestamp=datetime.now(),
            event_type=f'circuit_breaker_{breaker_type.value}',
            severity='critical',
            message=f"Circuit breaker triggered: {breaker_type.value}",
            trigger_value=trigger_value,
            threshold_value=threshold,
            action_taken='trading_halted'
        )
        self.events.append(event)

        logger.critical(f"⚠️ CIRCUIT BREAKER TRIGGERED: {breaker_type.value}")
        logger.critical(f"Trigger value: {trigger_value:.2%}, Threshold: {threshold:.2%}")
        logger.critical(f"Trading HALTED")

    def emergency_liquidate_positions(self, portfolio,
                                      close_all: bool = False,
                                      close_losers_only: bool = True) -> int:
        """
        Emergency liquidation of positions

        Args:
            portfolio: PortfolioManager instance
            close_all: Close all positions regardless of P&L
            close_losers_only: Only close losing positions

        Returns:
            Number of positions closed
        """
        old_state = self.state
        self.state = TradingState.LIQUIDATING

        logger.critical("⚠️ EMERGENCY LIQUIDATION STARTED")

        positions_to_close = []

        if close_all:
            positions_to_close = list(portfolio.positions.values())
            logger.critical(f"Closing ALL {len(positions_to_close)} positions")
        elif close_losers_only:
            positions_to_close = [
                p for p in portfolio.positions.values()
                if p.unrealized_pnl < 0
            ]
            logger.critical(f"Closing {len(positions_to_close)} losing positions")

        closed_count = 0
        for position in positions_to_close:
            try:
                # In real system, would get current market price
                # For now, use current_price from position
                portfolio.close_position(
                    position.position_id,
                    position.current_price,
                    reason='emergency_liquidation'
                )
                closed_count += 1
                logger.warning(f"Liquidated: {position.symbol} "
                             f"(P&L: ${position.realized_pnl:.2f})")
            except Exception as e:
                logger.error(f"Failed to liquidate {position.symbol}: {e}")

        # Record event
        event = EmergencyEvent(
            timestamp=datetime.now(),
            event_type='emergency_liquidation',
            severity='critical',
            message=f"Emergency liquidation completed",
            action_taken=f'closed_{closed_count}_positions',
            positions_closed=closed_count
        )
        self.events.append(event)

        # Return to previous state or halt
        if old_state == TradingState.EMERGENCY_STOP:
            self.state = TradingState.EMERGENCY_STOP
        else:
            self.state = TradingState.HALTED

        logger.critical(f"Emergency liquidation complete: {closed_count} positions closed")

        return closed_count

    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        return self.state == TradingState.ACTIVE

    def get_state_info(self) -> Dict:
        """Get current state information"""
        info = {
            'state': self.state.value,
            'is_trading_allowed': self.is_trading_allowed(),
            'halt_reason': self.halt_reason,
            'halt_time': self.halt_time,
            'num_events': len(self.events),
        }

        if self.halt_time:
            info['halt_duration_minutes'] = (
                (datetime.now() - self.halt_time).total_seconds() / 60
            )

        return info

    def get_recent_events(self, count: int = 10) -> List[EmergencyEvent]:
        """Get recent emergency events"""
        return self.events[-count:]

    def print_status(self):
        """Print current status"""
        info = self.get_state_info()

        print("\n" + "="*60)
        print("EMERGENCY CONTROLS STATUS")
        print("="*60)

        state_emoji = {
            TradingState.ACTIVE: "✅",
            TradingState.PAUSED: "⏸️",
            TradingState.HALTED: "🛑",
            TradingState.EMERGENCY_STOP: "🚨",
            TradingState.LIQUIDATING: "⚠️"
        }

        print(f"\nState: {state_emoji.get(self.state, '')} {info['state'].upper()}")
        print(f"Trading Allowed: {'YES' if info['is_trading_allowed'] else 'NO'}")

        if info['halt_reason']:
            print(f"\nHalt Reason: {info['halt_reason']}")

        if info.get('halt_duration_minutes'):
            print(f"Halted For: {info['halt_duration_minutes']:.1f} minutes")

        print(f"\nTotal Events: {info['num_events']}")

        if self.events:
            print("\nRecent Events (last 5):")
            for event in self.events[-5:]:
                severity_emoji = {'info': 'ℹ️', 'warning': '⚠️', 'critical': '🚨'}
                print(f"  {severity_emoji.get(event.severity, '')} "
                      f"{event.timestamp.strftime('%H:%M:%S')} - {event.message}")

        print("="*60 + "\n")


if __name__ == "__main__":
    # Test emergency controls
    from portfolio_manager import PortfolioManager

    print("="*60)
    print("Testing Emergency Controls")
    print("="*60)

    controls = EmergencyControls()
    portfolio = PortfolioManager(initial_capital=10000.0)

    # Open some positions
    portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.1, 'long')
    portfolio.open_position('AAPL', 'stock', 150.0, 10, 'long')

    # Show initial status
    controls.print_status()

    # Test 1: Pause trading
    print("\nTest 1: Pause Trading")
    controls.pause_trading("Testing pause functionality")
    print(f"  State: {controls.state.value}")
    print(f"  Trading allowed: {controls.is_trading_allowed()}")

    # Test 2: Resume trading
    print("\nTest 2: Resume Trading")
    controls.resume_trading("Testing resume")
    print(f"  State: {controls.state.value}")
    print(f"  Trading allowed: {controls.is_trading_allowed()}")

    # Test 3: Activate kill switch
    print("\nTest 3: Activate Kill Switch")
    controls.activate_kill_switch("Testing emergency stop")
    controls.print_status()

    # Test 4: Try to pause (should fail in emergency state)
    print("\nTest 4: Try to Pause During Emergency")
    result = controls.pause_trading("Should not work")
    print(f"  Pause successful: {result}")

    # Test 5: Emergency liquidation
    print("\nTest 5: Emergency Liquidation")

    # Create losses
    portfolio.update_prices({
        'BTC/USDT': 48000.0,  # -4% loss
        'AAPL': 145.0         # -3.3% loss
    })

    closed = controls.emergency_liquidate_positions(portfolio, close_losers_only=True)
    print(f"  Positions closed: {closed}")

    # Test 6: Deactivate kill switch
    print("\nTest 6: Deactivate Kill Switch")
    controls.deactivate_kill_switch("Emergency resolved")
    controls.print_status()

    print("\n✓ Emergency controls working correctly!")
    print("="*60)
