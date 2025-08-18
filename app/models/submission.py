from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List

class SourceFile(BaseModel):
    rel_path: str
    language: str
    content: str
    loc: int

class AttachmentArtifact(BaseModel):
    drive_file_id: str
    original_name: str
    mime_type: str
    storage_path: str                    # saved/exported file path
    text_path: Optional[str] = None      # extracted .txt path (non-zip case)
    extracted_text: Optional[str] = None # extracted text (non-zip case)
    unzipped_dir: Optional[str] = None   # folder where we unpacked the zip
    source_files: List[SourceFile] = Field(default_factory=list)

class SubmissionBundle(BaseModel):
    course_id: str
    coursework_id: str
    submission_id: str
    student_user_id: Optional[str] = None
    student_full_name: Optional[str] = None
    artifacts: List[AttachmentArtifact] = Field(default_factory=list)
