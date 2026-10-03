from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.routes.analysis import router as analysis_router
from app.routes.health import router as health_router
from app.routes.history import router as history_router
from app.routes.upload import router as upload_router
from app.routes.transcription import router as transcription_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="SATYA authenticity analysis API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(transcription_router, prefix="/api")
