"""Acesso a hospede, reserva e fila — sem regra de negocio."""

from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Connection


def inserir_hospede(conexao: Connection, *, nome_completo: str, telefone: str) -> int:
    return conexao.execute(
        text(
            "INSERT INTO hospede (nome_completo, telefone) "
            "VALUES (:nome, :telefone) RETURNING id_hospede"
        ),
        {"nome": nome_completo, "telefone": telefone},
    ).scalar_one()


def inserir_reserva(
    conexao: Connection,
    *,
    id_hotel: int,
    telefone_contato: str,
    data_checkin_prevista: date,
    data_checkout_prevista: date,
    status: str,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO reserva ("
            " id_hotel, telefone_contato, data_checkin_prevista,"
            " data_checkout_prevista, status"
            ") VALUES ("
            " :id_hotel, :telefone, :checkin, :checkout, :status"
            ") RETURNING id_reserva"
        ),
        {
            "id_hotel": id_hotel,
            "telefone": telefone_contato,
            "checkin": data_checkin_prevista,
            "checkout": data_checkout_prevista,
            "status": status,
        },
    ).scalar_one()


def inserir_vinculo_titular(
    conexao: Connection,
    *,
    id_reserva: int,
    id_hospede: int,
) -> None:
    conexao.execute(
        text(
            "INSERT INTO reserva_hospede ("
            " id_reserva, id_hospede, titular, ficha_completa"
            ") VALUES (:id_reserva, :id_hospede, TRUE, FALSE)"
        ),
        {"id_reserva": id_reserva, "id_hospede": id_hospede},
    )


def listar_fila_do_hotel(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_hotel, id_reserva, data_checkin_prevista,"
            " data_checkout_prevista, telefone_contato, status,"
            " nome_completo, ficha_completa, chegada_nao_confirmada,"
            " status_envio_coleta, estado_cadastro, boas_vindas_nao_enviadas,"
            " precisa_atendimento_humano"
            " FROM vw_fila_do_dia"
            " WHERE id_hotel = :id_hotel"
            " ORDER BY data_checkin_prevista ASC, id_reserva ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def contar_chegadas_do_dia(conexao: Connection, *, id_hotel: int) -> int:
    return conexao.execute(
        text(
            "SELECT COUNT(*) FROM reserva"
            " WHERE id_hotel = :id_hotel"
            " AND data_checkin_prevista = CURRENT_DATE"
            " AND status NOT IN ('encerrado', 'cancelada')"
        ),
        {"id_hotel": id_hotel},
    ).scalar_one()


def ler_titular_da_reserva(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT r.id_reserva, r.id_hotel, r.status, r.telefone_contato,"
            " rh.id_hospede, rh.ficha_completa,"
            " h.nome_completo, h.profissao, h.data_nascimento,"
            " h.tipo_documento, h.numero_documento, h.endereco, h.cep,"
            " h.cidade, h.telefone"
            " FROM reserva r"
            " JOIN reserva_hospede rh ON rh.id_reserva = r.id_reserva AND rh.titular"
            " JOIN hospede h ON h.id_hospede = rh.id_hospede"
            " WHERE r.id_reserva = :id_reserva AND r.id_hotel = :id_hotel"
        ),
        {"id_reserva": id_reserva, "id_hotel": id_hotel},
    ).mappings().first()
    return dict(linha) if linha else None


def atualizar_hospede_titular(
    conexao: Connection,
    *,
    id_hospede: int,
    campos: dict,
) -> None:
    from datetime import date

    mapeamento = {
        "nome_completo": "nome_completo",
        "profissao": "profissao",
        "data_nascimento": "data_nascimento",
        "tipo_documento": "tipo_documento",
        "numero_documento": "numero_documento",
        "endereco": "endereco",
        "cep": "cep",
        "cidade": "cidade",
        "telefone": "telefone",
    }
    sets = []
    params: dict = {"id": id_hospede}
    for chave, coluna in mapeamento.items():
        if chave not in campos:
            continue
        valor = campos[chave]
        if chave == "data_nascimento" and isinstance(valor, str):
            valor = date.fromisoformat(valor)
        sets.append(f"{coluna} = :{coluna}")
        params[coluna] = valor
    if not sets:
        return
    conexao.execute(
        text(f"UPDATE hospede SET {', '.join(sets)} WHERE id_hospede = :id"),
        params,
    )


def marcar_ficha_completa(
    conexao: Connection,
    *,
    id_reserva: int,
    completa: bool,
) -> None:
    conexao.execute(
        text(
            "UPDATE reserva_hospede SET ficha_completa = :completa"
            " WHERE id_reserva = :id AND titular"
        ),
        {"completa": completa, "id": id_reserva},
    )


