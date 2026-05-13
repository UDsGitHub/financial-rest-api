from fastapi import FastAPI

from api.watchlist import watchlist_router
from api.market import market_router
from api.stocks import stocks_router

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to FastStockRestAPI"}

app.include_router(stocks_router)
app.include_router(watchlist_router)
app.include_router(market_router)