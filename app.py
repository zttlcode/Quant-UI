"""Quant-UI: Stock Strategy Visualization Platform

Main Streamlit application entry point.

Usage:
    streamlit run app.py

The app provides:
- Home page: Strategy overview list
- Strategy page: Browse stocks for a strategy
- Stock detail page: Interactive charts with signals, MAs, MACD, and position info
"""

import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logging
from src.config.settings import get_config
from src.strategy.registry import init_registry, get_registry
from src.data_loader.price_loader import PriceLoader
from src.trade_engine.pairer import TradePairer
from src.trade_engine.pnl import PnLCalculator
from src.visualizer.chart_builder import ChartBuilder
from src.visualizer.components import (
    render_label_legend,
    render_position_status,
    render_trade_table,
    render_strategy_card,
    render_data_warnings,
    render_signal_filter_ui,
)

import streamlit as st
import pandas as pd

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="Quant-UI | 策略可视化平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Initialize Application
# ============================================================
@st.cache_resource
def init_app():
    """Initialize application: config, logging, strategy registry."""
    cfg = get_config()
    logger = setup_logging(cfg.log_level, cfg.log_file, "quant_ui")
    logger.info("Quant-UI starting...")
    registry = init_registry(cfg)
    logger.info("Application initialized with %d strategies", len(registry))
    return cfg, registry


config, registry = init_app()

# ============================================================
# Sidebar Navigation
# ============================================================
st.sidebar.title("📊 Quant-UI")
st.sidebar.caption("策略可视化平台")

# Navigation
page = st.sidebar.radio(
    "导航",
    ["🏠 首页", "📈 策略详情", "📋 股票详情"],
    label_visibility="collapsed",
)

# Strategy selector in sidebar
strategy_names = registry.list_names()
strategy_displays = {
    name: registry.get(name).display_name for name in strategy_names
}

if strategy_names:
    selected_strategy = st.sidebar.selectbox(
        "选择策略",
        options=strategy_names,
        format_func=lambda x: strategy_displays.get(x, x),
        key="sidebar_strategy",
    )
else:
    st.sidebar.warning("没有已注册的策略")
    selected_strategy = None

# Signal filter options
st.sidebar.markdown("---")
show_only_effective = st.sidebar.checkbox(
    "仅显示有效信号",
    value=config.show_only_effective_signal,
    help="只显示 label=1 (有效买入) 和 label=3 (有效卖出) 的信号",
)
show_unclosed = st.sidebar.checkbox(
    "显示未平仓持仓",
    value=config.show_unclosed_position,
)

# Market & Level filter
st.sidebar.markdown("---")
market_filter = st.sidebar.selectbox("市场", ["A"], disabled=True)
level_filter = st.sidebar.selectbox("级别", ["d", "w", "15", "30", "60"], index=0)

st.sidebar.markdown("---")
st.sidebar.caption(f"Quant-UI v1.0.0")
if st.sidebar.button("🔄 刷新数据"):
    st.cache_data.clear()
    st.rerun()


# ============================================================
# Page: Home
# ============================================================
def render_home():
    """Render the home page with strategy overview."""
    st.title("🏠 策略概览")
    st.markdown("股票策略可视化平台 — 多策略、多股票、交互式图表")

    st.markdown("---")

    if not strategy_names:
        st.warning("没有已注册的策略。请检查 config.yaml 中的 default_strategy_list。")
        return

    # Strategy cards
    for name in strategy_names:
        adapter = registry.get(name)
        if adapter is None:
            continue

        with st.container(border=True):
            st.subheader(f"📈 {adapter.display_name}")
            st.caption(adapter.description)

            try:
                # Load signals to compute summary
                signals = adapter.load_signals()
                stocks = sorted(set(s.stock_code for s in signals))
                buy_sigs = [s for s in signals if s.is_buy]
                sell_sigs = [s for s in signals if s.is_sell]

                # Basic stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("覆盖股票", len(stocks))
                with col2:
                    st.metric("交易信号总数", len(signals))
                with col3:
                    st.metric("买入信号", len(buy_sigs))
                with col4:
                    st.metric("卖出信号", len(sell_sigs))

                # Sample stocks
                if stocks:
                    sample_stocks = stocks[:5]
                    st.caption(f"示例股票: {', '.join(sample_stocks)}"
                               + (f" ... 等{len(stocks)}只" if len(stocks) > 5 else ""))

                # Click to explore
                if st.button(f"查看 {adapter.display_name} 详情 →", key=f"goto_{name}"):
                    st.session_state["page"] = "📈 策略详情"
                    st.session_state["selected_strategy"] = name
                    st.rerun()

            except Exception as e:
                st.error(f"加载策略 '{name}' 失败: {e}")

            st.markdown("---")


