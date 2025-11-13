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
.stMultiSelect [data-baseweb="tag"] {
    background-color: #e5e7eb !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
}
</style>
""", unsafe_allow_html=True)

app_root = Path(__file__).resolve().parents[1]
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

# add derived columns
blobs_df = blobs_df.copy()
blobs_df["status"] = blobs_df["name"].map(infer_status_from_name)
blobs_df["timestamp"] = blobs_df["name"].map(name_to_dt)


# ---- sidebar filters ----
with st.sidebar:
    st.header("Filters")

    # status filter
    status_options = ["pass", "fail"]
    selected_status = st.multiselect(
        "Status", options=status_options, default=status_options
    )

    # date filter
    ts_only = blobs_df.dropna(subset=["timestamp"])
    date_range = None
    if ts_only.empty:
        st.caption("No timestamps found in filenames.")
    else:
        min_dt, max_dt = ts_only["timestamp"].min(), ts_only["timestamp"].max()
        default = (min_dt.date(), max_dt.date())

        date_input = st.date_input("Date range", default)

        if isinstance(date_input, tuple) and len(date_input) == 2:
            start_date, end_date = date_input
        elif isinstance(date_input, date):
            start_date = end_date = date_input
        else:
            start_date, end_date = default

        date_range = (start_date, end_date)


# ---- apply filters ----
filtered = blobs_df[blobs_df["status"].isin(selected_status)].copy()

if date_range:
    start_dt = datetime.combine(date_range[0], datetime.min.time())
    end_dt   = datetime.combine(date_range[1], datetime.max.time())
    has_ts = filtered["timestamp"].notna()

    filtered = pd.concat(
        [
            filtered[~has_ts],
            filtered[has_ts & filtered["timestamp"].between(start_dt, end_dt)]
        ],
        ignore_index=True
    )

filtered = filtered.sort_values(
    by=["timestamp", "name"], ascending=[False, True], na_position="last"
).reset_index(drop=True)

if filtered.empty:
    st.info("No files match filters.")
    st.stop()


# ---- selector ----
# ---- selector ----
selected = st.selectbox(
    "Select a file",
    options=filtered["name"].tolist(),
    key="selected_file",
    format_func=lambda x: f"{status_icon(infer_status_from_name(x))} {x}"
)

# Force rerun whenever the user changes the file selection
if "previous_file" not in st.session_state:
    st.session_state.previous_file = selected

if selected != st.session_state.previous_file:
    st.session_state.previous_file = selected
    st.rerun()


# ---- details section ----
if selected:
    try:
        df = read_csv_blob(container, selected)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        st.stop()

    if df.empty:
        st.warning("This CSV has no rows.")
    else:
        record = df.iloc[0].to_dict()

        # pull special fields off first
        message_text = record.pop("message", None)
        failed_raw   = record.pop("failed", "")

        # ---- show validation message ABOVE table ----
        if message_text:
            st.markdown("#### Validation Message")
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    padding: 8px 10px;
                    background-color: #ffffff;
                    white-space: pre-wrap;
                    font-family: system-ui, sans-serif;
                    font-size: 0.9rem;
                ">
                    {message_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ---- Extracted data section ----
        st.markdown("### Extracted Data")

        # build error list
        if isinstance(failed_raw, str):
            error_list = [
                e.strip() for e in failed_raw.split("|")
                if e.strip() and e.strip().upper() != "PASS"
            ]
        else:
            error_list = []

        error_lower = [e.lower() for e in error_list]

        # ---- derive flags ----
        wrong_form_flag = any("wrong form" in e for e in error_lower)
        surgeon_flag    = any("surgeon" in e for e in error_lower)
        fit_flag        = any("positive fit" in e for e in error_lower)
        other_flag      = any("other condition" in e for e in error_lower)

        vertical_df = pd.DataFrame(list(record.items()), columns=["Field", "Value"])

        def highlight_errors(row):
            field_name = str(row["Field"])

            # ALL fields red for wrong form
            if wrong_form_flag:
                return ["background-color: #fee2e2"] * len(row)

            # surgeon routing issue
            if surgeon_flag and field_name in [
                "Refer to Next Available Surgeon",
                "Refer to Specific Hospital or Surgeon"
            ]:
                return ["background-color: #fee2e2"] * len(row)

            # Positive FIT issue
            if fit_flag and field_name in [
                "Positive FIT",
                "Reason for Ineligibility"
            ]:
                return ["background-color: #fee2e2"] * len(row)

            # Other Condition issue
            if other_flag and field_name in [
                "Other Condition Check",
                "Other Condition"
            ]:
                return ["background-color: #fee2e2"] * len(row)

            # default: no highlight, match length of row
            return [""] * len(row)


        styled = vertical_df.style.apply(highlight_errors, axis=1)
        st.dataframe(styled, use_container_width=True)

    # download button
    st.download_button(
        "Download this CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=selected.split("/")[-1],
        mime="text/csv",
        use_container_width=True
    )
