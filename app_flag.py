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
        @media (max-width: 900px) {
            .hero h1 { font-size: 1.8rem; }
            .hero p { font-size: 0.95rem; }
            .panel { padding: 0.85rem 0.9rem; }
            .sidebar-panel { position: static; }
        }
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
    st.set_page_config(page_title="Iran Emergency: Protect Civilians Now 🆘", layout="wide")
    inject_styles()

    flag_data_uri = get_flag_data_uri()
    render_flag_overlay(flag_data_uri)

    st.markdown("<div class='page-shell'>", unsafe_allow_html=True)
    hero_html = """
<div class="hero">
<div class="eyebrow" style="background:#fff; color:#111; padding:6px 10px; border-radius:999px; display:inline-block;">Act Now!</div>
<h1>Iran Emergency: Protect Civilians Now 🆘</h1>
<p>
Reports of internet and communications shutdowns are cutting people off while
repression escalates. With communications disrupted and access to independent
media severely limited, the world is seeing far too little and too many governments,
including many across Europe, aren't responding with real urgency.
</p>

<p>
This app helps Iranians abroad and their allies take swift action. You can easily find
<strong>contact information</strong> for members of the European Parliament and the Swedish
Parliament, as well as key influencers on X, Instagram, or TikTok, and send messages
demanding
</p>

<ul>
<li><strong>meaningful pressure to protect civilians,</strong></li>
<li><strong>stop the repression, and</strong></li>
<li><strong>restore internet access.</strong></li>
</ul>

<p>
There are two draft messages at the end of the page - in English and Swedish -
that you can use or adapt.
</p>
</div>
""".strip()
    st.markdown(hero_html, unsafe_allow_html=True)


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

    if "selected_sheet" not in st.session_state:
        st.session_state.selected_sheet = None

    st.markdown("### Choose a list to get started")
    options = [("-- Select a list --", None)]
    for cat_label, keys in CATEGORY_GROUPS:
        for key in keys:
            label = f"{cat_label} - {SHEET_CONFIG[key]['display_name']}"
            options.append((label, key))
    current = st.session_state.selected_sheet
    default_idx = next((i for i, (_, k) in enumerate(options) if k == current), 0)
    selected_label, selected_key = st.selectbox(
        "Lists",
        options,
        index=default_idx,
        format_func=lambda opt: opt[0],
        label_visibility="collapsed",
    )
    if selected_key != current:
        st.session_state.selected_sheet = selected_key
        current = selected_key

    if not current:
        st.info("Select a list above. Filters, table, and draft messages will appear here.")
        return

    selector_col, content_col = st.columns([1, 2], gap="large")

    with selector_col:
        st.markdown('<div class="panel sidebar-panel">', unsafe_allow_html=True)
        st.markdown(f"**Selected:** {SHEET_CONFIG[current]['display_name']}")
        st.caption("Change the list above to load a different dataset.")
        st.markdown("<hr class='soft-line' />", unsafe_allow_html=True)
        st.markdown(
            "<div class='footer-note'>Made with ❤️ for the people of Iran 🫂</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

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

        with st.expander("Filters", expanded=False):
            filter_area = st.container()
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
            "Subject: Iran — credible reports of killings under a communications blackout\n\n"
            "Hello,\n\n"
            "I’m writing because people are being killed in Iran while communications are being cut. "
          "When the internet and phone networks go dark, violence is easier to carry out and harder to prove. "
         "This is not just a “blackout”—it is cover.\n\n"
         "Please act with urgency. I urge you to:\n"
         "• Publicly condemn the killings and demand an immediate end to violence against civilians\n"
         "• Push for immediate protective and accountability measures (not statements)\n"
         "• Support independent investigation and human-rights monitoring\n\n"
         "Restoring open internet access is important—but first priority is stopping the killing and protecting civilians. "
         "Silence and delay cost lives.\n\n"
         "Sincerely,\n"
         "[Your name]\n"
         "[City/Country]"
        )
        st.text_area("Message template (English, editable)", default_message_en, height=220)

        default_message_sv = (
            "Ämne: Iran – dödligt våld i skuggan av nedsläckta kommunikationer\n\n"
            "Hej,\n\n"
         "Jag skriver med stor oro och brådska med anledning av rapporter om dödligt våld och brutalt förtryck i Iran, "
          "samtidigt som internet och kommunikationer stängs ner eller störs. "
         "När människor inte kan ringa, nå varandra eller dela bevis blir övergrepp lättare att genomföra – och svårare att "
         "dokumentera och utkräva ansvar för.\n\n"
         "Det här får inte behandlas som en avlägsen fråga. Jag uppmanar dig att agera skyndsamt och tydligt:\n"
         "• Fördöm dödandet och kräv ett omedelbart stopp för våld mot civila\n"
         "• Stöd oberoende granskning, dokumentation och människorättsövervakning\n"
         "• Driv på för verkliga, samordnade åtgärder och konsekvenser – inte bara uttalanden\n\n"
         "Att återställa ett öppet internet är viktigt, men först måste dödandet stoppas och civila skyddas. "
         "Varje dag av tystnad kostar liv.\n\n"
         "Vänliga hälsningar,\n"
         "[Ditt namn]\n"
         "[Stad/Land]"
        )
        st.text_area("Meddelande (svenska, redigerbar)", default_message_sv, height=220)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
