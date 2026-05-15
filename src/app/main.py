from fastapi import FastAPI
from app.api.watchlist import watchlist_router
from app.api.market import market_router
from app.api.stocks import stocks_router
from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to FastStockRestAPI"}

app.add_middleware(RateLimitMiddleware)
app.include_router(stocks_router)
app.include_router(watchlist_router)
app.include_router(market_router)