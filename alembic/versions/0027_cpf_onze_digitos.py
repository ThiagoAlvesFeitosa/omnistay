"""Converte CPF isolado para onze digitos; pula pares que colidiriam.

Revision ID: 0027_cpf_onze_digitos
Revises: 0026_omissoes_fila_do_dia
"""

from alembic import op
from sqlalchemy import text

from app.comum.log import obter_logger
from app.modulos.hospedagem.cpf_migracao import forma_digitos, planejar_migracao_cpf

revision = "0027_cpf_onze_digitos"
down_revision = "0026_omissoes_fila_do_dia"
branch_labels = None
depends_on = None

logger = obter_logger(__name__)


def upgrade() -> None:
    conexao = op.get_bind()
    linhas = conexao.execute(
        text(
            "SELECT id_hospede, numero_documento FROM hospede "
            "WHERE tipo_documento = 'cpf' "
            "AND numero_documento IS NOT NULL "
            "AND btrim(numero_documento) <> ''"
        )
    ).fetchall()
    por_id = {int(linha[0]): str(linha[1]) for linha in linhas}
    plano = planejar_migracao_cpf(list(por_id.items()))
    for id_hospede in plano.converter:
        conexao.execute(
            text(
                "UPDATE hospede SET numero_documento = :numero "
                "WHERE id_hospede = :id_hospede"
            ),
            {"numero": forma_digitos(por_id[id_hospede]), "id_hospede": id_hospede},
        )
    if plano.pares:
        logger.warning(
            "cpf_migracao_colisao pares=%s ids=%s",
            plano.pares,
            ",".join(str(identidade) for identidade in plano.pular),
        )


def downgrade() -> None:
    pass
