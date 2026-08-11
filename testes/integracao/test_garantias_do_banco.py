"""O banco recusa dado invalido por conta propria.

Regra na aplicacao protege o caminho normal; estas garantias protegem contra script de
correcao, importacao e acesso direto — que e quando o historico costuma ser corrompido.

Para conferir que cada teste falha na ausencia da migracao, e nao apenas passa depois
dela, rode este arquivo com a variavel de ambiente OMNISTAY_SEM_MIGRACAO=1: o banco
descartavel vem vazio e nenhuma garantia existe. Um teste que so foi visto passando nao
prova que verifica o que diz verificar.
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from testes.suporte.banco_descartavel import banco_vazio
from testes.suporte.migracao import aplicar_migracoes

VARIAVEL_SEM_MIGRACAO = "OMNISTAY_SEM_MIGRACAO"

TRANSICOES_RECUSADAS = [
    ("aguardando_cadastro", "hospedado"),
    ("encerrado", "hospedado"),
    ("hospedado", "cancelada"),
]

TRANSICOES_ACEITAS = [
    ("aguardando_cadastro", "ficha_recebida"),
    ("ficha_recebida", "hospedado"),
    ("hospedado", "encerrado"),
]

CAMINHO_ATE = {
    "aguardando_cadastro": [],
    "ficha_recebida": ["ficha_recebida"],
    "hospedado": ["ficha_recebida", "hospedado"],
    "encerrado": ["ficha_recebida", "hospedado", "encerrado"],
}


@pytest.fixture
def banco():
    with banco_vazio() as url:
        if os.environ.get(VARIAVEL_SEM_MIGRACAO) != "1":
            aplicar_migracoes(url)
        yield url


@pytest.fixture
def conexao(banco):
    engine = create_engine(banco)
    try:
        with engine.connect() as conexao_de_teste:
            yield conexao_de_teste
    finally:
        engine.dispose()


def criar_hotel(conexao) -> int:
    return conexao.execute(
        text(
            "INSERT INTO hotel (nome, telefone_whatsapp) "
            "VALUES ('Pousada de Teste', '5511999999999') RETURNING id_hotel"
        )
    ).scalar()


def criar_reserva(conexao, id_hotel: int) -> int:
    return conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista) "
            "VALUES (:id_hotel, '5511988888888', CURRENT_DATE, CURRENT_DATE + 3) "
            "RETURNING id_reserva"
        ),
        {"id_hotel": id_hotel},
    ).scalar()


def mudar_status(conexao, id_reserva: int, status: str) -> None:
    checkin = ", checkin_em = now()" if status == "hospedado" else ""
    conexao.execute(
        text(
            f"UPDATE reserva SET status = :status{checkin} WHERE id_reserva = :id_reserva"
        ),
        {"status": status, "id_reserva": id_reserva},
    )


def reserva_em(conexao, status: str) -> int:
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    for intermediario in CAMINHO_ATE[status]:
        mudar_status(conexao, id_reserva, intermediario)
    return id_reserva


@pytest.mark.postgres
def test_perfil_fora_do_dominio_permitido_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "INSERT INTO usuario (id_hotel, nome, email, senha_hash, perfil) "
                "VALUES (:id_hotel, 'Fulano', 'fulano@exemplo.com', 'hash', 'diretor')"
            ),
            {"id_hotel": id_hotel},
        )

    assert "ck_usuario_perfil" in str(erro.value)


@pytest.mark.postgres
@pytest.mark.parametrize(("origem", "destino"), TRANSICOES_RECUSADAS)
def test_transicao_de_status_invalida_e_recusada_pelo_banco(conexao, origem, destino):
    id_reserva = reserva_em(conexao, origem)

    with pytest.raises(DBAPIError) as erro:
        mudar_status(conexao, id_reserva, destino)

    assert "Transicao de status invalida" in str(erro.value)


@pytest.mark.postgres
@pytest.mark.parametrize(("origem", "destino"), TRANSICOES_ACEITAS)
def test_transicao_de_status_permitida_e_aceita(conexao, origem, destino):
    id_reserva = reserva_em(conexao, origem)

    mudar_status(conexao, id_reserva, destino)

    status_atual = conexao.execute(
        text("SELECT status FROM reserva WHERE id_reserva = :id_reserva"),
        {"id_reserva": id_reserva},
    ).scalar()
    assert status_atual == destino


@pytest.mark.postgres
def test_segundo_evento_com_mesmo_identificador_externo_e_recusado(conexao):
    inserir = text(
        "INSERT INTO evento_webhook (id_externo, payload) "
        "VALUES ('wamid.MESMO_ID', '{}'::jsonb)"
    )
    conexao.execute(inserir)

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(inserir)

    assert "evento_webhook_id_externo_key" in str(erro.value)


@pytest.mark.postgres
def test_valor_de_consumo_negativo_e_recusado(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_solicitacao = conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, tipo, descricao) "
            "VALUES (:id_reserva, 'consumo', 'Agua mineral') RETURNING id_solicitacao"
        ),
        {"id_reserva": id_reserva},
    ).scalar()

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "INSERT INTO consumo (id_solicitacao, descricao_item, valor_praticado) "
                "VALUES (:id_solicitacao, 'Agua mineral', -1)"
            ),
            {"id_solicitacao": id_solicitacao},
        )

    assert "ck_consumo_valor_nao_negativo" in str(erro.value)


@pytest.mark.postgres
def test_consumo_nasce_pendente_de_lancamento(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_solicitacao = conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, tipo, descricao) "
            "VALUES (:id_reserva, 'consumo', 'Agua mineral') RETURNING id_solicitacao"
        ),
        {"id_reserva": id_reserva},
    ).scalar()

    status = conexao.execute(
        text(
            "INSERT INTO consumo (id_solicitacao, descricao_item, valor_praticado) "
            "VALUES (:id_solicitacao, 'Agua mineral', 8.50) RETURNING status_lancamento"
        ),
        {"id_solicitacao": id_solicitacao},
    ).scalar()

    assert status == "pendente"
