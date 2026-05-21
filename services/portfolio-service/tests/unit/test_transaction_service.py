import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.transactions import (
    compute_avg_price,
    compute_realized_pnl,
    record_transaction,
)

PORTFOLIO_ID = uuid.uuid4()
ASSET_ID = uuid.uuid4()
NOW = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Pure calculation functions — no mocks, no async
# ---------------------------------------------------------------------------


class TestComputeAvgPrice:
    def test_equal_quantities(self) -> None:
        # 10 @ 100 + 10 @ 200 → avg = 150
        result = compute_avg_price(
            old_qty=Decimal("10"),
            old_avg=Decimal("100"),
            buy_qty=Decimal("10"),
            buy_price=Decimal("200"),
        )
        assert result == Decimal("150")

    def test_unequal_quantities_weighted(self) -> None:
        # 100 @ 50 + 50 @ 80 → avg = (5000+4000)/150 = 60
        result = compute_avg_price(
            old_qty=Decimal("100"),
            old_avg=Decimal("50"),
            buy_qty=Decimal("50"),
            buy_price=Decimal("80"),
        )
        assert result == Decimal("60")

    def test_buy_at_same_price_unchanged(self) -> None:
        result = compute_avg_price(
            old_qty=Decimal("5"),
            old_avg=Decimal("200"),
            buy_qty=Decimal("5"),
            buy_price=Decimal("200"),
        )
        assert result == Decimal("200")

    def test_small_decimal_precision(self) -> None:
        # 1 @ 100.5 + 2 @ 101 → avg = (100.5 + 202) / 3 = 100.8333...
        result = compute_avg_price(
            old_qty=Decimal("1"),
            old_avg=Decimal("100.5"),
            buy_qty=Decimal("2"),
            buy_price=Decimal("101"),
        )
        expected = (Decimal("1") * Decimal("100.5") + Decimal("2") * Decimal("101")) / Decimal(
            "3"
        )
        assert result == expected


class TestComputeRealizedPnl:
    def test_profitable_sell(self) -> None:
        result = compute_realized_pnl(
            avg_price=Decimal("100"),
            sell_price=Decimal("150"),
            qty_sold=Decimal("10"),
        )
        assert result == Decimal("500")

    def test_loss_sell(self) -> None:
        result = compute_realized_pnl(
            avg_price=Decimal("200"),
            sell_price=Decimal("150"),
            qty_sold=Decimal("5"),
        )
        assert result == Decimal("-250")

    def test_breakeven(self) -> None:
        result = compute_realized_pnl(
            avg_price=Decimal("100"),
            sell_price=Decimal("100"),
            qty_sold=Decimal("10"),
        )
        assert result == Decimal("0")

    def test_fractional_quantity(self) -> None:
        # 0.5 units, avg 200, sell at 220 → PnL = (220-200)*0.5 = 10
        result = compute_realized_pnl(
            avg_price=Decimal("200"),
            sell_price=Decimal("220"),
            qty_sold=Decimal("0.5"),
        )
        assert result == Decimal("10")


# ---------------------------------------------------------------------------
# record_transaction — mocked repos
# ---------------------------------------------------------------------------


def _mock_session(cash_balance: str = "0") -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    # Mock the Portfolio query for cash_balance update
    mock_portfolio = MagicMock()
    mock_portfolio.cash_balance = Decimal(cash_balance)
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_portfolio
    session.execute.return_value = mock_result
    return session


def _make_holding(qty: str, avg: str) -> MagicMock:
    h = MagicMock()
    h.quantity = Decimal(qty)
    h.avg_price = Decimal(avg)
    h.portfolio_id = PORTFOLIO_ID
    h.asset_id = ASSET_ID
    return h


