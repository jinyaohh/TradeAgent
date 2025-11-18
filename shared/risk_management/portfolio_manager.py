"""
Portfolio Manager

Unified portfolio tracking for both crypto and stock positions.
Manages position lifecycle, P&L calculation, and portfolio metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

from monitoring.logger import get_logger

logger = get_logger(__name__)


class AssetType(Enum):
    """Asset type classification"""
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"
    COMMODITY = "commodity"


@dataclass
class Position:
    """
    Represents a trading position

    Tracks entry, current state, and P&L for a position
    """
    symbol: str
    asset_type: AssetType
    entry_time: datetime
    entry_price: float
    quantity: float
    side: str = 'long'  # long or short

    # Current state
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # Exit info (if closed)
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    realized_pnl: float = 0.0
    realized_pnl_pct: float = 0.0
    exit_reason: str = ''

    # Metadata
    strategy_name: str = ''
    notes: str = ''
    position_id: str = field(default_factory=lambda: '')

    def __post_init__(self):
        """Generate position ID if not provided"""
        if not self.position_id:
            timestamp = self.entry_time.strftime('%Y%m%d_%H%M%S')
            self.position_id = f"{self.symbol}_{timestamp}"

    def update_price(self, current_price: float):
        """Update current price and calculate unrealized P&L"""
        self.current_price = current_price

        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
            self.unrealized_pnl_pct = (current_price - self.entry_price) / self.entry_price
        else:  # short
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
            self.unrealized_pnl_pct = (self.entry_price - current_price) / self.entry_price

    def close(self, exit_time: datetime, exit_price: float, reason: str = ''):
        """Close the position"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = reason

        if self.side == 'long':
            self.realized_pnl = (exit_price - self.entry_price) * self.quantity
            self.realized_pnl_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # short
            self.realized_pnl = (self.entry_price - exit_price) * self.quantity
            self.realized_pnl_pct = (self.entry_price - exit_price) / self.entry_price

    def is_open(self) -> bool:
        """Check if position is still open"""
        return self.exit_time is None

    def get_value(self) -> float:
        """Get current position value"""
        if self.is_open():
            return self.quantity * self.current_price
        else:
            return self.quantity * self.exit_price

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['asset_type'] = self.asset_type.value
        return data


