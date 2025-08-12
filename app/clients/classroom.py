from typing import List, Dict, Any
from .google_auth import classroom_client

def list_courses() -> List[Dict[str, Any]]:
    svc = classroom_client()
    resp = svc.courses().list().execute()
    return resp.get("courses", [])

def list_coursework(course_id: str) -> List[Dict[str, Any]]:
    svc = classroom_client()
    resp = svc.courses().courseWork().list(courseId=course_id).execute()
    return resp.get("courseWork", [])

def list_submissions(course_id: str, coursework_id: str) -> List[Dict[str, Any]]:
    svc = classroom_client()
    resp = svc.courses().courseWork().studentSubmissions().list(
        courseId=course_id, courseWorkId=coursework_id
    ).execute()
    return resp.get("studentSubmissions", [])
