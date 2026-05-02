from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings for the provider simulator."""

    base_dir: Path = Path(__file__).resolve().parent.parent
    app_name: str = "3D Printer Provider Simulator"
    version: str = "0.1.0"
    database_url: str = f"sqlite:///{(base_dir / 'data' / 'provider.sqlite').as_posix()}"
    default_seed_path: Path = base_dir / "data" / "seed-provider.json"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
