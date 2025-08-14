# app/clients/google_auth.py
from __future__ import annotations
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from ..config import settings
from ..logging import configure_logging

logger = configure_logging()

def load_credentials() -> Credentials:
    token_path = Path(settings.google_token_path).expanduser().resolve()
    cred_path  = Path(settings.google_credentials_path).expanduser().resolve()

    #logger.info(f"Using credentials at: {cred_path}")
    #logger.info(f"Token path: {token_path}")

    creds: Credentials | None = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(token_path), scopes=settings.google_oauth_scopes
            )
        except Exception as e:
            logger.warning(f"Ignoring invalid token file at {token_path}: {e}")
            try:
                token_path.unlink()
            except Exception:
                pass
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing Google credentials…")
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Refresh failed, starting OAuth: {e}")
                creds = None

        if not creds:
            cfg = json.loads(cred_path.read_text(encoding="utf-8"))
            flow = InstalledAppFlow.from_client_config(
                cfg, scopes=settings.google_oauth_scopes
            )
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")
        logger.info(f"Saved token to {token_path}")

    return creds

def classroom_client():
    creds = load_credentials()
    return build("classroom", "v1", credentials=creds, cache_discovery=False)

def drive_client():
    creds = load_credentials()
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def docs_client():
    creds = load_credentials()
    return build("docs", "v1", credentials=creds, cache_discovery=False)

def sheets_client():
    creds = load_credentials()
    return build("sheets", "v4", credentials=creds, cache_discovery=False)

__all__ = [
    "load_credentials",
    "classroom_client",
    "drive_client",
    "docs_client",
    "sheets_client",
]
