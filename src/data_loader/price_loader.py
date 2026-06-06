"""Historical price bar data loader.

Reads live bar CSV files with OHLCV data and validates against signals.
"""

import logging
from pathlib import Path
from typing import List, Optional, Set, Dict

import pandas as pd

from ..config.settings import AppConfig
from ..data_model.schemas import PriceBar
from ..utils.date_utils import parse_datetime
from ..utils.file_utils import scan_csv_files, parse_filename, find_price_file

logger = logging.getLogger(__name__)


class PriceLoader:
    """Loads historical price bar data (OHLCV) from CSV files.

    Usage:
        cfg = get_config()
        loader = PriceLoader(cfg)
        bars = loader.load_price_bars("000027", "A", "d")
        # bars is a list of PriceBar objects
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self._price_dir = Path(config.price_root_dir)
        self._cache: Dict[str, List[PriceBar]] = {}

    def _validate_price_dir(self) -> None:
        """Check that the price root directory exists."""
        if not self._price_dir.exists():
            raise FileNotFoundError(
                f"Price data directory not found: {self._price_dir}\n"
                f"Please check the price_root_dir configuration."
            )
        if not self._price_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {self._price_dir}")

    def _read_price_csv(self, filepath: Path) -> pd.DataFrame:
        """Read a price bar CSV file with robust header detection.

        Handles both files with headers (time, open, high, low, close, volume)
        and files without headers (first row is actual OHLCV data).
        """
        logger.debug("Reading price file: %s", filepath)

        # Read raw bytes for encoding/header detection
        raw_bytes = filepath.read_bytes()
        if raw_bytes[:3] == b"\xef\xbb\xbf":
            raw_bytes = raw_bytes[3:]

        if len(raw_bytes) == 0:
            logger.warning("Empty price file (0 bytes): %s", filepath)
            return pd.DataFrame()

        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw_bytes.decode("gbk")
            except Exception as e:
                logger.error("Failed to decode %s: %s", filepath, e)
                raise

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            logger.warning("Empty price file (no content): %s", filepath)
            return pd.DataFrame()

        # Detect header
        first_row_lower = lines[0].lower()
        has_header = any(
            keyword in first_row_lower
            for keyword in ("time", "open", "high", "low", "close")
        )

        import io

        if has_header:
            df = pd.read_csv(io.StringIO(text))
        else:
            num_cols = len(lines[0].split(","))
            col_names_map = {
                6: ["time", "open", "high", "low", "close", "volume"],
                5: ["time", "open", "high", "low", "close"],
            }
            col_names = col_names_map.get(num_cols, [f"col_{i}" for i in range(num_cols)])
            logger.debug(
                "%s: no header detected (%d cols), assigned: %s",
                filepath.name, num_cols, col_names,
            )
            df = pd.read_csv(io.StringIO(text), header=None, names=col_names)

        if df.empty:
            logger.warning("Empty price file: %s", filepath)
            return df

        # Normalize column names
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Validate required columns
        required = {"time", "open", "high", "low", "close"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Missing required columns in {filepath.name}: {missing}. "
                f"Found columns: {list(df.columns)}"
            )

        return df

    def _parse_price_bars(
        self,
        df: pd.DataFrame,
        stock_code: str,
        market: str,
        level: str,
    ) -> List[PriceBar]:
        """Parse a DataFrame of price data into PriceBar objects."""
        bars: List[PriceBar] = []

        for idx, row in df.iterrows():
            try:
                # Parse time
                time_val = parse_datetime(row["time"])
                if time_val is None:
                    logger.warning(
                        "Row %d in %s: could not parse time '%s', skipping",
                        idx, stock_code, row.get("time"),
                    )
                    continue

                # Parse OHLCV values, handling NaN
                try:
                    open_p = float(row["open"])
                    high_p = float(row["high"])
                    low_p = float(row["low"])
                    close_p = float(row["close"])
                    volume = float(row.get("volume", 0)) if pd.notna(row.get("volume", 0)) else 0.0
                except (ValueError, TypeError) as e:
                    logger.warning("Row %d in %s: invalid OHLCV values: %s", idx, stock_code, e)
                    continue

                # Validate OHLC relationships
                if any(pd.isna(v) for v in [open_p, high_p, low_p, close_p]):
                    logger.warning("Row %d in %s: NaN in OHLC values, skipping", idx, stock_code)
                    continue

                if high_p < low_p:
                    logger.warning(
                        "Row %d in %s: high (%.4f) < low (%.4f), flipping",
                        idx, stock_code, high_p, low_p,
                    )
                    high_p, low_p = low_p, high_p

                bar = PriceBar(
                    time=time_val,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=volume,
                    stock_code=stock_code,
                    market=market,
                    level=level,
                )
                bars.append(bar)

            except Exception as e:
                logger.warning("Row %d in %s: unexpected error: %s", idx, stock_code, e)
                continue

        return bars

    def load_price_bars(
        self,
        stock_code: str,
        market: str = "A",
        level: str = "d",
    ) -> List[PriceBar]:
        """Load price bars for a specific stock.

        Args:
            stock_code: Stock code (e.g., '000027').
            market: Market type (default 'A').
            level: Time level (default 'd').

        Returns:
            List of PriceBar objects sorted by time.

        Raises:
            FileNotFoundError: If the price file doesn't exist.
        """
        cache_key = f"{market}_{stock_code}_{level}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        self._validate_price_dir()

        filepath = find_price_file(str(self._price_dir), market, stock_code, level)
        if filepath is None:
            raise FileNotFoundError(
                f"Price file not found for {market}_{stock_code}_{level}. "
                f"Expected: live_bar_{market}_{stock_code}_{level}.csv in {self._price_dir}"
            )

        logger.info("Loading price bars: %s", filepath.name)

        try:
            df = self._read_price_csv(filepath)
            if df.empty:
                logger.warning("Empty price data for %s", stock_code)
                return []

            bars = self._parse_price_bars(df, stock_code, market, level)
            bars.sort(key=lambda b: b.time)

            logger.info("Loaded %d price bars for %s", len(bars), stock_code)

            self._cache[cache_key] = bars
            return bars

        except Exception as e:
            logger.error("Failed to load price bars for %s: %s", stock_code, e)
            raise

    def load_price_bars_df(
        self,
        stock_code: str,
        market: str = "A",
        level: str = "d",
    ) -> pd.DataFrame:
        """Load price bars and return as a pandas DataFrame.

        The DataFrame has columns: time, open, high, low, close, volume
        and is indexed by time.
        """
        bars = self.load_price_bars(stock_code, market, level)
        if not bars:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        data = [
            {
                "time": b.time,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ]
        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"])
        df = df.set_index("time").sort_index()
        return df

    def validate_signal_dates(
        self,
        stock_code: str,
        signal_dates: Set[str],
        market: str = "A",
        level: str = "d",
    ) -> List[str]:
        """Check that all signal dates have corresponding price data.

        Args:
            stock_code: Stock code.
            signal_dates: Set of date strings (YYYY-MM-DD) from signals.
            market: Market type.
            level: Time level.

        Returns:
            List of warning messages for dates with no matching price data.
            Empty list if all dates are covered.
        """
        warnings = []

        try:
            bars = self.load_price_bars(stock_code, market, level)
        except FileNotFoundError as e:
            return [f"Price file not found for {stock_code}: {e}"]

        bar_dates = {b.time.strftime("%Y-%m-%d") for b in bars}

        missing = signal_dates - bar_dates
        for date_str in sorted(missing):
            msg = (
                f"WARNING: Signal date {date_str} for {stock_code} has no "
                f"corresponding price data. Signal may not be displayed correctly."
            )
            warnings.append(msg)
            logger.warning(msg)

        return warnings

    def get_available_stocks(
        self,
        market: str = "A",
        level: str = "d",
    ) -> List[str]:
        """List all stocks with available price data.

        Returns:
            Sorted list of stock codes.
        """
        self._validate_price_dir()
        files = scan_csv_files(str(self._price_dir), f"live_bar_{market}_*_{level}.csv")

        stocks = []
        for fp in files:
            parsed = parse_filename(fp.name, pattern_type="live_bar")
            if parsed:
                stocks.append(parsed["code"])

        return sorted(set(stocks))

    def clear_cache(self):
        """Clear the internal price data cache."""
        self._cache.clear()
