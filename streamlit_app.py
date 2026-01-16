import pandas as pd
import streamlit as st

st.set_page_config(page_title="Research Elements Explorer", layout="wide")

st.title("🧪 Research Elements Explorer")
st.caption("Interactive viewer for the Periodic Table of Research Elements (AMJ-based). Search, filter, and open any element for details.")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

DATA_FILE = "final_element_sheet.xlsx"
df = load_data(DATA_FILE)
cols = df.columns.tolist()

# Sidebar filters
st.sidebar.header("Filters")

search = st.sidebar.text_input("Search (any field)", placeholder="e.g., RP, theory, sampling, integrity...").strip()

# Category filter
chosen_cats = None
if "Category" in cols:
    cat_vals = sorted(df["Category"].dropna().astype(str).unique().tolist())
    chosen_cats = st.sidebar.multiselect("Category", cat_vals, default=cat_vals)

# Action filter (DO/TH/ME etc.)
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

# Apply filters
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

# Top metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total elements", len(df))
c2.metric("Showing", len(filtered))
if "Category" in cols and chosen_cats is not None:
    c3.metric("Categories selected", len(chosen_cats))

st.divider()

st.subheader("Table")
st.dataframe(filtered, use_container_width=True, hide_index=True)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download filtered results (CSV)", data=csv_bytes,
                   file_name="filtered_research_elements.csv", mime="text/csv")

st.divider()

st.subheader("🔍 Element details")
if len(filtered) == 0:
    st.info("No matching elements. Adjust filters or search.")
else:
    # Pick element
    if "Element No" in cols and "Element Name" in cols:
        labels = filtered.apply(
            lambda r: f'{int(r["Element No"])} — {r["Element Name"]} ({r.get("Symbol","")})',
            axis=1
        ).tolist()
        pick = st.selectbox("Select an element", labels)
        picked_no = int(pick.split("—")[0].strip())
        row = filtered[filtered["Element No"] == picked_no].iloc[0]
    else:
        idx = st.number_input("Row (0-based index in filtered table)", 0, len(filtered)-1, 0)
        row = filtered.iloc[int(idx)]

    left, right = st.columns([1, 2])

    with left:
        if "Element No" in cols: st.markdown(f'**Element No:** {row["Element No"]}')
        if "Element Name" in cols: st.markdown(f'**Element Name:** {row["Element Name"]}')
        if "Symbol" in cols: st.markdown(f'**Symbol:** {row["Symbol"]}')
        if "Category" in cols: st.markdown(f'**Category:** {row["Category"]}')
        if "Action" in cols: st.markdown(f'**Action:** {row["Action"]}')

    with right:
        if "Definition" in cols:
            st.markdown("### Definition")
            st.write(row["Definition"])
        if "Detailed Explanation" in cols:
            st.markdown("### Detailed Explanation")
            st.write(row["Detailed Explanation"])
        if "AMJ Article Reference" in cols:
            st.markdown("### AMJ Article Reference")
            st.write(row["AMJ Article Reference"])

    with st.expander("Show raw record"):
        st.json({c: (None if pd.isna(row[c]) else str(row[c])) for c in cols})
