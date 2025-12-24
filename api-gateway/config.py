import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Порт сервиса
    api_gateway_port: int = int(os.getenv("API_GATEWAY_PORT", 8000))

    # Настройки сервисов
    orders_service_url: str = os.getenv(
        "ORDERS_SERVICE_URL",
        "http://orders-service:8000"
    )

    payments_service_url: str = os.getenv(
        "PAYMENTS_SERVICE_URL",
        "http://payments-service:8000"
    )

    # Таймауты
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", 30.0))

    # Логирование
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"


settings = Settings()