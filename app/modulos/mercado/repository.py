"""Acesso a concorrente. Nao conhece HTTP nem regra de URL."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def inserir(conexao: Connection, *, id_hotel: int, nome: str, url_fonte: str) -> dict:
    linha = conexao.execute(
        text(
            "INSERT INTO concorrente (id_hotel, nome, url_fonte) "
            "VALUES (:id_hotel, :nome, :url) "
            "RETURNING id_concorrente, id_hotel, nome, url_fonte, ativo"
        ),
        {"id_hotel": id_hotel, "nome": nome, "url": url_fonte},
    ).mappings().one()
    return dict(linha)


def existe_fonte(
    conexao: Connection,
    *,
    id_hotel: int,
    url_fonte: str,
    exceto_id: int | None = None,
) -> bool:
    return bool(
        conexao.execute(
            text(
                "SELECT 1 FROM concorrente"
                " WHERE id_hotel = :id_hotel"
                " AND lower(btrim(url_fonte)) = lower(btrim(:url))"
                " AND (:exceto_id IS NULL OR id_concorrente <> :exceto_id)"
            ),
            {"id_hotel": id_hotel, "url": url_fonte, "exceto_id": exceto_id},
        ).scalar()
    )


def atualizar(
    conexao: Connection,
    *,
    id_hotel: int,
    id_concorrente: int,
    nome: str | None = None,
    url_fonte: str | None = None,
    ativo: bool | None = None,
) -> dict | None:
    linha = conexao.execute(
        text(
            "UPDATE concorrente SET"
            " nome = COALESCE(:nome, nome),"
            " url_fonte = COALESCE(:url, url_fonte),"
            " ativo = COALESCE(:ativo, ativo)"
            " WHERE id_concorrente = :id AND id_hotel = :id_hotel"
            " RETURNING id_concorrente, id_hotel, nome, url_fonte, ativo"
        ),
        {
            "id_hotel": id_hotel,
            "id": id_concorrente,
            "nome": nome,
            "url": url_fonte,
            "ativo": ativo,
        },
    ).mappings().one_or_none()
    return dict(linha) if linha is not None else None


def listar_manutencao(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_concorrente, id_hotel, nome, url_fonte, ativo"
            " FROM concorrente"
            " WHERE id_hotel = :id_hotel"
            " ORDER BY nome ASC, id_concorrente ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def listar_ativos(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_concorrente, nome, url_fonte FROM concorrente"
            " WHERE id_hotel = :id_hotel AND ativo"
            " ORDER BY nome ASC, id_concorrente ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def listar_ativos_de_todos(conexao: Connection) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_concorrente, id_hotel, nome, url_fonte"
            " FROM concorrente"
            " WHERE ativo"
            " ORDER BY id_hotel ASC, nome ASC, id_concorrente ASC"
        )
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def obter_ativo(
    conexao: Connection, *, id_hotel: int, id_concorrente: int
) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_concorrente, id_hotel, nome, url_fonte, ativo"
            " FROM concorrente"
            " WHERE id_concorrente = :id AND id_hotel = :id_hotel AND ativo"
        ),
        {"id": id_concorrente, "id_hotel": id_hotel},
    ).mappings().one_or_none()
    return dict(linha) if linha is not None else None


def ultima_coleta(conexao: Connection, *, id_concorrente: int) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_coleta, id_concorrente, preco, nota_media, sucesso,"
            " coletado_em"
            " FROM coleta_mercado"
            " WHERE id_concorrente = :id"
            " ORDER BY coletado_em DESC, id_coleta DESC"
            " LIMIT 1"
        ),
        {"id": id_concorrente},
    ).mappings().one_or_none()
    return dict(linha) if linha is not None else None


def inserir_coleta(
    conexao: Connection,
    *,
    id_concorrente: int,
    sucesso: bool,
    preco=None,
    nota_media=None,
    coletado_em,
) -> dict:
    linha = conexao.execute(
        text(
            "INSERT INTO coleta_mercado"
            " (id_concorrente, preco, nota_media, sucesso, coletado_em)"
            " VALUES (:id, :preco, :nota, :sucesso, :em)"
            " RETURNING id_coleta, id_concorrente, preco, nota_media,"
            " sucesso, coletado_em"
        ),
        {
            "id": id_concorrente,
            "preco": preco,
            "nota": nota_media,
            "sucesso": sucesso,
            "em": coletado_em,
        },
    ).mappings().one()
    return dict(linha)


def criado_em_do_trabalho(conexao: Connection, *, id_trabalho: int):
    return conexao.execute(
        text("SELECT criado_em FROM trabalho WHERE id_trabalho = :id"),
        {"id": id_trabalho},
    ).scalar_one()
