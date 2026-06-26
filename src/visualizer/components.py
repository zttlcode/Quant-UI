"""Reusable Streamlit UI components for the Quant-UI platform.

Provides rendering functions for:
- Label legend cards
- Position status displays
- Trade history tables
- Strategy cards
- Stock summary cards
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

import streamlit as st
import pandas as pd

from ..data_model.schemas import (
    TradePair, TradeSignal, PositionState, StrategySummary, StockSummary,
    TradeRecord,
)
from ..data_model.enums import LabelType, SignalType

logger = logging.getLogger(__name__)


def render_label_legend():
    """Render a label legend card explaining signal labels."""
    with st.expander("📋 信号标签说明 (Label Legend)", expanded=False):
        cols = st.columns(4)
        with cols[0]:
            st.markdown("**Label 1**")
            st.success("有效买入 (Effective Buy)")
            st.caption("策略判断为有效的买入信号")
        with cols[1]:
            st.markdown("**Label 2**")
            st.warning("无效买入 (Ineffective Buy)")
            st.caption("策略判断为无效的买入信号")
        with cols[2]:
            st.markdown("**Label 3**")
            st.info("有效卖出 (Effective Sell)")
            st.caption("策略判断为有效的卖出信号")
        with cols[3]:
            st.markdown("**Label 4**")
            st.error("无效卖出 (Ineffective Sell)")
            st.caption("策略判断为无效的卖出信号")


def render_position_status(position: PositionState):
    """Render current position status card.

    Args:
        position: PositionState object with current position info.
    """
    if position.is_holding:
        st.markdown("### 📈 当前持仓状态")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pnl_color = "green" if (position.pnl_pct or 0) >= 0 else "red"
            st.metric(
                "浮动收益率",
                f"{position.pnl_pct * 100:.2f}%" if position.pnl_pct else "N/A",
            )
        with col2:
            st.metric(
                "入场价",
                f"{position.entry_price:.4f}" if position.entry_price else "N/A",
            )
        with col3:
            st.metric(
                "当前价",
                f"{position.current_price:.4f}" if position.current_price else "N/A",
            )
        with col4:
            stop_str = f"{position.stop_loss:.4f}" if position.stop_loss else "⚠️ ATR不足"
            st.metric("止损位", stop_str)

        if position.entry_time:
            st.caption(f"入场时间: {position.entry_time.strftime('%Y-%m-%d %H:%M')}")

        if position.atr_value is None:
            st.warning("⚠️ ATR 不足，无法计算止损位。请确认历史数据长度 ≥ 15 根K线。")
    else:
        st.markdown("### ✅ 已清仓")
        st.info("当前没有持仓。下方显示历史交易记录。")


def render_trade_table(
    trades: List[TradePair],
    stock_code: str = "",
    open_position: Optional[TradePair] = None,
):
    """Render a trade history table.

    Args:
        trades: List of completed trades.
        stock_code: Stock code filter.
        open_position: Current open position.
    """
    records = []

    # Add open position first
    if open_position is not None:
        entry = open_position.entry_signal
        records.append({
            "状态": "📈 持仓中",
            "入场时间": entry.time.strftime("%Y-%m-%d") if entry.time else "",
            "出场时间": "—",
            "入场价": f"{open_position.entry_price:.4f}",
            "出场价": f"{open_position.exit_price:.4f}" if open_position.exit_price else "—",
            "收益率": f"{open_position.pnl_pct * 100:.2f}%" if open_position.pnl_pct else "—",
            "入场Label": f"Label {entry.label.value}" if entry.label else "N/A",
            "出场Label": "—",
            "入场Prob": f"{entry.prob:.3f}" if entry.prob else "N/A",
            "备注": "未平仓",
        })

    # Add closed trades
    for trade in trades:
        if stock_code and trade.entry_signal.stock_code != stock_code:
            continue

        entry = trade.entry_signal
        ext = trade.exit_signal

        pnl_val = trade.pnl_pct
        pnl_str = f"{pnl_val * 100:.2f}%" if pnl_val is not None else "N/A"

        records.append({
            "状态": "✅ 已平仓",
            "入场时间": entry.time.strftime("%Y-%m-%d") if entry.time else "",
            "出场时间": ext.time.strftime("%Y-%m-%d") if ext else "",
            "入场价": f"{trade.entry_price:.4f}",
            "出场价": f"{trade.exit_price:.4f}" if trade.exit_price else "—",
            "收益率": pnl_str,
            "入场Label": f"Label {entry.label.value}" if entry.label else "N/A",
            "出场Label": f"Label {ext.label.value}" if ext and ext.label else "N/A",
            "入场Prob": f"{entry.prob:.3f}" if entry.prob else "N/A",
            "备注": "",
        })

    if records:
        df = pd.DataFrame(records)
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "收益率": st.column_config.TextColumn("收益率"),
            },
        )
    else:
        st.info("暂无交易记录。")


def render_strategy_card(summary: StrategySummary) -> None:
    """Render a strategy summary card on the home page.

    Args:
        summary: StrategySummary with computed statistics.
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("覆盖股票", summary.total_stocks)
    with col2:
        st.metric("已交易", summary.traded_stocks)
    with col3:
        return_color = "normal"
        st.metric(
            "总收益率",
            f"{summary.total_return_pct:.2f}%",
            delta=None,
        )
    with col4:
        st.metric("胜率", f"{summary.win_rate * 100:.1f}%")
    with col5:
        st.metric("当前持仓", summary.current_positions)


def render_stock_summary_card(stock_info: dict) -> None:
    """Render a stock summary card.

    Args:
        stock_info: Dict with stock summary fields.
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        holding = "📈 持仓" if stock_info.get("is_holding") else "✅ 已清仓"
        st.markdown(f"**状态:** {holding}")
    with col2:
        pnl = stock_info.get("pnl_pct")
        if pnl is not None:
            color = "green" if pnl >= 0 else "red"
            st.markdown(f"**收益率:** :{color}[{pnl * 100:.2f}%]")
        else:
            st.markdown("**收益率:** N/A")
    with col3:
        entry = stock_info.get("entry_price")
        if entry:
            st.markdown(f"**入场价:** {entry:.4f}")
    with col4:
        current = stock_info.get("current_price")
        if current:
            st.markdown(f"**当前价:** {current:.4f}")


def render_data_warnings(warnings: List[str]) -> None:
    """Render data validation warnings.

    Args:
        warnings: List of warning message strings.
    """
    if warnings:
        with st.expander(f"⚠️ 数据警告 ({len(warnings)})", expanded=True):
            for w in warnings:
                st.warning(w)


def render_signal_filter_ui(key_prefix: str = "") -> dict:
    """Render signal filter UI controls.

    Returns:
        Dict with filter parameters.
    """
    col1, col2 = st.columns(2)
    with col1:
        show_open = st.checkbox(
            "显示未平仓持仓",
            value=True,
            key=f"{key_prefix}_open",
        )
    with col2:
        show_volume = st.checkbox(
            "显示成交量",
            value=False,
            key=f"{key_prefix}_volume",
        )

    return {
        "show_unclosed": show_open,
        "show_volume": show_volume,
    }
