"""Index market condition chart builder.

Builds an interactive Plotly candlestick chart with market condition
classification overlay, plus Streamlit UI components for the latest bar display.
"""

import logging
from typing import Optional, Dict, List, Tuple

import numpy as np
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
    """Build candlestick chart with AI condition coloring + volume bars.

    Feeds ALL bars for zoom/pan, defaults to last ``visible_bars`` in view.
    Uses sequential integer x-axis so bars are continuous (adjacent) with no
    gaps for non-trading days — standard financial candlestick convention.

    Panels:
    - Panel 1: Candlestick (colored by AI market condition)
    - Panel 2: Volume bars (red up, green down)
    """
    df = data.df.copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark")
        return fig

    # Ensure DatetimeIndex for proper sorting; keep index for hover text
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
        df = df.set_index("time").sort_index()

    total_bars = len(df)

    # ---- Sequential positions for continuous bar display ----
    # No gaps for weekends/holidays — bars are adjacent like a real trading terminal
    df["pos"] = range(total_bars)
    date_labels = [d.strftime("%Y-%m-%d") for d in df.index]

    # Subplots: candle + volume
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.78, 0.22],
    )

    # ---- Panel 1: Candlestick (colored by AI condition) ----
    _add_colored_candlesticks(fig, df, row=1)

    # ---- Panel 2: Volume bars ----
    if "volume" in df.columns:
        close = df["close"] if "close" in df.columns else None
        open_p = df["open"] if "open" in df.columns else None
        if close is not None and open_p is not None:
            up_mask = close >= open_p
            colors = ["#EF4444" if u else "#00CC96" for u in up_mask]
        else:
            colors = "rgba(128,128,128,0.5)"

        # Build volume hover text with real dates
        vol_hover = [
            f"量: {v/1_0000_0000:.2f}亿<br>{d}"
            for v, d in zip(df["volume"].values, date_labels)
        ]

        fig.add_trace(
            go.Bar(
                x=df["pos"],
                y=df["volume"].values,
                name="成交量",
                marker=dict(color=colors, opacity=0.6),
                hovertext=vol_hover,
                hoverinfo="text",
                showlegend=True,
            ),
            row=2, col=1,
        )

    # ---- X-axis tick configuration: show dates at regular intervals ----
    tick_count = min(12, total_bars)
    step = max(1, total_bars // tick_count)
    tick_positions = list(range(0, total_bars, step))
    tick_texts = [date_labels[i] for i in tick_positions]

    # ---- Initial x-range ----
    if total_bars > visible_bars:
        vis_start = total_bars - visible_bars
        vis_end = total_bars - 1
        x_start = vis_start - 0.5
        x_end = vis_end + 0.5
    else:
        vis_start = 0
        vis_end = total_bars - 1
        x_start = -0.5
        x_end = vis_end + 0.5

    # ---- Adaptive y-range (based on visible bars only) ----
    visible_df = df.iloc[vis_start : vis_end + 1]
    y_low = visible_df["low"].min()
    y_high = visible_df["high"].max()
    y_padding = (y_high - y_low) * 0.08
    y_range = [y_low - y_padding, y_high + y_padding]

    # ---- Layout ----
    title_str = f"{data.index_name} ({data.index_code}) — AI 行情分类"
    fig.update_layout(
        title=dict(text=title_str, x=0.5, xanchor="center", font=dict(size=16)),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10),
        ),
        margin=dict(l=50, r=50, t=60, b=30),
        height=550,
        template="plotly_dark",
    )

    fig.layout.xaxis.range = [x_start, x_end]
    fig.layout.xaxis2.range = [x_start, x_end]

    fig.update_xaxes(
        tickmode="array",
        tickvals=tick_positions,
        ticktext=tick_texts,
        gridcolor=COLOR_GRID,
        showticklabels=False,
        row=1,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=tick_positions,
        ticktext=tick_texts,
        gridcolor=COLOR_GRID,
        row=2,
    )
    fig.update_yaxes(gridcolor=COLOR_GRID, title_text="价格", range=y_range, row=1)
    fig.update_yaxes(gridcolor=COLOR_GRID, title_text="成交量", row=2)

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
    # 使用 "pos" 列作为 x，让 bar 连续排列，无交易日间隙
    for condition, style in condition_styles.items():
        cond_df = df[df["market_condition"] == condition]
        if cond_df.empty:
            continue

        fig.add_trace(
            go.Candlestick(
                x=cond_df["pos"],
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
                x=no_cond_df["pos"],
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
    """为每根蜡烛构建悬停提示文本（兼容 DatetimeIndex 和 time 列）。"""
    texts = []
    for idx_val, row in df.iterrows():
        # Get time from index if DatetimeIndex, else from "time" column
        if isinstance(df.index, pd.DatetimeIndex):
            time_str = idx_val.strftime("%Y-%m-%d")
        else:
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


def build_avmood_chart(
    data: IndexConditionData,
    visible_bars: int = 60,
) -> go.Figure:
    """Build standalone avmood chart using the SAME FuzzyMAExtraDataLoader
    algorithm as individual stock charts.

    Feeds ALL bars, defaults to last ``visible_bars`` in view.
    Users can zoom/pan to see more history.

    Displays:
    - avmood curve (purple) — the 5-period rolling mean of mood
    - Zero line (yellow dotted)
    - Up-cross / Down-cross markers (green / red triangles)
    - Red/green background fill
    """
    from ..data_loader.extra_data import FuzzyMAExtraDataLoader
    from ..config.settings import get_config

    df = data.df.copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark")
        return fig

    # Prepare DatetimeIndex price DataFrame (same as stock chart)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
        price_df = df.set_index("time").sort_index()
    else:
        price_df = df

    # Use the EXACT same algorithm as individual stock avmood charts
    cfg = get_config()
    loader = FuzzyMAExtraDataLoader(cfg)
    try:
        avmood_df = loader._compute_avmood(price_df)
    except Exception:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark")
        return fig

    if avmood_df.empty or "avmood" not in avmood_df.columns:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark")
        return fig

    total_bars = len(avmood_df)
    idx = avmood_df.index
    avmood_vals = avmood_df["avmood"].values

    fig = go.Figure()

    # ---- Background fill ----
    fig.add_trace(go.Scatter(
        x=idx, y=np.maximum(avmood_vals, 0),
        mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=idx, y=np.minimum(avmood_vals, 0),
        mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(239,68,68,0.15)",
        showlegend=False, hoverinfo="skip",
    ))

    # ---- avmood curve ----
    fig.add_trace(go.Scatter(
        x=idx, y=avmood_vals,
        name="avmood",
        line=dict(color="#AB63FA", width=1.8),
        hovertemplate="avmood: %{y:.6f}<br>%{x|%Y-%m-%d}<extra></extra>",
    ))

    # ---- Zero-crossing markers ----
    if "avmood_cross" in avmood_df.columns:
        cross_data = avmood_df[avmood_df["avmood_cross"] != 0]
        if not cross_data.empty:
            cross_up = cross_data[cross_data["avmood_cross"] == 1]
            cross_down = cross_data[cross_data["avmood_cross"] == -1]
            if not cross_up.empty:
                fig.add_trace(go.Scatter(
                    x=cross_up.index, y=[0]*len(cross_up),
                    mode="markers", name="avmood 上穿0",
                    marker=dict(symbol="triangle-up", size=12,
                                color="#10B981", line=dict(width=1.5, color="#059669")),
                    hovertemplate="avmood 上穿0 → 多头<br>%{x|%Y-%m-%d}<extra></extra>",
                ))
            if not cross_down.empty:
                fig.add_trace(go.Scatter(
                    x=cross_down.index, y=[0]*len(cross_down),
                    mode="markers", name="avmood 下穿0",
                    marker=dict(symbol="triangle-down", size=12,
                                color="#EF4444", line=dict(width=1.5, color="#DC2626")),
                    hovertemplate="avmood 下穿0 → 空头<br>%{x|%Y-%m-%d}<extra></extra>",
                ))

    # ---- Zero line ----
    fig.add_hline(y=0, line=dict(color="#F59E0B", width=1.0, dash="dot"),
                  annotation_text="零轴", annotation_position="right")

    # ---- Initial x-range (last visible_bars) ----
    if total_bars > visible_bars:
        x_start = idx[-visible_bars]
        x_end = idx[-1]
        vis_slice = slice(-visible_bars, None)
    else:
        x_start = idx[0]
        x_end = idx[-1]
        vis_slice = slice(None)

    # ---- Adaptive y-range (based on visible avmood only) ----
    vis_avmood = avmood_vals[vis_slice]
    vis_finite = vis_avmood[np.isfinite(vis_avmood)]
    if len(vis_finite) > 0:
        y_data_min = float(np.nanmin(vis_finite))
        y_data_max = float(np.nanmax(vis_finite))
        # Ensure zero is always visible
        y_min = min(y_data_min, 0)
        y_max = max(y_data_max, 0)
        # Add 15% padding to make fluctuations visible
        y_range_margin = max((y_max - y_min) * 0.15, 0.002)
        y_range_avmood = [y_min - y_range_margin, y_max + y_range_margin]
    else:
        y_range_avmood = [-0.01, 0.01]

    # ---- Layout ----
    fig.update_layout(
        title=dict(
            text=f"Fuzzy MA avmood — {data.index_name} ({data.index_code})",
            x=0.5, xanchor="center", font=dict(size=15),
        ),
        xaxis=dict(range=[x_start, x_end]),
        height=350,
        margin=dict(l=40, r=40, t=50, b=30),
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(size=10)),
    )
    fig.update_xaxes(gridcolor="rgba(128,128,128,0.15)")
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", title_text="avmood",
                     zeroline=True, zerolinecolor="#F59E0B", zerolinewidth=1,
                     range=y_range_avmood)

    return fig


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