def atualizar_status_reserva(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    status: str,
) -> None:
    conexao.execute(
        text(
            "UPDATE reserva SET status = :status"
            " WHERE id_reserva = :id AND id_hotel = :id_hotel"
        ),
        {"status": status, "id": id_reserva, "id_hotel": id_hotel},
    )


def estado_cadastro_da_reserva(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
) -> str | None:
    return conexao.execute(
        text(
            "SELECT estado_cadastro FROM vw_fila_do_dia"
            " WHERE id_hotel = :id_hotel AND id_reserva = :id"
        ),
        {"id_hotel": id_hotel, "id": id_reserva},
    ).scalar_one_or_none()


def listar_reservas_aguardando_cadastro(conexao: Connection) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT r.id_reserva, r.id_hotel, r.data_checkin_prevista,"
            " r.reenvio_realizado, h.nome_completo"
            " FROM reserva r"
            " JOIN reserva_hospede rh"
            "   ON rh.id_reserva = r.id_reserva AND rh.titular"
            " JOIN hospede h ON h.id_hospede = rh.id_hospede"
            " WHERE r.status = 'aguardando_cadastro'"
            " ORDER BY r.id_reserva ASC"
        )
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def marcar_reenvio_realizado(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
) -> None:
    conexao.execute(
        text(
            "UPDATE reserva SET reenvio_realizado = TRUE"
            " WHERE id_reserva = :id AND id_hotel = :id_hotel"
        ),
        {"id": id_reserva, "id_hotel": id_hotel},
    )


def marcar_sem_cadastro_previo(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
) -> None:
    conexao.execute(
        text(
            "UPDATE reserva SET status = 'sem_cadastro_previo'"
            " WHERE id_reserva = :id AND id_hotel = :id_hotel"
            " AND status = 'aguardando_cadastro'"
        ),
        {"id": id_reserva, "id_hotel": id_hotel},
    )


def ler_reserva_do_hotel(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_reserva, id_hotel, status, checkin_em,"
            " data_checkin_prevista, data_checkout_prevista, telefone_contato"
            " FROM reserva"
            " WHERE id_reserva = :id AND id_hotel = :id_hotel"
        ),
        {"id": id_reserva, "id_hotel": id_hotel},
    ).mappings().first()
    return dict(linha) if linha else None


def confirmar_chegada(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
) -> dict | None:
    linha = conexao.execute(
        text(
            "UPDATE reserva SET status = 'hospedado', checkin_em = now()"
            " WHERE id_reserva = :id AND id_hotel = :id_hotel"
            " AND status IN ("
            " 'ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo'"
            " )"
            " RETURNING status, checkin_em"
        ),
        {"id": id_reserva, "id_hotel": id_hotel},
    ).mappings().first()
    return dict(linha) if linha else None


def listar_hospedados_sem_boas_vindas(conexao: Connection) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT r.id_reserva, r.id_hotel, r.checkin_em,"
            " r.data_checkout_prevista, h.nome_completo"
            " FROM reserva r"
            " JOIN reserva_hospede rh"
            "   ON rh.id_reserva = r.id_reserva AND rh.titular"
            " JOIN hospede h ON h.id_hospede = rh.id_hospede"
            " WHERE r.status = 'hospedado'"
            " AND r.checkin_em IS NOT NULL"
            " AND NOT EXISTS ("
            "   SELECT 1 FROM trabalho t"
            "    WHERE t.tipo = 'enviar_boas_vindas'"
            "      AND (t.payload->>'id_reserva')::bigint = r.id_reserva"
            " )"
            " ORDER BY r.id_reserva ASC"
        )
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def listar_hospedados_sem_pulso(conexao: Connection) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT r.id_reserva, r.id_hotel, r.checkin_em,"
            " r.data_checkout_prevista, h.nome_completo"
            " FROM reserva r"
            " JOIN reserva_hospede rh"
            "   ON rh.id_reserva = r.id_reserva AND rh.titular"
            " JOIN hospede h ON h.id_hospede = rh.id_hospede"
            " WHERE r.status = 'hospedado'"
            " AND r.checkin_em IS NOT NULL"
            " AND NOT EXISTS ("
            "   SELECT 1 FROM trabalho t"
            "    WHERE t.tipo = 'enviar_pulso'"
            "      AND (t.payload->>'id_reserva')::bigint = r.id_reserva"
            " )"
            " ORDER BY r.id_reserva ASC"
        )
    ).mappings().all()
    return [dict(linha) for linha in linhas]
