import sys
sys.path.append("/home/victor/proyectos/DGSI-Lab5/provider-app")
from src.database import SessionLocal
from src.services.provider import advance_day, place_order
from src.schemas.request import OrderCreate
import traceback

with SessionLocal() as db:
    try:
        # Place an order to trigger the bug
        order_data = OrderCreate(product_id=1, quantity=10)
        place_order(db, order_data)
        for i in range(10):
            advance_day(db)
        print("Success")
    except Exception as e:
        traceback.print_exc()
