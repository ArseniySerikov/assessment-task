from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./travel_planner.db"
    ARTIC_API_BASE_URL: str = "https://api.artic.edu/api/v1"
    ARTIC_CACHE_TTL: int = 300  # in order not to constantly take the API
    ARTIC_CACHE_MAX_SIZE: int = 512
    MAX_PLACES_PER_PROJECT: int = 10
    model_config = {"env_file": ".env"}

settings = Settings()