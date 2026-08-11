"""Inventario estrutural de um banco, para comparar esquemas sem comparar texto de SQL.

Indentacao, ordem de restricoes e a forma como o PostgreSQL normaliza uma expressao de
CHECK produzem diferencas que nao sao divergencia de esquema. Fazendo o proprio
PostgreSQL reconstruir as definicoes dos dois lados, a comparacao passa a ser sobre
estrutura.

O contrato desta estrutura esta em
specs/002-esquema-migracoes/contracts/inventario-de-esquema.md.
"""

import re

from sqlalchemy import create_engine, text

Inventario = dict[str, list[tuple[str, ...]]]

TABELA_DE_VERSAO = "alembic_version"

CATEGORIAS = ("tabelas", "restricoes", "indices", "triggers", "funcoes", "visoes")

_COLUNAS = """
SELECT c.relname,
       a.attname,
       format_type(a.atttypid, a.atttypmod),
       CASE WHEN a.attnotnull THEN 'NOT NULL' ELSE 'NULL' END,
       COALESCE(pg_get_expr(d.adbin, d.adrelid), '')
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
  JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
  LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
 WHERE c.relkind = 'r' AND c.relname <> :tabela_de_versao
 ORDER BY c.relname, a.attname
"""

_RESTRICOES = """
SELECT rel.relname, con.conname, pg_get_constraintdef(con.oid)
  FROM pg_constraint con
  JOIN pg_class rel ON rel.oid = con.conrelid
  JOIN pg_namespace n ON n.oid = rel.relnamespace AND n.nspname = 'public'
 WHERE rel.relname <> :tabela_de_versao
 ORDER BY rel.relname, con.conname
"""

_INDICES = """
SELECT tablename, indexname, indexdef
  FROM pg_indexes
 WHERE schemaname = 'public' AND tablename <> :tabela_de_versao
 ORDER BY tablename, indexname
"""

_TRIGGERS = """
SELECT rel.relname, tg.tgname, pg_get_triggerdef(tg.oid)
  FROM pg_trigger tg
  JOIN pg_class rel ON rel.oid = tg.tgrelid
  JOIN pg_namespace n ON n.oid = rel.relnamespace AND n.nspname = 'public'
 WHERE NOT tg.tgisinternal
 ORDER BY rel.relname, tg.tgname
"""

_FUNCOES = """
SELECT p.proname, pg_get_functiondef(p.oid)
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
 WHERE p.prokind = 'f'
 ORDER BY p.proname
"""

_VISOES = """
SELECT c.relname, pg_get_viewdef(c.oid, true)
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public'
 WHERE c.relkind = 'v'
 ORDER BY c.relname
"""

_PADRAO_TRIGGER = re.compile(
    r"CREATE(?: CONSTRAINT)? TRIGGER \S+ "
    r"(?P<momento>BEFORE|AFTER|INSTEAD OF) "
    r"(?P<eventos>.+?) ON \S+ "
    r"(?:FROM \S+ )?(?:NOT DEFERRABLE \S+ \S+ \S+ )?"
    r"FOR EACH (?P<orientacao>ROW|STATEMENT)"
    r"(?: WHEN \((?P<condicao>.+)\))? "
    r"EXECUTE (?:FUNCTION|PROCEDURE) (?P<funcao>.+)",
    re.DOTALL,
)


def _decompor_trigger(tabela: str, nome: str, definicao: str) -> tuple[str, ...]:
    """Separa a trigger em aspectos, para que a falha diga qual deles mudou.

    Trocar `BEFORE UPDATE OF status` por `BEFORE UPDATE` desarma a protecao sem alterar
    mais nada, e uma comparacao de texto unico nao nomearia isso.
    """
    achado = _PADRAO_TRIGGER.search(definicao)
    if achado is None:
        return (tabela, nome, definicao)

    return (
        tabela,
        nome,
        achado["momento"],
        achado["eventos"],
        f"FOR EACH {achado['orientacao']}",
        achado["condicao"] or "",
        achado["funcao"],
    )


def aplicar_sql(engine, sql: str) -> None:
    """Executa um script inteiro sem passar parametro nenhum ao driver.

    O cursor cru e necessario: com qualquer colecao de parametros, mesmo vazia, o
    psycopg2 tenta interpolar `%` — e a funcao de validacao de transicao usa `%` na
    mensagem de excecao.
    """
    conexao_crua = engine.raw_connection()
    try:
        cursor = conexao_crua.cursor()
        cursor.execute(sql)
        conexao_crua.commit()
    finally:
        conexao_crua.close()


def extrair_inventario(url_do_banco: str, sql_inicial: str | None = None) -> Inventario:
    """Aplica o SQL indicado, se houver, e extrai o inventario do banco."""
    engine = create_engine(url_do_banco)
    try:
        if sql_inicial:
            aplicar_sql(engine, sql_inicial)

        parametros = {"tabela_de_versao": TABELA_DE_VERSAO}
        with engine.connect() as conexao:

            def consultar(consulta: str) -> list[tuple[str, ...]]:
                linhas = conexao.execute(text(consulta), parametros).fetchall()
                return [tuple(str(valor) for valor in linha) for linha in linhas]

            triggers = [
                _decompor_trigger(*linha) for linha in consultar(_TRIGGERS)
            ]

            return {
                "tabelas": consultar(_COLUNAS),
                "restricoes": consultar(_RESTRICOES),
                "indices": consultar(_INDICES),
                "triggers": sorted(triggers),
                "funcoes": consultar(_FUNCOES),
                "visoes": consultar(_VISOES),
            }
    finally:
        engine.dispose()


def _descrever(categoria: str, rotulo: str, itens: list[tuple[str, ...]]) -> list[str]:
    return [f"{categoria}: {rotulo}: {' | '.join(item)}" for item in sorted(itens)]


def faltando(referencia: Inventario, obtido: Inventario) -> list[str]:
    """O que existe na referencia e nao existe no banco obtido."""
    mensagens: list[str] = []
    for categoria in CATEGORIAS:
        ausentes = set(referencia[categoria]) - set(obtido[categoria])
        mensagens.extend(_descrever(categoria, "falta", list(ausentes)))
    return mensagens


def diferencas(referencia: Inventario, obtido: Inventario) -> list[str]:
    """Toda diferenca entre os dois inventarios, nos dois sentidos."""
    mensagens: list[str] = []
    for categoria in CATEGORIAS:
        esperados = set(referencia[categoria])
        presentes = set(obtido[categoria])
        mensagens.extend(_descrever(categoria, "falta", list(esperados - presentes)))
        mensagens.extend(_descrever(categoria, "sobra", list(presentes - esperados)))
    return mensagens
