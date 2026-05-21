from fastapi import APIRouter

from app.api.v1.portfolios import router as portfolio_router

router = APIRouter()
router.include_router(portfolio_router)
