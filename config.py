"""Application-wide configuration and constants for AdLens Data Cleaner."""
from __future__ import annotations

APP_NAME = "AdLens Data Cleaner"
APP_VERSION = "1.0"

AUTHOR_NAME = "Shreyansh Saurav"
AUTHOR_EMAIL = "shreyanshsaurav0786@gmail.com"

# ---- Theme ----
APPEARANCE_MODE = "dark"
COLOR_THEME = "dark-blue"

# Dark SaaS palette
COLOR_BG = "#0F1115"
COLOR_PANEL = "#1A1D24"
COLOR_CARD = "#22262F"
COLOR_ACCENT = "#3B82F6"
COLOR_ACCENT_HOVER = "#2563EB"
COLOR_SUCCESS = "#22C55E"
COLOR_TEXT = "#E5E7EB"
COLOR_SUBTLE = "#9CA3AF"

# ---- Defaults ----
DEFAULT_MIN_IMPRESSION = 1_000_000

# Canonical output columns (order matters) and their lowercase match keys.
OUTPUT_COLUMNS = ["Filename", "Impressions", "First Seen", "Last Seen"]
REQUIRED_HEADERS = ["filename", "impressions", "first seen", "last seen"]

# Fallback fixed column letters per spec (used only if header names are missing).
FALLBACK_COLUMN_LETTERS = {
    "Filename": "D",
    "Impressions": "N",
    "First Seen": "R",
    "Last Seen": "S",
}

ALLOWED_EXTENSIONS = [".xlsx", ".xls"]
OUTPUT_PREFIX = "Cleaned_Data_"

# Month dropdown range (inclusive).
MONTH_START_YEAR = 2026
MONTH_END_YEAR = 2035

# Progress steps shown to the user.
PROGRESS_STEPS = [
    "Reading Excel",
    "Finding Header",
    "Cleaning Data",
    "Converting Impressions",
    "Converting Dates",
    "Filtering Month",
    "Filtering Impressions",
    "Removing Duplicates",
    "Sorting",
    "Exporting Excel",
    "Completed",
]