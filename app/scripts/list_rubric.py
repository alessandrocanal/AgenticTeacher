from loguru import logger
from app.services.rubric_loader import load_rubric_from_classroom

def main():
    COURSE_ID = "789297213544"       # pick an assignment that has a rubric
    COURSEWORK_ID = "798836974753"

    rb = load_rubric_from_classroom(course_id=COURSE_ID, coursework_id=COURSEWORK_ID)
    if not rb:
        logger.info("No rubric found.")
        return

    logger.info(f"Rubric source={rb.source}, criteria={len(rb.criteria)}")
    for c in rb.criteria:
        logger.info(f"- {c.title} (levels={len(c.levels)}, weight={c.weight})")
        for lv in c.levels:
            pts = "" if lv.points is None else f" ({lv.points} pts)"
            logger.info(f"   • {lv.title}{pts} — {lv.descriptor or ''}")

if __name__ == "__main__":
    main()
