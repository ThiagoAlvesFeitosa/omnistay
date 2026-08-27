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

    # Webhook WhatsApp (plataforma). Sem valores secretos versionados.
    whatsapp_app_secret: str = ""
    whatsapp_verify_token: str = ""
    # MVP: um hotel por numero de negocio; se 0, resolve pelo telefone da reserva.
    whatsapp_id_hotel: int = 0

    # Canal com o hospede. A fabrica recusa valor vazio ou desconhecido.
    mensageria_modo: str = ""

    # Cerebro. A fabrica recusa valor vazio ou desconhecido.
    llm_modo: str = ""
    gemini_api_key: str = ""
    llm_timeout_seconds: float = 15.0
    llm_modelo: str = "gemini-2.0-flash"


@lru_cache
def obter_configuracao() -> Configuracao:
    return Configuracao()
