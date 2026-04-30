from fastapi import APIRouter

from src.api.simulation import router as simulation_router
from src.api.orders import router as orders_router
from src.api.inventory import router as inventory_router
from src.api.purchasing import router as purchasing_router
from src.api.bom import router as bom_router
from src.api.export import router as export_router
from src.api.products import router as products_router

api_router = APIRouter()

api_router.include_router(simulation_router, tags=["Simulation"])
api_router.include_router(orders_router, tags=["Orders"])
api_router.include_router(inventory_router, tags=["Inventory"])
api_router.include_router(purchasing_router, tags=["Purchasing"])
api_router.include_router(bom_router, tags=["BOM"])
api_router.include_router(export_router, tags=["Events & Export"])
api_router.include_router(products_router, tags=["Products"])
