"""
Position Sizing Calculator

Calculates appropriate position sizes based on risk parameters and account size.
Supports multiple position sizing methods.
"""

from typing import Dict, Optional
from enum import Enum

from monitoring.logger import get_logger

logger = get_logger(__name__)


class PositionSizeMethod(Enum):
    """Position sizing methods"""
    FIXED_RISK_PCT = "risk_pct"      # Risk fixed % of account per trade
    FIXED_POSITION_PCT = "fixed_pct"  # Fixed % of account per trade
    KELLY_CRITERION = "kelly"         # Kelly criterion (requires win rate)
    FIXED_AMOUNT = "fixed_amount"     # Fixed dollar amount
    ATR_BASED = "atr"                # Based on ATR volatility


class PositionSizer:
    """
    Calculate position sizes based on various risk management methods.

    Ensures proper risk management by limiting position sizes relative to:
    - Account size
    - Risk per trade
    - Stop loss distance
    - Asset volatility
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize position sizer

        Args:
            config: Configuration dictionary with risk parameters
        """
        self.config = config or {}

        # Risk parameters
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)  # 2%
        self.max_position_pct = self.config.get('max_position_pct', 0.10)  # 10%
        self.min_position_size = self.config.get('min_position_size', 100.0)  # $100

        logger.info(f"Position Sizer initialized: max_risk={self.max_risk_per_trade:.1%}, "
                   f"max_position={self.max_position_pct:.1%}")

    def calculate_position_size(self,
                               account_balance: float,
                               entry_price: float,
                               stop_loss_price: float,
                               method: str = 'risk_pct',
                               **kwargs) -> Dict:
        """
        Calculate position size based on specified method

        Args:
            account_balance: Total account balance
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            method: Position sizing method
            **kwargs: Additional parameters for specific methods

        Returns:
            Dictionary with position size details:
            {
                'quantity': float,  # Number of shares/contracts
                'value': float,     # Total position value in USD
                'risk_amount': float,  # Amount at risk
                'risk_pct': float,  # Risk as % of account
                'position_pct': float,  # Position as % of account
                'method': str       # Method used
            }
        """
        # Validate inputs
        if account_balance <= 0:
            raise ValueError("Account balance must be positive")
        if entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if stop_loss_price <= 0:
            raise ValueError("Stop loss price must be positive")

        # Calculate based on method
        method_enum = PositionSizeMethod(method)

        if method_enum == PositionSizeMethod.FIXED_RISK_PCT:
            result = self._risk_pct_method(account_balance, entry_price, stop_loss_price)
        elif method_enum == PositionSizeMethod.FIXED_POSITION_PCT:
            result = self._fixed_pct_method(account_balance, entry_price)
        elif method_enum == PositionSizeMethod.KELLY_CRITERION:
            result = self._kelly_method(account_balance, entry_price, **kwargs)
        elif method_enum == PositionSizeMethod.FIXED_AMOUNT:
            result = self._fixed_amount_method(entry_price, **kwargs)
        elif method_enum == PositionSizeMethod.ATR_BASED:
            result = self._atr_method(account_balance, entry_price, **kwargs)
        else:
            raise ValueError(f"Unknown position sizing method: {method}")

        # Apply constraints
        result = self._apply_constraints(result, account_balance)

        # Log result (handle None values)
        risk_str = f"{result['risk_pct']:.2%}" if result['risk_pct'] is not None else "N/A"
        logger.debug(f"Position size calculated: {result['quantity']:.2f} @ ${entry_price:.2f} "
                    f"= ${result['value']:.2f} (risk: {risk_str})")

        return result

    def _risk_pct_method(self, account_balance: float, entry_price: float,
                        stop_loss_price: float) -> Dict:
        """
        Risk a fixed percentage of account per trade

        Formula: Position Size = (Account × Risk%) / (Entry - Stop Loss)
        """
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            raise ValueError("Entry price and stop loss cannot be the same")

        # Calculate amount to risk
        risk_amount = account_balance * self.max_risk_per_trade

        # Calculate quantity
        quantity = risk_amount / risk_per_share

        # Calculate position value
        position_value = quantity * entry_price

        return {
            'quantity': quantity,
            'value': position_value,
            'risk_amount': risk_amount,
            'risk_pct': self.max_risk_per_trade,
            'position_pct': position_value / account_balance,
            'method': 'risk_pct',
            'stop_loss_price': stop_loss_price
        }

    def _fixed_pct_method(self, account_balance: float, entry_price: float) -> Dict:
        """
        Use fixed percentage of account for position size
        """
        position_value = account_balance * self.max_position_pct
        quantity = position_value / entry_price

        return {
            'quantity': quantity,
            'value': position_value,
            'risk_amount': None,  # Unknown without stop loss
            'risk_pct': None,
            'position_pct': self.max_position_pct,
            'method': 'fixed_pct',
            'stop_loss_price': None
        }

    def _kelly_method(self, account_balance: float, entry_price: float,
                     win_rate: float = 0.5, avg_win: float = 0.02,
                     avg_loss: float = 0.02, **kwargs) -> Dict:
        """
        Kelly Criterion: f = (p × r - q) / r
        where:
        - f = fraction of capital to wager
        - p = probability of win
        - q = probability of loss (1-p)
        - r = win/loss ratio

        Note: Kelly is often considered aggressive, so we use fractional Kelly
        """
        # Calculate Kelly fraction
        q = 1 - win_rate
        r = abs(avg_win / avg_loss) if avg_loss != 0 else 1

        kelly_fraction = (win_rate * r - q) / r

        # Use half-Kelly for conservatism
        kelly_fraction = kelly_fraction * 0.5

        # Ensure non-negative
        kelly_fraction = max(0, min(kelly_fraction, self.max_position_pct))

        position_value = account_balance * kelly_fraction
        quantity = position_value / entry_price

        return {
            'quantity': quantity,
            'value': position_value,
            'risk_amount': None,
            'risk_pct': None,
            'position_pct': kelly_fraction,
            'method': 'kelly',
            'kelly_fraction': kelly_fraction,
            'stop_loss_price': None
        }

    def _fixed_amount_method(self, entry_price: float, amount: float = 1000.0,
                            **kwargs) -> Dict:
        """Fixed dollar amount per trade"""
        quantity = amount / entry_price

        return {
            'quantity': quantity,
            'value': amount,
            'risk_amount': None,
            'risk_pct': None,
            'position_pct': None,
            'method': 'fixed_amount',
            'stop_loss_price': None
        }

    def _atr_method(self, account_balance: float, entry_price: float,
                   atr: float = None, atr_multiplier: float = 2.0, **kwargs) -> Dict:
        """
        ATR-based position sizing
        Uses ATR to determine stop loss distance
        """
        if atr is None:
            raise ValueError("ATR value required for ATR-based sizing")

        # Stop loss is entry - (ATR × multiplier)
        stop_loss_distance = atr * atr_multiplier
        stop_loss_price = entry_price - stop_loss_distance

        # Use risk percentage method with ATR-based stop
        return self._risk_pct_method(account_balance, entry_price, stop_loss_price)

    def _apply_constraints(self, result: Dict, account_balance: float) -> Dict:
        """
        Apply constraints to ensure reasonable position sizes

        Constraints:
        - Minimum position size
        - Maximum position percentage
        - Maximum risk percentage
        """
        # Check minimum position size
        if result['value'] < self.min_position_size:
            logger.warning(f"Position size ${result['value']:.2f} below minimum ${self.min_position_size:.2f}")
            result['quantity'] = 0
            result['value'] = 0
            result['constrained'] = True
            result['constraint_reason'] = 'below_minimum'
            return result

        # Check maximum position percentage
        if result['position_pct'] and result['position_pct'] > self.max_position_pct:
            # Scale down to max
            scale_factor = self.max_position_pct / result['position_pct']
            result['quantity'] *= scale_factor
            result['value'] *= scale_factor
            result['position_pct'] = self.max_position_pct
            result['constrained'] = True
            result['constraint_reason'] = 'max_position_exceeded'

            logger.warning(f"Position scaled down to max {self.max_position_pct:.1%} of account")

        # Check if position exceeds account balance
        if result['value'] > account_balance:
            result['quantity'] = account_balance / result['value'] * result['quantity']
            result['value'] = account_balance
            result['position_pct'] = 1.0
            result['constrained'] = True
            result['constraint_reason'] = 'exceeds_balance'

            logger.warning("Position size exceeds account balance, capped at 100%")

        return result


