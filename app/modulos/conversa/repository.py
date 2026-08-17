"""Acesso a mensagem — sem regra de negocio."""

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection


def inserir_mensagem_enviada_pendente(
    conexao: Connection,
    *,
    id_reserva: int,
    conteudo: str,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo, status_envio) "
            "VALUES (:id_reserva, 'enviada', :conteudo, 'pendente') "
            "RETURNING id_mensagem"
        ),
        {"id_reserva": id_reserva, "conteudo": conteudo},
    ).scalar_one()


def atualizar_status_envio(
    conexao: Connection,
    *,
    id_mensagem: int,
    status_envio: str,
    id_externo: str | None = None,
    agora: datetime | None = None,
) -> None:
    instante = agora or datetime.now(UTC)
    if status_envio == "enviada":
        conexao.execute(
            text(
                "UPDATE mensagem SET status_envio = :status,"
                " enviada_em = :agora,"
                " id_externo = COALESCE(:id_externo, id_externo)"
                " WHERE id_mensagem = :id"
            ),
            {
                "status": status_envio,
                "id_externo": id_externo,
                "id": id_mensagem,
                "agora": instante,
            },
        )
        return
    conexao.execute(
        text(
            "UPDATE mensagem SET status_envio = :status,"
            " id_externo = COALESCE(:id_externo, id_externo)"
            " WHERE id_mensagem = :id"
        ),
        {
            "status": status_envio,
            "id_externo": id_externo,
            "id": id_mensagem,
        },
    )


def ler_mensagem(conexao: Connection, *, id_mensagem: int) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_mensagem, id_reserva, direcao, conteudo, status_envio,"
            " id_externo, intencao, sentimento, urgencia, classificacao_bruta"
            " FROM mensagem WHERE id_mensagem = :id"
        ),
        {"id": id_mensagem},
    ).mappings().first()
    return dict(linha) if linha else None


def listar_mensagens_da_reserva(conexao: Connection, *, id_reserva: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_mensagem, id_reserva, direcao, conteudo, status_envio,"
            " id_externo, classificacao_bruta"
            " FROM mensagem WHERE id_reserva = :id"
            " ORDER BY enviada_em ASC, id_mensagem ASC"
        ),
        {"id": id_reserva},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def ler_telefone_da_reserva(conexao: Connection, *, id_reserva: int) -> str | None:
    return conexao.execute(
        text("SELECT telefone_contato FROM reserva WHERE id_reserva = :id"),
        {"id": id_reserva},
    ).scalar_one_or_none()


def inserir_evento_webhook(
    conexao: Connection,
    *,
    id_externo: str,
    payload: dict,
) -> int | None:
    """Insere evento. Devolve id_evento ou None se id_externo ja existir."""
    import json

    return conexao.execute(
        text(
            "INSERT INTO evento_webhook (id_externo, payload) "
            "VALUES (:id_externo, CAST(:payload AS jsonb)) "
            "ON CONFLICT (id_externo) DO NOTHING "
            "RETURNING id_evento"
        ),
        {"id_externo": id_externo, "payload": json.dumps(payload)},
    ).scalar_one_or_none()


def inserir_mensagem_recebida(
    conexao: Connection,
    *,
    id_reserva: int,
    conteudo: str,
    id_externo: str | None = None,
    enviada_em=None,
) -> int:
    if enviada_em is None:
        return conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo, id_externo) "
                "VALUES (:id_reserva, 'recebida', :conteudo, :id_externo) "
                "RETURNING id_mensagem"
            ),
            {
                "id_reserva": id_reserva,
                "conteudo": conteudo,
                "id_externo": id_externo,
            },
        ).scalar_one()
    return conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo, id_externo,"
            " enviada_em) "
            "VALUES (:id_reserva, 'recebida', :conteudo, :id_externo, :enviada_em) "
            "RETURNING id_mensagem"
        ),
        {
            "id_reserva": id_reserva,
            "conteudo": conteudo,
            "id_externo": id_externo,
            "enviada_em": enviada_em,
        },
    ).scalar_one()


def gravar_classificacao_bruta(
    conexao: Connection,
    *,
    id_mensagem: int,
    classificacao: dict,
) -> None:
    import json

    conexao.execute(
        text(
            "UPDATE mensagem SET classificacao_bruta = CAST(:c AS jsonb)"
            " WHERE id_mensagem = :id"
        ),
        {"c": json.dumps(classificacao), "id": id_mensagem},
    )


