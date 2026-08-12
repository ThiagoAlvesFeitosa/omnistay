"""Desativacao de usuario e sessoes na mesma transacao."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

from app.modulos.acesso import service as acesso_service

INSTANTE = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)


@dataclass
class Usuario:
    id_usuario: int
    id_hotel: int
    ativo: bool = True


@dataclass
class Repositorio:
    usuarios: dict[int, Usuario]
    sessoes_revogadas: list = field(default_factory=list)
    falhar_ao_revogar: bool = False

    def buscar_por_id(self, conexao, id_usuario):
        return self.usuarios.get(id_usuario)

    def desativar_usuario(self, conexao, id_usuario):
        self.usuarios[id_usuario].ativo = False

    def revogar_sessoes_do_usuario(self, conexao, id_usuario, revogada_em):
        if self.falhar_ao_revogar:
            raise RuntimeError("falha na revogacao")
        self.sessoes_revogadas.append((id_usuario, revogada_em))


def test_desativacao_revoga_sessoes_na_mesma_operacao():
    repo = Repositorio(
        usuarios={
            1: Usuario(1, 10),
            2: Usuario(2, 10),
        }
    )

    acesso_service.desativar_usuario(
        conexao=object(),
        id_usuario=2,
        id_hotel_do_ator=10,
        id_usuario_do_ator=1,
        repositorio=repo,
        agora=lambda: INSTANTE,
    )

    assert repo.usuarios[2].ativo is False
    assert repo.sessoes_revogadas == [(2, INSTANTE)]


def test_falha_na_revogacao_nao_deixa_desativacao_solta():
    """Com transacao real a atomicidade e do banco; aqui a ordem importa.

    O servico desativa e depois revoga. Se a revogacao falha, o chamador —
    que usa transacao() — desfaz as duas. Este teste garante que a revogacao
    e chamada e que uma falha nela sobe.
    """
    repo = Repositorio(
        usuarios={1: Usuario(1, 10), 2: Usuario(2, 10)},
        falhar_ao_revogar=True,
    )

    with pytest.raises(RuntimeError, match="falha na revogacao"):
        acesso_service.desativar_usuario(
            conexao=object(),
            id_usuario=2,
            id_hotel_do_ator=10,
            id_usuario_do_ator=1,
            repositorio=repo,
            agora=lambda: INSTANTE,
        )
