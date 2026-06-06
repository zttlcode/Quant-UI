"""Enumerations for signal types, labels, markets, and time levels."""

from enum import Enum, IntEnum


class SignalType(str, Enum):
    """Buy or sell signal type."""
    BUY = "buy"
    SELL = "sell"

    @classmethod
    def from_string(cls, s: str) -> "SignalType":
        s = s.strip().lower()
        if s in ("buy", "b", "1", "2"):
            return cls.BUY
        if s in ("sell", "s", "3", "4"):
            return cls.SELL
        raise ValueError(f"Unknown signal type: '{s}'")


class LabelType(IntEnum):
    """Model inference classification label.

    1 = effective buy (有效买入)
    2 = ineffective buy (无效买入)
    3 = effective sell (有效卖出)
    4 = ineffective sell (无效卖出)
    """
    EFFECTIVE_BUY = 1
    INEFFECTIVE_BUY = 2
    EFFECTIVE_SELL = 3
    INEFFECTIVE_SELL = 4

    @property
    def is_buy(self) -> bool:
        return self in (LabelType.EFFECTIVE_BUY, LabelType.INEFFECTIVE_BUY)

    @property
    def is_sell(self) -> bool:
        return self in (LabelType.EFFECTIVE_SELL, LabelType.INEFFECTIVE_SELL)

    @property
    def is_effective(self) -> bool:
        return self in (LabelType.EFFECTIVE_BUY, LabelType.EFFECTIVE_SELL)

    @property
    def description(self) -> str:
        desc_map = {
            LabelType.EFFECTIVE_BUY: "有效买入",
            LabelType.INEFFECTIVE_BUY: "无效买入",
            LabelType.EFFECTIVE_SELL: "有效卖出",
            LabelType.INEFFECTIVE_SELL: "无效卖出",
        }
        return desc_map.get(self, "未知")


class MarketType(str, Enum):
    """Market type."""
    A = "A"        # A-Share
    SH = "SH"      # Shanghai
    SZ = "SZ"      # Shenzhen


class TimeLevel(str, Enum):
    """Bar time level."""
    D = "d"        # Daily
    W = "w"        # Weekly
    M15 = "15"     # 15-minute
    M30 = "30"     # 30-minute
    M60 = "60"     # 60-minute
