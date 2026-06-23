"""Index market condition data loader.

Reads live bar CSV (OHLCV) and market condition classification CSV,
merges them by date, and returns combined data for visualization.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)

# 行情分类中文标签和颜色
CONDITION_LABELS: Dict[str, str] = {
    "trend_up": "上涨",
    "trend_down": "下跌",
    "range": "震荡",
}

CONDITION_COLORS: Dict[str, str] = {
    "trend_up": "#10B981",     # 绿色
    "trend_down": "#EF4444",   # 红色
    "range": "#F59E0B",        # 琥珀色
}

CONDITION_BG_COLORS: Dict[str, str] = {
    "trend_up": "rgba(16, 185, 129, 0.15)",
    "trend_down": "rgba(239, 68, 68, 0.15)",
    "range": "rgba(245, 158, 11, 0.15)",
}


@dataclass
class IndexConditionData:
    """合并后的指数行情 + 分类数据。"""
    index_code: str
    index_name: str
    df: pd.DataFrame          # 合并后的 DataFrame，索引为 time
    total_bars: int
    bars_with_condition: int
    condition_counts: Dict[str, int]
    latest_bar: Optional[dict]


def load_index_condition_data() -> IndexConditionData:
    """加载并合并指数行情数据和行情分类数据。

    CSV file paths are read from config.yaml (index_price_csv_path and
    index_condition_csv_path).

    Returns:
        IndexConditionData with merged OHLCV data and market conditions.

    Raises:
        FileNotFoundError: If either CSV file is missing.
        ValueError: If the required config keys are not set.
    """
    from src.config.settings import get_config

    cfg = get_config()
    if not cfg.index_price_csv_path:
        raise ValueError("config.yaml 中未配置 index_price_csv_path")
    if not cfg.index_condition_csv_path:
        raise ValueError("config.yaml 中未配置 index_condition_csv_path")

    price_csv_path = Path(cfg.index_price_csv_path)
    condition_csv_path = Path(cfg.index_condition_csv_path)

    # 验证文件存在
    if not price_csv_path.exists():
        raise FileNotFoundError(f"价格数据文件不存在: {price_csv_path}")
    if not condition_csv_path.exists():
        raise FileNotFoundError(f"行情分类数据文件不存在: {condition_csv_path}")

    logger.info("Loading price data from: %s", price_csv_path)
    price_df = _read_price_csv(price_csv_path)

    logger.info("Loading condition data from: %s", condition_csv_path)
    condition_df = _read_condition_csv(condition_csv_path)

    # 合并：以价格数据为准，按日期匹配分类数据
    logger.info(
        "Merging %d price bars with %d condition records",
        len(price_df), len(condition_df),
    )
    df = price_df.merge(
        condition_df[["date", "market_condition", "probability"]],
        left_on="date",
        right_on="date",
        how="left",
    )
    df = df.drop(columns=["date"])  # date 列已冗余
    df = df.sort_values("time").reset_index(drop=True)

    # 统计
    bars_with_condition = df[df["market_condition"].notna()]
    condition_counts = {
        "trend_up": int((bars_with_condition["market_condition"] == "trend_up").sum()),
        "trend_down": int((bars_with_condition["market_condition"] == "trend_down").sum()),
        "range": int((bars_with_condition["market_condition"] == "range").sum()),
    }

    # 最新 bar
    latest_row = df.iloc[-1] if len(df) > 0 else None
    latest_bar = None
    if latest_row is not None:
        latest_bar = {
            "time": str(latest_row["time"]),
            "open": float(latest_row["open"]),
            "high": float(latest_row["high"]),
            "low": float(latest_row["low"]),
            "close": float(latest_row["close"]),
            "volume": float(latest_row["volume"]),
            "market_condition": latest_row.get("market_condition"),
            "probability": (
                float(latest_row["probability"])
                if pd.notna(latest_row.get("probability"))
                else None
            ),
        }

    logger.info(
        "Loaded %d bars, %d with condition. Conditions: %s",
        len(df), bars_with_condition, condition_counts,
    )

    return IndexConditionData(
        index_code="000001",
        index_name="上证指数",
        df=df,
        total_bars=len(df),
        bars_with_condition=len(bars_with_condition),
        condition_counts=condition_counts,
        latest_bar=latest_bar,
    )


def _read_price_csv(filepath: Path) -> pd.DataFrame:
    """读取价格 CSV 文件，返回含 date 列的 DataFrame。"""
    df = pd.read_csv(filepath)
    df.columns = [c.strip().lower() for c in df.columns]

    # 解析时间
    df["time"] = pd.to_datetime(df["time"])
    df["date"] = df["time"].dt.strftime("%Y-%m-%d")

    # 确保数值类型正确
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0)

    # 去掉无效行
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df.sort_values("time")

    logger.info("Loaded %d price bars from %s", len(df), filepath.name)
    return df


def _read_condition_csv(filepath: Path) -> pd.DataFrame:
    """读取行情分类 CSV 文件。"""
    df = pd.read_csv(filepath)
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = df["time"].astype(str).str.strip()
    df["market_condition"] = df["market_condition"].astype(str).str.strip()
    df["probability"] = pd.to_numeric(df["probability"], errors="coerce")

    logger.info("Loaded %d condition records from %s", len(df), filepath.name)
    return df
