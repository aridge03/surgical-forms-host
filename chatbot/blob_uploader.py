# services/blob_uploader.py
import io
import os
from datetime import datetime
from typing import Dict
import pandas as pd
from azure.storage.blob import BlobServiceClient

DEFAULT_CONTAINER = os.environ.get("BLOB_CONTAINER_FORMS_PASSED", "filled-forms")

def _dict_to_csv_bytes(data: Dict) -> bytes:
    df = pd.DataFrame([data or {}])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def save_csv_to_blob(data: Dict, container: str = DEFAULT_CONTAINER) -> str:
    """
    Save a single form dict as a CSV in Azure Blob Storage.
    Filename ends in _pass.csv or _fail.csv based on `validation_status`.
    """

    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        raise RuntimeError("Missing AZURE_STORAGE_CONNECTION_STRING environment variable.")

    svc = BlobServiceClient.from_connection_string(conn_str)
    container_client = svc.get_container_client(container)

    try:
        container_client.create_container()
    except Exception:
        pass

    # Determine pass/fail tag
    status = str(data.get("validation_status", "")).lower()
    if status not in ("pass", "fail"):
        status = "fail"  # default: anything not a clean PASS gets tagged fail

    ts = datetime.utcnow()
    file_name = f"form_{ts:%Y-%m-%d_%H-%M-%S}_{status}.csv"  # <-- add suffix here

    csv_bytes = _dict_to_csv_bytes(data)
    container_client.upload_blob(name=file_name, data=csv_bytes, overwrite=True)

    return f"{container}/{file_name}"
