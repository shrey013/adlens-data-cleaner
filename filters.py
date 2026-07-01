"""Filtering, de-duplication and sorting operations for cleaned data."""
from __future__ import annotations

import pandas as pd

from utils import month_bounds

def filter_by_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """Keep creatives active during the target month, but NOT running past it.

    Keep if:
      First Seen <= last day of month   (started on/before month end)
      AND Last Seen >= first day of month  (was active during the month)
      AND Last Seen <= last day of month   (does NOT continue past month end)
    """
    first_day, last_day = month_bounds(year, month)
    mask = (
        (df["First Seen"] <= last_day)
        & (df["Last Seen"] >= first_day)
        & (df["Last Seen"] <= last_day)   # <-- NEW: cut off anything after the month
    )
    return df[mask].copy()

def filter_by_impression(df: pd.DataFrame, minimum: int) -> pd.DataFrame:
    """Keep rows whose impressions are >= the minimum threshold."""
    return df[df["Impressions"] >= minimum].copy()

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates by Filename, keeping the first occurrence."""
    return df.drop_duplicates(subset=["Filename"], keep="first").copy()

def sort_by_impressions(df: pd.DataFrame) -> pd.DataFrame:
    """Sort descending so the largest impressions appear first."""
    return df.sort_values(by="Impressions", ascending=False).reset_index(drop=True)