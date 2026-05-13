from fastapi import APIRouter

market_router = APIRouter(prefix='/market')

@market_router.get('/')
async def get_market_summary():
    return {"hello": "world"}