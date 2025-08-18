from fastapi import FastAPI
from .logging import configure_logging
from app.ui.routes import router as ui_router   # <-- this must import cleanly

logger = configure_logging()
app = FastAPI(title="Classroom Agent")

@app.get("/health")
def health():
    return {"status": "ok"}

# Mount UI routes (no prefix)
app.include_router(ui_router)

# (temporary) Log the routes at startup to verify:
for r in app.routes:
    try:
        logger.info(f"Route: {r.path}  methods={getattr(r,'methods',{})}")
    except Exception:
        pass

