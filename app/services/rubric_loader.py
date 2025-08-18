from __future__ import annotations
from typing import Optional, Dict, Any, List
from loguru import logger
from app.clients.google_auth import classroom_client
from app.models.rubric import Rubric, RubricCriterion, RubricLevel

def load_rubric_from_classroom(course_id: str, coursework_id: str) -> Optional[Rubric]:
    """
    Returns the Classroom rubric (if present) as a Rubric model.
    There is at most one rubric per coursework.
    """
    svc = classroom_client()
    resp = svc.courses().courseWork().rubrics().list(
        courseId=course_id, courseWorkId=coursework_id
    ).execute()
    rubrics = resp.get("rubrics", [])
    if not rubrics:
        logger.info("No rubric on this coursework.")
        return None

    rb = rubrics[0]  # at most one
    # Shape is documented in the REST reference; be defensive as fields can be optional.
    # Typical structure:
    # {
    #   "id": "...",
    #   "criteria": [
    #       {"id":"c1","title":"...","description":"...","levels":[
    #           {"id":"l1","title":"...","description":"...","points":4.0}, ...
    #       ]}
    #   ]
    # }
    def map_level(l: Dict[str, Any]) -> RubricLevel:
        return RubricLevel(
            id=l.get("id"),
            title=l.get("title") or "",
            descriptor=l.get("description"),
            points=l.get("points"),
        )

    def map_criterion(c: Dict[str, Any]) -> RubricCriterion:
        levels = [map_level(l) for l in c.get("levels", [])]
        return RubricCriterion(
            id=c.get("id"),
            title=c.get("title") or "",
            description=c.get("description"),
            levels=levels,
        )

    criteria = [map_criterion(c) for c in rb.get("criteria", [])]
    return Rubric(
        id=rb.get("id"),
        source="classroom",
        course_id=course_id,
        coursework_id=coursework_id,
        criteria=criteria,
    )
