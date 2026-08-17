"""Porta de LLM — o dominio depende so desta interface."""

from dataclasses import dataclass, field
from typing import Protocol


class FalhaDeExtracao(Exception):
    """Extrator indisponivel ou erro tipado, sem eco do texto."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


CAMPOS_FICHA_CHAVE = (
    "nome_completo",
    "profissao",
    "data_nascimento",
    "tipo_documento",
    "numero_documento",
    "endereco",
    "cep",
    "cidade",
    "telefone",
)


@dataclass(frozen=True)
class ResultadoExtracao:
    """Campos opcionais da ficha — nunca inclui idade."""

    desfecho: str  # completa | parcial | irreconhecivel
    campos: dict[str, str] = field(default_factory=dict)
    campos_reconhecidos: tuple[str, ...] = ()


class FalhaDeClassificacao(Exception):
    """Classificador indisponivel, recusa ou tempo esgotado — sem eco do texto."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


@dataclass(frozen=True)
class ResultadoClassificacao:
    """Eixos da mensagem de estadia. Valores podem ser invalidos; o dominio valida."""

    intencao: str | None
    sentimento: str | None
    urgencia: str | None
    bruto: dict = field(default_factory=dict)


class LLMProvider(Protocol):
    def extrair_ficha(self, texto: str) -> ResultadoExtracao: ...
    def classificar(self, texto: str) -> ResultadoClassificacao: ...
