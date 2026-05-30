from typing import Annotated
from fastapi import APIRouter, Depends, Request
from app.core.dependencies import get_watchlist_service
from app.services.watchlist.watchlist_service import WatchlistService

watchlist_router = APIRouter(prefix="/watchlist")

WatchlistServiceDep = Annotated[WatchlistService, Depends(get_watchlist_service)]


@watchlist_router.get("/")
async def get_watchlist(request: Request, watchlist_service: WatchlistServiceDep):
    return await watchlist_service.get_items(request.client.host)


@watchlist_router.post("/{symbol}")
async def add_to_watchlist(
    request: Request, symbol: str, watchlist_service: WatchlistServiceDep
):
    return await watchlist_service.add_item(request.client.host, symbol)


@watchlist_router.delete("/{symbol}")
async def remove_from_watchlist(
    request: Request, symbol: str, watchlist_service: WatchlistServiceDep
):
    return await watchlist_service.remove_item(request.client.host, symbol)
