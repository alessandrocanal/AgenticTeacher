from __future__ import annotations
from typing import Dict, Any, Optional
from io import BytesIO
from pathlib import Path

from googleapiclient.http import MediaIoBaseDownload
from .google_auth import drive_client

# Metadata for a Drive file (name, mimeType, size)
def get_meta(file_id: str) -> Dict[str, Any]:
    svc = drive_client()
    fields = "id, name, mimeType, size"
    return svc.files().get(fileId=file_id, fields=fields).execute()

# Export a Google file (Docs/Slides/Sheets/etc.) to bytes of a target mime
def export_file(file_id: str, target_mime: str) -> bytes:
    svc = drive_client()
    data = svc.files().export(fileId=file_id, mimeType=target_mime).execute()
    return data

# Download a non-Google file by streaming to bytes
def download_file(file_id: str) -> bytes:
    svc = drive_client()
    request = svc.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return fh.getvalue()

# Save bytes to path (ensure parent exists)
def save_bytes(path: str | Path, data: bytes) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return str(p)
