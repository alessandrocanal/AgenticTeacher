from pydantic_settings import BaseSettings
from pydantic import Field, computed_field
from pathlib import Path
from typing import List
import json

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")

    # Read as raw string to avoid pydantic's pre-JSON parsing
    google_oauth_scopes_raw: str | None = Field(
        default=None, alias="GOOGLE_OAUTH_SCOPES"
    )

    google_credentials_path: str = Field(
        default=str(BASE_DIR / "credentials.json"), alias="GOOGLE_CREDENTIALS_PATH"
    )
    google_token_path: str = Field(
        default=str(BASE_DIR / "token.json"), alias="GOOGLE_TOKEN_PATH"
    )
    port: int = Field(default=8000, alias="PORT")

    @computed_field  # pydantic v2
    @property
    def google_oauth_scopes(self) -> List[str]:
        s = self.google_oauth_scopes_raw
        if not s:
            return DEFAULT_SCOPES
        s = s.strip()
        # Try JSON array first
        try:
            j = json.loads(s)
            if isinstance(j, list):
                return [str(x) for x in j]
        except Exception:
            pass
        # Fallback: comma-separated
        return [item.strip() for item in s.split(",") if item.strip()]

    # --- LLM (local) ---
    llm_provider: str = Field(default="stub", alias="LLM_PROVIDER")  # stub | openai_compat
    # OpenAI-compatible (LM Studio / llama-cpp / vLLM)
    openai_base_url: str = Field(default="http://127.0.0.1:1234/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="llama3.1-8b-instruct", alias="OPENAI_MODEL")
    openai_api_key: str = Field(default="lm-studio", alias="OPENAI_API_KEY")

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        # IMPORTANT: avoid crashes when you add unrelated env vars
        "extra": "ignore",
    }

settings = Settings()
