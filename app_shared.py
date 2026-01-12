from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

FILE_PATH = Path("iran_blackout_contacts.xlsx")

# Per-sheet configuration: which columns hold emails and which columns get filters.
SHEET_CONFIG = {
    "Riksdag_SeatHolders_349": {
        "display_name": "Riksdag MPs",
        "email_cols": ["Email"],
        "filters": ["Party"],
        "description": "Swedish Parliament seat holders",
    },
    "EU_MEPs_All_2024_2029": {
        "display_name": "EU MEPs 2024–2029",
        "email_cols": ["Email (generated guess)"],
        "filters": ["Country"],
        "description": "Members of the European Parliament",
    },
    "Sweden_Gov_Ministers": {
        "display_name": "Sweden Government Ministers",
        "email_cols": ["Contact email (registrator)"],
        "filters": ["Ministry"],
        "description": "Government ministers and registrator contacts",
    },
    "Sweden_Gov_Deputies_Links": {
        "display_name": "Sweden Government Deputies",
        "email_cols": [],
        "filters": [],
        "description": "Deputies/state secretaries (no emails in sheet)",
    },
    "Sweden_Embassies_All": {
        "display_name": "Sweden Embassies & Consulates",
        "email_cols": ["Email"],
        "filters": ["Location"],
        "description": "Swedish embassies and consulates",
    },
    "Influencers_IG_Top1000": {
        "display_name": "Influencers – Instagram Top 1000",
        "email_cols": [],
        "filters": [],
        "description": "Top Swedish Instagram accounts (no emails in sheet)",
        "dedupe_subset": ["IG_Handle"],
    },
    "Top_100_TikTok": {
        "display_name": "Influencers – TikTok Top 100",
        "email_cols": [],
        "filters": [],
        "description": "Top TikTok accounts",
    },
    "Top_200_X": {
        "display_name": "Influencers – X Top 200",
        "email_cols": [],
        "filters": ["Category"],
        "description": "Top X accounts",
    },
}

DISPLAY_COLUMNS = {
    "Riksdag_SeatHolders_349": ["Name", "Party", "Email"],
    "EU_MEPs_All_2024_2029": ["Name", "Profile_URL", "National_party", "Email (generated guess)"],
    "Sweden_Gov_Ministers": ["Name", "Title", "Contact email (registrator)"],
    "Sweden_Gov_Deputies_Links": ["Minister", "Minister title", "Deputies page (state secretaries)"],
    "Sweden_Embassies_All": ["Country/Area", "Location", "Contact_URL", "Email"],
    "Influencers_IG_Top1000": ["Name", "Instagram_URL"],
    "Top_100_TikTok": ["Name", "TikTok_Handle", "TikTok_URL", "Followers"],
    "Top_200_X": ["Name", "X_Handle", "X_URL", "Followers", "Followers_text", "Category"],
}


@st.cache_data
def load_sheet(sheet_name: str) -> pd.DataFrame:
    """Load a single sheet from the Excel file."""
    xl = load_workbook()
    if sheet_name not in xl.sheet_names:
        raise ValueError(f"Sheet '{sheet_name}' not found in workbook.")
    return xl.parse(sheet_name=sheet_name)


@st.cache_resource
def load_workbook() -> pd.ExcelFile:
    """Load the Excel workbook once."""
    if not FILE_PATH.exists():
        raise FileNotFoundError(f"Cannot find Excel file at {FILE_PATH}")
    return pd.ExcelFile(FILE_PATH)


def add_select_filter(df: pd.DataFrame, column: str, container: Any) -> pd.DataFrame:
    """Add a selectbox filter for a categorical column if values exist."""
    if column not in df.columns:
        return df

    values = sorted({v for v in df[column].dropna().astype(str).str.strip().tolist() if v})
    if not values:
        return df

    options = ["All"] + values
    choice = container.selectbox(column, options)
    if choice != "All":
        df = df[df[column].astype(str).str.strip() == choice]
    return df


def filter_frame(df: pd.DataFrame, filters: list[str], container: Any) -> pd.DataFrame:
    """Apply configured select filters and optional keyword search inside a container."""
    for col in filters:
        df = add_select_filter(df, col, container)

    keyword = container.text_input("Search (matches any column, case-insensitive)")
    if keyword:
        mask = df.apply(lambda s: s.astype(str).str.contains(keyword, case=False, na=False)).any(axis=1)
        df = df[mask]

    return df


def extract_emails(df: pd.DataFrame, email_cols: list[str]) -> pd.Series:
    """Collect unique emails from the configured columns."""
    if not email_cols:
        return pd.Series(dtype=str)

    series_list = []
    for col in email_cols:
        if col in df.columns:
            series_list.append(df[col])

    if not series_list:
        return pd.Series(dtype=str)

    emails = pd.concat(series_list, ignore_index=True).dropna().astype(str).str.strip()
    emails = emails[emails != ""].drop_duplicates().reset_index(drop=True)
    return emails
