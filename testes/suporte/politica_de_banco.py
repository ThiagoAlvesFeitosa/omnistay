"""Decide o que fazer com um teste que exige PostgreSQL quando o banco nao responde.

A decisao mora aqui, separada do gancho do pytest que a aplica, para que possa ser
verificada de dentro da propria suite.
"""

from dataclasses import dataclass
from enum import Enum

VARIAVEL_DE_EXIGENCIA = "EXIGIR_POSTGRES"

_MOTIVO_PULAR = (
    "PostgreSQL inalcancavel via DATABASE_URL. "
    f"Defina {VARIAVEL_DE_EXIGENCIA}=1 para que a ausencia do banco falhe em vez de pular."
)

_MOTIVO_FALHAR = (
    f"{VARIAVEL_DE_EXIGENCIA}=1 exige PostgreSQL alcancavel via DATABASE_URL, "
    "e o banco nao respondeu."
)


class Acao(Enum):
    EXECUTAR = "executar"
    PULAR = "pular"
    FALHAR = "falhar"


@dataclass(frozen=True)
class Decisao:
    acao: Acao
    motivo: str = ""


def decidir_execucao(banco_alcancavel: bool, banco_exigido: bool) -> Decisao:
    if banco_alcancavel:
        return Decisao(Acao.EXECUTAR)
    if banco_exigido:
        return Decisao(Acao.FALHAR, _MOTIVO_FALHAR)
    return Decisao(Acao.PULAR, _MOTIVO_PULAR)


def banco_exigido_pelo_ambiente(ambiente: dict[str, str]) -> bool:
    return ambiente.get(VARIAVEL_DE_EXIGENCIA, "").strip() == "1"
