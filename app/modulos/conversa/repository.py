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


def listar_mensagens_simulador(
    conexao: Connection, *, id_hotel: int, id_reserva: int
) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT m.id_mensagem, m.direcao, m.conteudo, m.status_envio,"
            " m.enviada_em"
            " FROM mensagem m"
            " JOIN reserva r ON r.id_reserva = m.id_reserva"
            " WHERE m.id_reserva = :id_reserva AND r.id_hotel = :id_hotel"
            " ORDER BY m.enviada_em ASC, m.id_mensagem ASC"
        ),
        {"id_reserva": id_reserva, "id_hotel": id_hotel},
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


def gravar_confirmacao_pedido(
    conexao: Connection,
    *,
    id_hotel: int,
    id_mensagem: int,
    id_mensagem_resposta: int,
    id_solicitacao: int,
) -> int:
    import json

    extra = {
        "resposta": "confirmacao_pedido",
        "id_mensagem_resposta": id_mensagem_resposta,
        "id_solicitacao": id_solicitacao,
    }
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


def gravar_confirmacao_consumo(
    conexao: Connection,
    *,
    id_hotel: int,
    id_mensagem: int,
    id_mensagem_resposta: int,
    id_solicitacao: int,
    id_item_vendavel: int,
    quantidade: int,
) -> int:
    import json

    extra = {
        "resposta": "confirmacao_consumo",
        "id_mensagem_resposta": id_mensagem_resposta,
        "id_solicitacao": id_solicitacao,
        "id_item_vendavel": id_item_vendavel,
        "quantidade": quantidade,
    }
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


def gravar_aviso_identificacao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_mensagem: int,
    id_mensagem_resposta: int,
    desfecho: str,
) -> int:
    import json

    extra = {
        "resposta": "aviso_identificacao",
        "desfecho": desfecho,
        "id_mensagem_resposta": id_mensagem_resposta,
    }
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


def gravar_confirmacao_reclamacao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_mensagem: int,
    id_mensagem_resposta: int,
    id_solicitacao: int,
) -> int:
    import json

    extra = {
        "resposta": "confirmacao_reclamacao",
        "id_mensagem_resposta": id_mensagem_resposta,
        "id_solicitacao": id_solicitacao,
    }
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


def pulso_foi_enviado(conexao: Connection, *, id_reserva: int) -> bool:
    return bool(
        conexao.execute(
            text(
                "SELECT 1 FROM trabalho t"
                " JOIN mensagem m"
                "   ON m.id_mensagem = (t.payload->>'id_mensagem')::bigint"
                " WHERE t.tipo = 'enviar_pulso'"
                " AND (t.payload->>'id_reserva')::bigint = :id"
                " AND m.status_envio = 'enviada'"
                " LIMIT 1"
            ),
            {"id": id_reserva},
        ).scalar()
    )


def gravar_resposta_pulso(
    conexao: Connection,
    *,
    id_hotel: int,
    id_mensagem: int,
    id_mensagem_resposta: int,
    resposta: str,
    id_solicitacao: int | None = None,
    id_avaliacao: int | None = None,
) -> int:
    import json

    extra = {
        "resposta": resposta,
        "id_mensagem_resposta": id_mensagem_resposta,
    }
    if id_solicitacao is not None:
        extra["id_solicitacao"] = id_solicitacao
    if id_avaliacao is not None:
        extra["id_avaliacao"] = id_avaliacao
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


def resolver_reserva_encerrada_pesquisa(
    conexao: Connection,
    *,
    id_hotel: int,
    telefone_contato: str,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT r.id_reserva, r.id_hotel, r.status, r.telefone_contato,"
            " r.checkout_em"
            " FROM reserva r"
            " WHERE r.id_hotel = :id_hotel"
            " AND r.telefone_contato = :telefone"
            " AND r.status = 'encerrado'"
            " AND EXISTS ("
            "   SELECT 1 FROM trabalho t"
            "    WHERE t.tipo = 'enviar_pesquisa_saida'"
            "      AND (t.payload->>'id_reserva')::bigint = r.id_reserva"
            " )"
            " AND NOT ("
            "   EXISTS ("
            "     SELECT 1 FROM avaliacao a"
            "      WHERE a.id_reserva = r.id_reserva"
            "        AND a.origem = 'checkout'"
            "        AND a.nota IS NOT NULL"
            "   )"
            "   AND EXISTS ("
            "     SELECT 1 FROM consentimento c"
            "     JOIN reserva_hospede rh"
            "       ON rh.id_hospede = c.id_hospede AND rh.titular"
            "      WHERE rh.id_reserva = r.id_reserva"
            "        AND c.origem = 'pesquisa_checkout'"
            "        AND c.momento >= r.checkout_em"
            "   )"
            " )"
            " ORDER BY r.id_reserva DESC"
            " LIMIT 1"
        ),
        {"id_hotel": id_hotel, "telefone": telefone_contato},
    ).mappings().first()
    return dict(linha) if linha else None


def resolver_reserva_encerrada(
    conexao: Connection,
    *,
    id_hotel: int,
    telefone_contato: str,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_reserva, id_hotel, status, telefone_contato, checkout_em"
            " FROM reserva"
            " WHERE id_hotel = :id_hotel"
            " AND telefone_contato = :telefone"
            " AND status = 'encerrado'"
            " ORDER BY id_reserva DESC"
            " LIMIT 1"
        ),
        {"id_hotel": id_hotel, "telefone": telefone_contato},
    ).mappings().first()
    return dict(linha) if linha else None


def ler_checkout_da_reserva(
    conexao: Connection, *, id_reserva: int
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_reserva, id_hotel, status, checkout_em"
            " FROM reserva WHERE id_reserva = :id"
        ),
        {"id": id_reserva},
    ).mappings().first()
    return dict(linha) if linha else None


def anonimizar_mensagens_vencidas(
    conexao: Connection,
    *,
    id_hotel: int,
    agora,
    meses: int,
    marca: str,
) -> int:
    resultado = conexao.execute(
        text(
            "UPDATE mensagem m SET conteudo = :marca, classificacao_bruta = NULL"
            " FROM reserva r"
            " WHERE m.id_reserva = r.id_reserva"
            " AND r.id_hotel = :id_hotel"
            " AND r.checkout_em IS NOT NULL"
            " AND r.checkout_em + make_interval(months => :meses) <= :agora"
            " AND m.conteudo IS DISTINCT FROM :marca"
        ),
        {
            "marca": marca,
            "id_hotel": id_hotel,
            "meses": meses,
            "agora": agora,
        },
    )
    return resultado.rowcount or 0


def anonimizar_payloads_vencidos(
    conexao: Connection,
    *,
    id_hotel: int,
    agora,
    meses: int,
    marca_json: str,
) -> int:
    resultado = conexao.execute(
        text(
            "UPDATE evento_webhook e SET payload = CAST(:marca AS jsonb)"
            " FROM mensagem m"
            " JOIN reserva r ON r.id_reserva = m.id_reserva"
            " WHERE e.id_externo = m.id_externo"
            " AND m.id_externo IS NOT NULL"
            " AND r.id_hotel = :id_hotel"
            " AND r.checkout_em IS NOT NULL"
            " AND r.checkout_em + make_interval(months => :meses) <= :agora"
            " AND e.payload IS DISTINCT FROM CAST(:marca AS jsonb)"
        ),
        {
            "marca": marca_json,
            "id_hotel": id_hotel,
            "meses": meses,
            "agora": agora,
        },
    )
    return resultado.rowcount or 0
