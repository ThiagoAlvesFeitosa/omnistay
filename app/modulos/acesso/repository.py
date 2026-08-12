"""Acesso a usuario e sessao. Nao conhece hotel nem parametro."""

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Connection, Row


def inserir_usuario(
    conexao: Connection,
    *,
    id_hotel: int,
    nome: str,
    email: str,
    senha_hash: str,
    perfil: str,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO usuario (id_hotel, nome, email, senha_hash, perfil) "
            "VALUES (:id_hotel, :nome, :email, :senha_hash, :perfil) "
            "RETURNING id_usuario"
        ),
        {
            "id_hotel": id_hotel,
            "nome": nome,
            "email": email,
            "senha_hash": senha_hash,
            "perfil": perfil,
        },
    ).scalar_one()


def buscar_por_email(conexao: Connection, email: str) -> Row | None:
    return conexao.execute(
        text(
            "SELECT id_usuario, id_hotel, nome, email, senha_hash, perfil, ativo "
            "FROM usuario WHERE email = :email"
        ),
        {"email": email},
    ).one_or_none()


def buscar_por_id(conexao: Connection, id_usuario: int) -> Row | None:
    return conexao.execute(
        text(
            "SELECT id_usuario, id_hotel, nome, email, senha_hash, perfil, ativo "
            "FROM usuario WHERE id_usuario = :id_usuario"
        ),
        {"id_usuario": id_usuario},
    ).one_or_none()


def desativar_usuario(conexao: Connection, id_usuario: int) -> None:
    conexao.execute(
        text("UPDATE usuario SET ativo = FALSE WHERE id_usuario = :id_usuario"),
        {"id_usuario": id_usuario},
    )


def inserir_sessao(
    conexao: Connection,
    *,
    id_usuario: int,
    token_hash: str,
    dispositivo: str | None,
    criada_em: datetime,
    expira_em: datetime,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO sessao "
            "(id_usuario, token_hash, dispositivo, criada_em, expira_em) "
            "VALUES (:id_usuario, :token_hash, :dispositivo, :criada_em, :expira_em) "
            "RETURNING id_sessao"
        ),
        {
            "id_usuario": id_usuario,
            "token_hash": token_hash,
            "dispositivo": dispositivo,
            "criada_em": criada_em,
            "expira_em": expira_em,
        },
    ).scalar_one()


def buscar_sessao_por_hash(conexao: Connection, token_hash: str) -> Row | None:
    return conexao.execute(
        text(
            "SELECT s.id_sessao, s.id_usuario, s.token_hash, s.dispositivo, "
            "s.criada_em, s.expira_em, s.revogada_em, "
            "u.id_hotel, u.nome, u.email, u.perfil, u.ativo "
            "FROM sessao s "
            "JOIN usuario u ON u.id_usuario = s.id_usuario "
            "WHERE s.token_hash = :token_hash"
        ),
        {"token_hash": token_hash},
    ).one_or_none()


def revogar_sessao(
    conexao: Connection, id_sessao: int, revogada_em: datetime
) -> None:
    conexao.execute(
        text(
            "UPDATE sessao SET revogada_em = :revogada_em "
            "WHERE id_sessao = :id_sessao AND revogada_em IS NULL"
        ),
        {"id_sessao": id_sessao, "revogada_em": revogada_em},
    )


def revogar_sessoes_do_usuario(
    conexao: Connection, id_usuario: int, revogada_em: datetime
) -> None:
    conexao.execute(
        text(
            "UPDATE sessao SET revogada_em = :revogada_em "
            "WHERE id_usuario = :id_usuario AND revogada_em IS NULL"
        ),
        {"id_usuario": id_usuario, "revogada_em": revogada_em},
    )


def listar_sessoes_ativas_do_hotel(
    conexao: Connection, id_hotel: int, agora: datetime
) -> list[Row]:
    return list(
        conexao.execute(
            text(
                "SELECT s.id_sessao, s.id_usuario, u.nome AS nome_usuario, u.perfil, "
                "s.dispositivo, s.criada_em, s.expira_em "
                "FROM sessao s "
                "JOIN usuario u ON u.id_usuario = s.id_usuario "
                "WHERE u.id_hotel = :id_hotel "
                "AND s.revogada_em IS NULL "
                "AND s.expira_em > :agora "
                "ORDER BY s.criada_em DESC"
            ),
            {"id_hotel": id_hotel, "agora": agora},
        ).all()
    )


def buscar_sessao_por_id(conexao: Connection, id_sessao: int) -> Row | None:
    return conexao.execute(
        text(
            "SELECT s.id_sessao, s.id_usuario, s.revogada_em, s.expira_em, "
            "u.id_hotel "
            "FROM sessao s "
            "JOIN usuario u ON u.id_usuario = s.id_usuario "
            "WHERE s.id_sessao = :id_sessao"
        ),
        {"id_sessao": id_sessao},
    ).one_or_none()
