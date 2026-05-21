"""Reverse proxy: /api/v1/portfolio/* → portfolio-service.

Auth flow:
  1. Validate user's Bearer JWT (get_current_user hits DB for session check).
  2. Mint a short-lived service JWT carrying {sub, email, role} — no sid.
  3. Forward full request (body, query params, headers) to portfolio-service.
  4. Return upstream response unchanged.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from jose import jwt

from app.core.config import settings
from app.dependencies.auth import get_current_user
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter(tags=["portfolio-proxy"])

# Headers that must not be forwarded (hop-by-hop + ones we replace)
_DROP_REQ_HEADERS = frozenset({
    "host",
    "connection",
    "keep-alive",
    "transfer-encoding",
    "te",
    "trailers",
    "upgrade",
    "proxy-authenticate",
    "proxy-authorization",
    "authorization",   # replaced with service token below
    "content-length",  # httpx sets this
})

_DROP_RESP_HEADERS = frozenset({
    "connection",
    "keep-alive",
    "transfer-encoding",
    "content-encoding",
    "content-length",  # Response() recalculates
})


def _service_token(user: User) -> str:
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": datetime.now(UTC) + timedelta(seconds=settings.INTERNAL_TOKEN_EXP_SECONDS),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


async def _forward(path: str, request: Request, user: User) -> Response:
    target = f"{settings.PORTFOLIO_SERVICE_URL}/api/v1/portfolio"
    if path:
        target = f"{target}/{path}"

    fwd_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _DROP_REQ_HEADERS
    }
    fwd_headers["authorization"] = f"Bearer {_service_token(user)}"

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                method=request.method,
                url=target,
                headers=fwd_headers,
                content=body or None,
                params=dict(request.query_params),
            )
    except httpx.ConnectError:
        logger.error("portfolio_proxy_unreachable", target=target)
        raise HTTPException(
            status_code=503,
            detail={"code": "SERVICE_UNAVAILABLE", "message": "portfolio-service unreachable"},
        )
    except httpx.TimeoutException:
        logger.error("portfolio_proxy_timeout", target=target)
        raise HTTPException(
            status_code=504,
            detail={"code": "GATEWAY_TIMEOUT", "message": "portfolio-service timed out"},
        )

    resp_headers: dict[str, Any] = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in _DROP_RESP_HEADERS
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=resp_headers,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.api_route(
    "/api/v1/portfolio",
    methods=["GET", "POST"],
)
async def proxy_portfolio_root(
    request: Request,
    user: User = Depends(get_current_user),
) -> Response:
    return await _forward("", request, user)


@router.api_route(
    "/api/v1/portfolio/{rest:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_portfolio_path(
    rest: str,
    request: Request,
    user: User = Depends(get_current_user),
) -> Response:
    return await _forward(rest, request, user)
