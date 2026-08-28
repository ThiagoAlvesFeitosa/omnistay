"""Linha de convite no recado de boas-vindas.

Revision ID: 0023_convite_boas_vindas
Revises: 0022_personalidade_assistente
"""

from pathlib import Path

from alembic import op

revision = "0023_convite_boas_vindas"
down_revision = "0022_personalidade_assistente"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0023_convite_boas_vindas.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(
        "DELETE FROM parametro_hotel WHERE chave = 'boas_vindas_convite';"
    )
    cursor.execute(
        """
        COMMENT ON TABLE parametro_hotel IS
            'Configuracao operacional por propriedade. Chaves previstas: horas_ate_reenvio, '
            'horas_corte_antes_checkin, periodicidade_coleta_mercado, horas_minimas_para_pulso, '
            'duracao_sessao_recepcao_horas, duracao_sessao_staff_horas, duracao_sessao_gestor_horas, '
            'contato_responsavel_dados, tentativas_max_envio_mensagem, boas_vindas_cafe, '
            'boas_vindas_wifi, boas_vindas_checkout, horas_validade_boas_vindas, '
            'horas_destaque_chamado_aberto, horas_atribuicao_pesquisa_saida, '
            'meses_retencao_conteudo_livre, anos_retencao_ficha, '
            'personalidade_assistente.';
        """
    )
