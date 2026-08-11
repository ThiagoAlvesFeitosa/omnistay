from collections.abc import Callable

from app.modulos.sistema.repository import verificar_conectividade_banco
from app.modulos.sistema.schema import HealthResponse, StatusComponente


def obter_saude(
    verificar_conectividade: Callable[[], bool] = verificar_conectividade_banco,
) -> HealthResponse:
    banco_respondeu = verificar_conectividade()
    return HealthResponse(
        banco=StatusComponente.OK if banco_respondeu else StatusComponente.INDISPONIVEL
    )
