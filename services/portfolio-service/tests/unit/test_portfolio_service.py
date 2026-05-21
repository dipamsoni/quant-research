import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.portfolio import (
    create_portfolio,
    delete_portfolio,
    get_portfolio,
    list_portfolios,
)

USER_ID = uuid.uuid4()
PORTFOLIO_ID = uuid.uuid4()


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


class TestCreatePortfolio:
    async def test_creates_and_commits(self) -> None:
        session = _mock_session()
        mock_portfolio = MagicMock()

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.create.return_value = mock_portfolio
            MockRepo.return_value = mock_repo

            result = await create_portfolio(
                session,
                user_id=USER_ID,
                name="My Portfolio",
                base_currency="INR",
            )

        from decimal import Decimal
        mock_repo.create.assert_called_once_with(
            user_id=USER_ID,
            name="My Portfolio",
            base_currency="INR",
            risk_profile=None,
            initial_cash=Decimal("0"),
        )
        session.commit.assert_called_once()
        assert result is mock_portfolio

    async def test_passes_risk_profile(self) -> None:
        session = _mock_session()

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.create.return_value = MagicMock()
            MockRepo.return_value = mock_repo

            await create_portfolio(
                session,
                user_id=USER_ID,
                name="Aggressive",
                risk_profile="high",
            )

        from decimal import Decimal
        mock_repo.create.assert_called_once_with(
            user_id=USER_ID,
            name="Aggressive",
            base_currency="INR",
            risk_profile="high",
            initial_cash=Decimal("0"),
        )


class TestGetPortfolio:
    async def test_found(self) -> None:
        session = _mock_session()
        mock_portfolio = MagicMock()

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_portfolio
            MockRepo.return_value = mock_repo

            result = await get_portfolio(session, PORTFOLIO_ID)

        mock_repo.get_by_id.assert_called_once_with(PORTFOLIO_ID)
        assert result is mock_portfolio

    async def test_not_found_returns_none(self) -> None:
        session = _mock_session()

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            MockRepo.return_value = mock_repo

            result = await get_portfolio(session, PORTFOLIO_ID)

        assert result is None


class TestListPortfolios:
    async def test_returns_all_user_portfolios(self) -> None:
        session = _mock_session()
        portfolios = [MagicMock(), MagicMock()]

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = portfolios
            MockRepo.return_value = mock_repo

            result = await list_portfolios(session, USER_ID)

        mock_repo.list_by_user.assert_called_once_with(USER_ID)
        assert result == portfolios

    async def test_returns_empty_list_when_none(self) -> None:
        session = _mock_session()

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            MockRepo.return_value = mock_repo

            result = await list_portfolios(session, USER_ID)

        assert result == []


class TestDeletePortfolio:
    async def test_deletes_existing_and_commits(self) -> None:
        session = _mock_session()

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.delete.return_value = True
            MockRepo.return_value = mock_repo

            result = await delete_portfolio(session, PORTFOLIO_ID)

        mock_repo.delete.assert_called_once_with(PORTFOLIO_ID)
        session.commit.assert_called_once()
        assert result is True

    async def test_not_found_skips_commit(self) -> None:
        session = _mock_session()

        with patch("app.services.portfolio.PortfolioRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.delete.return_value = False
            MockRepo.return_value = mock_repo

            result = await delete_portfolio(session, PORTFOLIO_ID)

        session.commit.assert_not_called()
        assert result is False
