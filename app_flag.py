from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

APP_IMPORT_ERROR = None
try:
    from app_shared import (
        FILE_PATH,
        SHEET_CONFIG,
        DISPLAY_COLUMNS,
        extract_emails,
        filter_frame,
        load_sheet,
    )
except ModuleNotFoundError as exc:
    APP_IMPORT_ERROR = str(exc)
    FILE_PATH = Path("contacts.xlsx")
    SHEET_CONFIG: dict[str, dict] = {}
    DISPLAY_COLUMNS: dict[str, list[str]] = {}

    def extract_emails(df: pd.DataFrame, email_cols: list[str]) -> list[str]:
        return []

    def filter_frame(df: pd.DataFrame, filters: dict, container) -> pd.DataFrame:
        return df

    def load_sheet(sheet_name: str) -> pd.DataFrame:
        raise FileNotFoundError("Missing app_shared.py with sheet loading logic.")

FLAG_PATH = Path(__file__).parent / "flag.png"
CATEGORY_GROUPS = [
    ("Europe", ["EU_MEPs_All_2024_2029"]),
    (
        "Sweden",
        [
            "Riksdag_SeatHolders_349",
            "Sweden_Gov_Ministers",
            "Sweden_Gov_Deputies_Links",
            "Sweden_Embassies_All",
            "Influencers_IG_Top1000",
            "Top_100_TikTok",
        ],
    ),
    ("International", ["Top_200_X"]),
]


@st.cache_resource
def get_flag_data_uri() -> str:
    """Return a data URI for the Lion & Sun flag image if present."""
    if not FLAG_PATH.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(FLAG_PATH.read_bytes()).decode("utf-8")


