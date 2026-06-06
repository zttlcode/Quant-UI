"""Trade engine: pair signals into trades, compute P&L, manage positions."""

from .pairer import TradePairer
from .pnl import PnLCalculator

__all__ = ["TradePairer", "PnLCalculator"]
