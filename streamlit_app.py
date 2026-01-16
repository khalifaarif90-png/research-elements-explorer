import pandas as pd
import streamlit as st

# ---- Page config (mobile-friendly) ----
st.set_page_config(page_title="Research Elements Explorer", layout="centered")

# ---- Small CSS tweaks for mobile readability ----
st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 900px;}
    h1 {font-size: 1.6rem;}
    .stExpander details {border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🧪 Research Elements Explorer")
st.caption("Search, filter, and open any element for details (mobile-friendly).")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

DATA_FILE = "final_element_sheet.xlsx"
df = load_data(DATA_FILE)
cols = df.columns.tolist()

# ---- Sidebar controls ----
st.sidebar.header("View")
mobile_mode = st.sidebar.toggle("📱 Mobile mode (recommended)", value=True)

st.sidebar.header("Filters")
search = st.sidebar.text_input(
    "Search (any field)",
    placeholder="e.g., RP, theory, sampling, integrity..."
).strip()

# Category filter
chosen_cats = None
if "Category" in cols:
    cat_vals = sorted(df["Category"].dropna().astype(str).unique().tolist())
    chosen_cats = st.sidebar.multiselect("Category", cat_vals, default=cat_vals)

# Action filter
chosen_actions = None
if "Action" in cols:
    act_vals = sorted(df["Action"].dropna().astype(str).unique().tolist())
    chosen_actions = st.sidebar.multiselect("Action", act_vals, default=act_vals)

# Element number range
chosen_range = None
if "Element No" in cols and pd.api.types.is_numeric_dtype(df["Element No"]):
    min_no = int(df["Element No"].min())
    max_no = int(df["Element No"].max())
    chosen_range = st.sidebar.slider("Element No range", min_no, max_no, (min_no, max_no))

# ---- Apply filters ----
filtered = df.copy()

if chosen_cats is not None:
    filtered = filtered[filtered["Category"].astype(str).isin(chosen_cats)]

if chosen_actions is not None:
    filtered = filtered[filtered["Action"].astype(str).isin(chosen_actions)]

if chosen_range is not None:
    filtered = filtered[(filtered["Element No"] >= chosen_range[0]) & (filtered["Element No"] <= chosen_range[1])]

if search:
    s = search.lower()
    mask = filtered.apply(lambda r: r.astype(str).str.lower().str.contains(s, na=False).any(), axis=1)
    filtered = filtered[mask]

# ---- Quick stats ----
st.write(f"**Showing {len(filtered)} of {len(df)} elements**")

# ---- Download filtered results ----
csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered results (CSV)",
    data=csv_bytes,
    file_name="filtered_research_elements.csv",
    mime="text/csv",
)

st.divider()

# ---- MOBILE MODE: card/expander layout ----
if mobile_mode:
    st.subheader("Results")

    if len(filtered) == 0:
        st.info("No matching elements. Adjust filters or search.")
    else:
        # Sort by Element No if present
        if "Element No" in cols and pd.api.types.is_numeric_dtype(filtered["Element No"]):
            filtered = filtered.sort_values("Element No")

        # Show as tap-friendly cards
        for _, row in filtered.iterrows():
            el_no = row["Element No"] if "Element No" in cols else ""
            el_name = row["Element Name"] if "Element Name" in cols else "Element"
            symbol = row["Symbol"] if "Symbol" in cols else ""
            cat = row["Category"] if "Category" in cols else ""
            action = row["Action"] if "Action" in cols else ""

            header = f"{el_no} — {el_name}"
            if symbol:
                header += f" ({symbol})"

            with st.expander(header):
                # Compact meta line
                meta = []
                if cat: meta.append(f"**Category:** {cat}")
                if action: meta.append(f"**Action:** {action}")
                if meta:
                    st.write(" | ".join(meta))

                if "Definition" in cols and pd.notna(row.get("Definition")):
                    st.markdown("**Definition**")
                    st.write(row["Definition"])

                if "Detailed Explanation" in cols and pd.notna(row.get("Detailed Explanation")):
                    st.markdown("**Detailed Explanation**")
                    st.write(row["Detailed Explanation"])

                if "AMJ Article Reference" in cols and pd.notna(row.get("AMJ Article Reference")):
                    st.markdown("**AMJ Article Reference**")
                    st.write(row["AMJ Article Reference"])

# ---- DESKTOP MODE: table + detail viewer ----
else:
    st.subheader("Table (desktop view)")
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=520)

    st.divider()
    st.subheader("🔍 Element details")

    if len(filtered) == 0:
        st.info("No matching elements. Adjust filters or search.")
    else:
        if "Element No" in cols and "Element Name" in cols:
            labels = filtered.apply(
                lambda r: f'{int(r["Element No"])} — {r["Element Name"]} ({r.get("Symbol","")})',
                axis=1
            ).tolist()
            pick = st.selectbox("Select an element", labels)
            picked_no = int(pick.split("—")[0].strip())
            row = filtered[filtered["Element No"] == picked_no].iloc[0]
        else:
            idx = st.number_input("Row (0-based index in filtered table)", 0, len(filtered) - 1, 0)
            row = filtered.iloc[int(idx)]

        st.markdown(f"### {row.get('Element Name','Element')} ({row.get('Symbol','')})")
        if "Category" in cols: st.write(f"**Category:** {row.get('Category','')}")
        if "Action" in cols: st.write(f"**Action:** {row.get('Action','')}")
        if "Definition" in cols:
            st.markdown("**Definition**")
            st.write(row.get("Definition",""))
        if "Detailed Explanation" in cols:
            st.markdown("**Detailed Explanation**")
            st.write(row.get("Detailed Explanation",""))
        if "AMJ Article Reference" in cols:
            st.markdown("**AMJ Article Reference**")
            st.write(row.get("AMJ Article Reference",""))
