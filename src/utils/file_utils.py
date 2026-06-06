"""File system utilities for scanning CSV files, parsing filenames, and directory management."""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Filename pattern: Market_StockCode_Level.csv
# e.g., A_000027_d.csv, A_sh515220_d.csv, A_sz159329_d.csv
FILENAME_PATTERN = re.compile(
    r"^(?P<market>[A-Za-z]+(?:_[a-z]+)?)_(?P<code>[A-Za-z]*\d+)_(?P<level>[a-z0-9]+)\.csv$"
)

# Live bar filename: live_bar_Market_StockCode_Level.csv
LIVE_BAR_PATTERN = re.compile(
    r"^live_bar_(?P<market>[A-Za-z]+(?:_[a-z]+)?)_(?P<code>[A-Za-z]*\d+)_(?P<level>[a-z0-9]+)\.csv$"
)


def parse_filename(filename: str, pattern_type: str = "signal") -> Optional[Dict[str, str]]:
    """Parse a CSV filename to extract market, code, and level.

    Args:
        filename: The filename to parse (with or without path).
        pattern_type: 'signal' for signal files, 'live_bar' for price files.

    Returns:
        Dict with keys: market, code, level. Or None if pattern doesn't match.
    """
    basename = os.path.basename(filename)
    pattern = LIVE_BAR_PATTERN if pattern_type == "live_bar" else FILENAME_PATTERN
    match = pattern.match(basename)
    if match:
        return match.groupdict()
    return None


def scan_csv_files(
    directory: str,
    pattern: str = "*.csv",
    recursive: bool = False,
) -> List[Path]:
    """Scan a directory for CSV files matching a glob pattern.

    Args:
        directory: Directory path to scan.
        pattern: Glob pattern for file matching.
        recursive: Whether to scan subdirectories.

    Returns:
        List of Path objects for matching files.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    if recursive:
        files = list(dir_path.rglob(pattern))
    else:
        files = list(dir_path.glob(pattern))

    logger.info("Scanned %s: found %d CSV files", directory, len(files))
    return sorted(files)


def ensure_dir(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        Path object for the directory.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_output_dir(path: str) -> Path:
    """Ensure output directory exists, creating it if necessary.

    Returns:
        Path object for the output directory.
    """
    return ensure_dir(path)


def file_exists(path: str) -> bool:
    """Check if a file exists and is accessible.

    Args:
        path: File path to check.

    Returns:
        True if the file exists and is a file.
    """
    p = Path(path)
    return p.exists() and p.is_file()


def find_price_file(
    price_root: str,
    market: str,
    stock_code: str,
    level: str,
) -> Optional[Path]:
    """Find a price bar file for the given market/stock/level combination.

    The file is expected to be named: live_bar_{market}_{stock_code}_{level}.csv

    Args:
        price_root: Root directory containing live price files.
        market: Market type (e.g., 'A').
        stock_code: Stock code (e.g., '000027').
        level: Time level (e.g., 'd').

    Returns:
        Path to the file if found, None otherwise.
    """
    # The live data directory has flat structure, no subdirectories
    filename = f"live_bar_{market}_{stock_code}_{level}.csv"
    filepath = Path(price_root) / filename
    if filepath.exists():
        return filepath
    return None


def extract_stock_code_from_signal_filename(filename: str) -> Optional[Tuple[str, str, str]]:
    """Extract (market, stock_code, level) from a signal filename.

    Args:
        filename: Signal filename like 'A_000027_d.csv' or 'A_sh515220_d.csv'.

    Returns:
        Tuple of (market, stock_code, level) or None if parsing fails.
    """
    parsed = parse_filename(filename, pattern_type="signal")
    if parsed:
        return parsed["market"], parsed["code"], parsed["level"]
    return None
