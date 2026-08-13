"""Acesso a mensagem — sem regra de negocio."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def inserir_mensagem_enviada_pendente(
    conexao: Connection,
    *,
    id_reserva: int,
    conteudo: str,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo, status_envio) "
            "VALUES (:id_reserva, 'enviada', :conteudo, 'pendente') "
            "RETURNING id_mensagem"
        ),
        {"id_reserva": id_reserva, "conteudo": conteudo},
    ).scalar_one()


def atualizar_status_envio(
    conexao: Connection,
    *,
    id_mensagem: int,
    status_envio: str,
    id_externo: str | None = None,
) -> None:
    conexao.execute(
        text(
            "UPDATE mensagem SET status_envio = :status,"
            " id_externo = COALESCE(:id_externo, id_externo)"
            " WHERE id_mensagem = :id"
        ),
        {
            "status": status_envio,
            "id_externo": id_externo,
            "id": id_mensagem,
        },
    )


def ler_mensagem(conexao: Connection, *, id_mensagem: int) -> dict | None:
    linha = conexao.execute(
        text(
            "SELECT id_mensagem, id_reserva, direcao, conteudo, status_envio, id_externo"
            " FROM mensagem WHERE id_mensagem = :id"
        ),
        {"id": id_mensagem},
    ).mappings().first()
    return dict(linha) if linha else None


def listar_mensagens_da_reserva(conexao: Connection, *, id_reserva: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_mensagem, id_reserva, direcao, conteudo, status_envio, id_externo"
            " FROM mensagem WHERE id_reserva = :id ORDER BY enviada_em ASC, id_mensagem ASC"
        ),
        {"id": id_reserva},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def ler_telefone_da_reserva(conexao: Connection, *, id_reserva: int) -> str | None:
    return conexao.execute(
        text("SELECT telefone_contato FROM reserva WHERE id_reserva = :id"),
        {"id": id_reserva},
    ).scalar_one_or_none()