def gravar_classificacao_intencao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_mensagem: int,
    intencao: str | None,
    sentimento: str | None,
    urgencia: str | None,
    classificacao: dict,
) -> int:
    import json

    resultado = conexao.execute(
        text(
            "UPDATE mensagem m SET"
            " intencao = :intencao,"
            " sentimento = :sentimento,"
            " urgencia = :urgencia,"
            " classificacao_bruta = CAST(:c AS jsonb)"
            " FROM reserva r"
            " WHERE m.id_mensagem = :id"
            " AND m.id_reserva = r.id_reserva"
            " AND r.id_hotel = :id_hotel"
        ),
        {
            "intencao": intencao,
            "sentimento": sentimento,
            "urgencia": urgencia,
            "c": json.dumps(classificacao),
            "id": id_mensagem,
            "id_hotel": id_hotel,
        },
    )
    return resultado.rowcount or 0


def gravar_resposta_duvida(
    conexao: Connection,
    *,
    id_hotel: int,
    id_mensagem: int,
    resposta: str,
    id_mensagem_resposta: int,
    desfecho: str | None = None,
) -> int:
    import json

    extra = {"resposta": resposta, "id_mensagem_resposta": id_mensagem_resposta}
    if desfecho is not None:
        extra["desfecho"] = desfecho
    resultado = conexao.execute(
        text(
            "UPDATE mensagem m SET"
            " classificacao_bruta = COALESCE(m.classificacao_bruta, '{}'::jsonb)"
            " || CAST(:extra AS jsonb)"
            " FROM reserva r"
            " WHERE m.id_mensagem = :id"
            " AND m.id_reserva = r.id_reserva"
            " AND r.id_hotel = :id_hotel"
        ),
        {
            "extra": json.dumps(extra),
            "id": id_mensagem,
            "id_hotel": id_hotel,
        },
    )
    return resultado.rowcount or 0


def ler_nome_titular(conexao: Connection, *, id_reserva: int) -> str | None:
    return conexao.execute(
        text(
            "SELECT h.nome_completo FROM reserva_hospede rh"
            " JOIN hospede h ON h.id_hospede = rh.id_hospede"
            " WHERE rh.id_reserva = :id AND rh.titular"
        ),
        {"id": id_reserva},
    ).scalar_one_or_none()


def resolver_reserva_aguardando_cadastro(
    conexao: Connection,
    *,
    id_hotel: int,
    telefone_contato: str,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_reserva, id_hotel, status, telefone_contato"
            " FROM reserva"
            " WHERE id_hotel = :id_hotel"
            " AND telefone_contato = :telefone"
            " AND status = 'aguardando_cadastro'"
            " ORDER BY id_reserva DESC"
            " LIMIT 1"
        ),
        {"id_hotel": id_hotel, "telefone": telefone_contato},
    ).mappings().first()
    return dict(linha) if linha else None


def resolver_reserva_hospedada(
    conexao: Connection,
    *,
    id_hotel: int,
    telefone_contato: str,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_reserva, id_hotel, status, telefone_contato"
            " FROM reserva"
            " WHERE id_hotel = :id_hotel"
            " AND telefone_contato = :telefone"
            " AND status = 'hospedado'"
            " ORDER BY id_reserva DESC"
            " LIMIT 1"
        ),
        {"id_hotel": id_hotel, "telefone": telefone_contato},
    ).mappings().first()
    return dict(linha) if linha else None


def instante_coleta_enviada(
    conexao: Connection, *, id_reserva: int
) -> datetime | None:
    return conexao.execute(
        text(
            "SELECT enviada_em FROM mensagem"
            " WHERE id_reserva = :id AND direcao = 'enviada'"
            " AND status_envio = 'enviada'"
            " ORDER BY enviada_em ASC, id_mensagem ASC"
            " LIMIT 1"
        ),
        {"id": id_reserva},
    ).scalar_one_or_none()


def tem_mensagem_recebida(conexao: Connection, *, id_reserva: int) -> bool:
    return bool(
        conexao.execute(
            text(
                "SELECT 1 FROM mensagem"
                " WHERE id_reserva = :id AND direcao = 'recebida'"
                " LIMIT 1"
            ),
            {"id": id_reserva},
        ).scalar()
    )
