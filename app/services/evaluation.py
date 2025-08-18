from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from collections import Counter

from loguru import logger
from app.models.rubric import Rubric, RubricCriterion, RubricLevel
from app.models.submission import SubmissionBundle, AttachmentArtifact, SourceFile
from app.models.feedback import ProposedEvaluation, CriterionAssessment
from app.llm.provider import LLMProvider, LLMStub

# ---------- metrics ----------
IGNORE_DIRS = {"node_modules", ".git", "venv", ".venv", "target", "build", "__pycache__"}

def _summarize_languages(sources: List[SourceFile]) -> Tuple[str, Counter]:
    cnt = Counter(s.language for s in sources)
    parts = [f"{k}:{v}" for k, v in cnt.most_common()]
    return ", ".join(parts), cnt

def _has_tests(sources: List[SourceFile]) -> bool:
    for s in sources:
        rp = s.rel_path.lower()
        if any(tok in rp for tok in ("test", "tests", "spec")):
            return True
        if s.language in {"python"} and rp.endswith((".py",)) and ("pytest" in s.content or "unittest" in s.content):
            return True
        if s.language in {"java"} and ("@Test" in s.content or "org.junit" in s.content):
            return True
        if s.language in {"cpp", "c"} and ("catch2" in s.content.lower() or "gtest" in s.content.lower()):
            return True
    return False

def _has_readme(artifact_dir: Optional[str]) -> bool:
    if not artifact_dir:
        return False
    d = Path(artifact_dir)
    for name in ("README.md","Readme.md","README","readme.md","readme"):
        if (d / name).exists():
            return True
    return False

def _comment_ratio(sources: List[SourceFile]) -> float:
    # naive per-language
    comment_lines = 0
    total = 0
    for s in sources:
        for line in s.content.splitlines():
            ls = line.strip()
            total += 1
            if not ls:
                continue
            if s.language in {"python", "python-notebook"}:
                if ls.startswith("#") or ls.startswith('"""') or ls.startswith("'''"):
                    comment_lines += 1
            elif s.language in {"java","kotlin","javascript","typescript","csharp","cpp","c"}:
                if ls.startswith("//") or ls.startswith("/*") or ls.startswith("*"):
                    comment_lines += 1
            else:
                if ls.startswith("#") or ls.startswith("//"):
                    comment_lines += 1
    return comment_lines / total if total else 0.0

def compute_metrics(bundle: SubmissionBundle) -> Dict[str, Any]:
    sources: List[SourceFile] = []
    artifact_root = None
    for a in bundle.artifacts:
        sources.extend(a.source_files)
        if a.unzipped_dir:
            artifact_root = a.unzipped_dir  # use first zip’s root for README check
    total_loc = sum(s.loc for s in sources)
    file_count = len(sources)
    lang_summary, lang_counter = _summarize_languages(sources)
    has_tests = _has_tests(sources)
    has_readme = _has_readme(artifact_root)
    comm_ratio = _comment_ratio(sources)
    avg_file_loc = (total_loc / file_count) if file_count else 0.0

    return {
        "file_count": file_count,
        "total_loc": total_loc,
        "avg_file_loc": avg_file_loc,
        "lang_summary": lang_summary,
        "lang_counter": lang_counter,
        "has_tests": has_tests,
        "has_readme": has_readme,
        "comment_ratio": comm_ratio,
    }

# ---------- rubric mapping ----------
def _sorted_levels_by_points(criterion: RubricCriterion) -> List[RubricLevel]:
    levels = list(criterion.levels)
    # if points missing, keep order; else sort ascending by points
    if any(l.points is not None for l in levels):
        levels.sort(key=lambda l: (l.points is None, l.points))
    return levels

def _pick_level_by_threshold(levels: List[RubricLevel], value: float, thresholds: List[float]) -> RubricLevel:
    """
    thresholds must have len = len(levels)-1, express cut points from low->high.
    """
    idx = 0
    for t in thresholds:
        if value > t:
            idx += 1
    idx = max(0, min(idx, len(levels)-1))
    return levels[idx]

