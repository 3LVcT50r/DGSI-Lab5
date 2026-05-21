import sys
sys.path.append("/home/victor/proyectos/DGSI-Lab5/provider-app")
from src.database import SessionLocal
from src.services.provider import advance_day
import traceback

with SessionLocal() as db:
    try:
        advance_day(db)
        print("Success")
    except Exception as e:
        traceback.print_exc()
