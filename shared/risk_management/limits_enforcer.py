"""
Portfolio Limits Enforcer

Enforces risk limits and trading rules to prevent excessive losses.
Acts as a safety layer before trade execution.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from monitoring.logger import get_logger

logger = get_logger(__name__)


class LimitType(Enum):
    """Types of limits"""
    MAX_POSITIONS = "max_positions"
    MAX_POSITION_SIZE = "max_position_size"
    MAX_CONCENTRATION = "max_concentration"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    MAX_DRAWDOWN = "max_drawdown"
    MAX_LEVERAGE = "max_leverage"
    MIN_CASH_RESERVE = "min_cash_reserve"


@dataclass
class LimitViolation:
    """Represents a limit violation"""
    limit_type: LimitType
    current_value: float
    limit_value: float
    message: str
    severity: str = 'warning'  # warning, error, critical

    def __str__(self):
        return f"[{self.severity.upper()}] {self.message} (current: {self.current_value}, limit: {self.limit_value})"


class LimitsEnforcer:
    """
    Enforces portfolio and risk limits

    Prevents trades that would violate:
    - Position limits (max positions, position size)
    - Concentration limits (per asset, per sector)
    - Loss limits (daily loss, max drawdown)
    - Cash reserves (minimum cash balance)
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize limits enforcer

        Args:
            config: Configuration dictionary with limit parameters
        """
        default_config = {
            # Position limits
            'max_open_positions': 10,
            'max_position_size_pct': 0.20,  # 20% of portfolio per position
            'max_single_asset_pct': 0.30,   # 30% max in single asset

            # Asset class limits
            'max_crypto_pct': 0.50,          # 50% max in crypto
            'max_stock_pct': 0.80,           # 80% max in stocks

            # Loss limits
            'max_daily_loss_pct': 0.05,      # 5% max daily loss
            'max_drawdown_pct': 0.20,        # 20% max drawdown from peak

            # Cash management
            'min_cash_reserve_pct': 0.10,    # Keep 10% in cash

            # Leverage
            'max_leverage': 1.0,             # No leverage by default
        }

        if config:
            default_config.update(config)

        self.config = default_config

        # Extract limits for easy access
        self.max_open_positions = self.config['max_open_positions']
        self.max_position_size_pct = self.config['max_position_size_pct']
        self.max_single_asset_pct = self.config['max_single_asset_pct']
        self.max_crypto_pct = self.config['max_crypto_pct']
        self.max_stock_pct = self.config['max_stock_pct']
        self.max_daily_loss_pct = self.config['max_daily_loss_pct']
        self.max_drawdown_pct = self.config['max_drawdown_pct']
        self.min_cash_reserve_pct = self.config['min_cash_reserve_pct']
        self.max_leverage = self.config['max_leverage']

        # State tracking
        self.daily_pnl_start = None
        self.daily_start_value = None
        self.peak_portfolio_value = None
        self.daily_reset_time = None

        logger.info(f"Limits Enforcer initialized: max_positions={self.max_open_positions}, "
                   f"max_position_size={self.max_position_size_pct:.1%}, "
                   f"max_daily_loss={self.max_daily_loss_pct:.1%}")

    def check_trade(self,
                   portfolio,
                   symbol: str,
                   position_value: float,
                   asset_type: str) -> Tuple[bool, List[LimitViolation]]:
        """
        Check if a trade would violate any limits

        Args:
            portfolio: PortfolioManager instance
            symbol: Symbol to trade
            position_value: Value of proposed position
            asset_type: Type of asset (crypto, stock, etc.)

        Returns:
            Tuple of (is_allowed, violations_list)
        """
        violations = []

        # Get portfolio metrics
        metrics = portfolio.get_portfolio_metrics()
        total_value = metrics['total_value']

        # Check each limit
        violations.extend(self._check_position_limits(portfolio, position_value, total_value))
        violations.extend(self._check_concentration_limits(portfolio, symbol, position_value,
                                                          asset_type, total_value))
        violations.extend(self._check_loss_limits(portfolio, total_value))
        violations.extend(self._check_cash_reserve(portfolio, position_value, total_value))

        # Determine if trade is allowed
        # Block on 'error' or 'critical' violations
        is_allowed = not any(v.severity in ['error', 'critical'] for v in violations)

        # Log violations
        for violation in violations:
            if violation.severity == 'critical':
                logger.error(f"CRITICAL LIMIT VIOLATION: {violation.message}")
            elif violation.severity == 'error':
                logger.error(f"Limit violation: {violation.message}")
            else:
                logger.warning(f"Limit warning: {violation.message}")

        if not is_allowed:
            logger.warning(f"Trade BLOCKED for {symbol}: {len(violations)} violation(s)")

        return is_allowed, violations

    def _check_position_limits(self, portfolio, position_value: float,
                               total_value: float) -> List[LimitViolation]:
        """Check position count and size limits"""
        violations = []

        # Max number of positions
        current_positions = len(portfolio.positions)
        if current_positions >= self.max_open_positions:
            violations.append(LimitViolation(
                limit_type=LimitType.MAX_POSITIONS,
                current_value=current_positions,
                limit_value=self.max_open_positions,
                message=f"Maximum positions reached: {current_positions}/{self.max_open_positions}",
                severity='error'
            ))

        # Max position size
        position_pct = position_value / total_value if total_value > 0 else 0
        if position_pct > self.max_position_size_pct:
            violations.append(LimitViolation(
                limit_type=LimitType.MAX_POSITION_SIZE,
                current_value=position_pct,
                limit_value=self.max_position_size_pct,
                message=f"Position size too large: {position_pct:.1%} > {self.max_position_size_pct:.1%}",
                severity='error'
            ))

        return violations

    def _check_concentration_limits(self, portfolio, symbol: str, position_value: float,
                                   asset_type: str, total_value: float) -> List[LimitViolation]:
        """Check concentration limits"""
        violations = []

        # Check if adding this position would create too much concentration

        # 1. Single asset concentration
        existing_positions = portfolio.get_positions_by_symbol(symbol)
        existing_value = sum(p.get_value() for p in existing_positions)
        total_asset_value = existing_value + position_value
        asset_concentration = total_asset_value / total_value if total_value > 0 else 0

        if asset_concentration > self.max_single_asset_pct:
            violations.append(LimitViolation(
                limit_type=LimitType.MAX_CONCENTRATION,
                current_value=asset_concentration,
                limit_value=self.max_single_asset_pct,
                message=f"Too much concentration in {symbol}: {asset_concentration:.1%} > {self.max_single_asset_pct:.1%}",
                severity='warning'
            ))

        # 2. Asset class concentration
        asset_type_positions = portfolio.get_positions_by_asset_type(asset_type)
        existing_class_value = sum(p.get_value() for p in asset_type_positions)
        total_class_value = existing_class_value + position_value
        class_concentration = total_class_value / total_value if total_value > 0 else 0

        # Check against asset-specific limits
        if asset_type == 'crypto' and class_concentration > self.max_crypto_pct:
            violations.append(LimitViolation(
                limit_type=LimitType.MAX_CONCENTRATION,
                current_value=class_concentration,
                limit_value=self.max_crypto_pct,
                message=f"Too much crypto exposure: {class_concentration:.1%} > {self.max_crypto_pct:.1%}",
                severity='warning'
            ))
        elif asset_type == 'stock' and class_concentration > self.max_stock_pct:
            violations.append(LimitViolation(
                limit_type=LimitType.MAX_CONCENTRATION,
                current_value=class_concentration,
                limit_value=self.max_stock_pct,
                message=f"Too much stock exposure: {class_concentration:.1%} > {self.max_stock_pct:.1%}",
                severity='warning'
            ))

        return violations

    def _check_loss_limits(self, portfolio, total_value: float) -> List[LimitViolation]:
        """Check daily loss and drawdown limits"""
        violations = []

        # Reset daily tracking if new day
        self._reset_daily_tracking_if_needed(total_value)

        # 1. Daily loss limit
        if self.daily_start_value is not None:
            daily_pnl = total_value - self.daily_start_value
            daily_pnl_pct = daily_pnl / self.daily_start_value if self.daily_start_value > 0 else 0

            if daily_pnl_pct < -self.max_daily_loss_pct:
                violations.append(LimitViolation(
                    limit_type=LimitType.DAILY_LOSS_LIMIT,
                    current_value=daily_pnl_pct,
                    limit_value=-self.max_daily_loss_pct,
                    message=f"Daily loss limit exceeded: {daily_pnl_pct:.2%} < -{self.max_daily_loss_pct:.1%}",
                    severity='critical'
                ))

        # 2. Maximum drawdown
        if self.peak_portfolio_value is None:
            self.peak_portfolio_value = total_value
        else:
            self.peak_portfolio_value = max(self.peak_portfolio_value, total_value)

        if self.peak_portfolio_value > 0:
            current_drawdown = (total_value - self.peak_portfolio_value) / self.peak_portfolio_value

            if current_drawdown < -self.max_drawdown_pct:
                violations.append(LimitViolation(
                    limit_type=LimitType.MAX_DRAWDOWN,
                    current_value=current_drawdown,
                    limit_value=-self.max_drawdown_pct,
                    message=f"Maximum drawdown exceeded: {current_drawdown:.2%} < -{self.max_drawdown_pct:.1%}",
                    severity='critical'
                ))

        return violations

    def _check_cash_reserve(self, portfolio, position_value: float,
                           total_value: float) -> List[LimitViolation]:
        """Check minimum cash reserve"""
        violations = []

        # Calculate cash after trade
        cash_after_trade = portfolio.cash - position_value
        cash_pct_after = cash_after_trade / total_value if total_value > 0 else 0

        if cash_pct_after < self.min_cash_reserve_pct:
            violations.append(LimitViolation(
                limit_type=LimitType.MIN_CASH_RESERVE,
                current_value=cash_pct_after,
                limit_value=self.min_cash_reserve_pct,
                message=f"Insufficient cash reserve: {cash_pct_after:.1%} < {self.min_cash_reserve_pct:.1%}",
                severity='warning'
            ))

        return violations

    def _reset_daily_tracking_if_needed(self, current_value: float):
        """Reset daily tracking at start of new trading day"""
        now = datetime.now()

        # Reset if new day or not initialized
        if (self.daily_reset_time is None or
            now.date() > self.daily_reset_time.date()):

            self.daily_start_value = current_value
            self.daily_reset_time = now

            logger.info(f"Daily tracking reset: start_value=${current_value:,.2f}")

    def check_portfolio_health(self, portfolio) -> Tuple[str, List[LimitViolation]]:
        """
        Check overall portfolio health

        Returns:
            Tuple of (health_status, violations)
            health_status: 'healthy', 'warning', 'danger', 'critical'
        """
        violations = []
        metrics = portfolio.get_portfolio_metrics()
        total_value = metrics['total_value']

        # Check all limits without assuming a new trade
        violations.extend(self._check_loss_limits(portfolio, total_value))

        # Check current position count
        if len(portfolio.positions) >= self.max_open_positions:
            violations.append(LimitViolation(
                limit_type=LimitType.MAX_POSITIONS,
                current_value=len(portfolio.positions),
                limit_value=self.max_open_positions,
                message=f"At maximum positions: {len(portfolio.positions)}/{self.max_open_positions}",
                severity='warning'
            ))

        # Check cash reserve
        cash_pct = metrics['cash_pct']
        if cash_pct < self.min_cash_reserve_pct:
            violations.append(LimitViolation(
                limit_type=LimitType.MIN_CASH_RESERVE,
                current_value=cash_pct,
                limit_value=self.min_cash_reserve_pct,
                message=f"Low cash reserve: {cash_pct:.1%} < {self.min_cash_reserve_pct:.1%}",
                severity='warning'
            ))

        # Determine health status
        if any(v.severity == 'critical' for v in violations):
            health_status = 'critical'
        elif any(v.severity == 'error' for v in violations):
            health_status = 'danger'
        elif any(v.severity == 'warning' for v in violations):
            health_status = 'warning'
        else:
            health_status = 'healthy'

        return health_status, violations

    def get_available_position_size(self, portfolio, symbol: str, asset_type: str) -> float:
        """
        Calculate maximum allowed position size for a symbol

        Takes into account all limits and returns the maximum position value allowed.

        Args:
            portfolio: PortfolioManager instance
            symbol: Symbol to trade
            asset_type: Type of asset

        Returns:
            Maximum position value in USD
        """
        metrics = portfolio.get_portfolio_metrics()
        total_value = metrics['total_value']

        # Start with max position size limit
        max_by_position_limit = total_value * self.max_position_size_pct

        # Check single asset concentration
        existing_positions = portfolio.get_positions_by_symbol(symbol)
        existing_value = sum(p.get_value() for p in existing_positions)
        max_by_asset_concentration = (total_value * self.max_single_asset_pct) - existing_value

        # Check asset class concentration
        asset_type_positions = portfolio.get_positions_by_asset_type(asset_type)
        existing_class_value = sum(p.get_value() for p in asset_type_positions)

        if asset_type == 'crypto':
            max_by_class = (total_value * self.max_crypto_pct) - existing_class_value
        elif asset_type == 'stock':
            max_by_class = (total_value * self.max_stock_pct) - existing_class_value
        else:
            max_by_class = float('inf')

        # Check cash reserve
        min_cash_required = total_value * self.min_cash_reserve_pct
        max_by_cash = portfolio.cash - min_cash_required

        # Take minimum of all limits
        max_allowed = min(
            max_by_position_limit,
            max_by_asset_concentration,
            max_by_class,
            max_by_cash,
            portfolio.cash  # Can't exceed available cash
        )

        return max(0, max_allowed)  # Never negative

    def print_limits(self):
        """Print current limit configuration"""
        print("\n" + "="*60)
        print("RISK LIMITS CONFIGURATION")
        print("="*60)

        print("\nPOSITION LIMITS:")
        print(f"  Max Open Positions:    {self.max_open_positions:>10}")
        print(f"  Max Position Size:     {self.max_position_size_pct:>10.1%}")
        print(f"  Max Single Asset:      {self.max_single_asset_pct:>10.1%}")

        print("\nASSET CLASS LIMITS:")
        print(f"  Max Crypto:            {self.max_crypto_pct:>10.1%}")
        print(f"  Max Stocks:            {self.max_stock_pct:>10.1%}")

        print("\nLOSS LIMITS:")
        print(f"  Max Daily Loss:        {self.max_daily_loss_pct:>10.1%}")
        print(f"  Max Drawdown:          {self.max_drawdown_pct:>10.1%}")

        print("\nCASH MANAGEMENT:")
        print(f"  Min Cash Reserve:      {self.min_cash_reserve_pct:>10.1%}")
        print(f"  Max Leverage:          {self.max_leverage:>10.1f}x")

        print("="*60 + "\n")


if __name__ == "__main__":
    # Test limits enforcer
    from portfolio_manager import PortfolioManager, AssetType

    print("="*60)
    print("Testing Limits Enforcer")
    print("="*60)

    # Create portfolio and enforcer
    portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')
    enforcer = LimitsEnforcer({
        'max_open_positions': 3,
        'max_position_size_pct': 0.25,
        'max_daily_loss_pct': 0.05,
        'max_crypto_pct': 0.50,
        'min_cash_reserve_pct': 0.20
    })

    enforcer.print_limits()

    # Test 1: Normal trade (should pass)
    print("\nTest 1: Normal trade (should pass)")
    allowed, violations = enforcer.check_trade(portfolio, 'BTC/USDT', 2000.0, 'crypto')
    print(f"  Allowed: {allowed}")
    print(f"  Violations: {len(violations)}")

    # Open the position
    if allowed:
        portfolio.open_position('BTC/USDT', 'crypto', 50000.0, 0.04, 'long')

    # Test 2: Too large position (should fail)
    print("\nTest 2: Too large position (should fail)")
    allowed, violations = enforcer.check_trade(portfolio, 'ETH/USDT', 3000.0, 'crypto')
    print(f"  Allowed: {allowed}")
    for v in violations:
        print(f"  - {v}")

    # Test 3: Fill up to max positions
    print("\nTest 3: Filling up to max positions...")
    portfolio.open_position('AAPL', 'stock', 150.0, 10, 'long')
    portfolio.open_position('GOOGL', 'stock', 140.0, 5, 'long')

    # Test 4: Exceed max positions (should fail)
    print("\nTest 4: Exceed max positions (should fail)")
    allowed, violations = enforcer.check_trade(portfolio, 'MSFT', 1000.0, 'stock')
    print(f"  Allowed: {allowed}")
    for v in violations:
        print(f"  - {v}")

    # Test 5: Check portfolio health
    print("\nTest 5: Portfolio health check")
    health, violations = enforcer.check_portfolio_health(portfolio)
    print(f"  Health Status: {health}")
    print(f"  Violations: {len(violations)}")
    for v in violations:
        print(f"  - {v}")

    portfolio.print_summary()

    print("\n✓ Limits enforcer working correctly!")
    print("="*60)
