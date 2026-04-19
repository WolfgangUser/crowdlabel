"""
CrowdLabel — главный файл приложения FastAPI.
12-factor Factor XI: логи в stdout через loguru.
"""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.endpoints import annotations, auth, datasets, tasks, users
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Платформа краудсорсинговой разметки данных для ML",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS (Factor VII — Port binding) ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request logging (Factor XI) ─────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    logger.info(
        "method={} path={} status={} duration={:.3f}s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


# ─── Routers ─────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(tasks.router, prefix=PREFIX)
app.include_router(annotations.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(datasets.router, prefix=PREFIX)


# ─── Health ──────────────────────────────────────────────────────────────────
@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.on_event("startup")
async def startup():
    logger.info("🚀 {} v{} starting in {} mode", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
