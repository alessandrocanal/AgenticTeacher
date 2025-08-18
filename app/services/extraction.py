from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
from io import BytesIO

from loguru import logger
from pdfminer.high_level import extract_text as pdf_extract_text

from app.clients.google_auth import classroom_client
from app.clients import drive as drive_cli
from app.models.submission import AttachmentArtifact, SubmissionBundle

# Where we keep local artifacts
ARTIFACT_ROOT = Path(".artifacts")

# Best export for Google files → something we can score
GOOGLE_EXPORT_MAP = {
    "application/vnd.google-apps.document": ("text/plain", ".txt"),
    "application/vnd.google-apps.presentation": ("text/plain", ".txt"),   # slide text
    "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
    # fallbacks for other google-apps types if you meet them:
    "application/vnd.google-apps.drawing": ("application/pdf", ".pdf"),   # then OCR/parse if needed
}

TEXT_MIMES = {"text/plain", "text/csv", "text/markdown"}
PDF_MIME = "application/pdf"

def _safe_name(s: str) -> str:
    return "".join(ch for ch in s if ch.isalnum() or ch in (" ",".","-","_")).strip().replace(" ","_")

def _extract_text_from_bytes(mime: str, data: bytes) -> Optional[str]:
    if mime in TEXT_MIMES:
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return data.decode("latin-1", errors="ignore")
    if mime == PDF_MIME:
        try:
            return pdf_extract_text(BytesIO(data))
        except Exception as e:
            logger.warning(f"PDF text extraction failed: {e}")
            return None
    return None  # binaries (images/zip) → no text

def _materialize_google_file(file_id: str, meta: Dict[str, Any], out_base: Path) -> AttachmentArtifact:
    src_mime = meta["mimeType"]
    name = meta.get("name") or file_id
    export = GOOGLE_EXPORT_MAP.get(src_mime)
    if not export:
        # Unknown google-apps type → export PDF as a generic fallback
        export = ("application/pdf", ".pdf")
    target_mime, ext = export
    data = drive_cli.export_file(file_id, target_mime)
    stored_path = out_base.with_suffix(ext)
    drive_cli.save_bytes(stored_path, data)

    text = _extract_text_from_bytes(target_mime, data)
    text_path = None
    if text:
        text_path = out_base.with_suffix(".txt")
        text_path.write_text(text, encoding="utf-8")

    return AttachmentArtifact(
        drive_file_id=file_id,
        original_name=name,
        mime_type=target_mime,
        storage_path=str(stored_path),
        text_path=str(text_path) if text_path else None,
        extracted_text=text,
    )

def _materialize_regular_file(file_id: str, meta: Dict[str, Any], out_base: Path) -> AttachmentArtifact:
    name = meta.get("name") or file_id
    src_mime = meta["mimeType"]
    data = drive_cli.download_file(file_id)
    guessed_ext = Path(name).suffix or {
        PDF_MIME: ".pdf",
        "text/plain": ".txt",
        "text/csv": ".csv",
    }.get(src_mime, ".bin")
    stored_path = out_base.with_suffix(guessed_ext)
    drive_cli.save_bytes(stored_path, data)

    text = _extract_text_from_bytes(src_mime, data)
    text_path = None
    if text:
        text_path = out_base.with_suffix(".txt")
        text_path.write_text(text, encoding="utf-8")

    return AttachmentArtifact(
        drive_file_id=file_id,
        original_name=name,
        mime_type=src_mime,
        storage_path=str(stored_path),
        text_path=str(text_path) if text_path else None,
        extracted_text=text,
    )

def _iter_submission_attachments(sub: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pull driveFile attachments from a StudentSubmission record."""
    att = []
    asg = sub.get("assignmentSubmission", {})
    for a in asg.get("attachments") or []:
        df = a.get("driveFile")
        if df and df.get("id"):
            att.append({"id": df["id"], "name": df.get("title")})
    return att

def build_submission_bundles(course_id: str, coursework_id: str) -> List[SubmissionBundle]:
    """
    For each student submission, download/export attachments to .artifacts/<course>/<cw>/<submission>/<file>.
    Return structured bundles ready for evaluation.
    """
    svc = classroom_client()
    #cw = get_coursework(course_id,coursework_id)
    #logger.info(f"CourseWork {cw}")
    subs = svc.courses().courseWork().studentSubmissions().list(
        courseId=course_id, courseWorkId=coursework_id
    ).execute().get("studentSubmissions", [])

    # Build userId -> fullName map (best effort)
    name_map = {}
    try:
        roster = svc.courses().students().list(courseId=course_id).execute().get("students", [])
        name_map = {
            s.get("userId"): (s.get("profile", {}).get("name", {}) or {}).get("fullName")
            for s in roster
        }
    except Exception as e:
        logger.warning(f"Couldn't load roster names (ok to continue): {e}")

    bundles: List[SubmissionBundle] = []
    for sub in subs:
        submission_id = sub["id"]
        user_id = sub.get("userId")
        # Optional: resolve student's name (takes one extra API call per submission)
        name = name_map.get(user_id)
        if not name:
            try:
                prof = svc.userProfiles().get(userId=user_id).execute()  # <- correct method name
                name = (prof.get("name") or {}).get("fullName")
            except Exception:
                name = None

        base_dir = ARTIFACT_ROOT / _safe_name(course_id) / _safe_name(coursework_id) / _safe_name(name)
        artifacts: List[AttachmentArtifact] = []
        attachments = _iter_submission_attachments(sub)

        if not attachments:
            # You may want to also check additionalStudentMaterial, or links, etc.
            bundles.append(SubmissionBundle(
                course_id=course_id, coursework_id=coursework_id,
                submission_id=submission_id, student_user_id=user_id,
                student_full_name=name, artifacts=[]
            ))
            continue

        for i, drv in enumerate(attachments, start=1):
            fid = drv["id"]
            meta = drive_cli.get_meta(fid)
            out_base = base_dir / f"file_{i:02d}__{_safe_name(meta.get('name') or fid)}"

            if meta["mimeType"].startswith("application/vnd.google-apps."):
                art = _materialize_google_file(fid, meta, out_base)
            else:
                art = _materialize_regular_file(fid, meta, out_base)
            artifacts.append(art)

        bundles.append(SubmissionBundle(
            course_id=course_id, coursework_id=coursework_id,
            submission_id=submission_id, student_user_id=user_id,
            student_full_name=name, artifacts=artifacts
        ))

    logger.info(f"Prepared {len(bundles)} submission bundles")
    return bundles
