from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.models.rubric import Rubric, RubricCriterion, RubricLevel
from app.models.submission import SubmissionBundle, SourceFile
from app.models.feedback import CriterionAssessment

# add a prompt builder that feeds the rubric + metrics + code snippets to the LLM (keeps context small and private)

MAX_CONTEXT_CHARS = 4000  # keep it small for 2k ctx servers

def _rubric_to_bullets(rubric: Rubric) -> str:
    lines = []
    for c in rubric.criteria[:8]:  # cap to keep things concise
        head = f"- {c.title}"
        sub = []
        for lv in c.levels[:5]:
            pts = ("" if lv.points is None else f" ({lv.points} pt)")
            sub.append(f"{lv.title}{pts}")
        if sub:
            head += f": livelli = " + " · ".join(sub)
        lines.append(head)
    return "\n".join(lines)

def _pick_representative_files(sources: List[SourceFile]) -> List[SourceFile]:
    # prefer main/entry/test + largest by LOC
    def score(s: SourceFile) -> int:
        rp = s.rel_path.lower()
        bonus = 0
        if "readme" in rp: bonus += 50
        if "main." in rp or "app." in rp or "program." in rp: bonus += 40
        if "test" in rp or "spec" in rp: bonus += 30
        return bonus + min(500, s.loc)
    # de-duplicate by rel_path
    seen = set()
    ranked = []
    for sf in sources:
        if sf.rel_path not in seen:
            seen.add(sf.rel_path)
            ranked.append(sf)
    ranked.sort(key=score, reverse=True)
    return ranked[:5]  # at most 5 snippets

def _clip(text: str, max_chars: int) -> str:
    if len(text) <= max_chars: return text
    head = int(max_chars * 0.7)
    tail = max_chars - head
    return text[:head] + "\n...\n" + text[-tail:]

def build_llm_context(
    rubric: Rubric,
    bundle: SubmissionBundle,
    assessments: List[CriterionAssessment] | None,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    rubric_txt = _rubric_to_bullets(rubric)

    # Make a tiny file list + snippets
    sources = []
    for a in bundle.artifacts:
        sources.extend(a.source_files)
    chosen = _pick_representative_files(sources)

    snippets = []
    remaining = MAX_CONTEXT_CHARS
    for sf in chosen:
        header = f"// {sf.rel_path} [{sf.language}] LOC={sf.loc}\n"
        budget = max(200, int(remaining / (len(chosen)-len(snippets) or 1)))
        body = _clip(sf.content, max(100, budget - len(header)))
        chunks = header + body
        snippets.append(chunks)
        remaining -= len(chunks)
        if remaining <= 0:
            break

    # Optional: include current chosen levels (so feedback is aligned)
    chosen_levels = []
    if assessments:
        for ca in assessments:
            chosen_levels.append(f"- {ca.criterion_title}: {ca.chosen_level_title}")

    prompt = (
        "Sei un insegnante di informatica di un istituto tecnico ad indirizzo informatico.\n"
        "Compito: fornisci un feedback sintetico e concreto (massimo 6 frasi) sul progetto dello studente, "
        "seguendo la rubrica indicata. Evita lodi generiche; dai suggerimenti operativi.\n\n"
        "RUBRICA:\n" + rubric_txt + "\n\n"
        "METRICHE:\n"
        f"- File totali: {metrics.get('file_count')}  LOC: {metrics.get('total_loc')}\n"
        f"- Linguaggi: {metrics.get('lang_summary')}\n"
        f"- README: {'sì' if metrics.get('has_readme') else 'no'}  Test: {'sì' if metrics.get('has_tests') else 'no'}\n"
    )
    if chosen_levels:
        prompt += "Livelli selezionati (provvisori):\n" + "\n".join(chosen_levels) + "\n"

    prompt += "\nFRAMMENTI DI CODICE (solo per contesto, non riscrivere il codice):\n"
    prompt += "\n\n".join(snippets)

    instructions = (
        "Rispondi in ITALIANO con:\n"
        "• 3–6 frasi mirate legate ai criteri della rubrica.\n"
        "• 2–4 suggerimenti pratici (bullet) alla fine.\n"
        "Non inventare funzionalità non presenti; se mancano test/README, suggeriscilo."
    )

    return {
        "prompt": prompt,
        "instructions": instructions,
        "metrics": metrics,
    }
