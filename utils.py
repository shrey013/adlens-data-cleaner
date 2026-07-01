"""Helper functions: impression parsing, date parsing, month bounds, column letters."""
from __future__ import annotations

import re
from calendar import monthrange
from datetime import datetime
from typing import Tuple

import pandas as pd

def column_letter_to_index(letter: str) -> int:
    """Convert an Excel column letter (e.g. 'A', 'D', 'AA') to a 0-based index."""
    letter = letter.strip().upper()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1

def parse_impressions(value: object) -> int:
    """Convert any AdClarity impression representation to an integer.

    Supports: '5.4M', '1M', '235K', '5K', '<5K', '927,000', '927000', '1.5B'.
    Any invalid/unparseable value becomes 0.
    """
    if value is None or isinstance(value, bool):
        return 0

    # Already numeric.
    if isinstance(value, (int, float)):
        try:
            if pd.isna(value):
                return 0
        except TypeError:
            pass
        return int(round(float(value)))

    text = str(value).strip()
    if not text:
        return 0

    # Strip comparison operators (e.g. '<5K'), thousands separators and spaces.
    for token in ("<", ">", "≤", "≥"):
        text = text.replace(token, "")
    text = text.replace(",", "").replace(" ", "").strip()
    if not text:
        return 0

    # Handle magnitude suffixes.
    multiplier = 1
    suffix = text[-1].upper()
    if suffix in ("K", "M", "B"):
        multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suffix]
        text = text[:-1]

    if not text:
        return 0

    try:
        number = float(text)
    except ValueError:
        return 0

    return int(round(number * multiplier))

def parse_date(value: object) -> pd.Timestamp:
    """Convert Excel serials, text dates and timestamps into a pandas Timestamp.

    Returns pd.NaT for invalid/unparseable values.
    """
    if value is None or isinstance(value, bool):
        return pd.NaT

    # Already datetime-like.
    if isinstance(value, (datetime, pd.Timestamp)):
        try:
            return pd.Timestamp(value)
        except (ValueError, OverflowError):
            return pd.NaT

    # Excel serial number (1900 date system, base 1899-12-30).
    if isinstance(value, (int, float)):
        try:
            if pd.isna(value):
                return pd.NaT
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(value))
        except (ValueError, OverflowError):
            return pd.NaT

    text = str(value).strip()
    if not text:
        return pd.NaT

    # Pure-numeric string => treat as Excel serial.
    if re.fullmatch(r"\d+(\.\d+)?", text):
        try:
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(text))
        except (ValueError, OverflowError):
            return pd.NaT

    # Standard text parsing (try month-first, then day-first).
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    return parsed

def month_bounds(year: int, month: int) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return (first_day 00:00:00, last_day 23:59:59) for the given month."""
    first_day = pd.Timestamp(year, month, 1)
    last_day_num = monthrange(year, month)[1]
    last_day = pd.Timestamp(year, month, last_day_num, 23, 59, 59)
    return first_day, last_day