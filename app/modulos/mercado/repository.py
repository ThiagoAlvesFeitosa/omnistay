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
