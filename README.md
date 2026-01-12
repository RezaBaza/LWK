# Iran Emergency: Protect Civilians Now 🆘

This Streamlit app helps Iranians abroad and allies act quickly when communications are cut inside Iran. It pulls together contact details for:
- Members of the European Parliament
- Swedish MPs, government ministers, and embassies
- Influencers across X, Instagram, and TikTok

What you can do with it:
- Pick a list (Europe, Sweden, or international influencers) and browse contacts in a clean layout.
- Filter by the columns relevant to each list and trim to a smaller set if needed.
- Export the visible table to CSV to use in your own tools.
- Copy ready-to-send draft messages in English and Swedish and adapt them for outreach.

Notes:
- The app also shows a Lion & Sun flag animation when the image file is present.
- Shared settings and data-loading helpers live in `app_shared.py` (tracked). If you keep a private `app.py`, ensure it stays in sync or move its contents into `app_shared.py` for deployments like Streamlit Cloud.
- The contact data must be available to the app. Commit `iran_blackout_contacts.xlsx` (unignored) or otherwise provide the workbook at runtime on Streamlit Cloud.
