from fastapi import FastAPI
from .logging import configure_logging

logger = configure_logging()
app = FastAPI(title="Classroom Agent")

@app.get("/health")
def health():
    logger.info("Health check hit")
    return {"status": "ok"}
