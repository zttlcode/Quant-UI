"""Date/time parsing and normalization utilities.

Handles various date formats found in the CSV data, including:
- YYYY-MM-DD
- YYYY-MM-DD HH:MM:SS
- ISO format variants
"""

import logging
from datetime import datetime, date
from typing import Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

# Common date formats to try
_DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y%m%d",
]


def parse_datetime(value: Union[str, datetime, pd.Timestamp, None]) -> Optional[datetime]:
    """Parse a string or value into a datetime object.

    Args:
        value: The value to parse. Can be str, datetime, pd.Timestamp, or None.

    Returns:
        Parsed datetime, or None if parsing fails.

    Raises:
        ValueError: If the value cannot be parsed and is not None.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())

    s = str(value).strip()
    if not s:
        return None

    # Try pandas first (handles most common formats robustly)
    try:
        ts = pd.Timestamp(s)
        return ts.to_pydatetime()
    except (ValueError, TypeError):
        pass

    # Fall back to explicit format list
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    error_msg = f"Unable to parse datetime from: '{value}'"
    logger.error(error_msg)
    raise ValueError(error_msg)


def parse_date(value: Union[str, datetime, date, pd.Timestamp, None]) -> Optional[date]:
    """Parse a value into a date object."""
    dt = parse_datetime(value)
    if dt is None:
        return None
    return dt.date()


def normalize_date(dt: Optional[Union[datetime, date, str]]) -> Optional[date]:
    """Normalize any date-like value to a date object."""
    if dt is None:
        return None
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    return parse_date(dt)


def date_to_str(d: Union[date, datetime, str, None], fmt: str = "%Y-%m-%d") -> Optional[str]:
    """Convert a date/datetime to a formatted string."""
    if d is None:
        return None
    if isinstance(d, str):
        return d
    return d.strftime(fmt)


def datetime_to_str(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """Convert a datetime to a formatted string."""
    return date_to_str(dt, fmt)
