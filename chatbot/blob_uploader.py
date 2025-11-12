# services/blob_uploader.py
import io
from datetime import datetime
from typing import Dict
import pandas as pd
import streamlit as st
from azure.storage.blob import BlobServiceClient

def _dict_to_csv_bytes(data: Dict) -> bytes:
    """Convert a dictionary to CSV bytes."""
    df = pd.DataFrame([data or {}])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def save_csv_to_blob(data: Dict, container: str = "filled-forms") -> str:
    """
    Save a single form dict as a CSV in Azure Blob Storage.
    Filename ends in _pass.csv or _fail.csv based on `validation_status`.
    Uses Azure connection from Streamlit secrets.
    """
    try:
        conn_str = st.secrets["AZURE_STORAGE_CONNECTION_STRING"]
    except KeyError:
        raise RuntimeError(
            "Missing AZURE_STORAGE_CONNECTION_STRING in Streamlit secrets.\n"
            "Go to your app → ⋯ → Edit secrets and add it there."
        )

    svc = BlobServiceClient.from_connection_string(conn_str)
    container_client = svc.get_container_client(container)

    # Create the container if it doesn't exist
    try:
        container_client.create_container()
    except Exception:
        pass  # ignore if already exists

    # Determine pass/fail tag
    status = str(data.get("validation_status", "")).lower()
    if status not in ("pass", "fail"):
        status = "fail"

    # Timestamp in UTC
    ts = datetime.utcnow()
    file_name = f"form_{ts:%Y-%m-%d_%H-%M-%S}_{status}.csv"

    csv_bytes = _dict_to_csv_bytes(data)
    container_client.upload_blob(name=file_name, data=csv_bytes, overwrite=True)

    return f"{container}/{file_name}"
