"""Esquema inicial do OmniStay.

O SQL nao e transcrito aqui: esta revisao aplica o arquivo companheiro
`sql/0001_esquema_inicial.sql`, copia congelada de `docs/04-schema.sql` no momento em
que a revisao foi criada. Transcrever o esquema em chamadas do Alembic criaria uma
segunda descricao a manter em acordo, e trigger, funcao plpgsql, visao e indices
parciais nao tem representacao natural nessa forma.

O arquivo companheiro nunca e editado depois de aplicado em ambiente duravel: mudanca de
esquema vira revisao nova, e `docs/04-schema.sql` passa a descrever o esquema resultante.

Revision ID: 0001_esquema_inicial
Revises: None
"""

from pathlib import Path

from alembic import op

revision = "0001_esquema_inicial"
down_revision = None
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0001_esquema_inicial.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")

    # Cursor cru, sem colecao de parametros: com qualquer uma, mesmo vazia, o psycopg2
    # tenta interpolar o `%` que a mensagem de RAISE EXCEPTION da funcao de validacao usa.
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    raise NotImplementedError(
        "Reversao nao e suportada: a revisao inicial parte de banco vazio, e reverter "
        "equivale a descartar o banco."
    )
