"""Persistencia da fila de trabalho."""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

TIPO_ENVIAR_COLETA = "enviar_coleta"
TIPO_INTERPRETAR_FICHA = "interpretar_ficha"
BLOQUEIO_PROCESSANDO = timedelta(minutes=5)


def enfileirar_enviar_coleta(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
) -> int:
    payload = json.dumps({"id_reserva": id_reserva, "id_mensagem": id_mensagem})
    return conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, :tipo, CAST(:payload AS jsonb), 'pendente') "
            "RETURNING id_trabalho"
        ),
        {
            "id_hotel": id_hotel,
            "tipo": TIPO_ENVIAR_COLETA,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_interpretar_ficha(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    id_evento: int,
) -> int:
    payload = json.dumps(
        {
            "id_reserva": id_reserva,
            "id_mensagem": id_mensagem,
            "id_evento": id_evento,
        }
    )
    return conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, :tipo, CAST(:payload AS jsonb), 'pendente') "
            "RETURNING id_trabalho"
        ),
        {
            "id_hotel": id_hotel,
            "tipo": TIPO_INTERPRETAR_FICHA,
            "payload": payload,
        },
    ).scalar_one()


def reclaim_expirados(
    conexao: Connection,
    *,
    agora: datetime | None = None,
    bloqueio: timedelta = BLOQUEIO_PROCESSANDO,
) -> int:
    instante = agora or datetime.now(UTC)
    limite = instante - bloqueio
    resultado = conexao.execute(
        text(
            "UPDATE trabalho SET status = 'pendente',"
            " processando_desde = NULL, atualizado_em = :agora"
            " WHERE status = 'processando'"
            " AND processando_desde IS NOT NULL"
            " AND processando_desde < :limite"
        ),
        {"agora": instante, "limite": limite},
    )
    return resultado.rowcount or 0


def reclamar_proximo(
    conexao: Connection,
    *,
    agora: datetime | None = None,
) -> dict | None:
    instante = agora or datetime.now(UTC)
    reclaim_expirados(conexao, agora=instante)
    linha = conexao.execute(
        text(
            "SELECT id_trabalho, id_hotel, tipo, payload, status, tentativas,"
            " proxima_tentativa_em, erro_ultima_tentativa"
            " FROM trabalho"
            " WHERE status = 'pendente'"
            " AND (proxima_tentativa_em IS NULL OR proxima_tentativa_em <= :agora)"
            " ORDER BY id_trabalho ASC"
            " FOR UPDATE SKIP LOCKED"
            " LIMIT 1"
        ),
        {"agora": instante},
    ).mappings().first()
    if linha is None:
        return None
    conexao.execute(
        text(
            "UPDATE trabalho SET status = 'processando',"
            " processando_desde = :agora, atualizado_em = :agora"
            " WHERE id_trabalho = :id"
        ),
        {"agora": instante, "id": linha["id_trabalho"]},
    )
    dados = dict(linha)
    payload = dados["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    dados["payload"] = dict(payload)
    return dados


def marcar_concluido(conexao: Connection, *, id_trabalho: int) -> None:
    conexao.execute(
        text(
            "UPDATE trabalho SET status = 'concluido',"
            " processando_desde = NULL, atualizado_em = now()"
            " WHERE id_trabalho = :id"
        ),
        {"id": id_trabalho},
    )


def reagendar(
    conexao: Connection,
    *,
    id_trabalho: int,
    tentativas: int,
    erro: str,
    proxima_tentativa_em: datetime,
) -> None:
    conexao.execute(
        text(
            "UPDATE trabalho SET status = 'pendente',"
            " tentativas = :tentativas,"
            " erro_ultima_tentativa = :erro,"
            " proxima_tentativa_em = :proxima,"
            " processando_desde = NULL,"
            " atualizado_em = now()"
            " WHERE id_trabalho = :id"
        ),
        {
            "id": id_trabalho,
            "tentativas": tentativas,
            "erro": erro,
            "proxima": proxima_tentativa_em,
        },
    )


def marcar_falha(
    conexao: Connection,
    *,
    id_trabalho: int,
    tentativas: int,
    erro: str,
) -> None:
    conexao.execute(
        text(
            "UPDATE trabalho SET status = 'falha',"
            " tentativas = :tentativas,"
            " erro_ultima_tentativa = :erro,"
            " processando_desde = NULL,"
            " atualizado_em = now()"
            " WHERE id_trabalho = :id"
        ),
        {"id": id_trabalho, "tentativas": tentativas, "erro": erro},
    )
