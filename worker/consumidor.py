"""Consumidor da fila de trabalho."""

from sqlalchemy.engine import Connection, Engine

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.comum.log import obter_logger
from app.fila import repository as fila_repository
from app.modulos.conversa import service as conversa_service
from app.modulos.hospedagem import service as hospedagem_service
from app.portas.llm import LLMProvider
from app.portas.mensageria import MensageriaGateway

logger = obter_logger(__name__)


def processar_uma_passagem(
    conexao: Connection,
    *,
    gateway: MensageriaGateway,
    llm: LLMProvider | None = None,
    limite: int = 100,
) -> int:
    """Processa ate `limite` trabalhos elegiveis. Devolve quantos foram claims."""
    porta_llm = llm or LLMFalso()
    processados = 0
    while processados < limite:
        trabalho = fila_repository.reclamar_proximo(conexao)
        if trabalho is None:
            break
        logger.info(
            "trabalho_claim id_trabalho=%s tipo=%s",
            trabalho["id_trabalho"],
            trabalho["tipo"],
        )
        if trabalho["tipo"] == "enviar_coleta":
            conversa_service.processar_trabalho_enviar_coleta(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "interpretar_ficha":
            conversa_service.processar_trabalho_interpretar_ficha(
                conexao,
                trabalho=trabalho,
                llm=porta_llm,
                consolidar=hospedagem_service.consolidar_ficha_titular,
            )
        elif trabalho["tipo"] == "enviar_lembrete":
            conversa_service.processar_trabalho_enviar_lembrete(
                conexao, trabalho=trabalho, gateway=gateway
            )
        else:
            fila_repository.marcar_falha(
                conexao,
                id_trabalho=trabalho["id_trabalho"],
                tentativas=trabalho["tentativas"] + 1,
                erro="tipo_desconhecido",
            )
        processados += 1
    return processados


def processar_uma_passagem_na_engine(
    engine: Engine,
    *,
    gateway: MensageriaGateway | None = None,
    llm: LLMProvider | None = None,
) -> int:
    porta = gateway or MensageriaFalsa()
    with engine.begin() as conexao:
        return processar_uma_passagem(conexao, gateway=porta, llm=llm)
