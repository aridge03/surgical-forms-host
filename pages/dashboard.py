# pages/Forms Browser.py
import streamlit as st
import pandas as pd
from chatbot.blob_reader import list_csv_blobs, read_csv_blob
from pathlib import Path
from PIL import Image
from datetime import datetime, date
import re

# ---------- helpers ----------
def infer_status_from_name(name: str) -> str:
    n = (name or "").lower()
    if "pass" in n:
        return "pass"
    if "fail" in n:
        return "fail"
    return "fail"  # your chosen default

def status_icon(status: str) -> str:
    return {"pass": "🟢", "fail": "🔴", "unknown": ""}.get(status, "")

# expects names like: form_YYYY-MM-DD_HH-MM-SS_pass.csv
TS_REGEX = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})")

def name_to_dt(name: str):
    m = TS_REGEX.search(name or "")
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H-%M-%S")
    except ValueError:
        return None

# ---------- UI ----------
st.set_page_config(page_title="Forms Dashboard", page_icon="📂", layout="wide")
st.markdown("""
<style>
/* Streamlit multiselect selected tag */
.stMultiSelect [data-baseweb="tag"] {
    background-color: #e5e7eb !important; /* soft grey */
    color: #111827 !important; /* dark text for readability */
    border: 1px solid #d1d5db !important; /* light grey border */
}
</style>
""", unsafe_allow_html=True)
app_root = Path(__file__).resolve().parents[1]  # one level up from /pages
logo_path = app_root / "cpe-government-of-alberta-logo.jpg"
if logo_path.exists():
    st.image(Image.open(logo_path), width=220)
st.title("Forms Dashboard")

# ---- load blobs ----
container = "filled-forms"
blobs_df = list_csv_blobs(container)

st.subheader("Open a form")
if blobs_df.empty:
    st.info("No files to open.")
    st.stop()

# derive status and timestamp from filename
blobs_df = blobs_df.copy()
blobs_df["status"] = blobs_df["name"].map(infer_status_from_name)
blobs_df["timestamp"] = blobs_df["name"].map(name_to_dt)

# ---- filters (sidebar) ----
# ---- filters (sidebar) ----
with st.sidebar:
    st.header("Filters")

    # status filter
    status_options = ["pass", "fail"]
    selected_status = st.multiselect(
        "Status",
        options=status_options,
        default=status_options
    )

    # date filter (based on filename timestamp)
    ts_only = blobs_df.dropna(subset=["timestamp"])
    date_range = None
    if ts_only.empty:
        st.caption("No timestamps detected in filenames; date filter disabled.")
    else:
        min_dt, max_dt = ts_only["timestamp"].min(), ts_only["timestamp"].max()
        start_default, end_default = min_dt.date(), max_dt.date()

        # SAFE: works for single date or range
        date_input_value = st.date_input(
            "Date range",
            (start_default, end_default)
        )

        if isinstance(date_input_value, tuple) and len(date_input_value) == 2:
            start_date, end_date = date_input_value
        elif isinstance(date_input_value, date):
            start_date = end_date = date_input_value
        else:
            start_date, end_date = start_default, end_default

        date_range = (start_date, end_date)

# apply filters
filtered = blobs_df[blobs_df["status"].isin(selected_status)].copy()

# Only apply date filter to rows that HAVE a timestamp; drop those without when a range is set
if date_range and filtered["timestamp"].notna().any():
    start_dt = datetime.combine(date_range[0], datetime.min.time())
    end_dt   = datetime.combine(date_range[1], datetime.max.time())
    has_ts = filtered["timestamp"].notna()
    filtered = filtered[has_ts & filtered["timestamp"].between(start_dt, end_dt)]


# apply filters
filtered = blobs_df[blobs_df["status"].isin(selected_status)].copy()

if date_range:
    start_dt = datetime.combine(date_range[0], datetime.min.time())
    end_dt   = datetime.combine(date_range[1], datetime.max.time())
    has_ts = filtered["timestamp"].notna()
    filtered = pd.concat(
        [
            filtered[~has_ts],  # keep files without timestamps
            filtered[has_ts & filtered["timestamp"].between(start_dt, end_dt)]
        ],
        ignore_index=True
    )

# sort newest first (then name)
filtered = filtered.sort_values(
    by=["timestamp", "name"],
    ascending=[False, True],
    na_position="last"
).reset_index(drop=True)

if filtered.empty:
    st.info("No files match the current filters.")
    st.stop()

# ---- selector ----
selected = st.selectbox(
    "Select a file",
    options=filtered["name"].tolist(),
    format_func=lambda x: f"{status_icon(infer_status_from_name(x))} {x}"
)

# ---- details ----
if selected:
    try:
        df = read_csv_blob(container, selected)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        st.stop()

    st.markdown("### Extracted Data")
    if df.empty:
        st.warning("This CSV has no rows.")
    else:
        record = df.iloc[0].to_dict()
        vertical_df = pd.DataFrame(list(record.items()), columns=["Field", "Value"])
        st.dataframe(vertical_df, use_container_width=True)

    st.download_button(
        "Download this CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=selected.split("/")[-1],
        mime="text/csv",
        use_container_width=True
    )
