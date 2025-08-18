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

def get_coursework(course_id: str, cw_id: str) -> List[Dict[str, Any]]:
    svc = classroom_client()
    resp = svc.courses().courseWork().get(courseId=course_id, id=cw_id).execute()
    return resp.get("courseWork", [])

def list_submissions(course_id: str, coursework_id: str) -> List[Dict[str, Any]]:
    svc = classroom_client()
    resp = svc.courses().courseWork().studentSubmissions().list(
        courseId=course_id, courseWorkId=coursework_id
    ).execute()
    return resp.get("studentSubmissions", [])

def list_teacher_courses() -> List[Dict[str, Any]]:
    svc = classroom_client()
    # Only active courses where you are the teacher
    resp = svc.courses().list(teacherId="me", courseStates=["ACTIVE"]).execute()
    courses = resp.get("courses", []) or []
    # nice ordering by name
    courses.sort(key=lambda c: c.get("name", ""))
    return courses

def list_teacher_coursework(course_id: str) -> List[Dict[str, Any]]:
    svc = classroom_client()
    resp = svc.courses().courseWork().list(courseId=course_id).execute()
    works = resp.get("courseWork", []) or []
    # newest first by creationTime, fallback to title
    works.sort(key=lambda w: (w.get("creationTime") or "", w.get("title") or ""), reverse=True)
    return works
