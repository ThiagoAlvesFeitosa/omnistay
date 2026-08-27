"""Escolhe o adaptador de inteligencia pela configuracao de plataforma."""

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.llm_gemini import LLMGemini
from app.comum.log import obter_logger
from app.portas.llm import LLMProvider

logger = obter_logger(__name__)


class ConfiguracaoDeInteligenciaInvalida(Exception):
    """Modo de cerebro ausente, desconhecido ou real sem chave — o processo nao sobe no escuro."""

    def __init__(self, codigo: str, modo: str = "") -> None:
        self.codigo = codigo
        self.modo = modo
        if codigo == "modo_invalido":
            super().__init__(f"modo_invalido:{modo}")
        else:
            super().__init__(codigo)


def construir_llm(config) -> LLMProvider:
    modo = getattr(config, "llm_modo", "") or ""
    if modo == "controlado":
        logger.info("llm_construido modo=controlado classe=LLMFalso")
        return LLMFalso()
    if modo == "real":
        chave = getattr(config, "gemini_api_key", "") or ""
        if not chave:
            raise ConfiguracaoDeInteligenciaInvalida("chave_ausente")
        timeout = getattr(config, "llm_timeout_seconds", None)
        modelo = getattr(config, "llm_modelo", None) or "gemini-2.0-flash"
        logger.info("llm_construido modo=real classe=LLMGemini")
        return LLMGemini(
            chave=chave,
            timeout=float(timeout) if timeout else 15.0,
            modelo=modelo,
        )
    raise ConfiguracaoDeInteligenciaInvalida("modo_invalido", modo=modo)
