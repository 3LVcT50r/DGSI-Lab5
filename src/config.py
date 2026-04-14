from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="3D Printer Factory Simulator")
    version: str = Field(default="0.1.0")
    database_url: str = Field(default="sqlite:///./data/database.sqlite")
    default_config_path: Path = Field(default=Path("data/default_config.json"))
    warehouse_capacity: int = Field(default=500)
    production_capacity_per_day: int = Field(default=10)
    demand_seed: int = Field(default=1234)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
