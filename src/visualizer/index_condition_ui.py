"""Streamlit UI components for the index market condition module.

Renders:
- Latest bar condition card (prominent)
- Candlestick chart with condition overlay
- Condition statistics
"""

import logging
from typing import Optional

import streamlit as st
import pandas as pd

from ..data_loader.index_condition_loader import (
    load_index_condition_data,
    IndexConditionData,
    CONDITION_LABELS,
    CONDITION_COLORS,
    CONDITION_BG_COLORS,
)
from .index_condition_chart import (
    build_index_condition_chart,
    build_simple_price_chart,
)

logger = logging.getLogger(__name__)

# 行情分类对应图标
CONDITION_ICONS = {
    "trend_up": "📈",
    "trend_down": "📉",
    "range": "↔️",
}


def render_latest_condition_card(latest_bar: dict):
    """渲染最新 bar 的行情分类卡片（醒目显示）。

    Args:
        latest_bar: 包含 time, open, high, low, close, volume,
                    market_condition, probability 的字典。
    """
    condition = latest_bar.get("market_condition")
    probability = latest_bar.get("probability")
    close_price = latest_bar.get("close", 0)
    open_price = latest_bar.get("open", 0)
    volume = latest_bar.get("volume", 0)
    change_pct = (close_price - open_price) / open_price * 100 if open_price > 0 else 0

    config = None
    if condition and condition in CONDITION_LABELS:
        config = {
            "label": CONDITION_LABELS[condition],
            "color": CONDITION_COLORS[condition],
            "bg": CONDITION_BG_COLORS[condition],
            "icon": CONDITION_ICONS.get(condition, "📊"),
        }

    # 构建自定义 HTML/CSS 卡片
    border_color = config["color"] if config else "#6B7280"
    bg_color = config["bg"] if config else "rgba(107,114,128,0.1)"

    # 使用 columns 布局
    with st.container(border=True):
        # ---- 标题行 ----
        col_title, col_badge = st.columns([3, 1])
        with col_title:
            st.markdown("##### 🤖 最新 AI 行情分类")
            st.caption(f"**{latest_bar['time']}**")
        with col_badge:
            if config:
                st.markdown(
                    f"""
                    <div style="
                        background-color: {config['color']};
                        color: white;
                        padding: 8px 16px;
                        border-radius: 20px;
                        text-align: center;
                        font-size: 1.2em;
                        font-weight: bold;
                    ">
                        {config['icon']} {config['label']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info("无分类数据")

        st.markdown("---")

        # ---- 详情行 ----
        col_price, col_prob = st.columns(2)

        with col_price:
            st.metric("收盘价", f"{close_price:.2f}")
            delta_str = f"{change_pct:+.2f}%"
            st.metric(
                "涨跌幅",
                delta_str,
                delta_color="normal" if change_pct >= 0 else "inverse",
            )
            st.caption(f"成交量: {volume/1_0000_0000:.2f}亿")

        with col_prob:
            if probability is not None:
                prob_pct = probability * 100
                prob_color = config["color"] if config else "#9CA3AF"
                st.markdown(
                    f"""
                    <div style="margin-bottom: 8px;">
                        <span style="color: #9CA3AF; font-size: 0.8em;">分类概率</span>
                        <span style="color: {prob_color}; font-size: 2.5em; font-weight: bold;
                                     font-family: monospace; float: right;">
                            {prob_pct:.0f}%
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # 概率进度条
                st.progress(min(probability, 1.0))

                # 置信度描述
                if probability >= 0.7:
                    st.success("🟢 模型置信度较高")
                elif probability >= 0.5:
                    st.warning("🟡 模型置信度中等")
                else:
                    st.error("🔴 模型置信度较低")
            else:
                st.caption("无分类概率数据")


def render_condition_statistics(data: IndexConditionData):
    """渲染行情分类统计概览。

    Args:
        data: IndexConditionData 对象。
    """
    counts = data.condition_counts
    total = sum(counts.values()) or 1  # 防止除零

    cols = st.columns(3)
    for idx, (condition, label) in enumerate(CONDITION_LABELS.items()):
        count = counts.get(condition, 0)
        pct = count / total * 100
        color = CONDITION_COLORS[condition]
        icon = CONDITION_ICONS.get(condition, "📊")

        with cols[idx]:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <span style="font-size: 1.5em;">{icon}</span><br>
                    <span style="color: {color}; font-weight: bold; font-size: 1.2em;">
                        {count}
                    </span>
                    <span style="color: #9CA3AF; font-size: 0.85em;"> ({pct:.1f}%)</span>
                    <br>
                    <span style="color: {color};">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_index_condition_section():
    """渲染完整的指数行情分类模块。

    包含：
    1. 最新 bar 行情分类卡片
    2. 行情分类统计
    3. 交互式蜡烛图（按分类着色）
    """
    st.markdown("---")
    st.header("🤖 AI 指数行情分类")
    st.caption("基于深度学习模型实时预测指数行情状态（趋势上涨 / 趋势下跌 / 震荡）")

    # 加载数据
    try:
        data = load_index_condition_data()
    except FileNotFoundError as e:
        st.error(f"数据文件未找到: {e}")
        return
    except Exception as e:
        st.error(f"加载数据失败: {e}")
        logger.exception("Failed to load index condition data")
        return

    st.markdown("---")

    # ---- 最新分类卡片 ----
    if data.latest_bar:
        render_latest_condition_card(data.latest_bar)

    st.markdown("---")

    # ---- 统计概览 ----
    st.subheader("📊 分类统计")
    st.caption(f"共 {data.total_bars} 个 Bar，其中 {data.bars_with_condition} 个有 AI 分类")
    render_condition_statistics(data)

    # ---- 可见 bar 数选择 ----
    col_opts, _ = st.columns([1, 3])
    with col_opts:
        visible_bars = st.select_slider(
            "显示 Bar 数量",
            options=[20, 40, 60, 90, 120, 180, 250],
            value=60,
        )

    # ---- 蜡烛图 ----
    st.subheader("📈 蜡烛图 + 行情分类")

    fig = build_index_condition_chart(data, visible_bars=visible_bars)
    st.plotly_chart(fig, width="stretch")

    # ---- 图例说明 ----
    with st.expander("📋 图例说明", expanded=False):
        cols = st.columns(3)
        for idx, (condition, label) in enumerate(CONDITION_LABELS.items()):
            color = CONDITION_COLORS[condition]
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="
                        border-left: 4px solid {color};
                        padding-left: 10px;
                        margin: 5px 0;
                    ">
                        <span style="color: {color}; font-weight: bold;">■ {label}</span><br>
                        <span style="font-size: 0.8em; color: #9CA3AF;">
                            蜡烛实体颜色 = {label}分类<br>
                            阳线 (收≥开): 实心<br>
                            阴线 (收<开): 半透明
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ---- 收盘价概览图 ----
    st.subheader("📉 收盘价走势 + AI 分类标注")
    fig2 = build_simple_price_chart(data, visible_bars=min(visible_bars * 2, len(data.df)))
    st.plotly_chart(fig2, width="stretch")

    # ---- 图表底部提示 ----
    st.caption(
        "💡 提示: 蜡烛图实体颜色对应 AI 行情分类（绿=上涨、红=下跌、橙=震荡）。"
        "悬停查看详细 OHLC 数据和分类概率。可使用鼠标滚轮缩放、拖拽平移。"
    )
