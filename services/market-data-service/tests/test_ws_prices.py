"""Tests for WS /ws/prices endpoint.

Uses httpx-ws (async ASGI transport) so publish() and receive() run in the
same event loop — no threading issues with asyncio.Queue.
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from httpx_ws import aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport
from jose import jwt

from app.core.config import settings
from app.main import app
from app.ws.connection_manager import PriceBus

_TICK = {"type": "tick", "symbol": "RELIANCE", "price": "2850.45", "ts": "2026-05-20T12:00:00Z"}


def _make_token(user_id: str = "test-user-1") -> str:
    return jwt.encode(
        {"sub": user_id, "email": "test@example.com", "role": "user"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


@pytest.fixture(autouse=True)
def inject_price_bus() -> PriceBus:
    """Replace app.state.price_bus with a fresh one for each test."""
    bus = PriceBus()
    app.state.price_bus = bus
    return bus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=ASGIWebSocketTransport(app=app),
        base_url="http://test",
    )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


async def test_ws_no_auth_rejected():
    """Connection without token must be closed with code 4001."""
    async with _async_client() as client:
        with pytest.raises(Exception):
            async with aconnect_ws("/ws/prices?symbols=RELIANCE", client):
                pass  # server closes before/during accept


async def test_ws_invalid_token_rejected():
    """Garbage token must be closed with code 4001."""
    async with _async_client() as client:
        with pytest.raises(Exception):
            async with aconnect_ws("/ws/prices?symbols=RELIANCE&token=notavalidjwt", client):
                pass


async def test_ws_header_auth_accepted():
    """Authorization: Bearer header must be accepted."""
    token = _make_token()
    async with _async_client() as client:
        async with aconnect_ws(
            "/ws/prices?symbols=RELIANCE",
            client,
            headers={"Authorization": f"Bearer {token}"},
        ) as ws:
            # Connected — send close from our side
            await ws.close()


async def test_ws_query_token_accepted():
    """?token= fallback must be accepted (browser WebSocket support)."""
    token = _make_token()
    async with _async_client() as client:
        async with aconnect_ws(f"/ws/prices?symbols=RELIANCE&token={token}", client) as ws:
            await ws.close()


# ---------------------------------------------------------------------------
# Tick delivery
# ---------------------------------------------------------------------------


async def test_ws_receives_published_tick(inject_price_bus: PriceBus):
    """Tick published to PriceBus must arrive at subscribed WS client."""
    token = _make_token()
    async with _async_client() as client:
        async with aconnect_ws(f"/ws/prices?symbols=RELIANCE&token={token}", client) as ws:
            inject_price_bus.publish("RELIANCE", _TICK)
            raw = await asyncio.wait_for(ws.receive_text(), timeout=2.0)
            msg = json.loads(raw)
            assert msg["type"] == "tick"
            assert msg["symbol"] == "RELIANCE"
            assert msg["price"] == "220.45"


async def test_ws_no_tick_for_unsubscribed_symbol(inject_price_bus: PriceBus):
    """Tick for a symbol the client did NOT subscribe to must not arrive."""
    token = _make_token()
    async with _async_client() as client:
        async with aconnect_ws(f"/ws/prices?symbols=RELIANCE&token={token}", client) as ws:
            inject_price_bus.publish("TCS", _TICK)  # client subscribed only to RELIANCE
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(ws.receive_text(), timeout=0.3)


async def test_ws_multi_symbol_subscription(inject_price_bus: PriceBus):
    """Client subscribed to multiple symbols receives ticks for each."""
    token = _make_token()
    async with _async_client() as client:
        async with aconnect_ws(f"/ws/prices?symbols=RELIANCE,TCS&token={token}", client) as ws:
            inject_price_bus.publish("RELIANCE", {**_TICK, "symbol": "RELIANCE"})
            inject_price_bus.publish("TCS", {**_TICK, "symbol": "TCS"})

            received = set()
            for _ in range(2):
                raw = await asyncio.wait_for(ws.receive_text(), timeout=2.0)
                received.add(json.loads(raw)["symbol"])

            assert received == {"RELIANCE", "TCS"}


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------


async def test_ws_server_sends_ping(inject_price_bus: PriceBus):
    """Server must send {"type":"ping"} after PING_INTERVAL with no ticks.

    We monkey-patch _PING_INTERVAL to 0.1s so the test runs fast.
    """
    import app.ws.router as ws_router_mod

    original = ws_router_mod._PING_INTERVAL
    ws_router_mod._PING_INTERVAL = 0.1
    try:
        token = _make_token()
        async with _async_client() as client:
            async with aconnect_ws(f"/ws/prices?symbols=RELIANCE&token={token}", client) as ws:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=2.0)
                msg = json.loads(raw)
                assert msg == {"type": "ping"}
                # Reply with pong to keep connection healthy
                await ws.send_text(json.dumps({"type": "pong"}))
    finally:
        ws_router_mod._PING_INTERVAL = original


# ---------------------------------------------------------------------------
# Sequence number / replay
# ---------------------------------------------------------------------------


async def test_publish_stamps_seq(inject_price_bus: PriceBus):
    """publish() must add a monotonically increasing 'seq' field to every tick."""
    inject_price_bus.publish("RELIANCE", {**_TICK})
    inject_price_bus.publish("RELIANCE", {**_TICK})
    buf = list(inject_price_bus._buffer["RELIANCE"])
    assert buf[0]["seq"] < buf[1]["seq"]


async def test_get_missed_returns_ticks_after_seq(inject_price_bus: PriceBus):
    """get_missed() must only return ticks with seq > since_seq."""
    inject_price_bus.publish("RELIANCE", {**_TICK})
    inject_price_bus.publish("RELIANCE", {**_TICK})
    inject_price_bus.publish("RELIANCE", {**_TICK})

    buf = list(inject_price_bus._buffer["RELIANCE"])
    pivot_seq = buf[1]["seq"]  # after second tick

    missed = inject_price_bus.get_missed(["RELIANCE"], since_seq=pivot_seq)
    assert len(missed) == 1
    assert missed[0]["seq"] == buf[2]["seq"]


async def test_ws_replays_missed_ticks_on_reconnect(inject_price_bus: PriceBus):
    """Client connecting with ?seq=N must receive all buffered ticks with seq > N."""
    token = _make_token()

    # Publish 3 ticks before client connects.
    for i in range(3):
        inject_price_bus.publish("RELIANCE", {**_TICK, "price": str(200 + i)})

    buf = list(inject_price_bus._buffer["RELIANCE"])
    # Simulate client last saw seq of first tick.
    last_seen = buf[0]["seq"]

    async with _async_client() as client:
        async with aconnect_ws(
            f"/ws/prices?symbols=RELIANCE&token={token}&seq={last_seen}", client
        ) as ws:
            # Expect 2 replayed ticks (seq > last_seen).
            replayed = []
            for _ in range(2):
                raw = await asyncio.wait_for(ws.receive_text(), timeout=2.0)
                replayed.append(json.loads(raw))

            assert len(replayed) == 2
            assert all(t["seq"] > last_seen for t in replayed)
            # Must be in seq order.
            assert replayed[0]["seq"] < replayed[1]["seq"]


async def test_ws_no_replay_without_seq_param(inject_price_bus: PriceBus):
    """Client connecting without ?seq must not receive pre-buffered ticks."""
    token = _make_token()

    inject_price_bus.publish("RELIANCE", {**_TICK})
    inject_price_bus.publish("RELIANCE", {**_TICK})

    async with _async_client() as client:
        async with aconnect_ws(f"/ws/prices?symbols=RELIANCE&token={token}", client) as ws:
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(ws.receive_text(), timeout=0.3)


async def test_ws_stale_connection_closed(inject_price_bus: PriceBus):
    """Server must close connection when no pong received within PONG_TIMEOUT."""
    import app.ws.router as ws_router_mod

    original_ping = ws_router_mod._PING_INTERVAL
    original_pong = ws_router_mod._PONG_TIMEOUT
    # Force: ping every 0.05s, pong timeout at 0.1s — so after ~2 pings without
    # a pong the connection should be closed.
    ws_router_mod._PING_INTERVAL = 0.05
    ws_router_mod._PONG_TIMEOUT = 0.1
    try:
        token = _make_token()
        async with _async_client() as client:
            async with aconnect_ws(f"/ws/prices?symbols=RELIANCE&token={token}", client) as ws:
                # Receive ping but DON'T reply — wait for server to close
                await asyncio.wait_for(ws.receive_text(), timeout=2.0)
                # Server should close with 4008 after pong timeout elapses
                await asyncio.sleep(0.2)
                # Next receive should raise (connection closed by server)
                with pytest.raises(Exception):
                    await asyncio.wait_for(ws.receive_text(), timeout=1.0)
    finally:
        ws_router_mod._PING_INTERVAL = original_ping
        ws_router_mod._PONG_TIMEOUT = original_pong
