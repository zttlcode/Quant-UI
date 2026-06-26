"""Streamlit UI components for the index market condition module.

Renders:
- Latest bar condition card (prominent)
- avmood trend indicator card (risk warning)
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
from ..indicators.risk import compute_risk_indicators, classify_risk_level
from .index_condition_chart import (
    build_index_condition_chart,
    build_avmood_chart,
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


def render_avmood_card(data: IndexConditionData):
    """Render the fuzzy_ma avmood trend indicator card.

    Uses the EXACT same FuzzyMAExtraDataLoader as the avmood chart and
    individual stock charts — values are always consistent.

    Args:
        data: IndexConditionData with merged OHLCV + condition data.
    """
    from ..data_loader.extra_data import FuzzyMAExtraDataLoader
    from ..config.settings import get_config
    from ..indicators.risk import compute_risk_indicators

    # Prepare price DataFrame (same as chart)
    price_df = data.df.copy()
    if "time" in price_df.columns:
        price_df["time"] = pd.to_datetime(price_df["time"])
        price_df = price_df.set_index("time").sort_index()

    if price_df.empty or "close" not in price_df.columns:
        st.warning("无法计算 avmood：缺少指数价格数据")
        return

    # ---- avmood from FuzzyMAExtraDataLoader (same as chart & stock detail) ----
    cfg = get_config()
    loader = FuzzyMAExtraDataLoader(cfg)
    try:
        avmood_df = loader._compute_avmood(price_df)
    except Exception:
        st.warning("无法计算 avmood：模糊推理失败")
        return

    if avmood_df.empty or "avmood" not in avmood_df.columns:
        st.warning("无法计算 avmood：数据不足")
        return

    avmood_val = float(avmood_df["avmood"].iloc[-1])
    avmood_slope = float(avmood_df["avmood"].diff(3).iloc[-1]) if len(avmood_df) >= 4 else 0.0
    if pd.isna(avmood_val):
        st.warning("无法计算 avmood：数据不足")
        return
    if pd.isna(avmood_slope):
        avmood_slope = 0.0

    # Supplementary detail from simplified indicators (MA, MACD, ATR, etc.)
    ind_df = compute_risk_indicators(price_df)
    latest_ind = ind_df.iloc[-1] if not ind_df.empty else None

    # Determine avmood status (real fuzzy scale: [-0.10, +0.10])
    is_bullish = avmood_val > 0
    abs_val = abs(avmood_val)

    if abs_val > 0.05:
        strength = "强势"
        strength_color = "#10B981" if is_bullish else "#EF4444"
    elif abs_val > 0.02:
        strength = "中等"
        strength_color = "#F59E0B"
    else:
        strength = "弱势"
        strength_color = "#9CA3AF"

    direction_text = "多头区间 ▲" if is_bullish else "空头区间 ▼"
    direction_color = "#10B981" if is_bullish else "#EF4444"
    direction_icon = "🟢" if is_bullish else "🔴"

    # Trend direction (based on slope) — real fuzzy scale diff
    if avmood_slope > 0.005:
        trend_text = "↑ 增强中"
        trend_color = "#10B981"
    elif avmood_slope < -0.005:
        trend_text = "↓ 减弱中"
        trend_color = "#EF4444"
    else:
        trend_text = "→ 走平"
        trend_color = "#9CA3AF"

    # Risk assessment — uses REAL avmood from FuzzyMAExtraDataLoader
    risk_indicators = {
        "avmood": avmood_val,
        "avmood_slope": avmood_slope,
        "ma_bullish": int(latest_ind.get("ma_bullish", 0)) if latest_ind is not None else 0,
        "macd_dif": float(latest_ind.get("macd_dif", 0)) if latest_ind is not None and not pd.isna(latest_ind.get("macd_dif")) else 0,
        "macd_hist": float(latest_ind.get("macd_hist", 0)) if latest_ind is not None and not pd.isna(latest_ind.get("macd_hist")) else 0,
        "atr_pct": float(latest_ind.get("atr_pct", 0)) if latest_ind is not None and not pd.isna(latest_ind.get("atr_pct")) else 0,
        "ret_5d": float(latest_ind.get("ret_5d", 0)) if latest_ind is not None and not pd.isna(latest_ind.get("ret_5d")) else 0,
    }
    # Note: classify_risk_level thresholds were set for the old percentage-scale proxy.
    # With real fuzzy avmood in [-0.10, +0.10] range, the thresholds already account for this.
    risk_level, risk_color, risk_warnings = classify_risk_level(risk_indicators)

    # ---- Render card ----
    with st.container(border=True):
        # Title row
        col_title, col_badge = st.columns([2, 1])
        with col_title:
            st.markdown("##### 🧠 Fuzzy MA 趋势指标 (avmood)")
            st.caption("基于模糊推理的自适应趋势判断 → avmood > 0 多头，< 0 空头")
        with col_badge:
            st.markdown(
                f"""
                <div style="
                    background-color: {direction_color};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    text-align: center;
                    font-size: 1.1em;
                    font-weight: bold;
                ">
                    {direction_icon} {direction_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Metrics row — 4 columns: avmood value, strength, trend, risk
        col_val, col_strength, col_trend, col_risk = st.columns(4)
        with col_val:
            delta_str = f"{avmood_slope:+.4f}"
            st.metric(
                "avmood 数值",
                f"{avmood_val:.6f}",
                delta=delta_str,
                delta_color="normal" if avmood_slope >= 0 else "inverse",
            )
            st.caption("FuzzyMA 模糊推理 (与个股一致)")
        with col_strength:
            st.markdown(
                f"""
                <div style="margin-top: 8px;">
                    <span style="color: #9CA3AF; font-size: 0.8em;">趋势强度</span><br>
                    <span style="color: {strength_color}; font-size: 1.3em; font-weight: bold;">
                        {strength}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_trend:
            st.markdown(
                f"""
                <div style="margin-top: 8px;">
                    <span style="color: #9CA3AF; font-size: 0.8em;">趋势方向</span><br>
                    <span style="color: {trend_color}; font-size: 1.3em; font-weight: bold;">
                        {trend_text}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_risk:
            risk_icon = {"低风险": "🟢", "中风险": "🟡", "高风险": "🔴"}.get(risk_level, "⚪")
            st.markdown(
                f"""
                <div style="margin-top: 8px;">
                    <span style="color: #9CA3AF; font-size: 0.8em;">综合风险</span><br>
                    <span style="color: {risk_color}; font-size: 1.3em; font-weight: bold;">
                        {risk_icon} {risk_level}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # avmood visual bar
        # Map avmood to a 0-1 range for progress bar
        # Range: [-0.10, +0.10] for display
        bar_val = min(abs_val / 0.10, 1.0)
        bar_color = direction_color
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin: 8px 0;">
                <span style="color: #EF4444; font-size: 0.8em; width: 45px; text-align: right;">
                    -0.10
                </span>
                <div style="
                    flex: 1; height: 20px; background: linear-gradient(
                        to right,
                        rgba(239,68,68,0.3) 0%,
                        rgba(239,68,68,0.1) 30%,
                        rgba(156,163,175,0.15) 50%,
                        rgba(16,185,129,0.1) 70%,
                        rgba(16,185,129,0.3) 100%
                    ); border-radius: 10px; position: relative; overflow: visible;
                ">
                    <div style="
                        position: absolute;
                        left: {bar_val * 100 if is_bullish else (1 - bar_val) * 100}%;
                        top: -3px;
                        width: 6px; height: 26px;
                        background: {bar_color};
                        border-radius: 3px;
                        transform: translateX(-50%);
                    "></div>
                </div>
                <span style="color: #10B981; font-size: 0.8em; width: 45px;">
                    +0.10
                </span>
            </div>
            <div style="text-align: center; margin-top: -8px;">
                <span style="color: #9CA3AF; font-size: 0.7em;">
                    空头 ← → 多头
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Supplementary detail row
        col_ma, col_macd, col_atr, col_ret = st.columns(4)
        with col_ma:
            if latest_ind is not None:
                ma_bull = latest_ind.get("ma_bullish")
                ma_status = "多头排列" if ma_bull == 1 else "非多头"
                pct_ma20 = latest_ind.get("pct_ma_20")
                pct_str = f"距MA20: {pct_ma20:+.1f}%" if not pd.isna(pct_ma20) else "N/A"
                st.caption(f"均线: {ma_status} ({pct_str})")
            else:
                st.caption("均线: N/A")
        with col_macd:
            if latest_ind is not None:
                macd_hist = latest_ind.get("macd_hist")
                macd_str = f"MACD柱: {macd_hist:+.4f}" if not pd.isna(macd_hist) else "N/A"
                st.caption(macd_str)
            else:
                st.caption("MACD: N/A")
        with col_atr:
            if latest_ind is not None:
                atr_pct = latest_ind.get("atr_pct")
                atr_str = f"ATR%: {atr_pct:.2f}%" if not pd.isna(atr_pct) else "N/A"
                st.caption(atr_str)
            else:
                st.caption("ATR: N/A")
        with col_ret:
            if latest_ind is not None:
                ret_5d = latest_ind.get("ret_5d")
                ret_str = f"前5日: {ret_5d:+.2f}%" if not pd.isna(ret_5d) else "N/A"
                st.caption(ret_str)
            else:
                st.caption("前5日: N/A")

        # Risk warnings
        if risk_warnings:
            st.markdown("---")
            for w in risk_warnings:
                if w.startswith("⚠️"):
                    st.error(w)
                else:
                    st.warning(w)
        else:
            st.success("✅ 当前无明显风险信号")


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
            "默认显示 Bar 数量（可拖拽/滚轮查看全部 {0} 根K线）".format(data.total_bars),
            options=[20, 40, 60, 90, 120, 180, 250],
            value=60,
        )

    # ---- 蜡烛图 + 成交量 ----
    st.subheader("📈 蜡烛图 + AI 行情分类")

    fig_candle = build_index_condition_chart(data, visible_bars=visible_bars)
    st.plotly_chart(fig_candle, width="stretch")

    st.caption(
        "💡 蜡烛颜色 = AI 行情分类（绿涨/红跌/橙震）。"
        f"当前共 {data.total_bars} 根K线，默认显示最近 {visible_bars} 根，可拖拽/滚轮查看更多。"
    )

    st.markdown("---")

    # ---- avmood 趋势图（与个股图表算法完全一致） ----
    st.subheader("🧠 Fuzzy MA 趋势图 (avmood)")

    fig_avmood = build_avmood_chart(data, visible_bars=visible_bars)
    st.plotly_chart(fig_avmood, width="stretch")

    st.caption(
        "💡 紫色曲线 = avmood (>0 多头区间, <0 空头区间)。"
        "算法与个股K线图中的 avmood 完全一致（FuzzyMAExtraDataLoader）。"
        "绿色 ▲ = 上穿零轴转多，红色 ▼ = 下穿零轴转空。"
        "灰色虚线 = mood（原始模糊推理值）。"
    )

    st.markdown("---")

    # ---- avmood 趋势指标卡片（放在图表下方，数值与图表一致） ----
    render_avmood_card(data)

    st.markdown("---")

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
