"""O banco recusa sessao incoerente por conta propria.

Unicidade e CHECK nao sao codigo nosso: precisam falhar na ausencia da revisao
`0002_sessao` e passar com ela. Rode com OMNISTAY_SEM_REVISAO_SESSAO=1 para aplicar
apenas a revisao inicial — hotel e usuario existem, sessao nao — e ver a falha pelo
motivo certo.
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from testes.suporte.banco_descartavel import banco_vazio
from testes.suporte.migracao import aplicar_migracoes

VARIAVEL_SEM_REVISAO = "OMNISTAY_SEM_REVISAO_SESSAO"
REVISAO_INICIAL = "0001_esquema_inicial"

INSERIR_SESSAO = text(
    "INSERT INTO sessao (id_usuario, token_hash, criada_em, expira_em, revogada_em) "
    "VALUES (:id_usuario, :token_hash, :criada_em, :expira_em, :revogada_em)"
)


@pytest.fixture
def conexao():
    with banco_vazio() as url:
        if os.environ.get(VARIAVEL_SEM_REVISAO) == "1":
            aplicar_migracoes(url, alvo=REVISAO_INICIAL)
        else:
            aplicar_migracoes(url)

        engine = create_engine(url)
        try:
            with engine.connect() as conexao_de_teste:
                yield conexao_de_teste
        finally:
            engine.dispose()


@pytest.fixture
def id_usuario(conexao) -> int:
    id_hotel = conexao.execute(
        text(
            "INSERT INTO hotel (nome, telefone_whatsapp) "
            "VALUES ('Pousada de Teste', '5511999999999') RETURNING id_hotel"
        )
    ).scalar()

    return conexao.execute(
        text(
            "INSERT INTO usuario (id_hotel, nome, email, senha_hash, perfil) "
            "VALUES (:id_hotel, 'Cleber Rocha', 'cleber@exemplo.com', 'hash', 'staff') "
            "RETURNING id_usuario"
        ),
        {"id_hotel": id_hotel},
    ).scalar()


def inserir_sessao(conexao, id_usuario, token_hash, criada, expira, revogada=None):
    conexao.execute(
        INSERIR_SESSAO,
        {
            "id_usuario": id_usuario,
            "token_hash": token_hash,
            "criada_em": criada,
            "expira_em": expira,
            "revogada_em": revogada,
        },
    )


@pytest.mark.postgres
def test_segunda_sessao_com_o_mesmo_hash_de_token_e_recusada(conexao, id_usuario):
    argumentos = ("2026-08-12 10:00:00+00", "2026-08-13 10:00:00+00")
    inserir_sessao(conexao, id_usuario, "a" * 64, *argumentos)

    with pytest.raises(DBAPIError) as erro:
        inserir_sessao(conexao, id_usuario, "a" * 64, *argumentos)

    assert "sessao_token_hash_key" in str(erro.value)


@pytest.mark.postgres
def test_sessao_que_expira_antes_de_ser_criada_e_recusada(conexao, id_usuario):
    with pytest.raises(DBAPIError) as erro:
        inserir_sessao(
            conexao,
            id_usuario,
            "b" * 64,
            "2026-08-12 10:00:00+00",
            "2026-08-12 09:00:00+00",
        )

    assert "ck_sessao_expira_depois_de_criada" in str(erro.value)


@pytest.mark.postgres
def test_sessao_revogada_antes_de_ser_criada_e_recusada(conexao, id_usuario):
    with pytest.raises(DBAPIError) as erro:
        inserir_sessao(
            conexao,
            id_usuario,
            "c" * 64,
            "2026-08-12 10:00:00+00",
            "2026-08-13 10:00:00+00",
            revogada="2026-08-12 09:00:00+00",
        )

    assert "ck_sessao_revogada_depois_de_criada" in str(erro.value)


@pytest.mark.postgres
def test_sessao_de_usuario_inexistente_e_recusada(conexao):
    with pytest.raises(DBAPIError) as erro:
        inserir_sessao(
            conexao,
            999_999,
            "d" * 64,
            "2026-08-12 10:00:00+00",
            "2026-08-13 10:00:00+00",
        )

    assert "sessao_id_usuario_fkey" in str(erro.value)


@pytest.mark.postgres
def test_sessao_coerente_e_aceita(conexao, id_usuario):
    inserir_sessao(
        conexao,
        id_usuario,
        "e" * 64,
        "2026-08-12 10:00:00+00",
        "2026-09-11 10:00:00+00",
    )

    revogadas = conexao.execute(
        text("SELECT count(*) FROM sessao WHERE revogada_em IS NULL")
    ).scalar()
    assert revogadas == 1
