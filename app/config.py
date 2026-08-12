from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    health_db_timeout_seconds: float = 1.0
    log_level: str = "INFO"

    # Parametro de seguranca de plataforma, nao de propriedade: nao pertence a
    # `parametro_hotel`. A suite de testes o reduz para manter o ciclo rapido;
    # o custo real vive na configuracao de producao.
    senha_iteracoes: int = 600_000


@lru_cache
def obter_configuracao() -> Configuracao:
    return Configuracao()
