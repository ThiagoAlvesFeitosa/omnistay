"""Acesso a solicitacao — sem regra de negocio."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def inserir_servico(
    conexao: Connection,
    *,
    id_reserva: int,
    id_mensagem: int,
    descricao: str,
    numero_quarto: str | None,
    urgencia: str,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, id_mensagem_origem, tipo,"
            " descricao, numero_quarto, urgencia, status) "
            "VALUES (:id_reserva, :id_mensagem, 'servico', :descricao,"
            " :numero_quarto, :urgencia, 'aberta') "
            "RETURNING id_solicitacao"
        ),
        {
            "id_reserva": id_reserva,
            "id_mensagem": id_mensagem,
            "descricao": descricao,
            "numero_quarto": numero_quarto,
            "urgencia": urgencia,
        },
    ).scalar_one()


def inserir_reclamacao(
    conexao: Connection,
    *,
    id_reserva: int,
    id_mensagem: int,
    descricao: str,
    numero_quarto: str | None,
    urgencia: str,
    janela_preferencia: str | None,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, id_mensagem_origem, tipo,"
            " descricao, numero_quarto, urgencia, janela_preferencia, status) "
            "VALUES (:id_reserva, :id_mensagem, 'reclamacao', :descricao,"
            " :numero_quarto, :urgencia, :janela, 'aberta') "
            "RETURNING id_solicitacao"
        ),
        {
            "id_reserva": id_reserva,
            "id_mensagem": id_mensagem,
            "descricao": descricao,
            "numero_quarto": numero_quarto,
            "urgencia": urgencia,
            "janela": janela_preferencia,
        },
    ).scalar_one()


def hotel_da_reserva(conexao: Connection, *, id_reserva: int) -> int | None:
    return conexao.execute(
        text("SELECT id_hotel FROM reserva WHERE id_reserva = :id"),
        {"id": id_reserva},
    ).scalar_one_or_none()


def listar_abertas(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT s.id_solicitacao, s.id_reserva, s.tipo, s.descricao,"
            " s.numero_quarto, s.urgencia, s.status, s.aberta_em,"
            " s.janela_preferencia"
            " FROM solicitacao s"
            " JOIN reserva r ON r.id_reserva = s.id_reserva"
            " WHERE r.id_hotel = :id_hotel"
            " AND s.status IN ('aberta', 'em_andamento')"
            " ORDER BY s.aberta_em ASC, s.id_solicitacao ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def completar_janela_aberta(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    janela: str,
) -> int | None:
    preenchida = conexao.execute(
        text(
            "UPDATE solicitacao SET janela_preferencia = :janela"
            " WHERE id_solicitacao = ("
            "   SELECT s.id_solicitacao FROM solicitacao s"
            "   JOIN reserva r ON r.id_reserva = s.id_reserva"
            "   WHERE s.id_reserva = :id_reserva"
            "   AND r.id_hotel = :id_hotel"
            "   AND s.tipo = 'reclamacao'"
            "   AND s.status IN ('aberta', 'em_andamento')"
            "   AND s.janela_preferencia IS NULL"
            "   ORDER BY s.aberta_em ASC, s.id_solicitacao ASC"
            "   LIMIT 1"
            " ) RETURNING id_solicitacao"
        ),
        {
            "id_hotel": id_hotel,
            "id_reserva": id_reserva,
            "janela": janela,
        },
    ).scalar_one_or_none()
    if preenchida is not None:
        return preenchida
    return conexao.execute(
        text(
            "SELECT s.id_solicitacao FROM solicitacao s"
            " JOIN reserva r ON r.id_reserva = s.id_reserva"
            " WHERE s.id_reserva = :id_reserva"
            " AND r.id_hotel = :id_hotel"
            " AND s.tipo = 'reclamacao'"
            " AND s.status IN ('aberta', 'em_andamento')"
            " ORDER BY s.aberta_em ASC, s.id_solicitacao ASC"
            " LIMIT 1"
        ),
        {"id_hotel": id_hotel, "id_reserva": id_reserva},
    ).scalar_one_or_none()


def marcar_resolvida(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
    id_usuario: int,
    resolvida_em,
) -> dict | None:
    linha = conexao.execute(
        text(
            "UPDATE solicitacao s SET status = 'resolvida',"
            " resolvida_em = :quando, id_usuario_responsavel = :uid"
            " FROM reserva r"
            " WHERE s.id_solicitacao = :id"
            " AND s.id_reserva = r.id_reserva"
            " AND r.id_hotel = :id_hotel"
            " AND s.tipo IN ('reclamacao', 'servico')"
            " AND s.status IN ('aberta', 'em_andamento')"
            " RETURNING s.id_solicitacao, s.id_reserva, s.tipo, s.status,"
            " s.resolvida_em, s.id_usuario_responsavel"
        ),
        {
            "id": id_solicitacao,
            "id_hotel": id_hotel,
            "uid": id_usuario,
            "quando": resolvida_em,
        },
    ).mappings().first()
    return dict(linha) if linha else None


def ler_do_hotel(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT s.id_solicitacao, s.id_reserva, s.tipo, s.status,"
            " s.resolvida_em, s.id_usuario_responsavel"
            " FROM solicitacao s"
            " JOIN reserva r ON r.id_reserva = s.id_reserva"
            " WHERE s.id_solicitacao = :id AND r.id_hotel = :id_hotel"
        ),
        {"id": id_solicitacao, "id_hotel": id_hotel},
    ).mappings().first()
    return dict(linha) if linha else None
