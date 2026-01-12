# LWK Streamlit App

This repo tracks the public-facing Streamlit entrypoint `app_flag.py`. 
## Setup
- Python 3.10+ recommended.
- Install deps: `pip install streamlit pandas openpyxl` (and any other libraries you use in `app.py`).

## Run
- Start the app: `streamlit run app_flag.py`.
- Ensure a local `app.py` exists alongside this file; `app_flag.py` imports shared constants and helpers from it but the file is not versioned.