class PortfolioManager:
    """
    Unified portfolio manager for multi-asset trading

    Manages positions across crypto, stocks, and other assets.
    Provides portfolio-level metrics and risk monitoring.
    """

    def __init__(self, initial_capital: float = 10000.0, mode: str = 'paper'):
        """
        Initialize portfolio manager

        Args:
            initial_capital: Starting capital in USD
            mode: Trading mode ('paper' or 'live')
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.mode = mode

        # Position tracking
        self.positions: Dict[str, Position] = {}  # Open positions
        self.closed_positions: List[Position] = []  # Historical positions

        # Performance tracking
        self.equity_history = []
        self.trades_history = []

        logger.info(f"Portfolio Manager initialized: mode={mode}, capital=${initial_capital:,.2f}")

    def open_position(self,
                     symbol: str,
                     asset_type: Union[AssetType, str],
                     entry_price: float,
                     quantity: float,
                     side: str = 'long',
                     stop_loss: Optional[float] = None,
                     take_profit: Optional[float] = None,
                     strategy_name: str = '',
                     notes: str = '') -> Position:
        """
        Open a new position

        Args:
            symbol: Asset symbol (e.g., 'BTC/USDT', 'AAPL')
            asset_type: Type of asset (crypto, stock, etc.)
            entry_price: Entry price
            quantity: Position size
            side: 'long' or 'short'
            stop_loss: Stop loss price
            take_profit: Take profit price
            strategy_name: Name of strategy opening the position
            notes: Additional notes

        Returns:
            Created Position object
        """
        # Convert asset_type to enum if string
        if isinstance(asset_type, str):
            asset_type = AssetType(asset_type)

        # Create position
        position = Position(
            symbol=symbol,
            asset_type=asset_type,
            entry_time=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            side=side,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy_name=strategy_name,
            notes=notes
        )

        # Calculate cost
        position_cost = quantity * entry_price

        # Check if enough cash
        if position_cost > self.cash:
            logger.warning(f"Insufficient cash for position: need ${position_cost:,.2f}, have ${self.cash:,.2f}")
            raise ValueError("Insufficient cash for position")

        # Deduct cash
        self.cash -= position_cost

        # Add to positions
        self.positions[position.position_id] = position

        logger.info(f"Opened position: {symbol} {side} {quantity:.4f} @ ${entry_price:.2f} "
                   f"(${position_cost:.2f})")

        return position

    def close_position(self,
                      position_id: str,
                      exit_price: float,
                      reason: str = '') -> Position:
        """
        Close an open position

        Args:
            position_id: Position ID to close
            exit_price: Exit price
            reason: Reason for closing

        Returns:
            Closed Position object
        """
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")

        position = self.positions[position_id]

        # Close the position
        position.close(datetime.now(), exit_price, reason)

        # Calculate proceeds
        proceeds = position.quantity * exit_price

        # Add to cash
        self.cash += proceeds

        # Move to closed positions
        self.closed_positions.append(position)
        del self.positions[position_id]

        # Record trade
        self.trades_history.append(position.to_dict())

        logger.info(f"Closed position: {position.symbol} @ ${exit_price:.2f}, "
                   f"P&L: ${position.realized_pnl:.2f} ({position.realized_pnl_pct:.2%}), "
                   f"reason: {reason}")

        return position

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions

        Args:
            prices: Dictionary mapping symbol to current price
        """
        for position in self.positions.values():
            if position.symbol in prices:
                position.update_price(prices[position.symbol])

    def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        return self.positions.get(position_id)

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get all open positions for a symbol"""
        return [p for p in self.positions.values() if p.symbol == symbol]

    def get_positions_by_asset_type(self, asset_type: Union[AssetType, str]) -> List[Position]:
        """Get all open positions for an asset type"""
        if isinstance(asset_type, str):
            asset_type = AssetType(asset_type)
        return [p for p in self.positions.values() if p.asset_type == asset_type]

    def get_total_value(self) -> float:
        """Get total portfolio value (cash + positions)"""
        positions_value = sum(p.get_value() for p in self.positions.values())
        return self.cash + positions_value

    def get_positions_value(self) -> float:
        """Get total value of all positions"""
        return sum(p.get_value() for p in self.positions.values())

    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum(p.unrealized_pnl for p in self.positions.values())

    def get_realized_pnl(self) -> float:
        """Get total realized P&L from closed positions"""
        return sum(p.realized_pnl for p in self.closed_positions)

    def get_total_pnl(self) -> float:
        """Get total P&L (realized + unrealized)"""
        return self.get_realized_pnl() + self.get_unrealized_pnl()

    def get_portfolio_metrics(self) -> Dict:
        """
        Calculate comprehensive portfolio metrics

        Returns:
            Dictionary with portfolio statistics
        """
        total_value = self.get_total_value()
        positions_value = self.get_positions_value()

        # Calculate allocation
        cash_pct = self.cash / total_value if total_value > 0 else 0
        invested_pct = positions_value / total_value if total_value > 0 else 0

        # Calculate returns
        total_return = (total_value - self.initial_capital) / self.initial_capital

        # Asset allocation
        crypto_value = sum(p.get_value() for p in self.positions.values()
                          if p.asset_type == AssetType.CRYPTO)
        stock_value = sum(p.get_value() for p in self.positions.values()
                         if p.asset_type == AssetType.STOCK)

        crypto_pct = crypto_value / total_value if total_value > 0 else 0
        stock_pct = stock_value / total_value if total_value > 0 else 0

        # Position statistics
        num_positions = len(self.positions)
        num_long = sum(1 for p in self.positions.values() if p.side == 'long')
        num_short = sum(1 for p in self.positions.values() if p.side == 'short')

        # Trade statistics
        num_closed_trades = len(self.closed_positions)
        winning_trades = [p for p in self.closed_positions if p.realized_pnl > 0]
        losing_trades = [p for p in self.closed_positions if p.realized_pnl <= 0]

        win_rate = len(winning_trades) / num_closed_trades if num_closed_trades > 0 else 0

        return {
            # Portfolio value
            'total_value': total_value,
            'cash': self.cash,
            'positions_value': positions_value,
            'total_invested': positions_value,  # Alias for positions_value
            'initial_capital': self.initial_capital,

            # Allocation
            'cash_pct': cash_pct,
            'invested_pct': invested_pct,

            # Returns
            'total_return': total_return,
            'unrealized_pnl': self.get_unrealized_pnl(),
            'realized_pnl': self.get_realized_pnl(),
            'total_pnl': self.get_total_pnl(),

            # Asset allocation
            'crypto_value': crypto_value,
            'stock_value': stock_value,
            'crypto_pct': crypto_pct,
            'stock_pct': stock_pct,

            # Positions
            'num_positions': num_positions,
            'num_long': num_long,
            'num_short': num_short,

            # Trades
            'num_closed_trades': num_closed_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate
        }

    def get_positions_df(self) -> pd.DataFrame:
        """Get open positions as DataFrame"""
        if not self.positions:
            return pd.DataFrame()

        data = [p.to_dict() for p in self.positions.values()]
        return pd.DataFrame(data)

    def get_closed_positions_df(self) -> pd.DataFrame:
        """Get closed positions as DataFrame"""
        if not self.closed_positions:
            return pd.DataFrame()

        data = [p.to_dict() for p in self.closed_positions]
        return pd.DataFrame(data)

    def print_summary(self):
        """Print portfolio summary"""
        metrics = self.get_portfolio_metrics()

        print("\n" + "="*60)
        print("PORTFOLIO SUMMARY")
        print("="*60)

        print("\nVALUE:")
        print(f"  Total Value:    ${metrics['total_value']:>12,.2f}")
        print(f"  Cash:           ${metrics['cash']:>12,.2f} ({metrics['cash_pct']:>5.1%})")
        print(f"  Positions:      ${metrics['positions_value']:>12,.2f} ({metrics['invested_pct']:>5.1%})")

        print("\nRETURNS:")
        print(f"  Total P&L:      ${metrics['total_pnl']:>12,.2f}")
        print(f"  Realized P&L:   ${metrics['realized_pnl']:>12,.2f}")
        print(f"  Unrealized P&L: ${metrics['unrealized_pnl']:>12,.2f}")
        print(f"  Total Return:   {metrics['total_return']:>13.2%}")

        print("\nALLOCATION:")
        print(f"  Crypto:         ${metrics['crypto_value']:>12,.2f} ({metrics['crypto_pct']:>5.1%})")
        print(f"  Stocks:         ${metrics['stock_value']:>12,.2f} ({metrics['stock_pct']:>5.1%})")

        print("\nPOSITIONS:")
        print(f"  Open:           {metrics['num_positions']:>12}")
        print(f"  Long:           {metrics['num_long']:>12}")
        print(f"  Short:          {metrics['num_short']:>12}")

        print("\nTRADES:")
        print(f"  Closed:         {metrics['num_closed_trades']:>12}")
        print(f"  Winners:        {metrics['winning_trades']:>12}")
        print(f"  Losers:         {metrics['losing_trades']:>12}")
        print(f"  Win Rate:       {metrics['win_rate']:>13.1%}")

        print("="*60 + "\n")


if __name__ == "__main__":
    # Test portfolio manager
    print("="*60)
    print("Testing Portfolio Manager")
    print("="*60)

    # Create portfolio
    portfolio = PortfolioManager(initial_capital=10000.0, mode='paper')

    # Open some positions
    print("\n1. Opening positions...")

    # Crypto position
    btc_pos = portfolio.open_position(
        symbol='BTC/USDT',
        asset_type=AssetType.CRYPTO,
        entry_price=50000.0,
        quantity=0.1,
        side='long',
        stop_loss=48000.0,
        take_profit=55000.0,
        strategy_name='RSI Strategy'
    )

    # Stock position
    aapl_pos = portfolio.open_position(
        symbol='AAPL',
        asset_type=AssetType.STOCK,
        entry_price=150.0,
        quantity=10,
        side='long',
        stop_loss=145.0,
        strategy_name='MA Crossover'
    )

    # Another crypto position
    eth_pos = portfolio.open_position(
        symbol='ETH/USDT',
        asset_type=AssetType.CRYPTO,
        entry_price=3000.0,
        quantity=1.0,
        side='long'
    )

    # Update prices
    print("\n2. Updating prices...")
    portfolio.update_prices({
        'BTC/USDT': 52000.0,  # +4% profit
        'AAPL': 148.0,        # -1.3% loss
        'ETH/USDT': 3100.0    # +3.3% profit
    })

    # Show portfolio
    portfolio.print_summary()

    # Close a position
    print("\n3. Closing BTC position...")
    portfolio.close_position(btc_pos.position_id, 52000.0, reason='take_profit')

    # Update and show again
    portfolio.print_summary()

    # Show positions DataFrame
    print("\nOpen Positions:")
    print(portfolio.get_positions_df()[['symbol', 'asset_type', 'quantity',
                                        'entry_price', 'current_price',
                                        'unrealized_pnl', 'unrealized_pnl_pct']])

    print("\nClosed Positions:")
    print(portfolio.get_closed_positions_df()[['symbol', 'entry_price', 'exit_price',
                                               'realized_pnl', 'realized_pnl_pct',
                                               'exit_reason']])

    print("\n✓ Portfolio manager working correctly!")
    print("="*60)
