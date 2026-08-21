"""Helpers de teste do painel de mercado. So INSERT; sem worker, sem URL."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def gravar_coleta(
    conexao: Connection,
    id_concorrente: int,
    *,
    sucesso: bool,
    preco,
    nota_media,
    coletado_em,
) -> dict:
    """Insere uma linha em coleta_mercado e devolve o registro. Uso so em teste."""
    linha = conexao.execute(
        text(
            "INSERT INTO coleta_mercado"
            " (id_concorrente, preco, nota_media, sucesso, coletado_em)"
            " VALUES (:id, :preco, :nota, :sucesso, :em)"
            " RETURNING id_coleta, id_concorrente, preco, nota_media,"
            " sucesso, coletado_em"
        ),
        {
            "id": id_concorrente,
            "preco": preco,
            "nota": nota_media,
            "sucesso": sucesso,
            "em": coletado_em,
        },
    ).mappings().one()
    return dict(linha)
