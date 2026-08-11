from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    health_db_timeout_seconds: float = 1.0
    log_level: str = "INFO"


@lru_cache
def obter_configuracao() -> Configuracao:
    return Configuracao()
