"""Base strategy adapter.

All strategies extend this base class. It defines the interface for:
- Providing strategy metadata
- Loading signals
- Computing strategy-specific indicators
- Providing extra visualization data
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

import pandas as pd

from ..config.settings import AppConfig
from ..data_model.schemas import TradeSignal, PositionState, TradePair, StrategySummary
from ..data_loader.signal_loader import SignalLoader
from ..data_loader.price_loader import PriceLoader
from ..data_loader.extra_data import StrategyExtraDataLoader

logger = logging.getLogger(__name__)


class BaseStrategyAdapter(ABC):
    """Abstract base for strategy adapters.

    Each strategy adapter handles:
    - Loading signals for the strategy
    - Computing strategy-specific indicators
    - Providing extra data for visualization (optional)
    - Generating strategy-level summary statistics
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._signal_loader = SignalLoader(config)
        self._price_loader = PriceLoader(config)
        self._extra_loader: Optional[StrategyExtraDataLoader] = None

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Unique strategy name matching the signal directory suffix."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable display name for the strategy."""
        ...

    @property
    def description(self) -> str:
        """Optional strategy description."""
        return ""

    @property
    def has_extra_data(self) -> bool:
        """Whether this strategy provides extra visualization data."""
        return self._extra_loader is not None

    def get_extra_loader(self) -> Optional[StrategyExtraDataLoader]:
        """Get the extra data loader for this strategy."""
        return self._extra_loader

    def load_signals(self) -> List[TradeSignal]:
        """Load all trade signals for this strategy (effective only)."""
        return self._signal_loader.load_strategy_signals(self.strategy_name)

    def load_all_signals(self) -> List[TradeSignal]:
        """Load ALL trade signals including ineffective ones.

        Ineffective signals (label=2/4) are kept for frontend display
        purposes (e.g. stop-loss markers). Do NOT use these for trade
        pairing — use load_signals() for that.
        """
        return self._signal_loader.load_strategy_signals_all(self.strategy_name)

    def load_stock_signals(self, stock_code: str) -> List[TradeSignal]:
        """Load signals for a specific stock (effective only)."""
        return self._signal_loader.load_stock_signals(self.strategy_name, stock_code)

    def get_stock_list(self) -> List[str]:
        """Get sorted list of stock codes with signals for this strategy."""
        return self._signal_loader.get_signal_stocks(self.strategy_name)

    def load_price_data(
        self,
        stock_code: str,
        market: str = "A",
        level: str = "d",
    ) -> pd.DataFrame:
        """Load price bars as DataFrame for a stock."""
        return self._price_loader.load_price_bars_df(stock_code, market, level)

    def load_extra_data(
        self,
        stock_code: str,
        price_df: pd.DataFrame,
        market: str = "A",
        level: str = "d",
    ) -> Optional[pd.DataFrame]:
        """Load strategy-specific extra data for visualization.

        Args:
            stock_code: Stock code.
            price_df: Price DataFrame.
            market: Market type.
            level: Time level.

        Returns:
            DataFrame with extra indicator columns, or None.
        """
        if self._extra_loader is None:
            return None
        return self._extra_loader.load(stock_code, price_df, market, level)

    def get_summary(self) -> StrategySummary:
        """Generate summary statistics for this strategy.

        Must be overridden for accurate trade-level stats.
        This base implementation provides signal-level stats.
        """
        signals = self.load_signals()
        stocks = set(s.stock_code for s in signals)
        buy_signals = [s for s in signals if s.is_buy]
        sell_signals = [s for s in signals if s.is_sell]

        return StrategySummary(
            name=self.display_name,
            total_stocks=len(stocks),
            traded_stocks=len(set(s.stock_code for s in buy_signals)),
            total_return_pct=0.0,  # Requires trade pairing
            win_rate=0.0,  # Requires trade pairing
            current_positions=0,  # Requires trade pairing
            total_trades=0,  # Requires trade pairing
            winning_trades=0,
        )

    def validate_data_availability(
        self,
        stock_code: str,
        market: str = "A",
        level: str = "d",
    ) -> Dict[str, Any]:
        """Check data availability for a stock.

        Returns:
            Dict with keys: has_signals, has_price, signal_count, price_count,
            warnings (list of warning messages).
        """
        result = {
            "has_signals": False,
            "has_price": False,
            "signal_count": 0,
            "price_count": 0,
            "warnings": [],
        }

        # Check signals
        signals = self.load_stock_signals(stock_code)
        if signals:
            result["has_signals"] = True
            result["signal_count"] = len(signals)

        # Check price data
        try:
            price_df = self.load_price_data(stock_code, market, level)
            if not price_df.empty:
                result["has_price"] = True
                result["price_count"] = len(price_df)
        except FileNotFoundError as e:
            result["warnings"].append(
                f"Price data not found for {market}_{stock_code}_{level}: {e}"
            )
        except Exception as e:
            result["warnings"].append(
                f"Error loading price data for {stock_code}: {e}"
            )

        # Cross-validate dates
        if result["has_signals"] and result["has_price"]:
            signal_dates = {s.date_str for s in signals}
            date_warnings = self._price_loader.validate_signal_dates(
                stock_code, signal_dates, market, level
            )
            result["warnings"].extend(date_warnings)

        return result
