"""PnL calculator for trade performance analysis.

Computes:
- Single trade P&L
- Cumulative P&L
- Strategy-level statistics (win rate, total return, etc.)
"""

import logging
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from ..data_model.schemas import TradePair, TradeSignal, PositionState, StrategySummary
from ..data_model.enums import LabelType

logger = logging.getLogger(__name__)


class PnLCalculator:
    """Computes profit/loss statistics for trades and strategies.

    Usage:
        calc = PnLCalculator(config)
        stats = calc.compute_strategy_stats(trades, strategy_name)
    """

    def __init__(self, commission: float = 0.0, slippage: float = 0.0):
        self.commission = commission
        self.slippage = slippage

    def compute_trade_pnl(
        self,
        entry_price: float,
        exit_price: float,
        is_long: bool = True,
    ) -> float:
        """Compute P&L for a single trade.

        Args:
            entry_price: Entry price.
            exit_price: Exit price.
            is_long: True for long positions.

        Returns:
            P&L as a decimal (e.g., 0.05 = 5%).
        """
        direction = 1 if is_long else -1
        gross = (exit_price - entry_price) / entry_price * direction
        # Apply costs
        cost_pct = self.commission * 2 / entry_price + self.slippage * 2
        return gross - cost_pct

    def compute_cumulative_returns(
        self,
        trades: List[TradePair],
    ) -> pd.Series:
        """Compute cumulative returns from a list of trades.

        Returns:
            Series of cumulative return at each trade.
        """
        returns = []
        cumulative = 1.0

        for trade in trades:
            if trade.pnl_pct is not None:
                cumulative *= (1 + trade.pnl_pct)
                returns.append(cumulative - 1)

        return pd.Series(returns)

    def compute_strategy_summary(
        self,
        trades: List[TradePair],
        strategy_name: str,
        total_stocks: int,
    ) -> StrategySummary:
        """Compute strategy-level summary statistics.

        Args:
            trades: All closed trades.
            strategy_name: Strategy display name.
            total_stocks: Total number of stocks in the strategy.

        Returns:
            StrategySummary with computed statistics.
        """
        closed = [t for t in trades if not t.is_open]
        open_trades = [t for t in trades if t.is_open]
        wins = [t for t in closed if t.pnl_pct is not None and t.pnl_pct > 0]

        total_return = 0.0
        for t in closed:
            if t.pnl_pct is not None:
                total_return += t.pnl_pct

        win_rate = len(wins) / len(closed) if closed else 0.0

        return StrategySummary(
            name=strategy_name,
            total_stocks=total_stocks,
            traded_stocks=len(set(t.entry_signal.stock_code for t in trades)),
            total_return_pct=total_return * 100,
            win_rate=win_rate,
            current_positions=len(open_trades),
            total_trades=len(closed),
            winning_trades=len(wins),
        )

    @staticmethod
    def get_position_state(
        open_trades: List[TradePair],
        stock_code: str,
        strategy_name: str,
        current_price: Optional[float] = None,
    ) -> PositionState:
        """Get current position state for a stock.

        Args:
            open_trades: List of open trades.
            stock_code: Stock code to check.
            strategy_name: Strategy name.
            current_price: Latest market price.

        Returns:
            PositionState describing the current position.
        """
        stock_open = [t for t in open_trades if t.entry_signal.stock_code == stock_code]

        if not stock_open:
            return PositionState(
                stock_code=stock_code,
                strategy_name=strategy_name,
                is_holding=False,
            )

        # Take the most recent open trade
        trade = stock_open[-1]

        return PositionState(
            stock_code=stock_code,
            strategy_name=strategy_name,
            is_holding=True,
            entry_price=trade.entry_price,
            current_price=current_price or trade.exit_price,
            pnl_pct=trade.pnl_pct,
            stop_loss=trade.stop_loss,
            entry_time=trade.entry_time,
            atr_value=trade.atr_at_entry,
            last_signal=trade.entry_signal,
        )

    @staticmethod
    def get_closed_trade_stats(
        closed_trades: List[TradePair],
        stock_code: str,
    ) -> dict:
        """Get statistics for closed trades of a stock.

        Returns:
            Dict with: total_trades, total_pnl_pct, win_count, loss_count,
            last_trade_pnl, last_exit_time.
        """
        stock_trades = [t for t in closed_trades if t.entry_signal.stock_code == stock_code]
        stock_trades.sort(key=lambda t: t.exit_time or t.entry_time)

        wins = [t for t in stock_trades if t.pnl_pct is not None and t.pnl_pct > 0]

        total_pnl = sum(t.pnl_pct for t in stock_trades if t.pnl_pct is not None)

        last_trade = stock_trades[-1] if stock_trades else None

        return {
            "total_trades": len(stock_trades),
            "total_pnl_pct": total_pnl * 100,
            "win_count": len(wins),
            "loss_count": len(stock_trades) - len(wins),
            "win_rate": len(wins) / len(stock_trades) if stock_trades else 0.0,
            "last_trade_pnl": (last_trade.pnl_pct * 100) if last_trade and last_trade.pnl_pct else None,
            "last_exit_time": last_trade.exit_time if last_trade else None,
        }
