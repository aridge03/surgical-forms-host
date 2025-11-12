# extract_text.py
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

load_dotenv()

ENDPOINT = os.getenv("AZURE_DOCINTEL_ENDPOINT")
KEY = os.getenv("AZURE_DOCINTEL_KEY")
MODEL_ID = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID")

if not (ENDPOINT and KEY and MODEL_ID):
    raise RuntimeError("Missing Azure env vars in .env")

_client = DocumentIntelligenceClient(ENDPOINT, AzureKeyCredential(KEY))


def _normalize_value(field: Optional[Dict[str, Any]]) -> str:
    """Convert Azure checkbox/selection output to Yes/No/Text."""
    if not field:
        return ""

    val = field.get("value")
    text = field.get("content")
    v = (str(val).strip() if val not in (None, "") else "")
    t = (str(text).strip() if text not in (None, "") else "")

    mapping = {
        ":selected:": "Yes", ":unselected:": "No",
        "selected": "Yes", "checked": "Yes", "true": "Yes", "yes": "Yes", "1": "Yes",
        "unselected": "No", "unchecked": "No", "false": "No", "no": "No", "0": "No"
    }

    if v.lower() in mapping: return mapping[v.lower()]
    if t.lower() in mapping: return mapping[t.lower()]
    return v or t


def extract_form_bytes(pdf_bytes: bytes) -> Dict[str, str]:
    """Main function: take PDF bytes, return dict of fields -> values."""
    req = AnalyzeDocumentRequest(bytes_source=pdf_bytes)
    poller = _client.begin_analyze_document(MODEL_ID, req)
    result = poller.result()

    data = {}
    if result.documents:
        doc = result.documents[0]
        for name, field in (doc.fields or {}).items():
            data[name] = _normalize_value({
                "value": getattr(field, "value", None),
                "content": getattr(field, "content", None)
            })
    return data


def extract_form_file(filepath: str) -> Dict[str, str]:
    """Convenience if you want to call with a file path instead of bytes."""
    file = Path(filepath)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(file, "rb") as f:
        return extract_form_bytes(f.read())
