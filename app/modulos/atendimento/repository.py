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


def inserir_consumo(
    conexao: Connection,
    *,
    id_reserva: int,
    id_mensagem: int,
    descricao: str,
    descricao_item: str,
    valor_praticado,
    numero_quarto: str | None,
    urgencia: str,
) -> int:
    id_solicitacao = conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, id_mensagem_origem, tipo,"
            " descricao, numero_quarto, urgencia, status) "
            "VALUES (:id_reserva, :id_mensagem, 'consumo', :descricao,"
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
    conexao.execute(
        text(
            "INSERT INTO consumo (id_solicitacao, descricao_item, valor_praticado) "
            "VALUES (:id, :item, :valor)"
        ),
        {
            "id": id_solicitacao,
            "item": descricao_item[:160],
            "valor": valor_praticado,
        },
    )
    return id_solicitacao


def hotel_da_reserva(conexao: Connection, *, id_reserva: int) -> int | None:
    return conexao.execute(
        text("SELECT id_hotel FROM reserva WHERE id_reserva = :id"),
        {"id": id_reserva},
    ).scalar_one_or_none()


def tem_reclamacao_aberta(conexao: Connection, *, id_reserva: int) -> bool:
    return bool(
        conexao.execute(
            text(
                "SELECT 1 FROM solicitacao"
                " WHERE id_reserva = :id"
                " AND tipo = 'reclamacao'"
                " AND status IN ('aberta', 'em_andamento')"
                " LIMIT 1"
            ),
            {"id": id_reserva},
        ).scalar()
    )


def tem_reclamacao_da_mensagem(conexao: Connection, *, id_mensagem: int) -> bool:
    return bool(
        conexao.execute(
            text(
                "SELECT 1 FROM solicitacao"
                " WHERE id_mensagem_origem = :id"
                " AND tipo = 'reclamacao'"
                " LIMIT 1"
            ),
            {"id": id_mensagem},
        ).scalar()
    )


def listar_abertas(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT s.id_solicitacao, s.id_reserva, s.tipo, s.descricao,"
            " s.numero_quarto, s.urgencia, s.status, s.aberta_em,"
            " s.janela_preferencia, c.valor_praticado, c.status_lancamento"
            " FROM solicitacao s"
            " JOIN reserva r ON r.id_reserva = s.id_reserva"
            " LEFT JOIN consumo c ON c.id_solicitacao = s.id_solicitacao"
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
            " AND s.tipo IN ('reclamacao', 'servico', 'consumo')"
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


def listar_pendentes(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT s.id_solicitacao, s.id_reserva, s.descricao, s.numero_quarto,"
            " s.aberta_em, s.resolvida_em, c.descricao_item, c.valor_praticado,"
            " c.status_lancamento"
            " FROM consumo c"
            " JOIN solicitacao s ON s.id_solicitacao = c.id_solicitacao"
            " JOIN reserva r ON r.id_reserva = s.id_reserva"
            " WHERE r.id_hotel = :id_hotel"
            " AND c.status_lancamento = 'pendente'"
            " ORDER BY s.aberta_em ASC, s.id_solicitacao ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def marcar_lancamento(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
    id_usuario: int,
    lancado_em,
    status_destino: str,
) -> dict | None:
    linha = conexao.execute(
        text(
            "UPDATE consumo c SET status_lancamento = :destino,"
            " id_usuario_lancamento = :uid, lancado_em = :quando"
            " FROM solicitacao s, reserva r"
            " WHERE c.id_solicitacao = s.id_solicitacao"
            " AND s.id_reserva = r.id_reserva"
            " AND c.id_solicitacao = :id"
            " AND r.id_hotel = :id_hotel"
            " AND s.tipo = 'consumo'"
            " AND c.status_lancamento = 'pendente'"
            " RETURNING c.id_solicitacao, c.status_lancamento,"
            " c.id_usuario_lancamento, c.lancado_em, c.valor_praticado"
        ),
        {
            "id": id_solicitacao,
            "id_hotel": id_hotel,
            "uid": id_usuario,
            "quando": lancado_em,
            "destino": status_destino,
        },
    ).mappings().first()
    return dict(linha) if linha else None


def ler_consumo_do_hotel(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT c.id_solicitacao, c.status_lancamento, c.valor_praticado,"
            " s.tipo"
            " FROM consumo c"
            " JOIN solicitacao s ON s.id_solicitacao = c.id_solicitacao"
            " JOIN reserva r ON r.id_reserva = s.id_reserva"
            " WHERE c.id_solicitacao = :id AND r.id_hotel = :id_hotel"
        ),
        {"id": id_solicitacao, "id_hotel": id_hotel},
    ).mappings().first()
    return dict(linha) if linha else None
