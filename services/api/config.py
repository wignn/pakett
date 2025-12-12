"""
Configuration management using Pydantic Settings.
Loads environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "Paket Routing API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql+asyncpg://paket:paket_secret@localhost:5432/paket_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 604800  # 7 days
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_consumer_group: str = "paket-processors"
    kafka_topics_ingest: str = "paket.ingest"
    kafka_topics_address: str = "paket.address"
    kafka_topics_route: str = "paket.route"
    
    # Geocoding
    geocoding_provider: str = "nominatim"  # nominatim, locationiq, opencage
    geocoding_api_key: Optional[str] = None
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    geocoding_rate_limit: float = 1.0  # requests per second
    
    # OCR
    tesseract_lang: str = "ind+eng"
    ocr_confidence_threshold: float = 0.7
    
    # VRP Optimizer
    vrp_max_solve_time_seconds: int = 300
    vrp_default_vehicle_capacity: int = 50
    vrp_default_service_time_minutes: int = 5
    
    # File uploads
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 10


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
