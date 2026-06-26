"""Signal data loader for reading strategy trade signal CSV files.

Handles:
- Directory scanning for signal files
- Parsing different CSV formats (3-column vs 5-column)
- Data cleaning and validation
- Duplicate signal handling
- Deduplication strategies
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict

import pandas as pd

from ..config.settings import AppConfig
from ..data_model.schemas import TradeSignal
from ..data_model.enums import SignalType, LabelType
from ..utils.date_utils import parse_datetime
from ..utils.file_utils import scan_csv_files, parse_filename

logger = logging.getLogger(__name__)

# Expected columns for different formats
_COLS_5 = ["time", "price", "signal", "label", "prob"]
_COLS_3 = ["time", "price", "signal"]


class SignalLoader:
    """Loads and validates trade signal CSV files for a given strategy.

    Usage:
        cfg = get_config()
        loader = SignalLoader(cfg)
        signals = loader.load_strategy_signals("fuzzy_ma")
        # signals is a list of TradeSignal objects
    """

    def __init__(self, config: AppConfig):
        self.config = config
        # Signal dir naming convention: trade_point_live_{strategy_name}
        self._signal_dir_pattern = "trade_point_live_{strategy_name}"

    def _get_strategy_dir(self, strategy_name: str) -> Path:
        """Resolve the signal directory for a strategy.

        Expected path: trade_point_live_inference_{strategy_name}
        """
        base = Path(self.config.signal_root_dir)
        dir_path = base / f"trade_point_live_inference_{strategy_name}"

        if dir_path.exists() and any(dir_path.glob("*.csv")):
            logger.info("Using signal dir: %s", dir_path)
            return dir_path

        raise FileNotFoundError(
            f"Signal directory not found for strategy '{strategy_name}'.\n"
            f"Expected: {dir_path}"
        )

    def _read_signal_csv(self, filepath: Path) -> pd.DataFrame:
        """Read a single signal CSV file with robust parsing.

        Handles:
        - Files WITH headers: first row is 'time,price,signal,...'
        - Files WITHOUT headers: first row is actual data (common in live
          signal exports). Auto-detected and named by column count.
        - 3-column format: time, price, signal
        - 5-column format: time, price, signal, label, prob
        - UTF-8 and GBK encodings
        - UTF-8 BOM
        """
        logger.debug("Reading signal file: %s", filepath)

        # --- Step 1: read raw bytes and detect encoding ---
        raw_bytes = filepath.read_bytes()

        # Strip UTF-8 BOM if present
        if raw_bytes[:3] == b"\xef\xbb\xbf":
            raw_bytes = raw_bytes[3:]

        if len(raw_bytes) == 0:
            logger.warning("Empty signal file (0 bytes): %s", filepath)
            return pd.DataFrame()

        # Try UTF-8 first, fall back to GBK
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
            logger.warning("Empty signal file (no content lines): %s", filepath)
            return pd.DataFrame()

        # --- Step 2: detect if first row is a header ---
        first_row_lower = lines[0].lower()
        has_header = any(
            keyword in first_row_lower
            for keyword in ("time", "price", "signal", "open", "close")
        )

        # --- Step 3: parse with pandas ---
        import io

        if has_header:
            # Standard CSV with header row
            df = pd.read_csv(io.StringIO(text))
        else:
            # No header — first row is data. Determine column count from first line.
            num_cols = len(lines[0].split(","))
            if num_cols == 5:
                col_names = ["time", "price", "signal", "label", "prob"]
            elif num_cols == 3:
                col_names = ["time", "price", "signal"]
            elif num_cols == 4:
                col_names = ["time", "price", "signal", "label"]
            elif num_cols == 2:
                col_names = ["time", "price"]
                logger.warning(
                    "%s: only 2 columns found (time, price), missing signal column", filepath.name
                )
            else:
                logger.warning(
                    "%s: unexpected column count %d, using generic names", filepath.name, num_cols
                )
                col_names = [f"col_{i}" for i in range(num_cols)]

            df = pd.read_csv(io.StringIO(text), header=None, names=col_names)
            logger.debug(
                "%s: no header detected (%d cols), assigned names: %s",
                filepath.name, num_cols, col_names,
            )

        if df.empty:
            logger.warning("Empty signal file (no data rows): %s", filepath)
            return df

        # Normalize column names (strip whitespace, lowercase)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Validate required columns
        required = {"time", "price", "signal"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Missing required columns in {filepath.name}: {missing}. "
                f"Found columns: {list(df.columns)}"
            )

        return df

    def _parse_signals(
        self,
        df: pd.DataFrame,
        stock_code: str,
        market: str,
        level: str,
        strategy_name: str,
        filter_ineffective: bool = True,
    ) -> List[TradeSignal]:
        """Parse a DataFrame of signals into TradeSignal objects.

        Performs:
        - Time parsing and validation
        - Signal type coercion
        - Label parsing (optional)
        - Signal-label cross-validation (when filter_ineffective=True):
            buy  → only label=1 (有效买入) kept
            sell → only label=3 (有效卖出) kept
            All other combinations (label=2/4, or mismatches like
            buy+label=3, sell+label=1) are discarded as invalid.
          When filter_ineffective=False, all signals are kept regardless
          of label, making ineffective signals available for frontend
          display (e.g. stop-loss markers).
        - Prob parsing (optional)
        - Data cleaning (NaN handling, type conversion)
        """
        signals: List[TradeSignal] = []
        filtered_ineffective = 0

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

                # Parse price
                try:
                    price = float(row["price"])
                except (ValueError, TypeError) as e:
                    logger.warning(
                        "Row %d in %s: invalid price '%s', skipping: %s",
                        idx, stock_code, row.get("price"), e,
                    )
                    continue

                if price <= 0:
                    logger.warning(
                        "Row %d in %s: non-positive price %.4f, skipping",
                        idx, stock_code, price,
                    )
                    continue

                # Parse signal type
                try:
                    signal = SignalType.from_string(str(row["signal"]))
                except ValueError as e:
                    logger.warning(
                        "Row %d in %s: invalid signal '%s', skipping: %s",
                        idx, stock_code, row.get("signal"), e,
                    )
                    continue

                # Parse label (optional)
                label = None
                if "label" in df.columns:
                    label_val = row.get("label")
                    if pd.notna(label_val):
                        try:
                            label_int = int(float(label_val))
                            label = LabelType(label_int)
                        except (ValueError, TypeError):
                            logger.warning(
                                "Row %d in %s: invalid label '%s', treating as None",
                                idx, stock_code, label_val,
                            )

                # Validate signal-label consistency.
                # Rules:
                #   buy  signal → only label=1 (有效买入) is valid
                #   sell signal → only label=3 (有效卖出) is valid
                # Everything else (label=2/4, or mismatched signal+label like
                # buy+label=3, sell+label=1) is invalid.
                # When filter_ineffective=False, all signals are kept and made
                # available for frontend display (e.g. stop-loss markers).
                if label is not None:
                    is_valid = (
                        (signal == SignalType.BUY and label == LabelType.EFFECTIVE_BUY) or
                        (signal == SignalType.SELL and label == LabelType.EFFECTIVE_SELL)
                    )
                    if not is_valid:
                        if filter_ineffective:
                            filtered_ineffective += 1
                            logger.warning(
                                "Row %d in %s: invalid signal-label combination "
                                "(signal=%s, label=%d=%s), discarding",
                                idx, stock_code,
                                signal.value, label.value, label.description,
                            )
                            continue
                        else:
                            logger.debug(
                                "Row %d in %s: ineffective signal kept for display "
                                "(signal=%s, label=%d=%s)",
                                idx, stock_code,
                                signal.value, label.value, label.description,
                            )

                # Parse prob (optional)
                prob = None
                if "prob" in df.columns:
                    prob_val = row.get("prob")
                    if pd.notna(prob_val):
                        try:
                            prob = float(prob_val)
                        except (ValueError, TypeError):
                            logger.debug(
                                "Row %d in %s: invalid prob '%s', treating as None",
                                idx, stock_code, prob_val,
                            )

                ts = TradeSignal(
                    time=time_val,
                    price=price,
                    signal=signal,
                    label=label,
                    prob=prob,
                    stock_code=stock_code,
                    market=market,
                    level=level,
                    strategy_name=strategy_name,
                )
                signals.append(ts)

            except Exception as e:
                logger.warning(
                    "Row %d in %s: unexpected error parsing signal: %s",
                    idx, stock_code, e,
                )
                continue

        if filtered_ineffective > 0:
            logger.info(
                "  %s: filtered %d ineffective signals (label=2,4), kept %d effective",
                stock_code, filtered_ineffective, len(signals),
            )

        return signals

    def _deduplicate_signals(
        self,
        signals: List[TradeSignal],
    ) -> List[TradeSignal]:
        """Deduplicate signals that share the same date AND stock code.

        Two signals are considered duplicates only if they are for the same
        stock on the same date. Different stocks on the same date are NOT duplicates.

        Strategy is controlled by config.duplicate_signal_strategy:
        - "first": keep the earliest signal by timestamp (default)
        - "last": keep the latest signal by timestamp
        """
        if not signals:
            return signals

        strategy = self.config.duplicate_signal_strategy

        # Group by (stock_code, date) — same stock + same day = duplicate
        groups: Dict[tuple, List[TradeSignal]] = {}
        for sig in signals:
            key = (sig.stock_code, sig.date_str)
            if key not in groups:
                groups[key] = []
            groups[key].append(sig)

        deduped = []
        for (stock_code, date_str), group in groups.items():
            # Sort by time within each group
            group.sort(key=lambda s: s.time)

            if len(group) > 1:
                logger.info(
                    "Duplicate signals on %s for %s: %d signals, keeping %s",
                    date_str, stock_code, len(group), strategy,
                )

            if strategy in ("first",):
                deduped.append(group[0])
            elif strategy in ("last", "latest"):
                deduped.append(group[-1])
            else:
                deduped.append(group[0])

        # Sort all signals by time
        deduped.sort(key=lambda s: s.time)
        return deduped

    def load_strategy_signals(self, strategy_name: str) -> List[TradeSignal]:
        """Load all trade signals for a given strategy.

        Args:
            strategy_name: Name of the strategy (e.g., 'fuzzy_ma').

        Returns:
            List of TradeSignal objects, sorted by time and deduplicated.

        Raises:
            FileNotFoundError: If the strategy signal directory doesn't exist.
        """
        signal_dir = self._get_strategy_dir(strategy_name)
        logger.info("Loading signals for strategy '%s' from: %s", strategy_name, signal_dir)

        csv_files = scan_csv_files(str(signal_dir), "*.csv")
        if not csv_files:
            logger.warning("No CSV files found in: %s", signal_dir)
            return []

        all_signals: List[TradeSignal] = []
        missing_info_files: List[Path] = []

        for filepath in csv_files:
            # Parse filename to extract market, code, level
            parsed = parse_filename(filepath.name, pattern_type="signal")
            if parsed is None:
                logger.warning("Cannot parse filename: %s, skipping", filepath.name)
                missing_info_files.append(filepath)
                continue

            market = parsed["market"]
            stock_code = parsed["code"]
            level = parsed["level"]

            try:
                df = self._read_signal_csv(filepath)
                if df.empty:
                    continue

                signals = self._parse_signals(df, stock_code, market, level, strategy_name)
                if signals:
                    all_signals.extend(signals)
                    logger.info(
                        "  %s: parsed %d signals (market=%s, level=%s)",
                        stock_code, len(signals), market, level,
                    )
                else:
                    logger.warning("  %s: no valid signals parsed from %s", stock_code, filepath.name)

            except Exception as e:
                logger.error("Error loading %s: %s", filepath.name, e)
                continue

        if missing_info_files:
            logger.warning(
                "%d files could not be parsed for market/code/level: %s",
                len(missing_info_files),
                [f.name for f in missing_info_files],
            )

        # Deduplicate
        deduped = self._deduplicate_signals(all_signals)
        logger.info(
            "Loaded %d signals (%d after dedup) for strategy '%s' across %d stocks",
            len(all_signals), len(deduped), strategy_name,
            len(set(s.stock_code for s in deduped)),
        )

        return deduped

    def load_strategy_signals_all(self, strategy_name: str) -> List[TradeSignal]:
        """Load ALL trade signals for a strategy, including ineffective ones.

        Unlike load_strategy_signals(), this keeps signals with label=2/4
        (ineffective buy/sell) so the frontend can display stop-loss markers
        and other auxiliary information. These signals are not meant to be
        used for trade pairing — use load_strategy_signals() for that.

        Args:
            strategy_name: Name of the strategy (e.g., 'fuzzy_ma').

        Returns:
            List of TradeSignal objects including ineffective ones,
            sorted by time and deduplicated.
        """
        signal_dir = self._get_strategy_dir(strategy_name)
        logger.info(
            "Loading ALL signals (incl. ineffective) for strategy '%s' from: %s",
            strategy_name, signal_dir,
        )

        csv_files = scan_csv_files(str(signal_dir), "*.csv")
        if not csv_files:
            logger.warning("No CSV files found in: %s", signal_dir)
            return []

        all_signals: List[TradeSignal] = []
        missing_info_files: List[Path] = []

        for filepath in csv_files:
            parsed = parse_filename(filepath.name, pattern_type="signal")
            if parsed is None:
                logger.warning("Cannot parse filename: %s, skipping", filepath.name)
                missing_info_files.append(filepath)
                continue

            market = parsed["market"]
            stock_code = parsed["code"]
            level = parsed["level"]

            try:
                df = self._read_signal_csv(filepath)
                if df.empty:
                    continue

                signals = self._parse_signals(
                    df, stock_code, market, level, strategy_name,
                    filter_ineffective=False,
                )
                if signals:
                    all_signals.extend(signals)
                    logger.info(
                        "  %s: parsed %d signals (incl. ineffective) (market=%s, level=%s)",
                        stock_code, len(signals), market, level,
                    )
            except Exception as e:
                logger.error("Error loading %s: %s", filepath.name, e)
                continue

        if missing_info_files:
            logger.warning(
                "%d files could not be parsed for market/code/level: %s",
                len(missing_info_files),
                [f.name for f in missing_info_files],
            )

        deduped = self._deduplicate_signals(all_signals)
        logger.info(
            "Loaded %d signals (%d after dedup, incl. ineffective) for strategy '%s'",
            len(all_signals), len(deduped), strategy_name,
        )
        return deduped

    def load_stock_signals(
        self,
        strategy_name: str,
        stock_code: str,
    ) -> List[TradeSignal]:
        """Load signals for a specific stock under a strategy.

        Args:
            strategy_name: Strategy name.
            stock_code: Stock code to filter by.

        Returns:
            List of TradeSignal for the stock, sorted by time.
        """
        all_signals = self.load_strategy_signals(strategy_name)
        stock_signals = [s for s in all_signals if s.stock_code == stock_code]
        stock_signals.sort(key=lambda s: s.time)
        return stock_signals

    def get_signal_stocks(self, strategy_name: str) -> List[str]:
        """Get list of unique stock codes that have signals for a strategy.

        Returns:
            Sorted list of stock codes.
        """
        signals = self.load_strategy_signals(strategy_name)
        codes = sorted(set(s.stock_code for s in signals))
        return codes
