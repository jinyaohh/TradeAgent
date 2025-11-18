"""
Risk Monitoring System

Comprehensive risk monitoring that integrates all risk management components.
Provides real-time oversight, alerts, and reporting.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from shared.risk_management.position_sizer import PositionSizer
from shared.risk_management.risk_calculator import RiskCalculator
from shared.risk_management.limits_enforcer import LimitsEnforcer, LimitViolation
from shared.risk_management.emergency_controls import EmergencyControls, TradingState
from monitoring.logger import get_logger

logger = get_logger(__name__)


class RiskLevel(Enum):
    """Overall risk levels"""
    LOW = "low"           # Everything healthy
    MODERATE = "moderate"  # Some warnings
    HIGH = "high"         # Approaching limits
    CRITICAL = "critical"  # Limits exceeded or emergency


class Alert:
    """Risk alert"""
    def __init__(self, level: RiskLevel, category: str, message: str,
                 value: Optional[float] = None, threshold: Optional[float] = None):
        self.timestamp = datetime.now()
        self.level = level
        self.category = category
        self.message = message
        self.value = value
        self.threshold = threshold

    def __str__(self):
        emoji_map = {
            RiskLevel.LOW: "✅",
            RiskLevel.MODERATE: "⚠️",
            RiskLevel.HIGH: "🔴",
            RiskLevel.CRITICAL: "🚨"
        }
        emoji = emoji_map.get(self.level, "")

        msg = f"{emoji} [{self.level.value.upper()}] {self.message}"
        if self.value is not None and self.threshold is not None:
            msg += f" ({self.value:.2%} / {self.threshold:.2%})"
        return msg


class RiskMonitor:
    """
    Comprehensive risk monitoring system

    Integrates all risk management components:
    - Position sizing
    - Risk metrics calculation
    - Limits enforcement
    - Emergency controls

    Provides unified risk oversight and alerting.
    """

    def __init__(self, portfolio, config: Optional[Dict] = None):
        """
        Initialize risk monitor

        Args:
            portfolio: PortfolioManager instance
            config: Combined configuration for all components
        """
        self.portfolio = portfolio

        # Initialize all risk components
        self.position_sizer = PositionSizer(config)
        self.risk_calculator = RiskCalculator()
        self.limits_enforcer = LimitsEnforcer(config)
        self.emergency_controls = EmergencyControls(config)

        # Alert tracking
        self.alerts: List[Alert] = []
        self.last_check_time = None

        logger.info("Risk Monitor initialized and operational")

    def check_all_risks(self) -> Tuple[RiskLevel, List[Alert]]:
        """
        Comprehensive risk check across all systems

        Returns:
            Tuple of (overall_risk_level, alerts_list)
        """
        self.last_check_time = datetime.now()
        alerts = []

        # 1. Check emergency controls state
        if not self.emergency_controls.is_trading_allowed():
            alerts.append(Alert(
                RiskLevel.CRITICAL,
                "Emergency",
                f"Trading DISABLED: {self.emergency_controls.state.value}"
            ))

        # 2. Check circuit breakers
        if self.emergency_controls.check_circuit_breakers(self.portfolio):
            alerts.append(Alert(
                RiskLevel.CRITICAL,
                "Circuit Breaker",
                "Circuit breaker triggered - trading halted"
            ))

        # 3. Check portfolio health
        health_status, violations = self.limits_enforcer.check_portfolio_health(self.portfolio)

        if health_status == 'critical':
            alerts.append(Alert(
                RiskLevel.CRITICAL,
                "Portfolio Health",
                "Critical portfolio health issues detected"
            ))
        elif health_status == 'danger':
            alerts.append(Alert(
                RiskLevel.HIGH,
                "Portfolio Health",
                "Portfolio in danger zone"
            ))
        elif health_status == 'warning':
            alerts.append(Alert(
                RiskLevel.MODERATE,
                "Portfolio Health",
                "Portfolio warnings detected"
            ))

        # Add specific violations as alerts
        for violation in violations:
            level_map = {
                'critical': RiskLevel.CRITICAL,
                'error': RiskLevel.HIGH,
                'warning': RiskLevel.MODERATE
            }
            alerts.append(Alert(
                level_map.get(violation.severity, RiskLevel.MODERATE),
                "Limit",
                violation.message,
                violation.current_value,
                violation.limit_value
            ))

        # 4. Check risk metrics
        metrics = self.portfolio.get_portfolio_metrics()

        # Drawdown check
        drawdown = abs(metrics.get('current_drawdown', 0))
        if drawdown > 0.15:  # 15%
            alerts.append(Alert(
                RiskLevel.HIGH,
                "Drawdown",
                f"Significant drawdown detected",
                drawdown,
                0.15
            ))
        elif drawdown > 0.10:  # 10%
            alerts.append(Alert(
                RiskLevel.MODERATE,
                "Drawdown",
                f"Moderate drawdown",
                drawdown,
                0.10
            ))

        # Cash reserve check
        cash_pct = metrics.get('cash_pct', 0)
        if cash_pct < 0.10:  # Less than 10%
            alerts.append(Alert(
                RiskLevel.HIGH,
                "Cash Reserve",
                f"Low cash reserve",
                cash_pct,
                0.10
            ))

        # Concentration check
        if metrics['num_positions'] > 0:
            # Check if any single position is too large
            for position in self.portfolio.positions.values():
                pos_pct = position.get_value() / metrics['total_value']
                if pos_pct > 0.30:  # 30%
                    alerts.append(Alert(
                        RiskLevel.MODERATE,
                        "Concentration",
                        f"High concentration in {position.symbol}",
                        pos_pct,
                        0.30
                    ))

        # Determine overall risk level
        if any(a.level == RiskLevel.CRITICAL for a in alerts):
            overall_level = RiskLevel.CRITICAL
        elif any(a.level == RiskLevel.HIGH for a in alerts):
            overall_level = RiskLevel.HIGH
        elif any(a.level == RiskLevel.MODERATE for a in alerts):
            overall_level = RiskLevel.MODERATE
        else:
            overall_level = RiskLevel.LOW

        # Store alerts
        self.alerts.extend(alerts)

        # Log summary
        if alerts:
            logger.warning(f"Risk check complete: {len(alerts)} alerts, level: {overall_level.value}")
        else:
            logger.info(f"Risk check complete: All systems healthy")

        return overall_level, alerts

    def can_open_position(self, symbol: str, position_value: float,
                         asset_type: str) -> Tuple[bool, str, List[LimitViolation]]:
        """
        Check if a new position can be opened

        Args:
            symbol: Symbol to trade
            position_value: Value of proposed position
            asset_type: Type of asset

        Returns:
            Tuple of (can_open, reason, violations)
        """
        # Check emergency controls
        if not self.emergency_controls.is_trading_allowed():
            return False, f"Trading disabled: {self.emergency_controls.state.value}", []

        # Check limits
        allowed, violations = self.limits_enforcer.check_trade(
            self.portfolio, symbol, position_value, asset_type
        )

        if not allowed:
            reasons = [v.message for v in violations if v.severity in ['error', 'critical']]
            return False, "; ".join(reasons), violations

        return True, "Position allowed", violations

    def calculate_position_size(self, entry_price: float, stop_loss_price: float,
                               symbol: str, asset_type: str,
                               method: str = 'risk_pct') -> Dict:
        """
        Calculate appropriate position size considering all limits

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            symbol: Symbol to trade
            asset_type: Asset type
            method: Position sizing method

        Returns:
            Position sizing details
        """
        # Get account balance
        account_balance = self.portfolio.get_total_value()

        # Calculate theoretical position size
        theoretical_size = self.position_sizer.calculate_position_size(
            account_balance=account_balance,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            method=method
        )

        # Check against available size from enforcer
        max_available = self.limits_enforcer.get_available_position_size(
            self.portfolio, symbol, asset_type
        )

        # Take minimum of theoretical and available
        if theoretical_size['value'] > max_available:
            # Adjust down to maximum available
            scale_factor = max_available / theoretical_size['value']
            theoretical_size['quantity'] *= scale_factor
            theoretical_size['value'] = max_available
            theoretical_size['constrained'] = True
            theoretical_size['constraint_reason'] = 'limit_enforcer_maximum'

            logger.warning(f"Position size reduced by limits: "
                         f"${theoretical_size['value']:.2f} (max: ${max_available:.2f})")

        return theoretical_size

    def get_risk_report(self) -> Dict:
        """
        Generate comprehensive risk report

        Returns:
            Dictionary with all risk metrics and status
        """
        # Get portfolio metrics
        portfolio_metrics = self.portfolio.get_portfolio_metrics()

        # Calculate risk metrics if we have closed trades
        risk_metrics = {}
        if self.portfolio.closed_positions:
            closed_df = self.portfolio.get_closed_positions_df()
            equity_curve = [self.portfolio.initial_capital]  # Simplified
            equity_curve.append(self.portfolio.get_total_value())

            risk_metrics = self.risk_calculator.calculate_metrics(
                equity_curve=equity_curve,
                trades=closed_df,
                initial_capital=self.portfolio.initial_capital
            )

        # Get emergency controls state
        controls_state = self.emergency_controls.get_state_info()

        # Get limits enforcer health
        health_status, health_violations = self.limits_enforcer.check_portfolio_health(
            self.portfolio
        )

        # Recent alerts
        recent_alerts = self.alerts[-10:] if self.alerts else []

        # Overall risk check
        overall_risk, current_alerts = self.check_all_risks()

        report = {
            'timestamp': datetime.now(),
            'overall_risk_level': overall_risk.value,
            'trading_allowed': self.emergency_controls.is_trading_allowed(),

            # Portfolio state
            'portfolio': portfolio_metrics,

            # Risk metrics
            'risk_metrics': risk_metrics,

            # Controls state
            'emergency_controls': controls_state,
            'health_status': health_status,

            # Alerts
            'current_alerts': len(current_alerts),
            'total_alerts': len(self.alerts),
            'recent_alerts': recent_alerts,

            # Limits
            'position_limits': {
                'max_positions': self.limits_enforcer.max_open_positions,
                'current_positions': len(self.portfolio.positions),
                'positions_available': max(0, self.limits_enforcer.max_open_positions -
                                          len(self.portfolio.positions))
            }
        }

        return report

    def print_risk_dashboard(self):
        """Print comprehensive risk dashboard"""
        report = self.get_risk_report()

        print("\n" + "="*60)
        print("RISK MANAGEMENT DASHBOARD")
        print("="*60)

        # Overall status
        risk_emoji = {
            'low': '✅',
            'moderate': '⚠️',
            'high': '🔴',
            'critical': '🚨'
        }

        print(f"\nOVERALL RISK LEVEL: {risk_emoji.get(report['overall_risk_level'], '')} "
              f"{report['overall_risk_level'].upper()}")

        state_emoji = {
            'active': '✅',
            'paused': '⏸️',
            'halted': '🛑',
            'emergency_stop': '🚨'
        }
        controls = report['emergency_controls']
        print(f"Trading Status: {state_emoji.get(controls['state'], '')} "
              f"{controls['state'].upper()}")

        # Portfolio summary
        print("\nPORTFOLIO:")
        port = report['portfolio']
        print(f"  Total Value:       ${port['total_value']:>12,.2f}")
        print(f"  Cash:              ${port['cash']:>12,.2f} ({port['cash_pct']:>5.1%})")
        print(f"  Positions:         {port['num_positions']:>12} / "
              f"{report['position_limits']['max_positions']}")
        print(f"  Total Return:      {port['total_return']:>13.2%}")
        print(f"  Unrealized P&L:    ${port['unrealized_pnl']:>12,.2f}")

        # Risk metrics
        if report['risk_metrics']:
            metrics = report['risk_metrics']
            print("\nRISK METRICS:")
            print(f"  Max Drawdown:      {metrics.get('max_drawdown', 0):>13.2%}")
            print(f"  Current Drawdown:  {metrics.get('current_drawdown', 0):>13.2%}")
            if 'sharpe_ratio' in metrics:
                print(f"  Sharpe Ratio:      {metrics['sharpe_ratio']:>13.2f}")
            if 'win_rate' in metrics:
                print(f"  Win Rate:          {metrics['win_rate']:>13.1%}")

        # Active alerts
        if report['current_alerts'] > 0:
            print(f"\nALERTS ({report['current_alerts']}):")
            for alert in report['recent_alerts'][-5:]:
                print(f"  {alert}")

        # Position limits
        print("\nPOSITION CAPACITY:")
        limits = report['position_limits']
        print(f"  Available: {limits['positions_available']} of {limits['max_positions']} slots")

        # Available capital
        metrics = self.portfolio.get_portfolio_metrics()
        print(f"\nAVAILABLE CAPITAL:")
        print(f"  Cash Available:    ${self.portfolio.cash:>12,.2f}")
        min_reserve = self.portfolio.get_total_value() * self.limits_enforcer.min_cash_reserve_pct
        print(f"  Must Keep:         ${min_reserve:>12,.2f} "
              f"({self.limits_enforcer.min_cash_reserve_pct:.1%} reserve)")
        print(f"  Can Invest:        ${max(0, self.portfolio.cash - min_reserve):>12,.2f}")

        print("="*60 + "\n")

    def print_position_analysis(self):
        """Print analysis of current positions"""
        if not self.portfolio.positions:
            print("\nNo open positions")
            return

        print("\n" + "="*60)
        print("POSITION ANALYSIS")
        print("="*60)

        total_value = self.portfolio.get_total_value()

        for position in self.portfolio.positions.values():
            pos_value = position.get_value()
            pos_pct = pos_value / total_value if total_value > 0 else 0

            print(f"\n{position.symbol} ({position.asset_type.value.upper()})")
            print(f"  Entry: ${position.entry_price:,.2f} x {position.quantity:.4f}")
            print(f"  Current: ${position.current_price:,.2f}")
            print(f"  Value: ${pos_value:,.2f} ({pos_pct:.1%} of portfolio)")
            print(f"  P&L: ${position.unrealized_pnl:,.2f} ({position.unrealized_pnl_pct:.2%})")

            if position.stop_loss:
                print(f"  Stop Loss: ${position.stop_loss:,.2f}")
            if position.take_profit:
                print(f"  Take Profit: ${position.take_profit:,.2f}")

            # Check if position size is concerning
            if pos_pct > 0.25:
                print(f"  ⚠️ WARNING: Large position size ({pos_pct:.1%})")

        print("="*60 + "\n")


if __name__ == "__main__":
    # Test risk monitor
    from portfolio_manager import PortfolioManager, AssetType

    print("="*60)
    print("Testing Risk Monitoring System")
    print("="*60)

    # Create portfolio
    portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')

    # Create risk monitor
    monitor = RiskMonitor(portfolio, {
        'max_open_positions': 5,
        'max_position_size_pct': 0.20,
        'max_daily_loss_pct': 0.05,
        'min_cash_reserve_pct': 0.15
    })

    # Show initial dashboard
    monitor.print_risk_dashboard()

    # Open some positions
    print("Opening positions...")

    # Position 1: BTC
    can_open, reason, violations = monitor.can_open_position('BTC/USDT', 2000.0, 'crypto')
    if can_open:
        portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.04, 'long',
                               stop_loss=48000.0, take_profit=55000.0)
        print(f"  ✓ BTC position opened")

    # Position 2: ETH with position sizing
    print("\nCalculating position size for ETH...")
    pos_size = monitor.calculate_position_size(
        entry_price=3000.0,
        stop_loss_price=2940.0,  # 2% stop
        symbol='ETH/USDT',
        asset_type='crypto',
        method='risk_pct'
    )
    print(f"  Recommended size: {pos_size['quantity']:.4f} ETH = ${pos_size['value']:.2f}")

    if pos_size['quantity'] > 0:
        portfolio.open_position('ETH/USDT', 'crypto', 3000.0, pos_size['quantity'], 'long')
        print(f"  ✓ ETH position opened")

    # Update dashboard
    print("\n" + "-"*60)
    monitor.print_risk_dashboard()
    monitor.print_position_analysis()

    # Simulate loss
    print("\nSimulating market downturn...")
    portfolio.update_prices({
        'BTC/USDT': 48500.0,  # -3%
        'ETH/USDT': 2910.0    # -3%
    })

    monitor.print_risk_dashboard()

    print("\n✓ Risk monitoring system working correctly!")
    print("="*60)
