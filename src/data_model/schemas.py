"""Standard data structures for the Quant-UI platform.

All data structures use dataclasses for type safety and pydantic-like validation.
Fields are named consistently across the platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

import pandas as pd

from .enums import SignalType, LabelType


@dataclass
class TradeSignal:
    """A single trade signal from a strategy.

    Attributes:
        time: Trade signal timestamp.
        price: Trade price at signal time.
        signal: Buy or sell direction.
        label: Model inference label (1-4). None if not provided.
        prob: Class probability from model. None if not provided.
        stock_code: Stock code (e.g., '000027').
        market: Market type (e.g., 'A').
        level: Time level (e.g., 'd').
        strategy_name: Name of the strategy that generated this signal.
    """
    time: datetime
    price: float
    signal: SignalType
    label: Optional[LabelType] = None
    prob: Optional[float] = None
    stock_code: str = ""
    market: str = "A"
    level: str = "d"
    strategy_name: str = ""

    @property
    def is_buy(self) -> bool:
        return self.signal == SignalType.BUY

    @property
    def is_sell(self) -> bool:
        return self.signal == SignalType.SELL

    @property
    def is_effective(self) -> bool:
        """A signal is effective if label is 1 or 3, or if no label is present."""
        if self.label is None:
            return True  # Without labels, all signals are treated as effective
        return self.label.is_effective

    @property
    def date_str(self) -> str:
        """Date string in YYYY-MM-DD format."""
        return self.time.strftime("%Y-%m-%d")

    def __post_init__(self):
        """Validate and coerce fields after initialization."""
        if self.price <= 0:
            raise ValueError(f"Price must be positive, got {self.price}")
        if self.label is not None and not isinstance(self.label, LabelType):
            self.label = LabelType(int(self.label))
        if self.prob is not None and not isinstance(self.prob, float):
            self.prob = float(self.prob)


@dataclass
class PriceBar:
    """A single OHLCV price bar.

    Attributes:
        time: Bar timestamp.
        open: Open price.
        high: High price.
        low: Low price.
        close: Close price.
        volume: Trading volume.
        stock_code: Stock code.
        market: Market type.
        level: Time level.
    """
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    stock_code: str = ""
    market: str = "A"
    level: str = "d"

    def __post_init__(self):
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) cannot be less than low ({self.low})")


@dataclass
class TradePair:
    """A completed or open trade pair (buy → sell).

    Attributes:
        entry_signal: The buy signal that opened the trade.
        exit_signal: The sell signal that closed the trade (None if still open).
        entry_price: Effective entry price.
        exit_price: Effective exit price (current market price if open).
        entry_time: Entry timestamp.
        exit_time: Exit timestamp (None if still open).
        is_open: Whether the position is still open.
        pnl_pct: Profit/loss percentage.
        stop_loss: Stop loss price (if open).
        atr_at_entry: ATR value at entry time (for stop loss).
    """
    entry_signal: TradeSignal
    exit_signal: Optional[TradeSignal] = None
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    is_open: bool = False
    pnl_pct: Optional[float] = None
    stop_loss: Optional[float] = None
    atr_at_entry: Optional[float] = None

    def __post_init__(self):
        if self.entry_price <= 0:
            self.entry_price = self.entry_signal.price
        if self.entry_time is None:
            self.entry_time = self.entry_signal.time

    @property
    def holding_bars(self) -> Optional[int]:
        """Number of bars held (None if still open and no current time)."""
        return None  # Must be computed with price data


@dataclass
class PositionState:
    """Current position state for a stock/strategy combination.

    Attributes:
        stock_code: Stock code.
        strategy_name: Strategy name.
        is_holding: Whether currently holding a position.
        entry_price: Entry price of current position.
        current_price: Latest market price.
        pnl_pct: Unrealized P&L percentage.
        stop_loss: Stop loss price.
        entry_time: Position entry time.
        holding_days: Number of days held.
        atr_value: Current ATR value.
        last_signal: Most recent signal that opened the position.
    """
    stock_code: str
    strategy_name: str
    is_holding: bool = False
    entry_price: Optional[float] = None
    current_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    stop_loss: Optional[float] = None
    entry_time: Optional[datetime] = None
    holding_days: Optional[int] = None
    atr_value: Optional[float] = None
    last_signal: Optional[TradeSignal] = None

    @property
    def status_label(self) -> str:
        if self.is_holding:
            return "📈 持仓中"
        return "✅ 已清仓"


@dataclass
class StrategyExtraData:
    """Abstract extra data interface for strategies.

    Each strategy can provide additional visualization data by implementing
    this interface. The data is keyed by stock code.

    Attributes:
        strategy_name: Name of the strategy.
        data: Dict of stock_code → DataFrame with extra indicator columns.
        description: Human-readable description of the extra data.
        needs_subplot: Whether this data needs its own subplot.
    """
    strategy_name: str
    data: Dict[str, pd.DataFrame] = field(default_factory=dict)
    description: str = ""
    needs_subplot: bool = True

    def has_data(self, stock_code: str) -> bool:
        return stock_code in self.data and not self.data[stock_code].empty

    def get_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        return self.data.get(stock_code)


@dataclass
class StrategySummary:
    """Summary statistics for a strategy."""
    name: str
    total_stocks: int = 0
    traded_stocks: int = 0
    total_return_pct: float = 0.0
    win_rate: float = 0.0
    current_positions: int = 0
    total_trades: int = 0
    winning_trades: int = 0


@dataclass
class StockSummary:
    """Summary for a single stock under a strategy."""
    stock_code: str
    strategy_name: str
    market: str = "A"
    level: str = "d"
    is_holding: bool = False
    pnl_pct: Optional[float] = None
    entry_price: Optional[float] = None
    current_price: Optional[float] = None
    total_trades: int = 0
    trade_count: int = 0


@dataclass
class TradeRecord:
    """A single trade record for display in trade history table."""
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    pnl_pct: Optional[float]
    entry_label: Optional[LabelType]
    exit_label: Optional[LabelType]
    entry_prob: Optional[float]
    exit_prob: Optional[float]
    is_open: bool
    note: str = ""
