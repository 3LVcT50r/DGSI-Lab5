from fastapi import APIRouter

from src.api.catalog import router as catalog_router
from src.api.stock import router as stock_router
from src.api.orders import router as orders_router
from src.api.day import router as day_router

api_router = APIRouter()

api_router.include_router(catalog_router, tags=["Catalog"])
api_router.include_router(stock_router, tags=["Stock"])
api_router.include_router(orders_router, tags=["Orders"])
api_router.include_router(day_router, tags=["Day"])