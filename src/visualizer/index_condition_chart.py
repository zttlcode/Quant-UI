"""Index market condition chart builder.

Builds an interactive Plotly candlestick chart with market condition
classification overlay, plus Streamlit UI components for the latest bar display.
"""

import logging
from typing import Optional, Dict, List, Tuple

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data_loader.index_condition_loader import (
    IndexConditionData,
    CONDITION_LABELS,
    CONDITION_COLORS,
    CONDITION_BG_COLORS,
)

logger = logging.getLogger(__name__)

# ---------- 颜色常量 ----------
COLOR_GRID = "rgba(128, 128, 128, 0.15)"
COLOR_TEXT = "#9CA3AF"


def build_index_condition_chart(
    data: IndexConditionData,
    visible_bars: int = 60,
) -> go.Figure:
    """构建带行情分类的蜡烛图。

    Args:
        data: 合并后的指数行情 + 分类数据。
        visible_bars: 默认显示的最近 bar 数量。

    Returns:
        Plotly Figure，单面板蜡烛图 + 底部条件指示条。
    """
    df = data.df

    if df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark")
        return fig

    # 默认显示最近 N 个 bar
    display_df = df.tail(visible_bars).copy()

    # 创建子图：主图 + 底部条件指示条
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.92, 0.08],
    )

    # ---- Panel 1: 蜡烛图（按行情分类着色） ----
    _add_colored_candlesticks(fig, display_df, row=1)

    # ---- Panel 2: 行情分类指示条 ----
    _add_condition_indicator(fig, display_df, row=2)

    # ---- 全局布局 ----
    title = f"{data.index_name} ({data.index_code}) — AI 行情分类"
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=16)),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        margin=dict(l=50, r=50, t=60, b=30),
        height=550,
        template="plotly_dark",
    )

    fig.update_xaxes(gridcolor=COLOR_GRID, showticklabels=False, row=1)
    fig.update_xaxes(gridcolor=COLOR_GRID, row=2)
    fig.update_yaxes(
        gridcolor=COLOR_GRID,
        title_text="价格",
        row=1,
    )
    fig.update_yaxes(
        showticklabels=False,
        range=[-0.5, 1.5],
        row=2,
    )

    return fig


def _add_colored_candlesticks(
    fig: go.Figure,
    df: pd.DataFrame,
    row: int = 1,
):
    """按行情分类分别绘制蜡烛图，不同分类用不同颜色。

    将数据按 market_condition 拆分为 3 组（+ 无分类组），
    每组绘制独立的 Candlestick 轨迹。
    """
    # 定义每种分类的颜色方案
    # 阳线 (close >= open): 实心深色
    # 阴线 (close < open): 浅色/半透明边框
    condition_styles = {
        "trend_up": {
            "increasing": dict(line=dict(color="#059669", width=1), fillcolor="#10B981"),
            "decreasing": dict(line=dict(color="#10B981", width=1), fillcolor="rgba(16,185,129,0.3)"),
            "legend": "上涨",
        },
        "trend_down": {
            "increasing": dict(line=dict(color="#DC2626", width=1), fillcolor="#EF4444"),
            "decreasing": dict(line=dict(color="#EF4444", width=1), fillcolor="rgba(239,68,68,0.3)"),
            "legend": "下跌",
        },
        "range": {
            "increasing": dict(line=dict(color="#D97706", width=1), fillcolor="#F59E0B"),
            "decreasing": dict(line=dict(color="#F59E0B", width=1), fillcolor="rgba(245,158,11,0.3)"),
            "legend": "震荡",
        },
    }

    # 绘制有分类的 candle（按分类分组）
    for condition, style in condition_styles.items():
        cond_df = df[df["market_condition"] == condition]
        if cond_df.empty:
            continue

        fig.add_trace(
            go.Candlestick(
                x=cond_df.index,
                open=cond_df["open"],
                high=cond_df["high"],
                low=cond_df["low"],
                close=cond_df["close"],
                name=style["legend"],
                increasing=style["increasing"],
                decreasing=style["decreasing"],
                hovertext=_build_hover_text(cond_df),
                hoverinfo="text",
                showlegend=True,
            ),
            row=row,
            col=1,
        )

    # 绘制无分类的 candle（灰色）
    no_cond_df = df[df["market_condition"].isna()]
    if not no_cond_df.empty:
        fig.add_trace(
            go.Candlestick(
                x=no_cond_df.index,
                open=no_cond_df["open"],
                high=no_cond_df["high"],
                low=no_cond_df["low"],
                close=no_cond_df["close"],
                name="未分类",
                increasing=dict(line=dict(color="#6B7280", width=1), fillcolor="#9CA3AF"),
                decreasing=dict(line=dict(color="#9CA3AF", width=1), fillcolor="rgba(156,163,175,0.3)"),
                hovertext=_build_hover_text(no_cond_df),
                hoverinfo="text",
                showlegend=True,
            ),
            row=row,
            col=1,
        )


