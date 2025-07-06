from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
from decouple import config


class Settings(BaseSettings):
    # App
    APP_NAME: str = config("APP_NAME", default="GlobeGenius")
    APP_VERSION: str = config("APP_VERSION", default="1.0.0")
    ENVIRONMENT: str = config("ENVIRONMENT", default="development")
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    
    # Database
    DATABASE_URL: str = config("DATABASE_URL")
    
    # Redis
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379/0")
    
    # Security
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    
    # SendGrid
    SENDGRID_API_KEY: str = config("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: str = config("SENDGRID_FROM_EMAIL")
    SENDGRID_FROM_NAME: str = config("SENDGRID_FROM_NAME", default="GlobeGenius")
    
    # Aviation APIs
    AVIATIONSTACK_API_KEY: str = config("AVIATIONSTACK_API_KEY")
    AVIATIONSTACK_BASE_URL: str = config("AVIATIONSTACK_BASE_URL", default="https://api.aviationstack.com/v1")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Frontend URL
    FRONTEND_URL: str = config("FRONTEND_URL", default="http://localhost:3003")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Flight Scanning Config
    TIER1_SCAN_INTERVAL_HOURS: int = 2
    TIER2_SCAN_INTERVAL_HOURS: int = 4
    TIER3_SCAN_INTERVAL_HOURS: int = 6
    
    # ML Config
    ANOMALY_THRESHOLD: float = 0.3
    MIN_PRICE_DROP_PERCENTAGE: float = 30.0
    
    class Config:
        case_sensitive = True


# IMPORTANT: Cette ligne crée l'instance settings
settings = Settings()