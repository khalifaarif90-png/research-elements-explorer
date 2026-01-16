# Research Elements Explorer (Streamlit)

This app lets readers **search and filter** the "Periodic Table of Research Elements" Excel sheet and open any element to view its details.

## Files
- `streamlit_app.py` — Streamlit app
- `final_element_sheet.xlsx` — data file
- `requirements.txt` — dependencies

## Run locally
```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Deploy (Streamlit Community Cloud)
1. Push these files to a **public GitHub repo**.
2. In Streamlit Cloud, click **New app** → select your repo.
3. Set **Main file path** to `streamlit_app.py`.
4. Deploy and share the generated link.
