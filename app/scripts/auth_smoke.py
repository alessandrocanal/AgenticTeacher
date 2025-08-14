from loguru import logger
from app.clients.classroom import list_courses, list_coursework, list_submissions


def main():
    logger.info("Fetching courses...")
    courses = list_courses()
    if not courses:
        logger.warning("No courses found. Are you using the teacher account?")
        return
    for c in courses:
        logger.info(f"[{c.get('id')}] {c.get('name')} - owner: {c.get('ownerId')}")
        cws = list_coursework(c.get('id'))
        logger.info(f"  Coursework: {len(cws)}")
        for cw in cws[:5]:
            logger.info(f"   - [{cw.get('id')}] {cw.get('title')}")
            subs = list_submissions(c.get('id'),cw.get('id'))
            for sub in subs[:5]:
                logger.info(f"       - [{sub.get('userId')}] - state: {sub.get('state')} - attachment: {sub.get('assignmentSubmission')}")

if __name__ == "__main__":
    main()
