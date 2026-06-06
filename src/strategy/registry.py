"""Strategy registry for pluggable strategy adapters.

New strategies can be added without modifying existing code by:
1. Creating a subclass of BaseStrategyAdapter
2. Registering it: registry.register(MyAdapter(config))
"""

import logging
from typing import Dict, List, Optional, Type

from .base import BaseStrategyAdapter
from ..config.settings import AppConfig

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Central registry for strategy adapters.

    Supports:
    - Registering adapter instances
    - Looking up adapters by strategy name
    - Auto-registering built-in adapters
    - Listing all registered strategies
    """

    def __init__(self):
        self._adapters: Dict[str, BaseStrategyAdapter] = {}

    def register(self, adapter: BaseStrategyAdapter) -> None:
        """Register a strategy adapter.

        Args:
            adapter: Strategy adapter instance.

        Raises:
            ValueError: If a strategy with the same name is already registered.
        """
        name = adapter.strategy_name
        if name in self._adapters:
            logger.warning(
                "Strategy '%s' already registered, overwriting", name
            )
        self._adapters[name] = adapter
        logger.info("Registered strategy: %s (%s)", name, adapter.display_name)

    def unregister(self, strategy_name: str) -> None:
        """Remove a strategy from the registry."""
        self._adapters.pop(strategy_name, None)

    def get(self, strategy_name: str) -> Optional[BaseStrategyAdapter]:
        """Get an adapter by strategy name.

        Returns None if not found.
        """
        return self._adapters.get(strategy_name)

    def get_required(self, strategy_name: str) -> BaseStrategyAdapter:
        """Get an adapter, raising if not found.

        Raises:
            KeyError: If strategy is not registered.
        """
        adapter = self.get(strategy_name)
        if adapter is None:
            available = ", ".join(self.list_names())
            raise KeyError(
                f"Strategy '{strategy_name}' not found in registry. "
                f"Available: [{available}]"
            )
        return adapter

    def list_all(self) -> List[BaseStrategyAdapter]:
        """List all registered strategy adapters."""
        return list(self._adapters.values())

    def list_names(self) -> List[str]:
        """List all registered strategy names."""
        return list(self._adapters.keys())

    def get_count(self) -> int:
        """Number of registered strategies."""
        return len(self._adapters)

    def __contains__(self, strategy_name: str) -> bool:
        return strategy_name in self._adapters

    def __iter__(self):
        return iter(self._adapters.values())

    def __len__(self):
        return len(self._adapters)


# Global singleton registry
_registry: Optional[StrategyRegistry] = None


def get_registry() -> StrategyRegistry:
    """Get the global strategy registry singleton."""
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
    return _registry


def init_registry(config: AppConfig) -> StrategyRegistry:
    """Initialize the registry with built-in strategy adapters.

    Args:
        config: Application configuration.

    Returns:
        The initialized registry with all known strategies registered.
    """
    from .adapters import FuzzyMAAdapter, TeaRadicalNatureAdapter

    registry = get_registry()

    # Register built-in adapters
    registry.register(FuzzyMAAdapter(config))
    registry.register(TeaRadicalNatureAdapter(config))

    logger.info(
        "Strategy registry initialized with %d strategies: %s",
        len(registry),
        ", ".join(registry.list_names()),
    )

    return registry
