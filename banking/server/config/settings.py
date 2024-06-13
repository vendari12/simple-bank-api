from datetime import datetime, timedelta
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V2_STR: str = "/api/banking/v1"
    APP_NAME: str = "Banking App"
    PAGE_SIZE: int = 20
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRY: int = 15  # in minutes
    REFRESH_TOKEN_EXPRY: int = 3  # in days

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost",
        "http://localhost:4200",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v


_client: Optional[Settings] = None


@lru_cache()
def get_settings() -> Settings:
    """Get a shared settings client instance."""
    global _client
    if _client:
        return _client
    _client = Settings()
    return _client


settings = get_settings()
