from fastapi import APIRouter, Response, status

from app.modulos.sistema.schema import HealthResponse, StatusComponente
from app.modulos.sistema.service import obter_saude

roteador = APIRouter(tags=["sistema"])


@roteador.get(
    "/health",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
def obter_health(resposta: Response) -> HealthResponse:
    saude = obter_saude()
    if saude.banco == StatusComponente.INDISPONIVEL:
        resposta.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return saude
