"""Integration tests for portfolio REST endpoints.

Requires a running PostgreSQL instance (same DATABASE_URL as settings).
Auth is bypassed via dependency_overrides in conftest.py.

Flow under test:
  create portfolio → BUY transaction → verify holdings → BUY again →
  verify avg price → SELL partial → verify reduced qty →
  verify allocation → verify metrics endpoint (empty then seeded)
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.dialects.postgresql import insert

from app.core.database import AsyncSessionLocal
from app.models.portfolio_metrics import PortfolioMetrics
from tests.integration.conftest import TEST_USER_ID, OTHER_USER_ID

ASSET_A = uuid.uuid4()
ASSET_B = uuid.uuid4()


# ---------------------------------------------------------------------------
# Happy-path flow (sequential within the class; order matters)
# ---------------------------------------------------------------------------


class TestPortfolioFlow:
    """Full create → transact → verify flow against a real DB."""

    portfolio_id: str = ""

    # ── 1. Create ────────────────────────────────────────────────────────────

    async def test_create_portfolio(self, client, cleanup_ids):
        resp = await client.post(
            "/api/v1/portfolio",
            json={"name": "Flow Test", "base_currency": "INR", "risk_profile": "moderate"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        p = body["data"]
        assert p["name"] == "Flow Test"
        assert p["base_currency"] == "INR"
        assert p["risk_profile"] == "moderate"
        assert p["user_id"] == str(TEST_USER_ID)
        TestPortfolioFlow.portfolio_id = p["id"]
        cleanup_ids.append(p["id"])

    # ── 2. List ──────────────────────────────────────────────────────────────

    async def test_list_includes_new_portfolio(self, client):
        resp = await client.get("/api/v1/portfolio")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["data"]]
        assert TestPortfolioFlow.portfolio_id in ids

    # ── 3. Detail before any transactions ────────────────────────────────────

    async def test_detail_empty_holdings(self, client):
        pid = TestPortfolioFlow.portfolio_id
        resp = await client.get(f"/api/v1/portfolio/{pid}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["holdings"] == []
        assert data["latest_metrics"] is None

    # ── 4. First BUY ─────────────────────────────────────────────────────────

    async def test_buy_transaction(self, client):
        pid = TestPortfolioFlow.portfolio_id
        resp = await client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(ASSET_A),
                "symbol": "RELIANCE",
                "transaction_type": "BUY",
                "quantity": "10",
                "price": "100.00",
                "fees": "0.50",
                "executed_at": "2026-01-10T10:00:00Z",
            },
        )
        assert resp.status_code == 201
        tx = resp.json()["data"]
        assert tx["transaction_type"] == "buy"
        assert tx["portfolio_id"] == pid
        assert Decimal(tx["quantity"]) == Decimal("10")

    # ── 5. Holdings visible after BUY ────────────────────────────────────────

    async def test_holdings_visible_after_buy(self, client):
        pid = TestPortfolioFlow.portfolio_id
        resp = await client.get(f"/api/v1/portfolio/{pid}")
        assert resp.status_code == 200
        holdings = resp.json()["data"]["holdings"]
        assert len(holdings) == 1
        h = holdings[0]
        assert uuid.UUID(h["asset_id"]) == ASSET_A
        assert float(h["quantity"]) == pytest.approx(10.0)
        assert float(h["avg_price"]) == pytest.approx(100.0)

    # ── 6. Second BUY — avg price recalculated ───────────────────────────────

    async def test_second_buy_updates_avg_price(self, client):
        pid = TestPortfolioFlow.portfolio_id
        # Buy 10 more at 120 → avg = (10*100 + 10*120) / 20 = 110
        await client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(ASSET_A),
                "symbol": "RELIANCE",
                "transaction_type": "BUY",
                "quantity": "10",
                "price": "120.00",
                "executed_at": "2026-01-11T10:00:00Z",
            },
        )
        resp = await client.get(f"/api/v1/portfolio/{pid}")
        holdings = resp.json()["data"]["holdings"]
        h = next(x for x in holdings if uuid.UUID(x["asset_id"]) == ASSET_A)
        assert float(h["quantity"]) == pytest.approx(20.0)
        assert float(h["avg_price"]) == pytest.approx(110.0)

    # ── 7. BUY a second asset ────────────────────────────────────────────────

    async def test_buy_second_asset(self, client):
        pid = TestPortfolioFlow.portfolio_id
        resp = await client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(ASSET_B),
                "symbol": "TCS",
                "transaction_type": "BUY",
                "quantity": "5",
                "price": "200.00",
                "executed_at": "2026-01-12T10:00:00Z",
            },
        )
        assert resp.status_code == 201

    # ── 8. Allocation reflects two assets ────────────────────────────────────

    async def test_allocation_two_assets(self, client):
        pid = TestPortfolioFlow.portfolio_id
        resp = await client.get(f"/api/v1/portfolio/{pid}/allocation")
        assert resp.status_code == 200
        body = resp.json()["data"]
        # ASSET_A: 20 * 110 = 2200; ASSET_B: 5 * 200 = 1000 → total 3200
        assert body["total_value"] == pytest.approx(3200.0)
        assert len(body["allocations"]) == 2
        asset_ids = {uuid.UUID(a["asset_id"]) for a in body["allocations"]}
        assert asset_ids == {ASSET_A, ASSET_B}
        total_pct = sum(a["pct"] for a in body["allocations"])
        assert total_pct == pytest.approx(100.0, abs=0.01)

    # ── 9. SELL partial ──────────────────────────────────────────────────────

    async def test_sell_partial(self, client):
        pid = TestPortfolioFlow.portfolio_id
        resp = await client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(ASSET_A),
                "symbol": "RELIANCE",
                "transaction_type": "SELL",
                "quantity": "5",
                "price": "130.00",
                "executed_at": "2026-01-15T10:00:00Z",
            },
        )
        assert resp.status_code == 201

        # Holdings should show 15 remaining
        resp = await client.get(f"/api/v1/portfolio/{pid}")
        holdings = resp.json()["data"]["holdings"]
        h = next(x for x in holdings if uuid.UUID(x["asset_id"]) == ASSET_A)
        assert float(h["quantity"]) == pytest.approx(15.0)

    # ── 10. Metrics endpoint — empty range ───────────────────────────────────

    async def test_metrics_empty(self, client):
        pid = TestPortfolioFlow.portfolio_id
        resp = await client.get(
            f"/api/v1/portfolio/{pid}/metrics",
            params={"from": "2026-01-01", "to": "2026-01-31"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    # ── 11. Metrics endpoint — seeded row via asyncpg ────────────────────────

    async def test_metrics_seeded_row(self, client):
        pid = TestPortfolioFlow.portfolio_id
        async with AsyncSessionLocal() as session:
            stmt = (
                insert(PortfolioMetrics)
                .values(
                    id=uuid.uuid4(),
                    portfolio_id=uuid.UUID(pid),
                    date=date(2026, 1, 20),
                    total_value=3500.0,
                    daily_return=0.015,
                    sharpe_ratio=1.2,
                    max_drawdown=-0.05,
                    volatility=0.18,
                    beta=0.9,
                    alpha=0.02,
                )
                .on_conflict_do_nothing(
                    constraint="uq_portfolio_metrics_portfolio_date"
                )
            )
            await session.execute(stmt)
            await session.commit()

        resp = await client.get(
            f"/api/v1/portfolio/{pid}/metrics",
            params={"from": "2026-01-01", "to": "2026-01-31"},
        )
        assert resp.status_code == 200
        rows = resp.json()["data"]
        assert len(rows) == 1
        assert rows[0]["total_value"] == pytest.approx(3500.0)
        assert rows[0]["sharpe_ratio"] == pytest.approx(1.2, abs=0.01)


# ---------------------------------------------------------------------------
# Authorization edge cases
# ---------------------------------------------------------------------------


class TestAuthorizationEdgeCases:
    async def test_other_user_cannot_access_portfolio(self, client, other_client, cleanup_ids):
        # Create a portfolio as TEST_USER
        resp = await client.post(
            "/api/v1/portfolio",
            json={"name": "Private Portfolio"},
        )
        assert resp.status_code == 201
        pid = resp.json()["data"]["id"]
        cleanup_ids.append(pid)

        # OTHER_USER tries to GET it
        resp = await other_client.get(f"/api/v1/portfolio/{pid}")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    async def test_other_user_cannot_add_transaction(self, client, other_client, cleanup_ids):
        resp = await client.post("/api/v1/portfolio", json={"name": "Protected"})
        pid = resp.json()["data"]["id"]
        cleanup_ids.append(pid)

        resp = await other_client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(uuid.uuid4()),
                "symbol": "RELIANCE",
                "transaction_type": "BUY",
                "quantity": "1",
                "price": "100",
            },
        )
        assert resp.status_code == 403

    async def test_get_nonexistent_portfolio_returns_404(self, client):
        resp = await client.get(f"/api/v1/portfolio/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Validation edge cases
# ---------------------------------------------------------------------------


class TestValidationEdgeCases:
    async def test_sell_insufficient_quantity_returns_422(self, client, cleanup_ids):
        resp = await client.post("/api/v1/portfolio", json={"name": "Validation Test"})
        pid = resp.json()["data"]["id"]
        cleanup_ids.append(pid)

        # BUY 1, then try to SELL 5
        await client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(ASSET_A),
                "symbol": "RELIANCE",
                "transaction_type": "BUY",
                "quantity": "1",
                "price": "100",
            },
        )
        resp = await client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(ASSET_A),
                "symbol": "RELIANCE",
                "transaction_type": "SELL",
                "quantity": "5",
                "price": "110",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "INSUFFICIENT_QUANTITY"

    async def test_invalid_transaction_type_returns_422(self, client, cleanup_ids):
        resp = await client.post("/api/v1/portfolio", json={"name": "Validation Test 2"})
        pid = resp.json()["data"]["id"]
        cleanup_ids.append(pid)

        resp = await client.post(
            f"/api/v1/portfolio/{pid}/transactions",
            json={
                "asset_id": str(uuid.uuid4()),
                "symbol": "RELIANCE",
                "transaction_type": "HOLD",
                "quantity": "1",
                "price": "100",
            },
        )
        assert resp.status_code == 422

    async def test_allocation_empty_portfolio_returns_zero(self, client, cleanup_ids):
        resp = await client.post("/api/v1/portfolio", json={"name": "Empty"})
        pid = resp.json()["data"]["id"]
        cleanup_ids.append(pid)

        resp = await client.get(f"/api/v1/portfolio/{pid}/allocation")
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert body["total_value"] == 0.0
        assert body["allocations"] == []
