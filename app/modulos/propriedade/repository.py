"""Acesso a hotel e parametro_hotel. Nao conhece usuario nem sessao."""

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError


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


def ler_nome_hotel(conexao: Connection, id_hotel: int) -> str | None:
    return conexao.execute(
        text("SELECT nome FROM hotel WHERE id_hotel = :id_hotel"),
        {"id_hotel": id_hotel},
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


def inserir_item_vendavel(
    conexao: Connection,
    *,
    id_hotel: int,
    nome: str,
    preco_atual,
) -> dict:
    linha = conexao.execute(
        text(
            "INSERT INTO item_vendavel (id_hotel, nome, preco_atual) "
            "VALUES (:id_hotel, :nome, :preco) "
            "RETURNING id_item_vendavel, id_hotel, nome, preco_atual, ativo,"
            " atualizado_em"
        ),
        {"id_hotel": id_hotel, "nome": nome, "preco": preco_atual},
    ).mappings().one()
    return dict(linha)


def atualizar_item_vendavel(
    conexao: Connection,
    *,
    id_hotel: int,
    id_item_vendavel: int,
    nome: str | None = None,
    preco_atual=None,
    ativo: bool | None = None,
) -> dict | None:
    linha = conexao.execute(
        text(
            "UPDATE item_vendavel SET"
            " nome = COALESCE(:nome, nome),"
            " preco_atual = COALESCE(:preco, preco_atual),"
            " ativo = COALESCE(:ativo, ativo),"
            " atualizado_em = now()"
            " WHERE id_item_vendavel = :id AND id_hotel = :id_hotel"
            " RETURNING id_item_vendavel, id_hotel, nome, preco_atual, ativo,"
            " atualizado_em"
        ),
        {
            "id_hotel": id_hotel,
            "id": id_item_vendavel,
            "nome": nome,
            "preco": preco_atual,
            "ativo": ativo,
        },
    ).mappings().one_or_none()
    return dict(linha) if linha is not None else None


def listar_itens_vendaveis_manutencao(
    conexao: Connection, *, id_hotel: int
) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_item_vendavel, id_hotel, nome, preco_atual, ativo,"
            " atualizado_em FROM item_vendavel"
            " WHERE id_hotel = :id_hotel"
            " ORDER BY nome ASC, id_item_vendavel ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def listar_itens_vendaveis_ativos(
    conexao: Connection, *, id_hotel: int
) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_item_vendavel, nome FROM item_vendavel"
            " WHERE id_hotel = :id_hotel AND ativo"
            " ORDER BY nome ASC, id_item_vendavel ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def ler_preco_item_ativo(
    conexao: Connection, *, id_hotel: int, id_item_vendavel: int
):
    return conexao.execute(
        text(
            "SELECT preco_atual FROM item_vendavel"
            " WHERE id_item_vendavel = :id AND id_hotel = :id_hotel AND ativo"
        ),
        {"id": id_item_vendavel, "id_hotel": id_hotel},
    ).scalar_one_or_none()


def existe_nome_ativo(
    conexao: Connection,
    *,
    id_hotel: int,
    nome: str,
    exceto_id: int | None = None,
) -> bool:
    return bool(
        conexao.execute(
            text(
                "SELECT 1 FROM item_vendavel"
                " WHERE id_hotel = :id_hotel AND ativo"
                " AND lower(nome) = lower(:nome)"
                " AND (:exceto_id IS NULL OR id_item_vendavel <> :exceto_id)"
            ),
            {"id_hotel": id_hotel, "nome": nome, "exceto_id": exceto_id},
        ).scalar()
    )


def listar_ids_hotel(conexao: Connection) -> list[int]:
    linhas = conexao.execute(
        text("SELECT id_hotel FROM hotel ORDER BY id_hotel ASC")
    ).scalars().all()
    return [int(id_hotel) for id_hotel in linhas]


def ja_executou_retencao_no_dia(
    conexao: Connection, *, id_hotel: int, agora
) -> bool:
    return bool(
        conexao.execute(
            text(
                "SELECT 1 FROM execucao_retencao"
                " WHERE id_hotel = :id_hotel"
                " AND (executado_em AT TIME ZONE 'UTC')::date"
                "     = (:agora AT TIME ZONE 'UTC')::date"
            ),
            {"id_hotel": id_hotel, "agora": agora},
        ).scalar()
    )


def registrar_execucao_retencao(
    conexao: Connection,
    *,
    id_hotel: int,
    executado_em,
    mensagens_anonimizadas: int = 0,
    comentarios_anonimizados: int = 0,
    payloads_anonimizados: int = 0,
    descricoes_anonimizadas: int = 0,
    fichas_apagadas: int = 0,
    prazo_conteudo_ausente: bool = False,
    prazo_ficha_ausente: bool = False,
) -> int | None:
    sql = text(
        "INSERT INTO execucao_retencao ("
        " id_hotel, executado_em, mensagens_anonimizadas,"
        " comentarios_anonimizados, payloads_anonimizados,"
        " descricoes_anonimizadas, fichas_apagadas,"
        " prazo_conteudo_ausente, prazo_ficha_ausente)"
        " VALUES ("
        " :id_hotel, :executado_em, :mensagens,"
        " :comentarios, :payloads, :descricoes, :fichas,"
        " :prazo_conteudo, :prazo_ficha)"
        " RETURNING id_execucao"
    )
    params = {
        "id_hotel": id_hotel,
        "executado_em": executado_em,
        "mensagens": mensagens_anonimizadas,
        "comentarios": comentarios_anonimizados,
        "payloads": payloads_anonimizados,
        "descricoes": descricoes_anonimizadas,
        "fichas": fichas_apagadas,
        "prazo_conteudo": prazo_conteudo_ausente,
        "prazo_ficha": prazo_ficha_ausente,
    }
    try:
        begin = getattr(conexao, "begin_nested", None)
        if begin is not None:
            with conexao.begin_nested():
                return int(conexao.execute(sql, params).scalar_one())
        return int(conexao.execute(sql, params).scalar_one())
    except IntegrityError as erro:
        if "uq_execucao_retencao_hotel_dia" not in str(erro):
            raise
        return None


def listar_execucoes_retencao(
    conexao: Connection, *, id_hotel: int
) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_execucao, executado_em,"
            " mensagens_anonimizadas, comentarios_anonimizados,"
            " payloads_anonimizados, descricoes_anonimizadas,"
            " fichas_apagadas, prazo_conteudo_ausente, prazo_ficha_ausente"
            " FROM execucao_retencao"
            " WHERE id_hotel = :id_hotel"
            " ORDER BY executado_em DESC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]
