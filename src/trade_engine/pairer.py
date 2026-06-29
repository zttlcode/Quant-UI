"""Trade pairing engine.

Pairs buy/sell signals into trades with defined rules:
- Time-ordered scanning
- Buy opens a position, sell closes it
- Consecutive buys: keep first or last (configurable)
- Consecutive sells: ignore or warn (configurable)
- Last unclosed position: marked as open, valued at current price
"""

import logging
from typing import List, Optional, Tuple

import pandas as pd

from ..config.settings import AppConfig
from ..data_model.schemas import TradeSignal, TradePair, PriceBar
from ..data_model.enums import SignalType
from ..indicators.atr import compute_atr, compute_stop_loss

logger = logging.getLogger(__name__)


class TradePairer:
    """Pairs buy and sell signals into complete or open trades.

    Usage:
        pairer = TradePairer(config)
        trades = pairer.pair_signals(signals, price_df)
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._consecutive_buy = config.consecutive_buy_handling
        self._consecutive_sell = config.consecutive_sell_handling

    def pair_signals(
        self,
        signals: List[TradeSignal],
        price_df: pd.DataFrame,
    ) -> Tuple[List[TradePair], Optional[TradePair]]:
        """Pair buy and sell signals into trades.

        Args:
            signals: List of TradeSignal objects, sorted by time.
            price_df: Price data DataFrame indexed by time.

        Returns:
            Tuple of (closed_trades, open_position).
            open_position is None if all positions are closed.
        """
        if not signals:
            return [], None

        # Sort signals by time
        signals = sorted(signals, key=lambda s: s.time)

        closed_trades: List[TradePair] = []
        current_buy: Optional[TradeSignal] = None

        for sig in signals:
            if sig.is_buy:
                current_buy = self._handle_buy_signal(sig, current_buy)
            elif sig.is_sell:
                result = self._handle_sell_signal(
                    sig, current_buy, closed_trades, price_df
                )
                current_buy = result

        # Handle remaining open position
        open_position = None
        if current_buy is not None and self.config.show_unclosed_position:
            open_position = self._create_open_trade(current_buy, price_df)
            logger.info(
                "Unclosed position: %s entry at %.4f on %s",
                current_buy.stock_code,
                current_buy.price,
                current_buy.date_str,
            )

        logger.info(
            "Paired signals: %d closed trades, %s open position",
            len(closed_trades),
            "1" if open_position else "no",
        )

        return closed_trades, open_position

    def _handle_buy_signal(
        self,
        buy_sig: TradeSignal,
        current_buy: Optional[TradeSignal],
    ) -> Optional[TradeSignal]:
        """Handle a buy signal when there may already be an open position.

        Consecutive buy handling:
        - "first": keep the first buy, ignore the new one
        - "last": replace with the new buy
        """
        if current_buy is None:
            return buy_sig

        # Already have a buy — consecutive buy signals
        logger.warning(
            "Consecutive buy signals for %s: existing at %s (%.4f), new at %s (%.4f)",
            buy_sig.stock_code,
            current_buy.date_str, current_buy.price,
            buy_sig.date_str, buy_sig.price,
        )

        if self._consecutive_buy == "last":
            logger.info("  → Using latest buy signal")
            return buy_sig
        else:
            logger.info("  → Keeping first buy signal")
            return current_buy

    def _handle_sell_signal(
        self,
        sell_sig: TradeSignal,
        current_buy: Optional[TradeSignal],
        closed_trades: List[TradePair],
        price_df: pd.DataFrame,
    ) -> Optional[TradeSignal]:
        """Handle a sell signal.

        If there's a matching buy, close the trade.
        If no buy (unexpected sell), warn or ignore.
        """
        if current_buy is None:
            # Sell without a buy — unexpected
            msg = (
                f"Sell signal without matching buy for {sell_sig.stock_code} "
                f"at {sell_sig.date_str} (price={sell_sig.price:.4f})"
            )
            if self._consecutive_sell == "warn":
                logger.warning("UNEXPECTED: %s", msg)
            else:
                logger.debug("IGNORED: %s", msg)
            return None

        # Close the trade
        trade = self._create_closed_trade(current_buy, sell_sig, price_df)
        closed_trades.append(trade)

        logger.info(
            "Closed trade: %s %s → %s, PnL=%.2f%%",
            sell_sig.stock_code,
            current_buy.date_str,
            sell_sig.date_str,
            trade.pnl_pct * 100 if trade.pnl_pct else 0,
        )

        return None  # Position closed

    def _create_closed_trade(
        self,
        buy_sig: TradeSignal,
        sell_sig: TradeSignal,
        price_df: pd.DataFrame,
    ) -> TradePair:
        """Create a closed trade pair from matched buy/sell signals."""
        commission = self.config.commission
        slippage = self.config.slippage

        # Adjust prices for costs
        entry_cost = buy_sig.price * (1 + slippage) + commission
        exit_cost = sell_sig.price * (1 - slippage) - commission

        pnl = (exit_cost - entry_cost) / entry_cost

        # Compute ATR at entry for reference
        atr_val = self._get_atr_at_time(buy_sig.time, price_df)

        return TradePair(
            entry_signal=buy_sig,
            exit_signal=sell_sig,
            entry_price=entry_cost,
            exit_price=exit_cost,
            entry_time=buy_sig.time,
            exit_time=sell_sig.time,
            is_open=False,
            pnl_pct=pnl,
            stop_loss=None,
            atr_at_entry=atr_val,
        )

    def _create_open_trade(
        self,
        buy_sig: TradeSignal,
        price_df: pd.DataFrame,
    ) -> TradePair:
        """Create an open trade for a position that hasn't been closed yet."""
        commission = self.config.commission
        slippage = self.config.slippage

        # Get current price (last available close)
        if price_df.empty:
            current_price = buy_sig.price
        else:
            current_price = float(price_df["close"].iloc[-1])

        # Apply costs consistently with _create_closed_trade
        entry_cost = buy_sig.price * (1 + slippage) + commission
        exit_cost = current_price * (1 - slippage) - commission
        pnl = (exit_cost - entry_cost) / entry_cost

        # Compute stop loss
        atr_val = self._get_atr_at_time(buy_sig.time, price_df)
        if atr_val is not None and not pd.isna(atr_val):
            stop_loss = compute_stop_loss(
                buy_sig.price, atr_val, self.config.hold_stop_atr_multiplier
            )
        else:
            stop_loss = None

        return TradePair(
            entry_signal=buy_sig,
            exit_signal=None,
            entry_price=entry_cost,
            exit_price=current_price,
            entry_time=buy_sig.time,
            exit_time=None,
            is_open=True,
            pnl_pct=pnl,
            stop_loss=stop_loss,
            atr_at_entry=atr_val,
        )

    def _get_atr_at_time(
        self,
        entry_time,
        price_df: pd.DataFrame,
    ) -> Optional[float]:
        """Get ATR value at or near a given entry time."""
        if price_df.empty:
            return None

        required_cols = {"high", "low", "close"}
        if not required_cols.issubset(price_df.columns):
            return None

        try:
            atr_series = compute_atr(
                price_df["high"],
                price_df["low"],
                price_df["close"],
                self.config.atr_period,
            )

            # Find the closest time index
            if isinstance(price_df.index, pd.DatetimeIndex):
                # Find nearest index position
                idx_pos = price_df.index.get_indexer(
                    [pd.Timestamp(entry_time)], method="nearest"
                )[0]
                if idx_pos >= 0 and idx_pos < len(atr_series):
                    atr_val = atr_series.iloc[idx_pos]
                    if not pd.isna(atr_val):
                        return float(atr_val)
            else:
                # For non-DatetimeIndex, try to find matching time
                for i, idx in enumerate(price_df.index):
                    idx_dt = pd.Timestamp(idx) if hasattr(idx, "strftime") else idx
                    entry_dt = pd.Timestamp(entry_time)
                    if abs((idx_dt - entry_dt).days) <= 1:
                        if i < len(atr_series) and not pd.isna(atr_series.iloc[i]):
                            return float(atr_series.iloc[i])

            # Fallback: use last valid ATR
            valid_atr = atr_series.dropna()
            if not valid_atr.empty:
                return float(valid_atr.iloc[-1])

        except Exception as e:
            logger.warning("Could not compute ATR at entry time: %s", e)

        return None
