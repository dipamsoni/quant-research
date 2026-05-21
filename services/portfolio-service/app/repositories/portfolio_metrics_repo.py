from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio_metrics import PortfolioMetrics



class PortfolioMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest(self, portfolio_id: uuid.UUID) -> PortfolioMetrics | None:
        result = await self._session.execute(
            select(PortfolioMetrics)
            .where(PortfolioMetrics.portfolio_id == portfolio_id)
            .order_by(PortfolioMetrics.date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_range(
        self,
        portfolio_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> list[PortfolioMetrics]:
        result = await self._session.execute(
            select(PortfolioMetrics)
            .where(
                PortfolioMetrics.portfolio_id == portfolio_id,
                PortfolioMetrics.date >= from_date,
                PortfolioMetrics.date <= to_date,
            )
            .order_by(PortfolioMetrics.date)
        )
        return list(result.scalars().all())

    async def get_recent(
        self, portfolio_id: uuid.UUID, limit: int = 32
    ) -> list[PortfolioMetrics]:
        """Return last `limit` metric rows, oldest first."""
        result = await self._session.execute(
            select(PortfolioMetrics)
            .where(PortfolioMetrics.portfolio_id == portfolio_id)
            .order_by(PortfolioMetrics.date.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda r: r.date)
        return rows

    async def upsert(
        self,
        portfolio_id: uuid.UUID,
        for_date: date,
        total_value: float,
        daily_return: float | None,
        sharpe_ratio: float | None,
        max_drawdown: float | None,
        volatility: float | None,
        beta: float | None,
        alpha: float | None,
        cost_basis: float | None = None,
        unrealized_pnl: float | None = None,
        realized_pnl: float | None = None,
    ) -> PortfolioMetrics:
        """Insert or update today's metrics row."""
        stmt = (
            insert(PortfolioMetrics)
            .values(
                id=uuid.uuid4(),
                portfolio_id=portfolio_id,
                date=for_date,
                total_value=total_value,
                daily_return=daily_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                volatility=volatility,
                beta=beta,
                alpha=alpha,
                cost_basis=cost_basis,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
            )
            .on_conflict_do_update(
                constraint="uq_portfolio_metrics_portfolio_date",
                set_={
                    "total_value": total_value,
                    "daily_return": daily_return,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "volatility": volatility,
                    "beta": beta,
                    "alpha": alpha,
                    "cost_basis": cost_basis,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": realized_pnl,
                },
            )
            .returning(PortfolioMetrics)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one()
        await self._session.flush()
        return row
