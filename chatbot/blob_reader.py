# services/blob_reader.py  (or chatbot/blob_reader.py)
import os
import io
from typing import Optional
import pandas as pd
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

CONN_ENV = "AZURE_STORAGE_CONNECTION_STRING"

def _svc() -> BlobServiceClient:
    conn = os.environ.get(CONN_ENV)
    if not conn:
        raise RuntimeError(f"Missing {CONN_ENV}")
    return BlobServiceClient.from_connection_string(conn)

def list_csv_blobs(container: str, prefix: Optional[str] = None) -> pd.DataFrame:
    """
    List CSV blobs in a container (optionally under a prefix).
    Returns a DataFrame with a single column: 'name'.
    No size/last_modified used.
    """
    client = _svc().get_container_client(container)

    # If container doesn't exist yet, return empty DF with expected column
    try:
        client.get_container_properties()
    except ResourceNotFoundError:
        return pd.DataFrame(columns=["name"])

    names = []
    try:
        for b in client.list_blobs(name_starts_with=prefix or ""):
            name = getattr(b, "name", "")
            if name and name.lower().endswith(".csv"):
                names.append({"name": name})
    except Exception:
        # Any unexpected error -> safe empty DF
        return pd.DataFrame(columns=["name"])

    df = pd.DataFrame(names, columns=["name"])
    if df.empty:
        return df

    # Optional: sort alphabetically by name (remove if you don't want sorting)
    df = df.sort_values("name", ascending=True).reset_index(drop=True)
    return df

def read_csv_blob(container: str, blob_name: str) -> pd.DataFrame:
    """
    Download a CSV blob and load it into a pandas DataFrame.
    """
    client = _svc().get_blob_client(container=container, blob=blob_name)
    stream = client.download_blob()
    buf = io.BytesIO(stream.readall())
    # If you have BOMs occasionally, use encoding='utf-8-sig' in read_csv
    return pd.read_csv(buf)
