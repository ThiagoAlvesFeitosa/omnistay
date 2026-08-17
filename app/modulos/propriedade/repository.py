"""Acesso a hotel e parametro_hotel. Nao conhece usuario nem sessao."""

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection


def existe_propriedade(conexao: Connection) -> bool:
    return bool(conexao.execute(text("SELECT 1 FROM hotel LIMIT 1")).scalar())


def inserir_hotel(conexao: Connection, nome: str, telefone_whatsapp: str) -> int:
    return conexao.execute(
        text(
            "INSERT INTO hotel (nome, telefone_whatsapp) "
            "VALUES (:nome, :telefone) RETURNING id_hotel"
        ),
        {"nome": nome, "telefone": telefone_whatsapp},
    ).scalar_one()


def inserir_parametro(
    conexao: Connection, id_hotel: int, chave: str, valor: str
) -> None:
    conexao.execute(
        text(
            "INSERT INTO parametro_hotel (id_hotel, chave, valor) "
            "VALUES (:id_hotel, :chave, :valor)"
        ),
        {"id_hotel": id_hotel, "chave": chave, "valor": valor},
    )


def ler_parametro(conexao: Connection, id_hotel: int, chave: str) -> str | None:
    return conexao.execute(
        text(
            "SELECT valor FROM parametro_hotel "
            "WHERE id_hotel = :id_hotel AND chave = :chave"
        ),
        {"id_hotel": id_hotel, "chave": chave},
    ).scalar_one_or_none()


def ler_parametros(
    conexao: Connection, id_hotel: int, chaves: list[str]
) -> dict[str, str]:
    if not chaves:
        return {}
    linhas = conexao.execute(
        text(
            "SELECT chave, valor FROM parametro_hotel "
            "WHERE id_hotel = :id_hotel AND chave IN :chaves"
        ).bindparams(bindparam("chaves", expanding=True)),
        {"id_hotel": id_hotel, "chaves": list(chaves)},
    ).mappings().all()
    return {linha["chave"]: linha["valor"] for linha in linhas}


def upsert_parametro(
    conexao: Connection, id_hotel: int, chave: str, valor: str
) -> None:
    conexao.execute(
        text(
            "INSERT INTO parametro_hotel (id_hotel, chave, valor) "
            "VALUES (:id_hotel, :chave, :valor) "
            "ON CONFLICT (id_hotel, chave) DO UPDATE "
            "SET valor = EXCLUDED.valor, atualizado_em = now()"
        ),
        {"id_hotel": id_hotel, "chave": chave, "valor": valor},
    )


def inserir_item(
    conexao: Connection,
    *,
    id_hotel: int,
    categoria: str,
    titulo: str,
    conteudo: str,
) -> dict:
    linha = conexao.execute(
        text(
            "INSERT INTO catalogo_item ("
            " id_hotel, categoria, titulo, conteudo"
            ") VALUES ("
            " :id_hotel, :categoria, :titulo, :conteudo"
            ") RETURNING id_catalogo_item, id_hotel, categoria, titulo,"
            " conteudo, ativo"
        ),
        {
            "id_hotel": id_hotel,
            "categoria": categoria,
            "titulo": titulo,
            "conteudo": conteudo,
        },
    ).mappings().one()
    return dict(linha)


def atualizar_item(
    conexao: Connection,
    *,
    id_hotel: int,
    id_catalogo_item: int,
    titulo: str | None = None,
    conteudo: str | None = None,
    ativo: bool | None = None,
) -> dict | None:
    linha = conexao.execute(
        text(
            "UPDATE catalogo_item SET"
            " titulo = COALESCE(:titulo, titulo),"
            " conteudo = COALESCE(:conteudo, conteudo),"
            " ativo = COALESCE(:ativo, ativo),"
            " atualizado_em = now()"
            " WHERE id_catalogo_item = :id_catalogo_item"
            " AND id_hotel = :id_hotel"
            " RETURNING id_catalogo_item, id_hotel, categoria, titulo,"
            " conteudo, ativo"
        ),
        {
            "id_hotel": id_hotel,
            "id_catalogo_item": id_catalogo_item,
            "titulo": titulo,
            "conteudo": conteudo,
            "ativo": ativo,
        },
    ).mappings().one_or_none()
    return dict(linha) if linha is not None else None


def listar_manutencao(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_catalogo_item, id_hotel, categoria, titulo, conteudo, ativo"
            " FROM catalogo_item"
            " WHERE id_hotel = :id_hotel"
            " ORDER BY categoria ASC, id_catalogo_item ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def listar_ativos(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_catalogo_item, id_hotel, categoria, titulo, conteudo, ativo"
            " FROM catalogo_item"
            " WHERE id_hotel = :id_hotel AND ativo"
            " ORDER BY categoria ASC, id_catalogo_item ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]