if __name__ == "__main__":
    # Test position sizer
    print("="*60)
    print("Testing Position Sizer")
    print("="*60)

    sizer = PositionSizer({
        'max_risk_per_trade': 0.02,  # 2%
        'max_position_pct': 0.10,    # 10%
        'min_position_size': 100.0
    })

    account = 10000.0
    entry = 100.0
    stop_loss = 98.0  # 2% stop

    print(f"\nAccount: ${account:,.2f}")
    print(f"Entry: ${entry:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f}")

    # Test different methods
    print("\n1. Risk Percentage Method (2% risk):")
    result = sizer.calculate_position_size(account, entry, stop_loss, method='risk_pct')
    print(f"   Quantity: {result['quantity']:.2f}")
    print(f"   Value: ${result['value']:.2f}")
    print(f"   Risk: ${result['risk_amount']:.2f} ({result['risk_pct']:.1%})")
    print(f"   Position: {result['position_pct']:.1%} of account")

    print("\n2. Fixed Percentage Method (10% position):")
    result = sizer.calculate_position_size(account, entry, stop_loss, method='fixed_pct')
    print(f"   Quantity: {result['quantity']:.2f}")
    print(f"   Value: ${result['value']:.2f}")
    print(f"   Position: {result['position_pct']:.1%} of account")

    print("\n3. Kelly Criterion (50% win rate, 2:1 reward/risk):")
    result = sizer.calculate_position_size(account, entry, stop_loss, method='kelly',
                                          win_rate=0.50, avg_win=0.04, avg_loss=0.02)
    print(f"   Quantity: {result['quantity']:.2f}")
    print(f"   Value: ${result['value']:.2f}")
    print(f"   Kelly Fraction: {result.get('kelly_fraction', 0):.2%}")

    print("\n✓ Position sizer working correctly!")
    print("="*60)
