from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class CriterionAssessment(BaseModel):
    criterion_id: Optional[str] = None
    criterion_title: str
    chosen_level_title: str
    points_awarded: Optional[float] = None
    max_points: Optional[float] = None
    rationale: str

class ProposedEvaluation(BaseModel):
    course_id: str
    coursework_id: str
    submission_id: str
    student_user_id: Optional[str] = None
    student_full_name: Optional[str] = None
    total_points: Optional[float] = None
    max_points: Optional[float] = None
    overall_comment_it: str
    criteria: List[CriterionAssessment] = Field(default_factory=list)