class TestRecordTransactionBuy:
    async def test_buy_creates_new_holding_when_none_exists(self) -> None:
        session = _mock_session()
        new_holding = MagicMock()

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = None
            mock_hr.create.return_value = new_holding
            MockHR.return_value = mock_hr

            mock_tr = AsyncMock()
            mock_tr.create.return_value = MagicMock()
            MockTR.return_value = mock_tr

            result = await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="RELIANCE",
                transaction_type="buy",
                quantity=Decimal("10"),
                price=Decimal("100"),
                executed_at=NOW,
            )

        mock_hr.create.assert_called_once_with(
            portfolio_id=PORTFOLIO_ID,
            asset_id=ASSET_ID,
            symbol="RELIANCE",
            quantity=10.0,
            avg_price=100.0,
        )
        assert result.holding is new_holding
        assert result.realized_pnl == Decimal("0")
        session.commit.assert_called_once()

    async def test_buy_buy_blends_avg_price(self) -> None:
        """BUY 10 @ 100, then BUY 10 @ 200 → avg = 150, qty = 20."""
        session = _mock_session()
        existing = _make_holding("10", "100")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = existing
            mock_hr.update.return_value = existing
            MockHR.return_value = mock_hr

            mock_tr = AsyncMock()
            mock_tr.create.return_value = MagicMock()
            MockTR.return_value = mock_tr

            result = await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="RELIANCE",
                transaction_type="buy",
                quantity=Decimal("10"),
                price=Decimal("200"),
                executed_at=NOW,
            )

        assert existing.avg_price == pytest.approx(150.0)
        assert existing.quantity == pytest.approx(20.0)
        assert result.realized_pnl == Decimal("0")
        mock_hr.update.assert_called_once_with(existing)

    async def test_buy_case_insensitive(self) -> None:
        session = _mock_session()

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = None
            mock_hr.create.return_value = MagicMock()
            MockHR.return_value = mock_hr
            MockTR.return_value = AsyncMock(create=AsyncMock(return_value=MagicMock()))

            result = await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="reliance",
                transaction_type="BUY",
                quantity=Decimal("5"),
                price=Decimal("100"),
                executed_at=NOW,
            )

        assert result.realized_pnl == Decimal("0")

    async def test_buy_debits_cash_balance(self) -> None:
        """BUY 10 @ 100 with fees=5 → cash_balance decreases by 1005."""
        session = _mock_session(cash_balance="10000")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = None
            mock_hr.create.return_value = MagicMock()
            MockHR.return_value = mock_hr
            MockTR.return_value = AsyncMock(create=AsyncMock(return_value=MagicMock()))

            await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="TCS",
                transaction_type="buy",
                quantity=Decimal("10"),
                price=Decimal("100"),
                fees=Decimal("5"),
                executed_at=NOW,
            )

        # portfolio.cash_balance should be updated to 10000 - (10*100 + 5) = 8995
        mock_portfolio = session.execute.return_value.scalar_one.return_value
        assert mock_portfolio.cash_balance == Decimal("8995")


