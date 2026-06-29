"""Plotly chart builder for interactive stock strategy visualization.

Builds multi-panel charts with:
- Panel 1: Candlestick + MA lines + Buy/Sell markers
- Panel 2: MACD (DIF, DEA, histogram)
- Panel 3 (optional): Fuzzy extra data (avmood)

All charts are interactive with hover tooltips, zoom, and pan.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data_model.schemas import TradeSignal, TradePair, PriceBar
from ..data_model.enums import SignalType, LabelType
from ..indicators.ma import compute_ma, compute_multiple_mas
from ..indicators.macd import compute_macd
from ..indicators.atr import compute_atr

logger = logging.getLogger(__name__)

# Color scheme
COLOR_BUY = "#00CC96"          # Green for buy markers
COLOR_SELL = "#EF553B"         # Red for sell markers
COLOR_MA5 = "#636EFA"          # Blue
COLOR_MA10 = "#FFA15A"         # Orange
COLOR_MA20 = "#B6E880"         # Light green
COLOR_CANDLE_UP = "#EF553B"    # Red for up (Chinese convention: red = up)
COLOR_CANDLE_DOWN = "#00CC96"  # Green for down
COLOR_MACD_POS = "#EF553B"     # Red
COLOR_MACD_NEG = "#00CC96"     # Green
COLOR_DIF = "#636EFA"          # Blue
COLOR_DEA = "#FFA15A"          # Orange
COLOR_AVMOOD = "#AB63FA"       # Purple
COLOR_STOP_LOSS = "#FF0000"    # Red dashed
COLOR_VOLUME = "rgba(128, 128, 128, 0.3)"


class ChartBuilder:
    """Builds interactive Plotly charts for stock strategy visualization.

    Usage:
        builder = ChartBuilder()
        fig = builder.build_chart(price_df, signals, trades, ...)
    """

    def __init__(self, ma_periods: Optional[List[int]] = None):
        self.ma_periods = ma_periods or [5, 10, 20]

    def build_chart(
        self,
        price_df: pd.DataFrame,
        signals: List[TradeSignal],
        trades: List[TradePair],
        open_position: Optional[TradePair] = None,
        extra_data: Optional[pd.DataFrame] = None,
        extra_label: str = "",
        title: str = "",
    ) -> go.Figure:
        """Build the complete multi-panel chart.

        Args:
            price_df: OHLCV data indexed by time.
            signals: List of trade signals (label 2/4 already filtered at load time).
            trades: List of completed trades.
            open_position: Current open position (if any).
            extra_data: Strategy-specific extra indicator data.
            extra_label: Label for the extra data subplot.
            title: Chart title.

        Returns:
            Plotly Figure with subplots.
        """
        # Determine number of panels
        has_extra = extra_data is not None and not extra_data.empty
        n_rows = 3 if has_extra else 2
        row_heights = [0.55, 0.15, 0.30] if has_extra else [0.65, 0.35]

        subplot_titles = [title, "MACD (DIF / DEA)"]
        if has_extra:
            subplot_titles.append(extra_label or "Extra Indicators")

        fig = make_subplots(
            rows=n_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=subplot_titles,
        )

        # Panel 1: Candlestick + MAs + Trade Markers
        self._add_candlestick(fig, price_df, row=1)
        self._add_moving_averages(fig, price_df, row=1)
        self._add_trade_markers(fig, price_df, signals, trades, open_position, row=1)
        self._add_stop_loss_line(fig, price_df, open_position, row=1)

        # Panel 2: MACD
        self._add_macd_panel(fig, price_df, row=2)

        # Panel 3: Extra data (fuzzy_ma avmood)
        if has_extra:
            self._add_extra_panel(fig, extra_data, row=3)

        # Global layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor="center"),
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            height=900 if has_extra else 700,
            template="plotly_dark",
        )

        # Update axes
        fig.update_xaxes(gridcolor="rgba(128,128,128,0.1)")
        fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)")

        # X-axis labels only on bottom panel
        if n_rows > 1:
            fig.update_xaxes(showticklabels=False, row=1)

        return fig

    def _add_candlestick(self, fig: go.Figure, price_df: pd.DataFrame, row: int = 1):
        """Add candlestick chart."""
        if price_df.empty:
            return

        fig.add_trace(
            go.Candlestick(
                x=price_df.index,
                open=price_df["open"],
                high=price_df["high"],
                low=price_df["low"],
                close=price_df["close"],
                name="K线",
                increasing=dict(line=dict(color=COLOR_CANDLE_UP), fillcolor=COLOR_CANDLE_UP),
                decreasing=dict(line=dict(color=COLOR_CANDLE_DOWN), fillcolor=COLOR_CANDLE_DOWN),
                hovertext=[
                    f"日期: {idx.strftime('%Y-%m-%d')}<br>"
                    f"开: {row['open']:.4f}<br>"
                    f"高: {row['high']:.4f}<br>"
                    f"低: {row['low']:.4f}<br>"
                    f"收: {row['close']:.4f}<br>"
                    f"量: {row['volume']:,.0f}"
                    for idx, (_, row) in zip(price_df.index, price_df.iterrows())
                ],
                hoverinfo="text",
            ),
            row=row,
            col=1,
        )

    def _add_moving_averages(
        self,
        fig: go.Figure,
        price_df: pd.DataFrame,
        row: int = 1,
    ):
        """Add MA5, MA10, MA20 lines."""
        if "close" not in price_df.columns:
            return

        close = price_df["close"]
        ma_colors = {5: COLOR_MA5, 10: COLOR_MA10, 20: COLOR_MA20}

        for period in self.ma_periods:
            if len(close) < period:
                continue
            ma = compute_ma(close, period)
            color = ma_colors.get(period, "white")
            fig.add_trace(
                go.Scatter(
                    x=price_df.index,
                    y=ma.values,
                    name=f"MA{period}",
                    line=dict(color=color, width=1.2),
                    opacity=0.7,
                    hovertemplate=f"MA{period}: %{{y:.4f}}<extra></extra>",
                ),
                row=row,
                col=1,
            )

    def _add_trade_markers(
        self,
        fig: go.Figure,
        price_df: pd.DataFrame,
        signals: List[TradeSignal],
        trades: List[TradePair],
        open_position: Optional[TradePair],
        row: int = 1,
    ):
        """Add buy/sell markers on the main chart.

        Note: Ineffective signals (label=2/4) are filtered at load time
        by SignalLoader, so all signals here are guaranteed effective.
        """
        if price_df.empty:
            return

        # Collect buy and sell markers
        buy_markers: List[Tuple[pd.Timestamp, float, str, TradeSignal]] = []
        sell_markers: List[Tuple[pd.Timestamp, float, str, TradeSignal]] = []

        # From closed trades
        for trade in trades:
            entry = trade.entry_signal
            self._add_signal_marker(buy_markers, entry, price_df, "buy")

            if trade.exit_signal:
                ext = trade.exit_signal
                self._add_signal_marker(sell_markers, ext, price_df, "sell")

        # Open position
        if open_position:
            entry = open_position.entry_signal
            self._add_signal_marker(buy_markers, entry, price_df, "buy")

        # Unmatched signals
        used_times = set()
        for trade in trades:
            used_times.add(trade.entry_signal.time)
            if trade.exit_signal:
                used_times.add(trade.exit_signal.time)
        if open_position:
            used_times.add(open_position.entry_signal.time)

        for sig in signals:
            if sig.time not in used_times:
                if sig.is_buy:
                    self._add_signal_marker(buy_markers, sig, price_df, "buy")
                else:
                    self._add_signal_marker(sell_markers, sig, price_df, "sell")

        # Plot buy markers
        if buy_markers:
            buy_times, buy_prices, buy_texts, _ = zip(*buy_markers)
            fig.add_trace(
                go.Scatter(
                    x=list(buy_times),
                    y=list(buy_prices),
                    mode="markers",
                    name="买入 (Buy)",
                    marker=dict(
                        symbol="triangle-up",
                        size=12,
                        color=COLOR_BUY,
                        line=dict(width=1, color="darkgreen"),
                    ),
                    text=list(buy_texts),
                    hoverinfo="text",
                    hoverlabel=dict(bgcolor=COLOR_BUY),
                ),
                row=row,
                col=1,
            )

        # Plot sell markers
        if sell_markers:
            sell_times, sell_prices, sell_texts, _ = zip(*sell_markers)
            fig.add_trace(
                go.Scatter(
                    x=list(sell_times),
                    y=list(sell_prices),
                    mode="markers",
                    name="卖出 (Sell)",
                    marker=dict(
                        symbol="triangle-down",
                        size=12,
                        color=COLOR_SELL,
                        line=dict(width=1, color="darkred"),
                    ),
                    text=list(sell_texts),
                    hoverinfo="text",
                    hoverlabel=dict(bgcolor=COLOR_SELL),
                ),
                row=row,
                col=1,
            )

    def _add_signal_marker(
        self,
        markers: list,
        sig: TradeSignal,
        price_df: pd.DataFrame,
        _type: str,
    ):
        """Add a single signal marker with hover tooltip."""
        try:
            ts = pd.Timestamp(sig.time)
        except Exception:
            return

        label_str = f" (label={sig.label.value})" if sig.label else ""
        prob_str = f", prob={sig.prob:.3f}" if sig.prob is not None else ""
        effective = "✓有效" if sig.is_effective else "✗无效"

        hover = (
            f"时间: {sig.date_str}<br>"
            f"价格: {sig.price:.4f}<br>"
            f"信号: {sig.signal.value}{label_str}<br>"
            f"{effective}{prob_str}"
        )

        markers.append((ts, sig.price, hover, sig))

    def _add_stop_loss_line(
        self,
        fig: go.Figure,
        price_df: pd.DataFrame,
        open_position: Optional[TradePair],
        row: int = 1,
    ):
        """Add stop loss line for open positions."""
        if open_position is None or open_position.stop_loss is None:
            return

        if price_df.empty:
            return

        # Draw horizontal line at stop loss price
        stop_price = open_position.stop_loss
        fig.add_hline(
            y=stop_price,
            line=dict(color=COLOR_STOP_LOSS, width=1.5, dash="dash"),
            annotation_text=f"止损: {stop_price:.4f}",
            annotation_position="right",
            row=row,
            col=1,
        )

    def _add_macd_panel(self, fig: go.Figure, price_df: pd.DataFrame, row: int = 2):
        """Add MACD subplot with DIF, DEA, and histogram."""
        if price_df.empty or "close" not in price_df.columns:
            return

        close = price_df["close"]
        macd_df = compute_macd(close)

        if macd_df.empty:
            return

        idx = price_df.index

        # MACD histogram
        macd_vals = macd_df["MACD"].values
        colors = [COLOR_MACD_POS if v >= 0 else COLOR_MACD_NEG for v in macd_vals]

        fig.add_trace(
            go.Bar(
                x=idx,
                y=macd_vals,
                name="MACD",
                marker=dict(color=colors),
                hovertemplate="MACD: %{y:.6f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        # DIF line
        fig.add_trace(
            go.Scatter(
                x=idx,
                y=macd_df["DIF"].values,
                name="DIF",
                line=dict(color=COLOR_DIF, width=1.2),
                hovertemplate="DIF: %{y:.6f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        # DEA line
        fig.add_trace(
            go.Scatter(
                x=idx,
                y=macd_df["DEA"].values,
                name="DEA",
                line=dict(color=COLOR_DEA, width=1.2),
                hovertemplate="DEA: %{y:.6f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        # Zero line
        fig.add_hline(
            y=0,
            line=dict(color="gray", width=0.5, dash="dot"),
            row=row,
            col=1,
        )

    def _add_extra_panel(
        self,
        fig: go.Figure,
        extra_data: pd.DataFrame,
        row: int = 3,
    ):
        """Add strategy-specific extra data subplot (e.g., avmood)."""
        if extra_data.empty:
            return

        idx = extra_data.index

        # avmood curve
        if "avmood" in extra_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=idx,
                    y=extra_data["avmood"].values,
                    name="avmood",
                    line=dict(color=COLOR_AVMOOD, width=1.5),
                    hovertemplate="avmood: %{y:.6f}<extra></extra>",
                ),
                row=row,
                col=1,
            )

            # Mark cross points
            cross_data = extra_data[extra_data["avmood_cross"] != 0]
            if not cross_data.empty:
                cross_up = cross_data[cross_data["avmood_cross"] == 1]
                cross_down = cross_data[cross_data["avmood_cross"] == -1]

                if not cross_up.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=cross_up.index,
                            y=[0] * len(cross_up),
                            mode="markers",
                            name="avmood ↑0",
                            marker=dict(
                                symbol="triangle-up",
                                size=10,
                                color="lime",
                                line=dict(width=1, color="green"),
                            ),
                            hovertemplate="avmood 上穿0<br>%{x}<extra></extra>",
                        ),
                        row=row,
                        col=1,
                    )

                if not cross_down.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=cross_down.index,
                            y=[0] * len(cross_down),
                            mode="markers",
                            name="avmood ↓0",
                            marker=dict(
                                symbol="triangle-down",
                                size=10,
                                color="red",
                                line=dict(width=1, color="darkred"),
                            ),
                            hovertemplate="avmood 下穿0<br>%{x}<extra></extra>",
                        ),
                        row=row,
                        col=1,
                    )

            # Zero line
            fig.add_hline(
                y=0,
                line=dict(color="yellow", width=0.8, dash="dot"),
                row=row,
                col=1,
            )

        # mood curve (optional, thinner)
        if "mood" in extra_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=idx,
                    y=extra_data["mood"].values,
                    name="mood",
                    line=dict(color="gray", width=0.8, dash="dot"),
                    opacity=0.5,
                    hovertemplate="mood: %{y:.6f}<extra></extra>",
                ),
                row=row,
                col=1,
            )

    def build_simple_price_chart(
        self,
        price_df: pd.DataFrame,
        title: str = "Price Chart",
    ) -> go.Figure:
        """Build a simple price overview chart (for thumbnails).

        Args:
            price_df: OHLCV data.
            title: Chart title.

        Returns:
            Plotly Figure.
        """
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=price_df.index,
                y=price_df["close"],
                name="Close",
                line=dict(color="#636EFA", width=1.5),
                hovertemplate="%{x}<br>%{y:.4f}<extra></extra>",
            )
        )

        fig.update_layout(
            title=dict(text=title, x=0.5),
            height=300,
            margin=dict(l=30, r=30, t=40, b=30),
            template="plotly_dark",
            showlegend=False,
        )

        return fig
