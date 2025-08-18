from loguru import logger

from app.services.rubric_loader import load_rubric_from_classroom
from app.services.extraction import build_submission_bundles
from app.services.evaluation import assess_with_rubric
from app.repositories.results_repo import memory_results_repo
from app.llm.provider import LLMStub  # swap with your real provider later

COURSE_ID = "***"
COURSEWORK_ID = "***" 

def main():
    rb = load_rubric_from_classroom(COURSE_ID, COURSEWORK_ID)
    if not rb:
        logger.error("No rubric found on this coursework.")
        return

    bundles = build_submission_bundles(COURSE_ID, COURSEWORK_ID)
    llm = LLMStub()

    for b in bundles:
        pe = assess_with_rubric(rb, b, llm=llm)
        memory_results_repo.save(pe)
        # Console summary
        name = pe.student_full_name or pe.student_user_id or "Studente"
        logger.info(f"== {name} ==")
        if pe.max_points:
            logger.info(f"Punteggio: {pe.total_points}/{pe.max_points}")
        for ca in pe.criteria:
            pts = f" ({ca.points_awarded}/{ca.max_points})" if ca.max_points else ""
            logger.info(f"- {ca.criterion_title}: {ca.chosen_level_title}{pts}")
        logger.info(pe.overall_comment_it)
        logger.info("")

    logger.info("Done.")

if __name__ == "__main__":
    main()