def _assess_criterion(criterion: RubricCriterion, metrics: Dict[str, Any]) -> Tuple[RubricLevel, str]:
    title = criterion.title.lower()
    levels = _sorted_levels_by_points(criterion)
    # Default thresholds (low → high)
    # We try to infer intent by keywords (Italian/English)
    if any(k in title for k in ["correttezza","correctness","functionalità","funzionale"]):
        # Proxy: tests present + minimal size
        score = (1.0 if metrics["has_tests"] else 0.4) + (0.2 if metrics["file_count"]>=2 else 0.0)
        chosen = _pick_level_by_threshold(levels, score, [0.45, 0.75, 0.9][:max(0,len(levels)-1)])
        why = "Valutazione della correttezza basata su presenza di test e struttura minima del progetto."
        return chosen, why

    if any(k in title for k in ["qualità","stile","code quality","manutenibilità","leggibilità"]):
        # Proxy: comment ratio and avg file length
        cr = metrics["comment_ratio"]     # 0..1
        afl = metrics["avg_file_loc"]
        score = min(1.0, cr*1.2 + (0.3 if afl<=200 else 0.1))
        chosen = _pick_level_by_threshold(levels, score, [0.35, 0.6, 0.85][:max(0,len(levels)-1)])
        why = "Qualità del codice stimata da rapporto di commenti e dimensione media dei file."
        return chosen, why

    if any(k in title for k in ["documentazione","relazione","readme","report"]):
        score = 1.0 if metrics["has_readme"] else 0.3
        chosen = _pick_level_by_threshold(levels, score, [0.4, 0.7, 0.9][:max(0,len(levels)-1)])
        why = "Documentazione valutata dalla presenza del README e dalla chiarezza complessiva."
        return chosen, why

    if any(k in title for k in ["organizzazione","struttura","architettura","progettazione","design"]):
        # Proxy: multiple files + multiple languages penalized a bit (unless small)
        score = 0.3
        if metrics["file_count"] >= 3:
            score += 0.4
        if len(metrics["lang_counter"]) > 1 and metrics["total_loc"] > 150:
            score -= 0.1
        chosen = _pick_level_by_threshold(levels, score, [0.4, 0.7, 0.9][:max(0,len(levels)-1)])
        why = "Organizzazione del progetto stimata da numero di file e coerenza del linguaggio."
        return chosen, why

    if any(k in title for k in ["efficienza","performance","complessità"]):
        # Proxy: smaller avg file size + tests present hints at efficiency
        score = (0.2 if metrics["avg_file_loc"] < 150 else 0.05) + (0.3 if metrics["has_tests"] else 0.0)
        chosen = _pick_level_by_threshold(levels, score, [0.25, 0.5, 0.8][:max(0,len(levels)-1)])
        why = "Efficienza stimata in modo approssimativo da dimensioni e presenza test."
        return chosen, why

    # Fallback: mid level
    mid = levels[len(levels)//2]
    return mid, "Criterio non riconosciuto: assegnato livello intermedio come default."

def assess_with_rubric(rubric: Rubric, bundle: SubmissionBundle, llm: Optional[LLMProvider] = None) -> ProposedEvaluation:
    llm = llm or LLMStub()
    metrics = compute_metrics(bundle)

    crit_assessments: List[CriterionAssessment] = []
    total_points = 0.0
    max_points = 0.0

    for c in rubric.criteria:
        level, why = _assess_criterion(c, metrics)
        # find max points in criterion (highest level points if numeric)
        c_max = max((l.points for l in c.levels if l.points is not None), default=None)
        pts = None
        if level.points is not None:
            pts = level.points
            if c_max is not None:
                max_points += c_max
                total_points += pts
        crit_assessments.append(CriterionAssessment(
            criterion_id=c.id,
            criterion_title=c.title,
            chosen_level_title=level.title,
            points_awarded=pts,
            max_points=c_max,
            rationale=why
        ))

    ctx = {"metrics": metrics, "criteria": [c.model_dump() for c in crit_assessments]}
    overall = llm.draft_feedback_it(ctx)

    return ProposedEvaluation(
        course_id=bundle.course_id,
        coursework_id=bundle.coursework_id,
        submission_id=bundle.submission_id,
        student_user_id=bundle.student_user_id,
        student_full_name=bundle.student_full_name,
        total_points=(total_points if max_points else None),
        max_points=(max_points if max_points else None),
        overall_comment_it=overall,
        criteria=crit_assessments
    )
