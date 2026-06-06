"""Strategy adapter layer.

Provides a pluggable architecture for supporting multiple trading strategies.
Add a new strategy by:
1. Creating a subclass of BaseStrategyAdapter
2. Registering it in the StrategyRegistry
3. Placing signal CSV files in the appropriate directory
"""

from .base import BaseStrategyAdapter
from .registry import StrategyRegistry, get_registry
from .adapters import FuzzyMAAdapter, TeaRadicalNatureAdapter

__all__ = [
    "BaseStrategyAdapter",
    "StrategyRegistry",
    "get_registry",
    "FuzzyMAAdapter",
    "TeaRadicalNatureAdapter",
]
