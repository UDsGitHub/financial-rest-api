from typing import Annotated
from fastapi import APIRouter, Depends, Request
from app.core.dependencies import get_market_service
from app.services.market.market_service import MarketService

market_router = APIRouter(prefix="/market")

MarketServiceDep = Annotated[MarketService, Depends(get_market_service)]


@market_router.get("/status")
async def get_market_status(
    request: Request,
    market_service: MarketServiceDep,
    region: str | None = None,
):
    return await market_service.get_market_status(request.client.host, region)
