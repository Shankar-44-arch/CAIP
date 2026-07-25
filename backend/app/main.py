"""
CAIP-Karnataka — FastAPI Application Entrypoint
Simplified lifespan: PostgreSQL only, optional Redis.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.db import check_db_connection, close_redis

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("caip_karnataka")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 %s starting up (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    yield
    logger.info("🛑 Shutting down")
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Karnataka Crime Intelligence Platform — built on real NCRB district-level "
        "IPC crime data (2013) and the official Karnataka Police FIR schema. "
        "See /docs and docs/DATA_LIMITATIONS.md for what is and isn't supported."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.onrender\.com|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["System"])
async def health_check():
    db_ok = await check_db_connection()
    return {"status": "healthy" if db_ok else "degraded", "database": db_ok, "version": settings.APP_VERSION}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "data_limitations": "See docs/DATA_LIMITATIONS.md in the repository.",
    }
