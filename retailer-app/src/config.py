import json
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and config file."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    app_name: str = "3D Printer Retailer Simulator"
    version: str = "0.1.0"
    database_url: str = f"sqlite:///{(base_dir / 'data' / 'retailer.sqlite').as_posix()}"
    default_seed_path: Path = base_dir / "data" / "seed-retailer.json"
    default_config_path: Path = base_dir / "data" / "retailer-config.json"
    manufacturer_url: str = "http://localhost:8002"
    markup_pct: float = 30.0
    retailer_name: str = "PrinterWorld"
    port: int = 8003

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    def __init__(self, **values):
        super().__init__(**values)
        config_path = self.default_config_path
        if config_path.exists():
            try:
                config_data = json.loads(config_path.read_text(encoding="utf-8"))
                retailer = config_data.get("retailer", {})
                self.retailer_name = retailer.get("name", self.retailer_name)
                self.manufacturer_url = retailer.get("manufacturer", {}).get("url", self.manufacturer_url)
                self.markup_pct = retailer.get("markup_pct", self.markup_pct)
                self.port = retailer.get("port", self.port)
            except ValueError:
                pass
