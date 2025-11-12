# services/blob_reader.py  (or chatbot/blob_reader.py)
import io
from typing import Optional
import pandas as pd
import streamlit as st
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError


def _svc() -> BlobServiceClient:
    """
    Create a BlobServiceClient using the connection string from Streamlit secrets.
    """
    try:
        conn = st.secrets["AZURE_STORAGE_CONNECTION_STRING"]
    except KeyError:
        raise RuntimeError(
            "Missing AZURE_STORAGE_CONNECTION_STRING in Streamlit secrets.\n"
            "Go to your Streamlit app → ⋯ → Edit secrets and add:\n"
            'AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=...;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"'
        )
    return BlobServiceClient.from_connection_string(conn)


def list_csv_blobs(container: str, prefix: Optional[str] = None) -> pd.DataFrame:
    """
    List CSV blobs in a container (optionally under a prefix).
    Returns a DataFrame with a single column: 'name'.
    """
    client = _svc().get_container_client(container)

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
        return pd.DataFrame(columns=["name"])

    df = pd.DataFrame(names, columns=["name"])
    return df.sort_values("name", ascending=True).reset_index(drop=True) if not df.empty else df


def read_csv_blob(container: str, blob_name: str) -> pd.DataFrame:
    """
    Download a CSV blob and load it into a pandas DataFrame.
    """
    client = _svc().get_blob_client(container=container, blob=blob_name)
    stream = client.download_blob()
    buf = io.BytesIO(stream.readall())
    return pd.read_csv(buf)  # add encoding='utf-8-sig' if needed
