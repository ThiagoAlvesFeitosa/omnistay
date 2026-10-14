"""Constantes e montagem de trabalho para testes de isolamento.

Uso so em teste. Sem segredo, sem worker, sem canal de mensagem.
"""

import json

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

CPF_NA_MENSAGEM = "529.982.247-25"

__all__ = [
    "CPF_NA_MENSAGEM",
    "excecao_com_cpf",
    "trabalho_minimo",
]


def excecao_com_cpf() -> IntegrityError:
    orig = Exception(
        f"duplicate key value violates unique constraint: {CPF_NA_MENSAGEM}"
    )
    return IntegrityError(
        "INSERT INTO hospede (numero_documento) VALUES (%(doc)s)",
        {"doc": CPF_NA_MENSAGEM},
        orig,
    )


def trabalho_minimo(
    conexao: Connection,
    tipo: str,
    *,
    id_hotel: int,
    id_reserva: int | None = None,
    id_mensagem: int | None = None,
    tentativas: int = 0,
    status: str = "pendente",
) -> int:
    payload: dict = {}
    if id_reserva is not None:
        payload["id_reserva"] = id_reserva
    if id_mensagem is not None:
        payload["id_mensagem"] = id_mensagem
    if not payload:
        payload["id_concorrente"] = 1
    return conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status, tentativas) "
            "VALUES (:id_hotel, :tipo, CAST(:payload AS jsonb), :status, :tentativas) "
            "RETURNING id_trabalho"
        ),
        {
            "id_hotel": id_hotel,
            "tipo": tipo,
            "payload": json.dumps(payload),
            "status": status,
            "tentativas": tentativas,
        },
    ).scalar_one()
