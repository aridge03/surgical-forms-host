# app.py
import io
import pandas as pd
import streamlit as st
from pathlib import Path
from PIL import Image

from chatbot.extract_text import extract_form_bytes
from chatbot.blob_uploader import save_csv_to_blob
from chatbot.openai_client import OpenAIClient
from chatbot.reply_generator import ReplyGenerator
from chatbot.sanity_check import data_sanity_check


st.set_page_config(
    page_title="Page Verifier",
    page_icon="✅",
    layout="wide"
)

# Logo + Title
logo_path = Path(__file__).parent / "cpe-government-of-alberta-logo.jpg"
if logo_path.exists():
    st.image(Image.open(logo_path), width=220)
st.title("Surgical Referral Form Assistant")

# State for last response
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_text" not in st.session_state:
    st.session_state.last_text = None
if "last_data" not in st.session_state:   # <-- keep the extracted fields for CSV / case update
    st.session_state.last_data = None

# ----- helpers -----
def dict_to_lines(d: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in (d or {}).items())

def badge(label: str) -> str:
    colors = {"PASS":"#16a34a","FAIL":"#dc2626"}
    lab = (label or "").upper()
    return f"<span style='background:{colors.get(lab, '#374151')};color:#fff;padding:6px 12px;border-radius:8px;font-weight:600'>{lab}</span>"

def dict_to_csv_bytes(d: dict) -> bytes:
    df = pd.DataFrame([d or {}])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def update_case_management(data: dict) -> bool:
    """Stub: replace with your real integration (e.g., Salesforce)."""
    # TODO: push `data` to your case management system
    return True

# ----- TOP RESULT WINDOW -----
st.subheader("Validation Result")
result_container = st.container()

with result_container:
    if st.session_state.last_result:
        st.markdown(badge(st.session_state.last_result), unsafe_allow_html=True)

        # Only show explanation when not PASS
        if st.session_state.last_result != "PASS":
            st.write(st.session_state.last_text)

        # If PASS, show CSV download + Update Case Management
    if st.session_state.last_data:
        status_tag = "pass" if st.session_state.last_result == "PASS" else "fail"

        # include the status_tag in CSV contents too
        data_with_status = dict(st.session_state.last_data)
        data_with_status["validation_status"] = status_tag.upper()

        csv_bytes = dict_to_csv_bytes(data_with_status)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "Download CSV",
                data=csv_bytes,
                file_name="surgical_form.csv",
                mime="text/csv",
                key="download_csv_btn",
                use_container_width=True
            )

        with col2:
            if st.button("Update Case Management", key="update_case_btn", use_container_width=True):
                try:
                    blob_path = save_csv_to_blob(data_with_status)
                    st.success(f"Case saved ✅\nBlob Path: {blob_path}")
                except Exception as e:
                    st.error(f"Could not save to case management: {e}")

    else:
        st.info("No validation yet. Upload a PDF below and click Validate.")


# ----- INPUT + VALIDATE BELOW -----
uploaded = st.file_uploader("Upload Surgical Referral PDF", type=["pdf"], key="upload_box")

if st.button("Validate"):
    if not uploaded:
        st.error("Please upload a PDF first.")
        st.stop()

    with st.spinner("Reading form..."):
        pdf_bytes = uploaded.read()
        data = extract_form_bytes(pdf_bytes)
       
    form_text = dict_to_lines(data)

    with st.spinner("Checking against rules..."):
        openai_client = OpenAIClient()
        generator = ReplyGenerator(openai_client)
        check = data_sanity_check(data)
        reply_text = generator.generate(form_text,check)

    # Determine PASS/FAIL/etc.
    first_word = (reply_text or "").strip().split(maxsplit=1)[0].upper()
    if first_word not in {"PASS", "FAIL"}:
        first_word = "FAIL"  # fallback if model forgets

    # Save to state so it stays visible at top
    st.session_state.last_result = first_word
    parts = reply_text.split(maxsplit=1)
    clean_text = parts[1] if len(parts) > 1 else ""
    st.session_state.last_text = clean_text.strip()
    st.session_state.last_data = data  # <-- store extracted fields for CSV & case update

    st.rerun()