def inject_styles() -> None:
    """Global page styles to mirror the Exifa-style split layout."""
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(120% 120% at 12% 10%, #0f172a 0%, #0c152a 45%, #070d1a 100%);
            color: #e2e8f0;
        }
        .page-shell { position: relative; z-index: 2; }
        .hero { padding: 0.5rem 0 0.9rem; }
        .hero .eyebrow { text-transform: uppercase; letter-spacing: 0.15em; font-size: 0.78rem; color: #cbd5e1; }
        .hero h1 { margin: 0.2rem 0 0.4rem; color: #f8fafc; }
        .hero p { color: #cbd5e1; max-width: 900px; font-size: 1rem; }
        .panel { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1rem 1.1rem; box-shadow: 0 12px 38px rgba(0,0,0,0.35); }
        .sidebar-panel { position: sticky; top: 1rem; }
        .sidebar-panel .stRadio > label { font-weight: 600; color: #e2e8f0; }
        .sidebar-panel div[role="radiogroup"] { gap: 0.45rem !important; }
        .sidebar-panel div[role="radiogroup"] label { 
            width: 100%; 
            background: linear-gradient(90deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); 
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px; padding: 0.65rem 0.9rem; color: #e2e8f0;
            display: flex; align-items: center; gap: 0.5rem; 
            transition: all 0.2s ease;
        }
        .sidebar-panel div[role="radiogroup"] label:hover {
            border-color: rgba(34,211,238,0.35);
            box-shadow: 0 0 0 1px rgba(34,211,238,0.2);
        }
        .sidebar-panel div[role="radiogroup"] label[data-checked="true"],
        .sidebar-panel div[role="radiogroup"] label[aria-checked="true"] {
            border-color: #22d3ee;
            background: rgba(34,211,238,0.10);
        }
        .filters-box { margin-bottom: 1rem; }
        .cta-badge { display:inline-block; padding: 0.25rem 0.55rem; border-radius: 999px; background: rgba(34,211,238,0.1); color:#22d3ee; font-weight:600; font-size:0.8rem; }
        .cat-label { margin: 0.25rem 0 0.35rem; font-size: 0.9rem; font-weight: 700; letter-spacing: 0.04em; color: #94a3b8; text-transform: uppercase; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_flag_overlay(flag_data_uri: str, count: int = 22) -> None:
    """Add a falling Lion & Sun overlay in place of snowflakes."""
    if not flag_data_uri:
        return

    spans = []
    for i in range(count):
        left = (i * 37) % 100
        # Keep all animations inside a ~5s window: short durations and small delays.
        duration = 3.3 + (i % 3) * 0.4
        delay = (i % 10) * 0.15
        size = 60 + (i % 5) * 12
        spans.append(
            f"<span class='flag' style='left:{left}vw; animation-duration:{duration}s; animation-delay:{delay}s; width:{size}px; height:{size}px;'></span>"
        )

    st.markdown(
        f"""
        <style>
        .flag-snow-container {{
            pointer-events: none;
            position: fixed;
            inset: 0;
            overflow: hidden;
            z-index: 1;
            animation: flag-hide 5s forwards;
        }}
        .flag-snow-container .flag {{
            position: absolute;
            top: -120px;
            background-image: url('{flag_data_uri}');
            background-size: contain;
            background-repeat: no-repeat;
            opacity: 0.92;
            animation-name: flag-fall;
            animation-timing-function: linear;
            animation-iteration-count: 1;
            animation-fill-mode: forwards;
        }}
        @keyframes flag-fall {{
            0% {{ transform: translateY(-120px) rotate(0deg); opacity: 0.95; }}
            100% {{ transform: translateY(115vh) rotate(360deg); opacity: 0.9; }}
        }}
        @keyframes flag-hide {{
            0% {{ opacity: 1; }}
            90% {{ opacity: 1; }}
            100% {{ opacity: 0; visibility: hidden; }}
        }}
        </style>
        <div class="flag-snow-container">{''.join(spans)}</div>
        """,
        unsafe_allow_html=True,
    )


def prepare_sheet(sheet_name: str) -> pd.DataFrame:
    """Load and normalize a sheet using the original app rules."""
    df = load_sheet(sheet_name)
    cfg = SHEET_CONFIG[sheet_name]

    if "dedupe_subset" in cfg and cfg["dedupe_subset"]:
        df = df.drop_duplicates(subset=cfg["dedupe_subset"])

    if sheet_name == "Influencers_IG_Top1000":
        for col in ["Followers", "Avg_Engagement", "Authentic_Engagement"]:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace(" ", "", regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors="coerce")
    elif sheet_name == "Top_100_TikTok":
        if "TikTok_URL" not in df.columns:
            df["TikTok_URL"] = ""
        else:
            df["TikTok_URL"] = df["TikTok_URL"].astype(str).str.strip()
        if "TikTok_Handle" in df.columns:
            df["TikTok_Handle"] = df["TikTok_Handle"].astype(str).str.strip().str.removeprefix("@")
            mask_missing_url = df["TikTok_URL"].eq("") | df["TikTok_URL"].eq("nan")
            df.loc[mask_missing_url, "TikTok_URL"] = (
                "https://www.tiktok.com/@" + df.loc[mask_missing_url, "TikTok_Handle"].fillna("")
            )
        if "Followers" in df.columns:
            df["Followers"] = (
                df["Followers"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
            )
            df["Followers"] = pd.to_numeric(df["Followers"], errors="coerce")
    elif sheet_name == "Top_200_X":
        if "X_Handle" in df.columns:
            df["X_Handle"] = df["X_Handle"].astype(str).str.strip().str.removeprefix("@")
        if "X_URL" in df.columns:
            df["X_URL"] = df["X_URL"].astype(str).str.strip()
        else:
            df["X_URL"] = ""

        mask_missing_handle = df["X_Handle"].eq("") | df["X_Handle"].eq("nan")
        if mask_missing_handle.any():
            derived_handles = (
                df.loc[mask_missing_handle, "X_URL"]
                .str.extract(r"https?://(?:www\\.)?x\\.com/([^/?#]+)")[0]
                .fillna("")
            )
            df.loc[mask_missing_handle, "X_Handle"] = derived_handles

        mask_missing_url = df["X_URL"].eq("") | df["X_URL"].eq("nan")
        df.loc[mask_missing_url, "X_URL"] = (
            "https://x.com/" + df.loc[mask_missing_url, "X_Handle"].fillna("")
        )
        if "Followers" in df.columns:
            df["Followers"] = (
                df["Followers"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
            )
            df["Followers"] = pd.to_numeric(df["Followers"], errors="coerce")

    return df


def main() -> None:
    st.set_page_config(page_title="Help Break the Blackout in Iran", layout="wide")
    inject_styles()

    flag_data_uri = get_flag_data_uri()
    render_flag_overlay(flag_data_uri)

    st.markdown("<div class='page-shell'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero">
            <span class="cta-badge">Act now</span>
            <h1>Help Break the Blackout in Iran</h1>
            <p>
            Reports of internet and communications shutdowns are cutting people off while repression escalates.
            With communications disrupted and independent media access limited, the world isn’t seeing enough and too many governments, including across Europe, aren’t responding with real urgency.
            <br/><br/>
            This app helps Iranians abroad and their allies take swift action. Easily find contact information for members of European and Swedish Parliaments, key influencers across X, Instagram, or TikTok. Send messages and demand meaningful pressure to protect civilians, stop repression, and restore internet access
            <br/><br/>
            There are two draft messages at the end of the page in English and Swedish that you can use..
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if APP_IMPORT_ERROR:
        st.error(
            "Cannot load app configuration. Ensure `app_shared.py` is present with FILE_PATH, "
            "SHEET_CONFIG, DISPLAY_COLUMNS, extract_emails, filter_frame, and load_sheet defined."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not FILE_PATH.exists():
        st.error(f"Cannot find {FILE_PATH}. Please place the Excel file next to this app.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    default_sheet = CATEGORY_GROUPS[0][1][0]
    if "selected_sheet" not in st.session_state:
        st.session_state.selected_sheet = default_sheet

    selector_col, content_col = st.columns([1, 2], gap="large")

    with selector_col:
        st.markdown('<div class="panel sidebar-panel">', unsafe_allow_html=True)
        current = st.session_state.selected_sheet
        for cat_label, keys in CATEGORY_GROUPS:
            st.markdown(f"<div class='cat-label'>{cat_label}</div>", unsafe_allow_html=True)
            for key in keys:
                cfg_entry = SHEET_CONFIG[key]
                is_selected = current == key
                if st.button(
                    cfg_entry["display_name"],
                    key=f"btn_{key}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.selected_sheet = key
                    current = key
        st.caption("Choose a list by category; filters and exports are on the right.")
        st.markdown("<hr class='soft-line' />", unsafe_allow_html=True)
        st.markdown(
            "<div class='footer-note'>Made with ❤️ for the people of Iran.</div>",
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    sheet_name = st.session_state.selected_sheet
    cfg = SHEET_CONFIG[sheet_name]

    with content_col:
        st.markdown('<div class="panel content-panel">', unsafe_allow_html=True)
        st.subheader(cfg["display_name"])
        if cfg.get("description"):
            st.caption(cfg["description"])

        try:
            df = prepare_sheet(sheet_name)
        except FileNotFoundError as exc:
            st.error(str(exc))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            return
        except ValueError as exc:
            st.error(str(exc))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            return
        except Exception as exc:
            st.error(f"Failed to load sheet '{sheet_name}': {exc}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            return

        filter_area = st.container()
        filter_area.subheader("Filters")
        filter_area.caption(
            f"Rows: {len(df)} | Email columns: {', '.join(cfg['email_cols']) or 'None'}"
        )

        filtered_df = filter_frame(df, cfg["filters"], filter_area)

        if sheet_name == "Influencers_IG_Top1000":
            if "Followers" in df.columns:
                followers_series = df["Followers"].fillna(0)
                followers_min = float(followers_series.min()) if not followers_series.empty else 0.0
                followers_max = float(followers_series.max()) if not followers_series.empty else 0.0
                min_val, max_val = filter_area.slider(
                    "Followers range",
                    min_value=0.0,
                    max_value=max(followers_max, 1.0),
                    value=(followers_min, followers_max),
                    step=max(followers_max, 1.0) / 100 if followers_max else 1.0,
                )
                filtered_df = filtered_df[
                    (filtered_df["Followers"].fillna(0) >= min_val)
                    & (filtered_df["Followers"].fillna(0) <= max_val)
                ]
        elif sheet_name == "Top_100_TikTok":
            if "Followers" in df.columns:
                followers_series = df["Followers"].fillna(0)
                followers_min = float(followers_series.min()) if not followers_series.empty else 0.0
                followers_max = float(followers_series.max()) if not followers_series.empty else 0.0
                min_val, max_val = filter_area.slider(
                    "Followers range",
                    min_value=0.0,
                    max_value=max(followers_max, 1.0),
                    value=(followers_min, followers_max),
                    step=max(followers_max, 1.0) / 100 if followers_max else 1.0,
                )
                filtered_df = filtered_df[
                    (filtered_df["Followers"].fillna(0) >= min_val)
                    & (filtered_df["Followers"].fillna(0) <= max_val)
                ]
        elif sheet_name == "Top_200_X":
            if "Followers" in df.columns:
                followers_series = df["Followers"].fillna(0)
                followers_min = float(followers_series.min()) if not followers_series.empty else 0.0
                followers_max = float(followers_series.max()) if not followers_series.empty else 0.0
                min_val, max_val = filter_area.slider(
                    "Followers range",
                    min_value=0.0,
                    max_value=max(followers_max, 1.0),
                    value=(followers_min, followers_max),
                    step=max(followers_max, 1.0) / 100 if followers_max else 1.0,
                )
                filtered_df = filtered_df[
                    (filtered_df["Followers"].fillna(0) >= min_val)
                    & (filtered_df["Followers"].fillna(0) <= max_val)
                ]

        limit_label = "Limit rows (0 = no limit)"
        if sheet_name == "Top_200_X":
            limit_label = "Limit to N influencers (0 = all)"
        limit = filter_area.number_input(limit_label, min_value=0, value=0, step=10)
        if limit and limit < len(filtered_df):
            filtered_df = filtered_df.head(limit)

        emails = extract_emails(filtered_df, cfg["email_cols"])

        st.markdown("**Filtered table**")
        display_cols = DISPLAY_COLUMNS.get(sheet_name, [])
        if display_cols:
            cols_present = [c for c in display_cols if c in filtered_df.columns]
            display_df = filtered_df[cols_present]
        else:
            display_df = filtered_df

        column_config = {}
        if "Instagram_URL" in display_df.columns:
            column_config["Instagram_URL"] = st.column_config.LinkColumn(
                "Instagram URL", display_text="Open profile"
            )
        if "X_URL" in display_df.columns:
            column_config["X_URL"] = st.column_config.LinkColumn(
                "X URL", display_text="Open profile"
            )
        if "TikTok_URL" in display_df.columns:
            column_config["TikTok_URL"] = st.column_config.LinkColumn(
                "TikTok URL", display_text="Open profile"
            )
        if "Profile_URL" in display_df.columns:
            column_config["Profile_URL"] = st.column_config.LinkColumn(
                "Profile URL", display_text="Open profile"
            )
        if "SwedenAbroad_URL" in display_df.columns:
            column_config["SwedenAbroad_URL"] = st.column_config.LinkColumn(
                "SwedenAbroad URL", display_text="Open profile"
            )
        if "Contact_URL" in display_df.columns:
            column_config["Contact_URL"] = st.column_config.LinkColumn(
                "Contact URL", display_text="Open profile"
            )

        st.dataframe(display_df, column_config=column_config, use_container_width=True)
        csv_data = display_df.to_csv(index=False)
        st.download_button(
            "Download table (.csv)", data=csv_data, file_name="contacts.csv"
        )

        st.markdown("**Draft message**")
        default_message_en = (
            "Subject: Iran blackout — don’t let repression happen in the dark\n\n"
            "Hello,\n\n"
            "I’m writing with urgency about reports of widespread internet and communications disruptions in Iran. "
            "When people can’t call, upload, or be reached, abuses become harder to document—and easier to deny.\n\n"
            "Please do not treat this as a distant issue. We need clear, public leadership and real pressure. "
            "I urge you to:\n"
            "• Speak out and keep attention on Iran’s blackout and repression\n"
            "• Support independent reporting and human-rights monitoring\n"
            "• Back practical measures that help restore connectivity and protect civilians\n\n"
            "Every day of silence gives more cover for violence. Please act.\n\n"
            "Sincerely,\n"
            "[Your name]\n"
            "[City/Country]"
        )
        st.text_area("Message template (English, editable)", default_message_en, height=220)

        default_message_sv = (
            "Ämne: Iran stängs ner — låt inte förtryck ske i mörker\n\n"
            "Hej,\n\n"
            "Jag skriver med stor oro och brådska om rapporter om omfattande störningar i internet och kommunikation i Iran. "
            "När människor inte kan ringa, dela information eller ens nå varandra blir övergrepp svårare att dokumentera "
            "och lättare att förneka.\n\n"
            "Det här får inte behandlas som en avlägsen fråga. Vi behöver tydligt, offentligt ledarskap och verklig press. "
            "Jag uppmanar dig att:\n"
            "• Agera offentligt och hålla fokus på Irans blackout och repression\n"
            "• Stödja oberoende rapportering och människorättsövervakning\n"
            "• Ställa dig bakom konkreta åtgärder som återställer uppkoppling och skyddar civila\n\n"
            "Varje dag av tystnad ger mer utrymme för våld. Snälla, agera.\n\n"
            "Vänliga hälsningar,\n"
            "[Ditt namn]\n"
            "[Stad/Land]"
        )
        st.text_area("Meddelande (svenska, redigerbar)", default_message_sv, height=220)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
