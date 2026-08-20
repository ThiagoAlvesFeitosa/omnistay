"""Persistencia da fila de trabalho."""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

TIPO_ENVIAR_COLETA = "enviar_coleta"
TIPO_INTERPRETAR_FICHA = "interpretar_ficha"
TIPO_ENVIAR_LEMBRETE = "enviar_lembrete"
TIPO_ENVIAR_BOAS_VINDAS = "enviar_boas_vindas"
TIPO_CLASSIFICAR_MENSAGEM = "classificar_mensagem"
TIPO_RESPONDER_DUVIDA = "responder_duvida"
TIPO_REGISTRAR_PEDIDO_SERVICO = "registrar_pedido_servico"
TIPO_ABRIR_CHAMADO_RECLAMACAO = "abrir_chamado_reclamacao"
TIPO_ENVIAR_CONFIRMACAO_RESOLUCAO = "enviar_confirmacao_resolucao"
TIPO_ENVIAR_PULSO = "enviar_pulso"
TIPO_REGISTRAR_RESPOSTA_PULSO = "registrar_resposta_pulso"
TIPOS_CONSUMIVEIS = (
    TIPO_ENVIAR_COLETA,
    TIPO_INTERPRETAR_FICHA,
    TIPO_ENVIAR_LEMBRETE,
    TIPO_ENVIAR_BOAS_VINDAS,
    TIPO_CLASSIFICAR_MENSAGEM,
    TIPO_RESPONDER_DUVIDA,
    TIPO_REGISTRAR_PEDIDO_SERVICO,
    TIPO_ABRIR_CHAMADO_RECLAMACAO,
    TIPO_ENVIAR_CONFIRMACAO_RESOLUCAO,
    TIPO_ENVIAR_PULSO,
    TIPO_REGISTRAR_RESPOSTA_PULSO,
)
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


def enfileirar_enviar_lembrete(
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
            "tipo": TIPO_ENVIAR_LEMBRETE,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_enviar_boas_vindas(
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
            "tipo": TIPO_ENVIAR_BOAS_VINDAS,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_classificar_mensagem(
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
            "tipo": TIPO_CLASSIFICAR_MENSAGEM,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_responder_duvida(
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
            "tipo": TIPO_RESPONDER_DUVIDA,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_registrar_pedido_servico(
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
            "tipo": TIPO_REGISTRAR_PEDIDO_SERVICO,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_abrir_chamado_reclamacao(
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
            "tipo": TIPO_ABRIR_CHAMADO_RECLAMACAO,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_enviar_confirmacao_resolucao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_solicitacao: int,
    id_mensagem: int,
) -> int:
    payload = json.dumps(
        {
            "id_reserva": id_reserva,
            "id_solicitacao": id_solicitacao,
            "id_mensagem": id_mensagem,
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
            "tipo": TIPO_ENVIAR_CONFIRMACAO_RESOLUCAO,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_enviar_pulso(
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
            "tipo": TIPO_ENVIAR_PULSO,
            "payload": payload,
        },
    ).scalar_one()


def enfileirar_registrar_resposta_pulso(
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
            "tipo": TIPO_REGISTRAR_RESPOSTA_PULSO,
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
            " AND tipo IN ('enviar_coleta', 'interpretar_ficha',"
            " 'enviar_lembrete', 'enviar_boas_vindas', 'classificar_mensagem',"
            " 'responder_duvida', 'registrar_pedido_servico',"
            " 'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',"
            " 'enviar_pulso', 'registrar_resposta_pulso')"
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
