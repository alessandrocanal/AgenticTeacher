from __future__ import annotations
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.clients.classroom import list_teacher_courses, list_teacher_coursework
from app.repositories.results_repo import memory_results_repo
from app.services.rubric_loader import load_rubric_from_classroom
from app.services.extraction import build_submission_bundles
from app.services.evaluation import assess_with_rubric
from app.llm.provider import LLMStub

templates = Jinja2Templates(directory="app/ui/templates")
router = APIRouter()

def _get_proposal(course_id: str, coursework_id: str, submission_id: str):
    items = memory_results_repo.list_all(course_id, coursework_id)
    for it in items:
        if it.submission_id == submission_id:
            return it
    return None

@router.get("/", include_in_schema=False)
def home_redirect():
    return RedirectResponse(url="/start", status_code=307)

@router.get("/start", response_class=HTMLResponse)
def start_page(request: Request):
    courses = list_teacher_courses()
    return templates.TemplateResponse(
        "start.html",
        {"request": request, "courses": courses}
    )

@router.get("/review/ajax/courseworks", response_class=HTMLResponse)
def ajax_courseworks(course_id: str):
    """Returns <option>...</option> snippets for the coursework select (HTMX)."""
    works = list_teacher_coursework(course_id)
    if not works:
        # return a single disabled option
        html = '<option value="" disabled selected>Nessun compito trovato</option>'
        return HTMLResponse(html)
    options = ['<option value="" disabled selected>Seleziona un compito…</option>']
    for w in works:
        title = (w.get("title") or f"ID {w.get('id')}")
        options.append(f'<option value="{w["id"]}">{title}</option>')
    return HTMLResponse("\n".join(options))

@router.post("/start/go")
def start_go(course_id: str = Form(...), coursework_id: str = Form(...)):
    # land on the review list for that assignment
    return RedirectResponse(url=f"/review/{course_id}/{coursework_id}", status_code=303)

@router.get("/review/{course_id}/{coursework_id}", response_class=HTMLResponse)
def review_list(request: Request, course_id: str, coursework_id: str):
    proposals = memory_results_repo.list_all(course_id, coursework_id)
    return templates.TemplateResponse(
        "review_list.html",
        {"request": request, "course_id": course_id, "coursework_id": coursework_id, "proposals": proposals},
    )

@router.post("/review/{course_id}/{coursework_id}/ingest")
def review_ingest(course_id: str, coursework_id: str):
    # Build proposals end-to-end from within the web process
    rubric = load_rubric_from_classroom(course_id, coursework_id)
    if not rubric:
        raise HTTPException(400, "Nessuna rubrica trovata su questo compito.")
    bundles = build_submission_bundles(course_id, coursework_id)
    llm = LLMStub()
    for b in bundles:
        pe = assess_with_rubric(rubric, b, llm=llm)
        memory_results_repo.save(pe)
    return RedirectResponse(url=f"/review/{course_id}/{coursework_id}", status_code=303)

@router.get("/review/{course_id}/{coursework_id}/{submission_id}", response_class=HTMLResponse)
def review_detail(request: Request, course_id: str, coursework_id: str, submission_id: str):
    pe = _get_proposal(course_id, coursework_id, submission_id)
    if not pe:
        raise HTTPException(404, "Proposta non trovata. Hai eseguito l’ingest?")
    rubric = load_rubric_from_classroom(course_id, coursework_id)
    if not rubric:
        raise HTTPException(400, "Rubrica non disponibile.")
    # Build a map criterion_id/title → selected level id/title
    selected = {}
    for ca in pe.criteria:
        selected[ca.criterion_id or ca.criterion_title] = ca.chosen_level_title  # we’ll match by title

    return templates.TemplateResponse(
        "review_detail.html",
        {
            "request": request,
            "course_id": course_id,
            "coursework_id": coursework_id,
            "submission_id": submission_id,
            "pe": pe,
            "rubric": rubric,
            "selected": selected,
        },
    )

@router.post("/review/{course_id}/{coursework_id}/{submission_id}/save")
async def review_save(request: Request, course_id: str, coursework_id: str, submission_id: str):
    pe = _get_proposal(course_id, coursework_id, submission_id)
    if not pe:
        raise HTTPException(404, "Proposta non trovata.")
    rubric = load_rubric_from_classroom(course_id, coursework_id)
    if not rubric:
        raise HTTPException(400, "Rubrica non disponibile.")

    form = await request.form()
    overall = form.get("overall_comment_it", "").strip()

    # Update per-criterion selection by matching on criterion id (if present) else title
    new_criteria = []
    total_points = 0.0
    max_points = 0.0

    # Build a quick lookup to the existing CriterionAssessment to preserve rationale (we’ll replace it anyway)
    old_by_key = {}
    for ca in pe.criteria:
        old_by_key[ca.criterion_id or ca.criterion_title] = ca

    for c in rubric.criteria:
        key = c.id or c.title
        chosen_label = form.get(f"crit_{key}")  # radio value is level title
        # Fallback: if nothing sent (shouldn’t happen), keep previous
        if not chosen_label and key in old_by_key:
            chosen_label = old_by_key[key].chosen_level_title

        # Find the level by title
        chosen_level = None
        c_max = None
        for lv in c.levels:
            if lv.title == chosen_label:
                chosen_level = lv
            if lv.points is not None:
                c_max = max(c_max or 0.0, lv.points)

        if chosen_level is None:
            # If no match by title, default to first level
            chosen_level = c.levels[0]

        pts = chosen_level.points if (chosen_level.points is not None) else None
        if c_max is not None:
            max_points += c_max
            if pts is not None:
                total_points += pts

        new_criteria.append({
            "criterion_id": c.id,
            "criterion_title": c.title,
            "chosen_level_title": chosen_level.title,
            "points_awarded": pts,
            "max_points": c_max,
            "rationale": old_by_key.get(key).rationale if key in old_by_key else "",
        })

    pe.criteria = [type(pe.criteria[0])(**x) for x in new_criteria] if pe.criteria else []
    pe.overall_comment_it = overall
    pe.max_points = (max_points if max_points else None)
    pe.total_points = (total_points if max_points else None)

    memory_results_repo.save(pe)
    return RedirectResponse(url=f"/review/{course_id}/{coursework_id}/{submission_id}", status_code=303)