# ============================================================
# Page: Strategy Detail
# ============================================================
def render_strategy_detail():
    """Render the strategy detail page with stock list."""
    st.title("📈 策略详情")

    if selected_strategy is None:
        st.warning("请从侧边栏选择一个策略。")
        return

    adapter = registry.get(selected_strategy)
    if adapter is None:
        st.error(f"策略 '{selected_strategy}' 未注册。")
        return

    st.subheader(adapter.display_name)
    st.caption(adapter.description)

    st.markdown("---")

    # Load data
    with st.spinner(f"加载 {adapter.display_name} 的信号数据..."):
        try:
            signals = adapter.load_signals()
        except Exception as e:
            st.error(f"加载信号数据失败: {e}")
            return

    if not signals:
        st.warning("该策略没有交易信号数据。")
        return

    # Build stock summary
    price_loader = PriceLoader(config)

    stocks = sorted(set(s.stock_code for s in signals))

    # Search and filter
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input(
            "🔍 搜索股票代码",
            placeholder="输入代码如 000027",
            key="strategy_search",
        )
    with col2:
        status_filter = st.selectbox(
            "持仓状态",
            ["全部", "持仓中", "已清仓"],
            key="strategy_status",
        )
    with col3:
        st.caption(f"共 {len(stocks)} 只股票")

    # Filter stocks by search
    if search_term:
        stocks = [s for s in stocks if search_term.strip() in s]
        st.caption(f"搜索 '{search_term}': 匹配 {len(stocks)} 只股票")

    st.markdown("---")

    # Display stock list
    if not stocks:
        st.info("没有匹配的股票。")
        return

    # Build summaries for each stock
    pairer = TradePairer(config)
    pnl_calc = PnLCalculator(config.commission, config.slippage)

    stock_data = []
    for stock_code in stocks:
        stock_signals = [s for s in signals if s.stock_code == stock_code]
        stock_signals.sort(key=lambda s: s.time)

        # Try to load price data
        try:
            price_df = adapter.load_price_data(stock_code, market_filter, level_filter)
        except Exception:
            price_df = pd.DataFrame()

        # Pair trades
        closed_trades, open_pos = pairer.pair_signals(stock_signals, price_df)

        is_holding = open_pos is not None
        pnl = open_pos.pnl_pct if is_holding else (
            closed_trades[-1].pnl_pct if closed_trades else None
        )
        entry_price = open_pos.entry_price if is_holding else (
            closed_trades[-1].entry_price if closed_trades else None
        )
        current_price = open_pos.exit_price if is_holding else (
            closed_trades[-1].exit_price if closed_trades else None
        )

        stock_data.append({
            "code": stock_code,
            "is_holding": is_holding,
            "pnl_pct": pnl,
            "entry_price": entry_price,
            "current_price": current_price,
            "signal_count": len(stock_signals),
            "trade_count": len(closed_trades) + (1 if is_holding else 0),
        })

    # Apply status filter
    if status_filter == "持仓中":
        stock_data = [s for s in stock_data if s["is_holding"]]
    elif status_filter == "已清仓":
        stock_data = [s for s in stock_data if not s["is_holding"]]

    # Render stock table
    rows = []
    for sd in stock_data:
        code = sd["code"]
        holding_icon = "📈" if sd["is_holding"] else "✅"
        pnl_str = f"{sd['pnl_pct'] * 100:.2f}%" if sd["pnl_pct"] is not None else "—"
        entry_str = f"{sd['entry_price']:.4f}" if sd["entry_price"] else "—"
        current_str = f"{sd['current_price']:.4f}" if sd["current_price"] else "—"

        pnl_display = pnl_str
        if sd["pnl_pct"] is not None:
            if sd["pnl_pct"] > 0:
                pnl_display = f"🟢 {pnl_str}"
            elif sd["pnl_pct"] < 0:
                pnl_display = f"🔴 {pnl_str}"

        rows.append({
            "状态": holding_icon,
            "股票代码": code,
            "信号数": sd["signal_count"],
            "交易数": sd["trade_count"],
            "入场价": entry_str,
            "当前/出场价": current_str,
            "收益率": pnl_display,
        })

    # Display as dataframe with clickable stock codes
    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
        column_config={
            "股票代码": st.column_config.TextColumn("股票代码", width="medium"),
        },
    )

    # Stock detail section
    st.markdown("---")
    st.subheader("📋 查看单只股票详情")

    selected_stock = st.selectbox(
        "选择股票代码",
        options=[s["code"] for s in stock_data],
        key="strategy_stock_selector",
    )

    if selected_stock and st.button("查看详情 →", key="goto_stock_detail"):
        st.session_state["page"] = "📋 股票详情"
        st.session_state["detail_stock"] = selected_stock
        st.rerun()


