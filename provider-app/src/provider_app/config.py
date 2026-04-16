from pathlib import Path


class Settings:
    project_root: Path = Path(__file__).resolve().parents[1]
    db_path: Path = project_root / "provider.db"
    database_url: str = f"sqlite:///{db_path}"
    seed_path: Path = project_root / "seed-provider.json"


settings = Settings()
