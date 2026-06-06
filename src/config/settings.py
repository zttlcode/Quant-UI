"""Configuration loader for Quant-UI.

Loads settings from config.yaml with environment variable overrides.
Supports Windows paths and provides typed access to all configuration.
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import yaml


logger = logging.getLogger(__name__)

# Path to the default config file relative to project root
_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


@dataclass
class AppConfig:
    """Typed application configuration loaded from config.yaml."""

    # Data paths
    signal_root_dir: str = ""
    price_root_dir: str = ""
    output_dir: str = "./output"

    # Strategy
    default_strategy_list: List[str] = field(default_factory=list)

    # Market & Level defaults
    default_market: str = "A"
    default_level: str = "d"

    # Signal display
    show_only_effective_signal: bool = False
    show_unclosed_position: bool = True
    hold_stop_atr_multiplier: float = 1.0

    # Trading costs
    commission: float = 0.0
    slippage: float = 0.0

    # Indicator parameters
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    ma_periods: List[int] = field(default_factory=lambda: [5, 10, 20])
    atr_period: int = 14

    # Duplicate signal handling
    duplicate_signal_strategy: str = "first"
    consecutive_buy_handling: str = "first"
    consecutive_sell_handling: str = "ignore"

    # Logging
    log_level: str = "INFO"
    log_file: str = "./output/app.log"

    # Web app
    app_title: str = "Quant-UI | Stock Strategy Visualization"
    app_port: int = 8501
    app_host: str = "localhost"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Create AppConfig from a dictionary, filtering known keys."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def _resolve_path(path_str: str) -> str:
    """Resolve a path string, converting to absolute and normalizing slashes."""
    if not path_str:
        return path_str
    p = Path(path_str)
    if not p.is_absolute():
        p = Path.cwd() / p
    return str(p.resolve()).replace("\\", "/")


def _override_from_env(cfg: AppConfig) -> AppConfig:
    """Allow environment variables to override config values.

    Supported env vars:
        QUANT_UI_SIGNAL_ROOT_DIR
        QUANT_UI_PRICE_ROOT_DIR
        QUANT_UI_OUTPUT_DIR
        QUANT_UI_LOG_LEVEL
        QUANT_UI_SHOW_ONLY_EFFECTIVE
    """
    env_map = {
        "QUANT_UI_SIGNAL_ROOT_DIR": ("signal_root_dir", str),
        "QUANT_UI_PRICE_ROOT_DIR": ("price_root_dir", str),
        "QUANT_UI_OUTPUT_DIR": ("output_dir", str),
        "QUANT_UI_LOG_LEVEL": ("log_level", str),
        "QUANT_UI_SHOW_ONLY_EFFECTIVE": ("show_only_effective_signal", lambda v: v.lower() in ("true", "1", "yes")),
    }
    for env_var, (attr, converter) in env_map.items():
        val = os.environ.get(env_var)
        if val is not None:
            setattr(cfg, attr, converter(val))
            logger.info("Config override from env: %s = %s", env_var, val)
    return cfg


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to config.yaml. If None, uses the default.

    Returns:
        AppConfig with all settings loaded and paths resolved.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is malformed.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}\n"
            f"Please create a config.yaml based on the template."
        )

    logger.info("Loading configuration from: %s", path)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Invalid config format in {path}: expected YAML mapping")

    cfg = AppConfig.from_dict(raw)

    # Resolve path separators for Windows compatibility
    cfg.signal_root_dir = _resolve_path(cfg.signal_root_dir)
    cfg.price_root_dir = _resolve_path(cfg.price_root_dir)
    cfg.output_dir = _resolve_path(cfg.output_dir)

    # Override from environment
    cfg = _override_from_env(cfg)

    # Validate required paths
    if not cfg.signal_root_dir:
        raise ValueError("signal_root_dir is not configured")
    if not cfg.price_root_dir:
        raise ValueError("price_root_dir is not configured")

    return cfg


# Module-level singleton cache
_config_singleton: Optional[AppConfig] = None


def get_config(config_path: Optional[str] = None) -> AppConfig:
    """Get the global configuration singleton.

    On first call, loads from config file. Subsequent calls return the cached instance.
    Pass config_path to force a reload from a different file.
    """
    global _config_singleton
    if _config_singleton is None or config_path is not None:
        _config_singleton = load_config(config_path)
    return _config_singleton


def reset_config():
    """Reset the config singleton (useful for testing)."""
    global _config_singleton
    _config_singleton = None
