from __future__ import annotations
import os, httpx
from typing import Dict, Any
from .provider import LLMProvider

OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
OPENAI_MODEL  = os.getenv("OPENAI_MODEL",  "llama3.1-8b-instruct")

def _ensure_local():
    # safety: keep it local-only to avoid privacy leaks
    assert "localhost" in OPENAI_BASE or "127.0.0.1" in OPENAI_BASE, \
        f"Refusing to call non-local LLM endpoint: {OPENAI_BASE}"

class OpenAICompatProvider(LLMProvider):
    def draft_feedback_it(self, context: Dict[str, Any]) -> str:
        _ensure_local()
        prompt = context["prompt"] + "\n\n" + context["instructions"]
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "Sei un insegnante di informatica. Sii chiaro, conciso e costruttivo."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 320,
        }
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        r = httpx.post(f"{OPENAI_BASE}/chat/completions", json=payload, headers=headers, timeout=120)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
