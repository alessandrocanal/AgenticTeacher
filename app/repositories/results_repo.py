from __future__ import annotations
from typing import List, Dict
from app.models.feedback import ProposedEvaluation

class ResultsRepo:
    def save(self, pe: ProposedEvaluation) -> None:
        raise NotImplementedError
    def list_all(self, course_id: str, coursework_id: str) -> List[ProposedEvaluation]:
        raise NotImplementedError

class MemoryResultsRepo(ResultsRepo):
    def __init__(self):
        self._data: Dict[tuple, ProposedEvaluation] = {}

    def save(self, pe: ProposedEvaluation) -> None:
        key = (pe.course_id, pe.coursework_id, pe.submission_id)
        self._data[key] = pe

    def list_all(self, course_id: str, coursework_id: str) -> List[ProposedEvaluation]:
        return [
            v for (c, w, _), v in self._data.items()
            if c == course_id and w == coursework_id
        ]

# singleton for now
memory_results_repo = MemoryResultsRepo()