def _build_hover_text(df: pd.DataFrame) -> List[str]:
    """为每根蜡烛构建悬停提示文本。"""
    texts = []
    for _, row in df.iterrows():
        time_str = str(row.get("time", ""))[:10]
        o, h, l, c = row["open"], row["high"], row["low"], row["close"]
        vol = row.get("volume", 0)
        change = (c - o) / o * 100 if o > 0 else 0

        lines = [
            f"<b>{time_str}</b>",
            f"开: {o:.2f}  高: {h:.2f}",
            f"低: {l:.2f}  收: {c:.2f}",
            f"涨跌: {'+' if change >= 0 else ''}{change:.2f}%",
            f"量: {vol/1_0000_0000:.2f}亿",
        ]

        # 添加行情分类信息
        cond = row.get("market_condition")
        prob = row.get("probability")
        if pd.notna(cond) and cond in CONDITION_LABELS:
            label = CONDITION_LABELS[cond]
            color = CONDITION_COLORS.get(cond, "#fff")
            lines.append(
                f'<span style="color:{color}">▶ AI分类: {label}</span>'
            )
        if pd.notna(prob):
            lines.append(f"概率: {prob*100:.0f}%")

        texts.append("<br>".join(lines))
    return texts


def _add_condition_indicator(
    fig: go.Figure,
    df: pd.DataFrame,
    row: int = 2,
):
    """在底部添加行情分类颜色指示条。"""
    # 为每个 bar 创建一个分类指示点（用散点图/条形图）
    conditions_order = ["trend_up", "trend_down", "range"]
    y_values = {"trend_up": 1.0, "trend_down": 0.5, "range": 0.0}

    for condition in conditions_order:
        cond_df = df[df["market_condition"] == condition]
        if cond_df.empty:
            continue

        color = CONDITION_COLORS.get(condition, "#6B7280")
        label = CONDITION_LABELS.get(condition, condition)

        fig.add_trace(
            go.Bar(
                x=cond_df.index,
                y=[y_values[condition]] * len(cond_df),
                name=f"{label}",
                marker=dict(color=color, opacity=0.8),
                hovertext=[
                    f"{str(row.get('time', ''))[:10]}<br>"
                    f"分类: {label}<br>"
                    f"概率: {row.get('probability', 0)*100:.0f}%"
                    if pd.notna(row.get("probability"))
                    else f"{str(row.get('time', ''))[:10]}<br>分类: {label}"
                    for _, row in cond_df.iterrows()
                ],
                hoverinfo="text",
                showlegend=False,
            ),
            row=row,
            col=1,
        )


def build_simple_price_chart(
    data: IndexConditionData,
    visible_bars: int = 120,
) -> go.Figure:
    """构建简化的收盘价走势图（用于概览）。

    Args:
        data: 指数数据。
        visible_bars: 显示的 bar 数量。

    Returns:
        Plotly Figure with close price line colored by condition.
    """
    df = data.df.tail(visible_bars)

    fig = go.Figure()

    # 收盘价线
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["close"],
            name="收盘价",
            line=dict(color="#636EFA", width=1.5),
            hovertemplate="%{text}<br>收盘: %{y:.2f}<extra></extra>",
            text=[str(t)[:10] for t in df["time"]],
        )
    )

    # 为每个分类区域添加背景色带
    for condition, color in CONDITION_BG_COLORS.items():
        cond_df = df[df["market_condition"] == condition]
        if cond_df.empty:
            continue

        label = CONDITION_LABELS.get(condition, condition)
        line_color = CONDITION_COLORS.get(condition, "#6B7280")

        fig.add_trace(
            go.Scatter(
                x=cond_df.index,
                y=cond_df["close"],
                mode="markers",
                name=f"AI: {label}",
                marker=dict(color=line_color, size=6, opacity=0.8),
                hovertemplate=(
                    "%{text}<br>收盘: %{y:.2f}<br>"
                    f"AI分类: {label}<br>"
                    "概率: %{customdata:.0f}%<extra></extra>"
                ),
                text=[str(t)[:10] for t in cond_df["time"]],
                customdata=(
                    cond_df["probability"].fillna(0) * 100
                ),
            )
        )

    fig.update_layout(
        title=dict(text=f"{data.index_name} ({data.index_code}) — 收盘价 + AI分类", x=0.5),
        height=400,
        margin=dict(l=30, r=30, t=50, b=30),
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_xaxes(gridcolor=COLOR_GRID)
    fig.update_yaxes(gridcolor=COLOR_GRID, title_text="价格")

    return fig
