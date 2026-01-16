import pandas as pd
import streamlit as st
from urllib.parse import urlencode

# ---------- Page ----------
st.set_page_config(page_title="Research Elements Explorer", layout="centered")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 980px;}
h1 {font-size: 1.6rem;}
.small {font-size: 0.9rem; opacity: 0.85;}
.pill {display:inline-block; padding: 0.25rem 0.6rem; border-radius: 999px; background:#f2f3f5; margin-right:0.4rem; margin-bottom:0.35rem;}
</style>
""", unsafe_allow_html=True)

st.title("🧪 Research Elements Explorer")
st.caption("Search, filter, bookmark, compare, and share direct links to any element (AMJ-based).")

# ---------- Data ----------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    return df

DATA_FILE = "final_element_sheet.xlsx"
df = load_data(DATA_FILE)
cols = df.columns.tolist()

# Helpful column detection (keeps your sheet flexible)
def col_exists(name): return name in cols

NUM = "Element No" if col_exists("Element No") else None
NAME = "Element Name" if col_exists("Element Name") else cols[0]
SYM = "Symbol" if col_exists("Symbol") else None
CAT = "Category" if col_exists("Category") else None
ACT = "Action" if col_exists("Action") else None
DEF = "Definition" if col_exists("Definition") else None
DEXP = "Detailed Explanation" if col_exists("Detailed Explanation") else None
REF = "AMJ Article Reference" if col_exists("AMJ Article Reference") else None

# ---------- State ----------
if "favorites" not in st.session_state:
    st.session_state.favorites = set()
if "compare" not in st.session_state:
    st.session_state.compare = set()

# ---------- Sidebar ----------
st.sidebar.header("View")
mobile_mode = st.sidebar.toggle("📱 Mobile mode", value=True)
show_insights = st.sidebar.toggle("📊 Show insights", value=True)

st.sidebar.header("Search & Filters")
search = st.sidebar.text_input("Search", placeholder="e.g., 12, RP, theory, sampling...").strip()

# Quick filters (chips) in sidebar
def multiselect_all(label, series):
    vals = sorted(series.dropna().astype(str).unique().tolist())
    chosen = st.multiselect(label, vals, default=vals)
    return vals, chosen

cat_vals = chosen_cats = None
act_vals = chosen_actions = None

if CAT:
    cat_vals, chosen_cats = multiselect_all("Category", df[CAT])
if ACT:
    act_vals, chosen_actions = multiselect_all("Action", df[ACT])

chosen_range = None
if NUM and pd.api.types.is_numeric_dtype(df[NUM]):
    min_no = int(df[NUM].min())
    max_no = int(df[NUM].max())
    chosen_range = st.sidebar.slider("Element No range", min_no, max_no, (min_no, max_no))

st.sidebar.divider()

# ---------- Apply filters ----------
filtered = df.copy()

if CAT and chosen_cats is not None:
    filtered = filtered[filtered[CAT].astype(str).isin(chosen_cats)]
if ACT and chosen_actions is not None:
    filtered = filtered[filtered[ACT].astype(str).isin(chosen_actions)]
if chosen_range is not None and NUM:
    filtered = filtered[(filtered[NUM] >= chosen_range[0]) & (filtered[NUM] <= chosen_range[1])]

# Smart search: boost exact matches on Element No or Symbol or Name
def smart_search(df_in: pd.DataFrame, q: str) -> pd.DataFrame:
    ql = q.lower()
    if not ql:
        return df_in

    # exact number match
    exact_num = pd.Series([False]*len(df_in), index=df_in.index)
    if NUM:
        try:
            n = int(ql)
            exact_num = df_in[NUM].astype("Int64") == n
        except:
            pass

    exact_sym = pd.Series([False]*len(df_in), index=df_in.index)
    if SYM:
        exact_sym = df_in[SYM].astype(str).str.lower().eq(ql)

    exact_name = df_in[NAME].astype(str).str.lower().eq(ql)

    # broad contains
    contains = df_in.apply(lambda r: r.astype(str).str.lower().str.contains(ql, na=False).any(), axis=1)

    out = df_in[contains].copy()
    if len(out) == 0:
        return out

    # score
    score = (
        exact_num.loc[out.index].astype(int) * 100
        + exact_sym.loc[out.index].astype(int) * 80
        + exact_name.loc[out.index].astype(int) * 60
    )
    out["_score"] = score.values
    out = out.sort_values(by=["_score"] + ([NUM] if NUM else []), ascending=[False] + ([True] if NUM else []))
    out = out.drop(columns=["_score"])
    return out

filtered = smart_search(filtered, search)

# Sort default
if NUM and pd.api.types.is_numeric_dtype(filtered[NUM]):
    filtered = filtered.sort_values(NUM)

# ---------- Top bar: stats + actions ----------
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
c1.metric("Total", len(df))
c2.metric("Showing", len(filtered))
c3.metric("Favorites", len(st.session_state.favorites))
c4.metric("Compare", len(st.session_state.compare))

st.write("")  # spacing

# Buttons row
b1, b2, b3 = st.columns([1, 1, 1])

with b1:
    if st.button("🎲 Random element", use_container_width=True):
        if len(filtered) > 0:
            pick_row = filtered.sample(1).iloc[0]
            # store in query params for deep link style behavior
            if NUM:
                st.query_params["el"] = str(int(pick_row[NUM]))
            else:
                st.query_params["el"] = str(pick_row[NAME])

with b2:
    if st.button("⭐ Show favorites", use_container_width=True):
        st.query_params["view"] = "favorites"

with b3:
    if st.button("🧾 Compare selected", use_container_width=True):
        st.query_params["view"] = "compare"

# ---------- Insights ----------
if show_insights and (CAT or ACT):
    st.markdown("### 📊 Quick insights")
    ic1, ic2 = st.columns(2)
    if CAT:
        with ic1:
            st.caption("Top Categories")
            top = filtered[CAT].astype(str).value_counts().head(6)
            for k, v in top.items():
                st.markdown(f"<span class='pill'>{k} · {v}</span>", unsafe_allow_html=True)
    if ACT:
        with ic2:
            st.caption("Top Actions")
            top = filtered[ACT].astype(str).value_counts().head(6)
            for k, v in top.items():
                st.markdown(f"<span class='pill'>{k} · {v}</span>", unsafe_allow_html=True)

st.divider()

# ---------- Views ----------
view = st.query_params.get("view", "")

# Helper to build a shareable link for an element
def element_share_link(val: str) -> str:
    # Streamlit Cloud will preserve query params in the URL
    qp = {"el": val}
    return "?" + urlencode(qp)

def row_key(row):
    if NUM:
        return str(int(row[NUM]))
    return str(row[NAME])

# Deep link: open an element directly if ?el= is present
deep_el = st.query_params.get("el", None)

def render_detail(row):
    # Stacked layout = mobile-friendly
    header = f"{row.get(NUM,'')} — {row.get(NAME,'')}"
    if SYM and pd.notna(row.get(SYM)):
        header += f" ({row.get(SYM)})"
    st.markdown(f"## {header}")

    meta = []
    if CAT and pd.notna(row.get(CAT)): meta.append(f"**Category:** {row.get(CAT)}")
    if ACT and pd.notna(row.get(ACT)): meta.append(f"**Action:** {row.get(ACT)}")
    if meta:
        st.write(" | ".join(meta))

    if DEF and pd.notna(row.get(DEF)):
        st.markdown("### Definition")
        st.write(row.get(DEF))

    if DEXP and pd.notna(row.get(DEXP)):
        st.markdown("### Detailed Explanation")
        st.write(row.get(DEXP))

    if REF and pd.notna(row.get(REF)):
        st.markdown("### AMJ Article Reference")
        st.write(row.get(REF))

    st.divider()

# If deep link provided, show that element first
if deep_el:
    match = None
    if NUM:
        try:
            n = int(str(deep_el).strip())
            m = df[df[NUM].astype("Int64") == n]
            if len(m) > 0:
                match = m.iloc[0]
        except:
            pass
    if match is None:
        # try match by name
        m = df[df[NAME].astype(str) == str(deep_el)]
        if len(m) > 0:
            match = m.iloc[0]

    if match is not None:
        st.info("Opened via shareable link ✅")
        render_detail(match)

# Favorites view
if view == "favorites":
    st.subheader("⭐ Favorites")
    fav_rows = df[df.apply(lambda r: row_key(r) in st.session_state.favorites, axis=1)]
    if len(fav_rows) == 0:
        st.warning("No favorites yet. Tap ⭐ on any element to save it here.")
    else:
        for _, row in fav_rows.sort_values(NUM) .iterrows() if NUM else fav_rows.iterrows():
            key = row_key(row)
            title = f"{row.get(NUM,'')} — {row.get(NAME,'')}"
            with st.expander(title):
                st.write(f"Share link: `{element_share_link(key)}`")
                render_detail(row)

    st.stop()

# Compare view
if view == "compare":
    st.subheader("🧾 Compare")
    if len(st.session_state.compare) < 2:
        st.warning("Select at least 2 elements to compare (tap ➕ Compare inside an element card).")
        st.stop()

    comp_rows = df[df.apply(lambda r: row_key(r) in st.session_state.compare, axis=1)]
    if NUM:
        comp_rows = comp_rows.sort_values(NUM)

    # Mobile = stacked, Desktop = columns
    if mobile_mode or len(comp_rows) > 3:
        for _, row in comp_rows.iterrows():
            st.markdown("---")
            render_detail(row)
    else:
        cols_ui = st.columns(len(comp_rows))
        for i, (_, row) in enumerate(comp_rows.iterrows()):
            with cols_ui[i]:
                st.markdown(f"### {row.get(NUM,'')} — {row.get(NAME,'')}")
                if CAT: st.write(f"**Category:** {row.get(CAT,'')}")
                if ACT: st.write(f"**Action:** {row.get(ACT,'')}")
                if DEF: st.write(row.get(DEF,""))
    st.stop()

# ---------- Main results list ----------
st.subheader("Results")

if len(filtered) == 0:
    st.info("No matching elements. Adjust filters or search.")
else:
    # Mobile-friendly cards
    if mobile_mode:
        for _, row in filtered.iterrows():
            key = row_key(row)

            title = f"{row.get(NUM,'')} — {row.get(NAME,'')}"
            if SYM and pd.notna(row.get(SYM)):
                title += f" ({row.get(SYM)})"

            with st.expander(title):
                # mini meta
                meta = []
                if CAT and pd.notna(row.get(CAT)): meta.append(f"**Category:** {row.get(CAT)}")
                if ACT and pd.notna(row.get(ACT)): meta.append(f"**Action:** {row.get(ACT)}")
                if meta:
                    st.write(" | ".join(meta))

                # quick buttons row
                cA, cB, cC = st.columns(3)
                with cA:
                    fav = key in st.session_state.favorites
                    if st.button("⭐ Favorite" if not fav else "✅ Favorited", key=f"fav_{key}", use_container_width=True):
                        if fav:
                            st.session_state.favorites.remove(key)
                        else:
                            st.session_state.favorites.add(key)
                        st.rerun()

                with cB:
                    comp = key in st.session_state.compare
                    if st.button("➕ Compare" if not comp else "➖ Remove", key=f"cmp_{key}", use_container_width=True):
                        if comp:
                            st.session_state.compare.remove(key)
                        else:
                            st.session_state.compare.add(key)
                        st.rerun()

                with cC:
                    st.code(element_share_link(key), language="text")

                if DEF and pd.notna(row.get(DEF)):
                    st.markdown("**Definition**")
                    st.write(row.get(DEF))
                if DEXP and pd.notna(row.get(DEXP)):
                    st.markdown("**Detailed Explanation**")
                    st.write(row.get(DEXP))
                if REF and pd.notna(row.get(REF)):
                    st.markdown("**AMJ Article Reference**")
                    st.write(row.get(REF))

    # Desktop view: show table + click-to-open
    else:
        st.dataframe(filtered, use_container_width=True, hide_index=True, height=520)

st.divider()
st.caption("Tip: Share any element by sending the link with `?el=<ElementNo>` (for example: `?el=12`).")
