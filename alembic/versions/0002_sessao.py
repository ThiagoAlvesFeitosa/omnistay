"""Sessao do painel.

Mesma forma da revisao inicial: o SQL nao e transcrito em chamadas do Alembic, e
sim aplicado a partir do arquivo companheiro `sql/0002_sessao.sql`, copia congelada
do bloco que entrou em `docs/04-schema.sql`. Manter uma unica forma de descrever
esquema no projeto e o que permite ao teste de conformidade comparar os dois lados.

Diferente da revisao inicial, esta tem `downgrade` de verdade: reverter derruba os
logins e nao perde historico, e a operacao inversa e exata.

Revision ID: 0002_sessao
Revises: 0001_esquema_inicial
"""

from pathlib import Path

from alembic import op

revision = "0002_sessao"
down_revision = "0001_esquema_inicial"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0002_sessao.sql"

COMENTARIO_ANTERIOR_DE_PARAMETRO = (
    "Configuracao operacional por propriedade. Chaves previstas: horas_ate_reenvio, "
    "horas_corte_antes_checkin, periodicidade_coleta_mercado, horas_minimas_para_pulso."
)


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")

    # Cursor cru, sem colecao de parametros, como na revisao inicial: com qualquer
    # colecao, mesmo vazia, o psycopg2 tenta interpolar `%` no script.
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(
        "DROP TABLE sessao; "
        f"COMMENT ON TABLE parametro_hotel IS '{COMENTARIO_ANTERIOR_DE_PARAMETRO}';"
    )
