"""Acesso a hotel e parametro_hotel. Nao conhece usuario nem sessao."""

from sqlalchemy import text
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
