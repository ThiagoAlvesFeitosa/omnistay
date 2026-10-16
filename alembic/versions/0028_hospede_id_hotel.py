"""Cada hospede pertence a um hotel; UNIQUE de documento por casa.

Revision ID: 0028_hospede_id_hotel
Revises: 0027_cpf_onze_digitos
"""

from alembic import op
from sqlalchemy import bindparam, text

from app.comum.log import obter_logger
from app.modulos.hospedagem.hospede_migracao import planejar_hospede_por_hotel

revision = "0028_hospede_id_hotel"
down_revision = "0027_cpf_onze_digitos"
branch_labels = None
depends_on = None

logger = obter_logger(__name__)

CAMPOS_FICHA = (
    "nome_completo, profissao, data_nascimento, tipo_documento, "
    "numero_documento, endereco, cep, cidade, telefone"
)


def upgrade() -> None:
    conexao = op.get_bind()
    conexao.execute(
        text(
            "ALTER TABLE hospede ADD COLUMN id_hotel BIGINT "
            "REFERENCES hotel (id_hotel)"
        )
    )
    conexao.execute(text("DROP INDEX IF EXISTS uq_hospede_documento"))

    ids_hospede = list(
        conexao.execute(text("SELECT id_hospede FROM hospede ORDER BY id_hospede"))
        .scalars()
        .all()
    )
    ids_hotel = list(
        conexao.execute(text("SELECT id_hotel FROM hotel ORDER BY id_hotel"))
        .scalars()
        .all()
    )
    vinculos = [
        (int(linha[0]), int(linha[1]), int(linha[2]))
        for linha in conexao.execute(
            text(
                "SELECT rh.id_hospede, r.id_hotel, r.id_reserva "
                "FROM reserva_hospede rh "
                "JOIN reserva r ON r.id_reserva = rh.id_reserva"
            )
        )
    ]
    plano = planejar_hospede_por_hotel(
        ids_hospede=ids_hospede,
        vinculos=vinculos,
        ids_hotel=ids_hotel,
    )
    if plano.orfaos:
        ids = ",".join(str(identidade) for identidade in plano.orfaos)
        logger.warning(
            "hospede_migracao_orfao n=%s ids=%s",
            len(plano.orfaos),
            ids,
        )
        raise RuntimeError("hospede_migracao_orfao")

    for id_hospede, id_hotel in plano.atribuir:
        conexao.execute(
            text(
                "UPDATE hospede SET id_hotel = :id_hotel "
                "WHERE id_hospede = :id_hospede"
            ),
            {"id_hotel": id_hotel, "id_hospede": id_hospede},
        )

    for copia in plano.copias:
        novo = conexao.execute(
            text(
                f"INSERT INTO hospede ({CAMPOS_FICHA}, id_hotel) "
                f"SELECT {CAMPOS_FICHA}, :id_hotel FROM hospede "
                "WHERE id_hospede = :origem RETURNING id_hospede"
            ),
            {"id_hotel": copia.id_hotel, "origem": copia.id_hospede_origem},
        ).scalar_one()
        conexao.execute(
            text(
                "UPDATE reserva_hospede SET id_hospede = :copia "
                "WHERE id_reserva IN :ids"
            ).bindparams(bindparam("ids", expanding=True)),
            {"copia": novo, "ids": list(copia.ids_reserva)},
        )

    conexao.execute(text("ALTER TABLE hospede ALTER COLUMN id_hotel SET NOT NULL"))
    conexao.execute(
        text(
            "CREATE UNIQUE INDEX uq_hospede_documento "
            "ON hospede (id_hotel, tipo_documento, numero_documento) "
            "WHERE tipo_documento IS NOT NULL AND numero_documento IS NOT NULL"
        )
    )
    conexao.execute(
        text(
            "COMMENT ON COLUMN hospede.id_hotel IS "
            "'Controlador dos dados deste cadastro. Artigo XIV.'"
        )
    )


def downgrade() -> None:
    pass
