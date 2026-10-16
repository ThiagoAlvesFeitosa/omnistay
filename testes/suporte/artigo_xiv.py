"""Verificacao estrutural do Artigo XIV: dono do cadastro.

Cada tabela em `public` precisa ter `id_hotel` ou ser filha, por
chave estrangeira obrigatoria, de uma tabela que ja tem dono.
Ser referenciada nao conta.

Excecoes sao nomeadas aqui, com o motivo. Testes de unidade passam
um inventario falso; o head usa `inventario_do_banco`.
"""

from sqlalchemy import text

EXCECOES = {
    "alembic_version": "Versionamento, nao dominio",
    "evento_webhook": (
        "Idempotencia do canal (id_externo); o hotel entra no processamento"
    ),
}


def tabelas_sem_dono(inventario: dict) -> list[str]:
    """Tabelas sem `id_hotel` e sem pai obrigatorio com dono.

    `inventario` mapeia nome da tabela para `colunas` (conjunto) e
    `fks` (lista de `{tabela, nula}`). Ser referenciado nao conta.
    """
    donos: set[str] = set()
    mudou = True
    while mudou:
        mudou = False
        for nome, tabela in inventario.items():
            if nome in donos:
                continue
            if "id_hotel" in tabela.get("colunas", ()):
                donos.add(nome)
                mudou = True
                continue
            for fk in tabela.get("fks", ()):
                if not fk.get("nula", True) and fk.get("tabela") in donos:
                    donos.add(nome)
                    mudou = True
                    break
    return sorted(
        nome for nome in inventario if nome not in donos and nome not in EXCECOES
    )


def inventario_do_banco(conexao) -> dict:
    """Catalogo de `public`: colunas e FKs, sem olhar linhas."""
    nomes = list(
        conexao.execute(
            text(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relkind = 'r' "
                "ORDER BY c.relname"
            )
        ).scalars()
    )
    inventario = {nome: {"colunas": set(), "fks": []} for nome in nomes}
    for tabela, coluna in conexao.execute(
        text(
            "SELECT c.relname, a.attname FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            " AND n.nspname = 'public' "
            "JOIN pg_attribute a ON a.attrelid = c.oid "
            " AND a.attnum > 0 AND NOT a.attisdropped "
            "WHERE c.relkind = 'r'"
        )
    ):
        inventario[tabela]["colunas"].add(coluna)
    for origem, destino, nula in conexao.execute(
        text(
            "SELECT src.relname, dst.relname, bool_or(NOT a.attnotnull) "
            "FROM pg_constraint con "
            "JOIN pg_class src ON src.oid = con.conrelid "
            "JOIN pg_class dst ON dst.oid = con.confrelid "
            "JOIN pg_namespace n ON n.oid = src.relnamespace "
            " AND n.nspname = 'public' "
            "JOIN unnest(con.conkey) AS cols(attnum) ON true "
            "JOIN pg_attribute a ON a.attrelid = src.oid "
            " AND a.attnum = cols.attnum "
            "WHERE con.contype = 'f' "
            "GROUP BY con.oid, src.relname, dst.relname"
        )
    ):
        inventario[origem]["fks"].append({"tabela": destino, "nula": bool(nula)})
    return inventario
