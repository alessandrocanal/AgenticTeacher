from __future__ import annotations
from typing import Dict, Any

class LLMProvider:
    def draft_feedback_it(self, context: Dict[str, Any]) -> str:
        """Return an Italian feedback paragraph. Override in concrete providers."""
        raise NotImplementedError

class LLMStub(LLMProvider):
    def draft_feedback_it(self, context: Dict[str, Any]) -> str:
        met = context.get("metrics", {})
        lines = [
            "Feedback sintetico:",
            f"- Struttura del progetto: {met.get('file_count',0)} file, {met.get('lang_summary','')}",
            f"- Commenti nel codice: ~{int(100*met.get('comment_ratio',0))}%",
            f"- Presenza di test: {'sì' if met.get('has_tests') else 'no'}",
            f"- Documentazione: {'README trovato' if met.get('has_readme') else 'README mancante'}",
            "Suggerimenti:",
            "- Mantieni funzioni/metodi brevi e con nomi chiari.",
            "- Aggiungi test automatici almeno per i casi principali.",
            "- Scrivi un README con istruzioni di build/esecuzione."
        ]
        return "\n".join(lines)
