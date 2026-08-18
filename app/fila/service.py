"""Orquestracao da fila de trabalho — sem texto de mensagem."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.engine import Connection

from app.fila import repository as repositorio_padrao
from app.modulos.propriedade import repository as propriedade_repository

CHAVE_TENTATIVAS_MAX = "tentativas_max_envio_mensagem"
TENTATIVAS_MAX_PADRAO = 5


def enfileirar_enviar_coleta(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_enviar_coleta(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )


def enfileirar_interpretar_ficha(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    id_evento: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_interpretar_ficha(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        id_evento=id_evento,
    )


def enfileirar_enviar_lembrete(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_enviar_lembrete(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )


def enfileirar_enviar_boas_vindas(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_enviar_boas_vindas(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )


def enfileirar_classificar_mensagem(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    id_evento: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_classificar_mensagem(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        id_evento=id_evento,
    )


def enfileirar_responder_duvida(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_responder_duvida(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )


def enfileirar_registrar_pedido_servico(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_registrar_pedido_servico(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )


def enfileirar_abrir_chamado_reclamacao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_abrir_chamado_reclamacao(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )


def enfileirar_enviar_confirmacao_resolucao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_solicitacao: int,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> int:
    return repositorio.enfileirar_enviar_confirmacao_resolucao(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_solicitacao=id_solicitacao,
        id_mensagem=id_mensagem,
    )


def tentativas_maximas(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio_propriedade=propriedade_repository,
) -> int:
    valor = repositorio_propriedade.ler_parametro(
        conexao, id_hotel, CHAVE_TENTATIVAS_MAX
    )
    if valor is None:
        return TENTATIVAS_MAX_PADRAO
    return int(valor)


def backoff_apos(tentativas: int) -> datetime:
    # Espera crescente tecnica: 60s * 2^(tentativas-1)
    segundos = 60 * (2 ** max(tentativas - 1, 0))
    return datetime.now(UTC) + timedelta(seconds=segundos)


def registrar_falha_de_envio(
    conexao: Connection,
    *,
    id_trabalho: int,
    id_hotel: int,
    tentativas_atuais: int,
    codigo_erro: str,
    repositorio=repositorio_padrao,
    repositorio_propriedade=propriedade_repository,
) -> str:
    """Atualiza o trabalho apos falha. Devolve 'reagendado' ou 'falha'."""
    novas = tentativas_atuais + 1
    teto = tentativas_maximas(
        conexao, id_hotel=id_hotel, repositorio_propriedade=repositorio_propriedade
    )
    if novas >= teto:
        repositorio.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=novas,
            erro=codigo_erro,
        )
        return "falha"
    repositorio.reagendar(
        conexao,
        id_trabalho=id_trabalho,
        tentativas=novas,
        erro=codigo_erro,
        proxima_tentativa_em=backoff_apos(novas),
    )
    return "reagendado"
