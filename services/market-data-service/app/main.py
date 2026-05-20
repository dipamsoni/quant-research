from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.redis import close_redis, init_redis
from app.scheduler import register_jobs, scheduler
from app.ws.connection_manager import PriceBus
from app.api.v1.assets import router as assets_router
from app.api.v1.candles import router as candles_router
from app.api.v1.news import router as news_router
from app.api.v1.price import router as price_router
from app.api.v1.watchlist import router as watchlist_router
from app.ws.router import router as ws_router

configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", environment=settings.ENVIRONMENT, version=settings.VERSION)
    app.state.price_bus = PriceBus()
    await init_redis()
    register_jobs()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
    await close_redis()
    logger.info("shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        content: dict[str, Any] = {"error": exc.detail}
    else:
        content = {"error": {"code": "ERROR", "message": str(exc.detail)}}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": exc.errors(),
            }
        },
    )


app.include_router(ws_router)
app.include_router(assets_router)
app.include_router(candles_router)
app.include_router(price_router)
app.include_router(news_router)
app.include_router(watchlist_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