class TestRecordTransactionSell:
    async def test_partial_sell_computes_realized_pnl(self) -> None:
        """BUY 20 @ 100, SELL 10 @ 150 → realized PnL = (150-100)*10 = 500."""
        session = _mock_session()
        existing = _make_holding("20", "100")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = existing
            mock_hr.update.return_value = existing
            MockHR.return_value = mock_hr

            mock_tr = AsyncMock()
            mock_tr.create.return_value = MagicMock()
            MockTR.return_value = mock_tr

            result = await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="RELIANCE",
                transaction_type="sell",
                quantity=Decimal("10"),
                price=Decimal("150"),
                executed_at=NOW,
            )

        assert result.realized_pnl == Decimal("500")
        assert existing.quantity == pytest.approx(10.0)
        assert result.holding is existing
        mock_hr.update.assert_called_once_with(existing)

    async def test_partial_sell_loss(self) -> None:
        """BUY 10 @ 200, SELL 5 @ 150 → realized PnL = (150-200)*5 = -250."""
        session = _mock_session()
        existing = _make_holding("10", "200")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = existing
            mock_hr.update.return_value = existing
            MockHR.return_value = mock_hr
            MockTR.return_value = AsyncMock(create=AsyncMock(return_value=MagicMock()))

            result = await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="RELIANCE",
                transaction_type="sell",
                quantity=Decimal("5"),
                price=Decimal("150"),
                executed_at=NOW,
            )

        assert result.realized_pnl == Decimal("-250")

    async def test_full_sell_closes_position(self) -> None:
        """Sell all shares → holding deleted, result.holding is None."""
        session = _mock_session()
        existing = _make_holding("10", "100")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = existing
            MockHR.return_value = mock_hr

            mock_tr = AsyncMock()
            mock_tr.create.return_value = MagicMock()
            MockTR.return_value = mock_tr

            result = await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="RELIANCE",
                transaction_type="sell",
                quantity=Decimal("10"),
                price=Decimal("120"),
                executed_at=NOW,
            )

        mock_hr.delete.assert_called_once_with(existing)
        mock_hr.update.assert_not_called()
        assert result.holding is None
        assert result.realized_pnl == Decimal("200")  # (120-100)*10

    async def test_sell_avg_price_unchanged_after_partial_sell(self) -> None:
        """Avg price must not change when selling; only quantity decreases."""
        session = _mock_session()
        existing = _make_holding("20", "150")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = existing
            mock_hr.update.return_value = existing
            MockHR.return_value = mock_hr
            MockTR.return_value = AsyncMock(create=AsyncMock(return_value=MagicMock()))

            await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="RELIANCE",
                transaction_type="sell",
                quantity=Decimal("5"),
                price=Decimal("200"),
                executed_at=NOW,
            )

        # avg_price was not modified by the service
        assert existing.avg_price == Decimal("150")

    async def test_sell_credits_cash_balance(self) -> None:
        """SELL 5 @ 200 with fees=2 → cash_balance increases by 998."""
        session = _mock_session(cash_balance="5000")
        existing = _make_holding("10", "100")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = existing
            mock_hr.update.return_value = existing
            MockHR.return_value = mock_hr
            MockTR.return_value = AsyncMock(create=AsyncMock(return_value=MagicMock()))

            await record_transaction(
                session,
                portfolio_id=PORTFOLIO_ID,
                asset_id=ASSET_ID,
                symbol="RELIANCE",
                transaction_type="sell",
                quantity=Decimal("5"),
                price=Decimal("200"),
                fees=Decimal("2"),
                executed_at=NOW,
            )

        mock_portfolio = session.execute.return_value.scalar_one.return_value
        # 5000 + (5*200 - 2) = 5000 + 998 = 5998
        assert mock_portfolio.cash_balance == Decimal("5998")


class TestRecordTransactionValidation:
    async def test_sell_more_than_held_raises_422(self) -> None:
        session = _mock_session()
        existing = _make_holding("5", "100")

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = existing
            MockHR.return_value = mock_hr
            MockTR.return_value = AsyncMock()

            with pytest.raises(Exception) as exc_info:
                await record_transaction(
                    session,
                    portfolio_id=PORTFOLIO_ID,
                    asset_id=ASSET_ID,
                    symbol="RELIANCE",
                    transaction_type="sell",
                    quantity=Decimal("10"),
                    price=Decimal("150"),
                    executed_at=NOW,
                )

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INSUFFICIENT_QUANTITY"

    async def test_sell_with_no_position_raises_422(self) -> None:
        session = _mock_session()

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository") as MockTR,
        ):
            mock_hr = AsyncMock()
            mock_hr.get_by_portfolio_asset.return_value = None
            MockHR.return_value = mock_hr
            MockTR.return_value = AsyncMock()

            with pytest.raises(Exception) as exc_info:
                await record_transaction(
                    session,
                    portfolio_id=PORTFOLIO_ID,
                    asset_id=ASSET_ID,
                    symbol="RELIANCE",
                    transaction_type="sell",
                    quantity=Decimal("5"),
                    price=Decimal("100"),
                    executed_at=NOW,
                )

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INSUFFICIENT_QUANTITY"

    async def test_invalid_transaction_type_raises_422(self) -> None:
        session = _mock_session()

        with (
            patch("app.services.transactions.HoldingRepository") as MockHR,
            patch("app.services.transactions.TransactionRepository"),
        ):
            MockHR.return_value = AsyncMock()

            with pytest.raises(Exception) as exc_info:
                await record_transaction(
                    session,
                    portfolio_id=PORTFOLIO_ID,
                    asset_id=ASSET_ID,
                    symbol="RELIANCE",
                    transaction_type="short",
                    quantity=Decimal("5"),
                    price=Decimal("100"),
                    executed_at=NOW,
                )

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_TRANSACTION_TYPE"
