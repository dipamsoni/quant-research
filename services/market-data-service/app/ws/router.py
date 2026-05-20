"""WebSocket endpoint: WS /ws/prices?symbols=AAPL,TSLA

Auth strategy
-------------
Browser JS WebSocket() cannot send custom headers, so we support both:
  1. Authorization: Bearer <jwt>  (preferred — header not logged by most proxies)
  2. ?token=<jwt>                 (fallback for browser clients)
Header takes priority when both are present.

Heartbeat
---------
Server sends {"type":"ping"} every 30s. If no {"type":"pong"} received within
60s of the last pong, the connection is considered stale and closed (code 4008).

Notification
------------
Price ticks arrive via app.state.price_bus (PriceBus — asyncio.Queue fan-out).
No Redis pub/sub: single-process Phase 2, no cross-instance fan-out needed.
"""

from __future__ import annotations

import asyncio
import json
import time

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.core.config import settings
from app.ws.connection_manager import PriceBus

logger = structlog.get_logger()

router = APIRouter()

_PING_INTERVAL = 30.0  # seconds between server pings
_PONG_TIMEOUT = 60.0   # close if no pong received within this window


def _decode_ws_token(websocket: WebSocket, token: str | None) -> dict:
    """Extract and decode JWT from Authorization header or ?token= query param."""
    raw: str | None = None
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        raw = auth_header[7:]
    elif token:
        raw = token

    if not raw:
        raise PermissionError("Missing auth token")

    try:
        return jwt.decode(raw, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise PermissionError("Invalid or expired token") from exc


@router.websocket("/ws/prices")
async def ws_prices(
    websocket: WebSocket,
    symbols: str = Query(..., description="Comma-separated symbols, e.g. AAPL,TSLA,BTCUSDT"),
    token: str | None = Query(
        None,
        description="JWT bearer token (use when Authorization header is unavailable, e.g. browser WebSocket)",
    ),
    seq: int | None = Query(
        None,
        description="Last sequence number seen by client; server replays all missed ticks (seq > N) on connect.",
    ),
) -> None:
    # --- auth (before accept so unauthenticated clients never complete handshake) ---
    try:
        payload = _decode_ws_token(websocket, token)
    except PermissionError as exc:
        await websocket.close(code=4001, reason=str(exc))
        return

    user_id: str = payload.get("sub", "unknown")
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        await websocket.close(code=4000, reason="No valid symbols provided")
        return

    await websocket.accept()
    log = logger.bind(user_id=user_id, symbols=symbol_list)
    log.info("ws_prices_connected", replay_since=seq)

    price_bus: PriceBus = websocket.app.state.price_bus

    # --- replay missed ticks before subscribing to live feed ---
    if seq is not None:
        missed = price_bus.get_missed(symbol_list, since_seq=seq)
        for tick in missed:
            await websocket.send_text(json.dumps(tick))
        if missed:
            log.info("ws_prices_replayed", count=len(missed))

    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=256)
    price_bus.subscribe(symbol_list, queue)

    # Mutable single-element list so both tasks share the timestamp without a class.
    last_pong_at = [time.monotonic()]

    async def _send_loop() -> None:
        while True:
            tick = await queue.get()
            await websocket.send_text(json.dumps(tick))

    async def _recv_loop() -> None:
        try:
            while True:
                text = await websocket.receive_text()
                try:
                    msg = json.loads(text)
                    if isinstance(msg, dict) and msg.get("type") == "pong":
                        last_pong_at[0] = time.monotonic()
                except (json.JSONDecodeError, AttributeError):
                    pass  # ignore malformed frames
        except WebSocketDisconnect:
            pass  # client closed — let asyncio.wait(FIRST_COMPLETED) proceed

    async def _heartbeat_loop() -> None:
        """Periodically send pings and enforce pong timeout independent of queue activity."""
        while True:
            await asyncio.sleep(_PING_INTERVAL)
            if time.monotonic() - last_pong_at[0] > _PONG_TIMEOUT:
                log.info("ws_prices_stale_close")
                await websocket.close(code=4008, reason="Pong timeout")
                return
            await websocket.send_text(json.dumps({"type": "ping"}))

    send_task = asyncio.create_task(_send_loop(), name=f"ws-send-{user_id}")
    recv_task = asyncio.create_task(_recv_loop(), name=f"ws-recv-{user_id}")
    heartbeat_task = asyncio.create_task(_heartbeat_loop(), name=f"ws-hb-{user_id}")

    try:
        _done, pending = await asyncio.wait(
            [send_task, recv_task, heartbeat_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
    finally:
        price_bus.unsubscribe(symbol_list, queue)
        log.info("ws_prices_disconnected")
