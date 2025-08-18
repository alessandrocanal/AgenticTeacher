from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class RubricLevel(BaseModel):
    id: Optional[str] = None        # Classroom levelId if available
    title: str
    descriptor: Optional[str] = None
    points: Optional[float] = None  # None means unscored rubric

class RubricCriterion(BaseModel):
    id: Optional[str] = None        # Classroom criterionId if available
    title: str
    description: Optional[str] = None
    weight: float = 1.0
    levels: List[RubricLevel]

class Rubric(BaseModel):
    id: Optional[str] = None        # Classroom rubric id if available
    source: str                     # "classroom" | "csv" | "xlsx" | "pdf" | "sheets"
    course_id: Optional[str] = None
    coursework_id: Optional[str] = None
    title: Optional[str] = None
    criteria: List[RubricCriterion]