# ============================================================
# Page: Stock Detail
# ============================================================
def render_stock_detail():
    """Render the detailed stock chart page."""
    st.title("📋 股票详情")

    if selected_strategy is None:
        st.warning("请从侧边栏选择一个策略。")
        return

    adapter = registry.get(selected_strategy)
    if adapter is None:
        st.error(f"策略 '{selected_strategy}' 未注册。")
        return

    # Stock selection
    stocks = adapter.get_stock_list()
    if not stocks:
        st.warning(f"策略 '{selected_strategy}' 没有信号数据。")
        return

    # Use session state for stock selection
    default_stock = st.session_state.get("detail_stock", stocks[0] if stocks else "")

    col1, col2 = st.columns([1, 3])
    with col1:
        selected_stock = st.selectbox(
            "选择股票代码",
            options=stocks,
            index=stocks.index(default_stock) if default_stock in stocks else 0,
            key="stock_detail_selector",
        )

    if not selected_stock:
        st.info("请选择一只股票。")
        return

    # Load data
    with st.spinner(f"加载 {selected_stock} 数据..."):
        # Load signals
        signals = adapter.load_stock_signals(selected_stock)
        if not signals:
            st.warning(f"股票 {selected_stock} 没有信号数据。")
            return

        # Load price data
        try:
            price_df = adapter.load_price_data(selected_stock, market_filter, level_filter)
        except FileNotFoundError as e:
            st.error(f"找不到行情数据: {e}")
            return
        except Exception as e:
            st.error(f"加载行情数据失败: {e}")
            return

        if price_df.empty:
            st.error(f"股票 {selected_stock} 没有行情数据。")
            return

        # Validate signal dates
        price_loader = PriceLoader(config)
        signal_dates = {s.date_str for s in signals}
        warnings = price_loader.validate_signal_dates(selected_stock, signal_dates, market_filter, level_filter)
        if warnings:
            render_data_warnings(warnings)

        # Pair trades
        pairer = TradePairer(config)
        closed_trades, open_position = pairer.pair_signals(signals, price_df)

        # Compute PnL stats
        pnl_calc = PnLCalculator(config.commission, config.slippage)
        closed_stats = pnl_calc.get_closed_trade_stats(closed_trades, selected_stock)

        # Load extra data for fuzzy_ma
        extra_data = None
        extra_label = ""
        if adapter.has_extra_data:
            with st.spinner("计算 Fuzzy MA 辅助指标..."):
                extra_data = adapter.load_extra_data(selected_stock, price_df, market_filter, level_filter)
                if extra_data is not None:
                    extra_label = adapter.get_extra_loader().get_description()

    # ============================================================
    # Header: Stock info and position status
    # ============================================================
    st.markdown("---")

    # Top metrics row
    latest_price = float(price_df["close"].iloc[-1]) if not price_df.empty else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("股票代码", selected_stock)
    with col2:
        st.metric("策略", adapter.display_name)
    with col3:
        st.metric("最新价格", f"{latest_price:.4f}")
    with col4:
        if open_position:
            pnl_pct = open_position.pnl_pct
            st.metric(
                "浮动收益率",
                f"{pnl_pct * 100:.2f}%" if pnl_pct is not None else "N/A",
                delta_color="normal",
            )
        else:
            last_pnl = closed_stats.get("last_trade_pnl")
            st.metric(
                "最近交易收益",
                f"{last_pnl:.2f}%" if last_pnl is not None else "N/A",
            )
    with col5:
        if open_position:
            stop_str = f"{open_position.stop_loss:.4f}" if open_position.stop_loss else "⚠️ N/A"
            st.metric("止损位", stop_str)
        else:
            st.metric("累计收益", f"{closed_stats.get('total_pnl_pct', 0):.2f}%")

    # Position status
    st.markdown("---")

    if open_position:
        position_state = pnl_calc.get_position_state(
            [open_position], selected_stock, selected_strategy, latest_price
        )
        render_position_status(position_state)
    else:
        st.markdown("### ✅ 已清仓")
        if closed_stats.get("total_trades", 0) > 0:
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("历史交易数", closed_stats["total_trades"])
            with col_b:
                st.metric("盈利次数", closed_stats["win_count"])
            with col_c:
                st.metric("胜率", f"{closed_stats['win_rate'] * 100:.1f}%")
            with col_d:
                st.metric("累计收益", f"{closed_stats['total_pnl_pct']:.2f}%")

    # Label legend
    render_label_legend()

    st.markdown("---")

    # ============================================================
    # Chart
    # ============================================================
    st.subheader("📊 交易图表")

    # Filter controls
    filter_opts = render_signal_filter_ui("detail")

    # Build chart
    chart_builder = ChartBuilder(ma_periods=config.ma_periods)

    title = f"{selected_stock} — {adapter.display_name} ({market_filter}_{level_filter})"

    fig = chart_builder.build_chart(
        price_df=price_df,
        signals=signals,
        trades=closed_trades,
        open_position=open_position if filter_opts["show_unclosed"] else None,
        extra_data=extra_data,
        extra_label=extra_label,
        show_only_effective=filter_opts["show_only_effective"],
        title=title,
    )

    st.plotly_chart(fig, width="stretch")

    # ============================================================
    # Trade History Table
    # ============================================================
    st.markdown("---")
    st.subheader("📝 交易明细")

    render_trade_table(
        closed_trades,
        stock_code=selected_stock,
        open_position=open_position if filter_opts["show_unclosed"] else None,
    )

    # ============================================================
    # Export
    # ============================================================
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 导出 HTML 报表"):
            export_path = Path(config.output_dir) / f"{selected_strategy}_{selected_stock}.html"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(export_path))
            st.success(f"报表已导出到: {export_path}")
    with col2:
        st.caption("💡 提示: 使用鼠标滚轮缩放图表，拖拽平移。")


# ====================================================Empty signal file========
# Route to Page
# ============================================================
if "page" not in st.session_state:
    st.session_state["page"] = "🏠 首页"

# Check for session redirect
page = st.session_state.get("page", page)

if page == "🏠 首页":
    render_home()
elif page == "📈 策略详情":
    render_strategy_detail()
elif page == "📋 股票详情":
    render_stock_detail()
else:
    render_home()
