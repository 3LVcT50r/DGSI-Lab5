from pathlib import Path
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "3D Printer Factory Simulator"
    version: str = "0.1.0"
    database_url: str = "sqlite:///./data/database.sqlite"
    default_config_path: Path = Path("data/default_config.json")
    warehouse_capacity: int = 500
    production_capacity_per_day: int = 10
    demand_seed: int = 1234

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
