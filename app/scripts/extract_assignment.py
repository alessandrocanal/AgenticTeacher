from loguru import logger
from app.services.extraction import build_submission_bundles

COURSE_ID = "***"
COURSEWORK_ID = "***" 

def main():
    bundles = build_submission_bundles(COURSE_ID, COURSEWORK_ID)
    for b in bundles:
        logger.info(f"Submission {b.submission_id} — {b.student_full_name or b.student_user_id}")
        for a in b.artifacts:
            if a.unzipped_dir:
                logger.info(f"  ZIP {a.original_name} -> {a.unzipped_dir} ({len(a.source_files)} source files)")
                for s in a.source_files[:5]:  # show a few
                    logger.info(f"     • {s.rel_path} [{s.language}] LOC={s.loc}")
            else:
                logger.info(f"  File {a.original_name} -> {a.storage_path}")

if __name__ == "__main__":
    main()
