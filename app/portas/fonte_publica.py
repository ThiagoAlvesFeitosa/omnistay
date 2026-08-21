"""Porta de fonte publica — o dominio depende so desta interface."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

DIRETIVA_PERMITE = "permite"
DIRETIVA_RECUSA = "recusa"
DIRETIVA_AUSENTE = "ausente"

DESFECHO_ENCONTRADO = "encontrado"
DESFECHO_SEM_DADO = "sem_dado"
DESFECHO_INDISPONIVEL = "indisponivel"
DESFECHO_EXIGE_AUTENTICACAO = "exige_autenticacao"


@dataclass(frozen=True)
class ResultadoPublico:
    """Preco e nota agregada publicados sem login. Sem HTML nem avaliador."""

    desfecho: str
    preco: Decimal | None = None
    nota_media: Decimal | None = None


class FontePublica(Protocol):
    def consultar_diretiva(self, url_fonte: str) -> str: ...

    def coletar_publico(self, url_fonte: str) -> ResultadoPublico: ...
