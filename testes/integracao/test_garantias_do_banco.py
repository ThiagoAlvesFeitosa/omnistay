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
    ("ficha_parcial", "hospedado"),
    ("sem_cadastro_previo", "hospedado"),
    ("hospedado", "encerrado"),
]

CAMINHO_ATE = {
    "aguardando_cadastro": [],
    "ficha_recebida": ["ficha_recebida"],
    "ficha_parcial": ["ficha_parcial"],
    "sem_cadastro_previo": ["sem_cadastro_previo"],
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


@pytest.mark.postgres
def test_categoria_de_catalogo_fora_do_dominio_e_recusada(conexao):
    id_hotel = criar_hotel(conexao)

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "INSERT INTO catalogo_item (id_hotel, categoria, titulo, conteudo) "
                "VALUES (:id_hotel, 'spa', 'Massagem', 'Sob agendamento')"
            ),
            {"id_hotel": id_hotel},
        )

    assert "ck_catalogo_categoria" in str(erro.value)


def _inserir_trabalho_boas_vindas(conexao, id_hotel: int, id_reserva: int) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'enviar_boas_vindas',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_mensagem": 1}' % id_reserva
            ),
        },
    )


@pytest.mark.postgres
def test_tipo_enviar_boas_vindas_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_boas_vindas(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text(
            "SELECT tipo FROM trabalho WHERE tipo = 'enviar_boas_vindas'"
        )
    ).scalar_one()
    assert tipo == "enviar_boas_vindas"


def _inserir_trabalho_enviar_pulso(conexao, id_hotel: int, id_reserva: int) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'enviar_pulso',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": '{"id_reserva": %s, "id_mensagem": 1}' % id_reserva,
        },
    )


def _inserir_trabalho_registrar_resposta_pulso(
    conexao, id_hotel: int, id_reserva: int, id_mensagem: int = 1
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'registrar_resposta_pulso',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem)
            ),
        },
    )


def _inserir_avaliacao_pulso(conexao, id_reserva: int) -> None:
    conexao.execute(
        text(
            "INSERT INTO avaliacao (id_reserva, origem, comentario) "
            "VALUES (:id_reserva, 'pulso_segundo_dia', 'ok')"
        ),
        {"id_reserva": id_reserva},
    )


@pytest.mark.postgres
def test_tipo_enviar_pulso_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_enviar_pulso(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text("SELECT tipo FROM trabalho WHERE tipo = 'enviar_pulso'")
    ).scalar_one()
    assert tipo == "enviar_pulso"


@pytest.mark.postgres
def test_segundo_trabalho_de_pulso_da_mesma_reserva_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_enviar_pulso(conexao, id_hotel, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_enviar_pulso(conexao, id_hotel, id_reserva)

    assert "uq_trabalho_enviar_pulso_reserva" in str(erro.value)


@pytest.mark.postgres
def test_tipo_registrar_resposta_pulso_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_registrar_resposta_pulso(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text("SELECT tipo FROM trabalho WHERE tipo = 'registrar_resposta_pulso'")
    ).scalar_one()
    assert tipo == "registrar_resposta_pulso"


@pytest.mark.postgres
def test_segunda_resposta_de_pulso_da_mesma_mensagem_e_recusada(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_registrar_resposta_pulso(
        conexao, id_hotel, id_reserva, id_mensagem=7
    )

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_registrar_resposta_pulso(
            conexao, id_hotel, id_reserva, id_mensagem=7
        )

    assert "uq_trabalho_registrar_resposta_pulso_mensagem" in str(erro.value)


@pytest.mark.postgres
def test_segunda_avaliacao_de_pulso_da_mesma_reserva_e_recusada(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    _inserir_avaliacao_pulso(conexao, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        _inserir_avaliacao_pulso(conexao, id_reserva)

    assert "uq_avaliacao_reserva_origem" in str(erro.value)


@pytest.mark.postgres
def test_segundo_trabalho_de_boas_vindas_da_mesma_reserva_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_boas_vindas(conexao, id_hotel, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_boas_vindas(conexao, id_hotel, id_reserva)

    assert "uq_trabalho_enviar_boas_vindas_reserva" in str(erro.value)


def _inserir_trabalho_classificar(
    conexao, id_hotel: int, id_reserva: int, id_mensagem: int = 1
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'classificar_mensagem',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_mensagem": %s, "id_evento": 1}'
                % (id_reserva, id_mensagem)
            ),
        },
    )


@pytest.mark.postgres
def test_tipo_classificar_mensagem_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_classificar(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text(
            "SELECT tipo FROM trabalho WHERE tipo = 'classificar_mensagem'"
        )
    ).scalar_one()
    assert tipo == "classificar_mensagem"


@pytest.mark.postgres
def test_segundo_trabalho_classificar_da_mesma_mensagem_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_classificar(conexao, id_hotel, id_reserva, id_mensagem=7)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_classificar(conexao, id_hotel, id_reserva, id_mensagem=7)

    assert "uq_trabalho_classificar_mensagem_mensagem" in str(erro.value)


def _inserir_trabalho_responder(
    conexao, id_hotel: int, id_reserva: int, id_mensagem: int = 1
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'responder_duvida',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem)
            ),
        },
    )


@pytest.mark.postgres
def test_tipo_responder_duvida_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_responder(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text("SELECT tipo FROM trabalho WHERE tipo = 'responder_duvida'")
    ).scalar_one()
    assert tipo == "responder_duvida"


@pytest.mark.postgres
def test_segundo_trabalho_responder_da_mesma_mensagem_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_responder(conexao, id_hotel, id_reserva, id_mensagem=7)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_responder(conexao, id_hotel, id_reserva, id_mensagem=7)

    assert "uq_trabalho_responder_duvida_mensagem" in str(erro.value)


def _inserir_trabalho_registrar_pedido(
    conexao, id_hotel: int, id_reserva: int, id_mensagem: int = 1
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'registrar_pedido_servico',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem)
            ),
        },
    )


@pytest.mark.postgres
def test_tipo_registrar_pedido_servico_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_registrar_pedido(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text(
            "SELECT tipo FROM trabalho WHERE tipo = 'registrar_pedido_servico'"
        )
    ).scalar_one()
    assert tipo == "registrar_pedido_servico"


@pytest.mark.postgres
def test_segundo_trabalho_registrar_pedido_da_mesma_mensagem_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_registrar_pedido(conexao, id_hotel, id_reserva, id_mensagem=7)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_registrar_pedido(
            conexao, id_hotel, id_reserva, id_mensagem=7
        )

    assert "uq_trabalho_registrar_pedido_servico_mensagem" in str(erro.value)


def _inserir_mensagem_recebida(conexao, id_reserva: int, conteudo: str = "toalha") -> int:
    return conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
            "VALUES (:id_reserva, 'recebida', :conteudo) RETURNING id_mensagem"
        ),
        {"id_reserva": id_reserva, "conteudo": conteudo},
    ).scalar()


@pytest.mark.postgres
def test_segunda_solicitacao_da_mesma_mensagem_origem_e_recusada(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_mensagem = _inserir_mensagem_recebida(conexao, id_reserva)
    conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, id_mensagem_origem, tipo, descricao) "
            "VALUES (:id_reserva, :id_mensagem, 'servico', 'toalha extra')"
        ),
        {"id_reserva": id_reserva, "id_mensagem": id_mensagem},
    )

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, id_mensagem_origem, tipo, descricao) "
                "VALUES (:id_reserva, :id_mensagem, 'servico', 'toalha extra')"
            ),
            {"id_reserva": id_reserva, "id_mensagem": id_mensagem},
        )

    assert "uq_solicitacao_mensagem_origem" in str(erro.value)


def _inserir_trabalho_abrir_chamado(
    conexao, id_hotel: int, id_reserva: int, id_mensagem: int = 1
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'abrir_chamado_reclamacao',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem)
            ),
        },
    )


@pytest.mark.postgres
def test_tipo_abrir_chamado_reclamacao_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_abrir_chamado(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text(
            "SELECT tipo FROM trabalho WHERE tipo = 'abrir_chamado_reclamacao'"
        )
    ).scalar_one()
    assert tipo == "abrir_chamado_reclamacao"


@pytest.mark.postgres
def test_segundo_trabalho_abrir_chamado_da_mesma_mensagem_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_abrir_chamado(conexao, id_hotel, id_reserva, id_mensagem=7)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_abrir_chamado(
            conexao, id_hotel, id_reserva, id_mensagem=7
        )

    assert "uq_trabalho_abrir_chamado_reclamacao_mensagem" in str(erro.value)


def _inserir_trabalho_confirmacao_resolucao(
    conexao, id_hotel: int, id_reserva: int, id_solicitacao: int = 1
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'enviar_confirmacao_resolucao',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_solicitacao": %s, "id_mensagem": 1}'
                % (id_reserva, id_solicitacao)
            ),
        },
    )


def _criar_usuario(conexao, id_hotel: int) -> int:
    return conexao.execute(
        text(
            "INSERT INTO usuario (id_hotel, nome, email, senha_hash, perfil) "
            "VALUES (:id_hotel, 'Staff Teste', :email, 'hash', 'staff') "
            "RETURNING id_usuario"
        ),
        {"id_hotel": id_hotel, "email": f"staff-{id_hotel}@exemplo.com"},
    ).scalar()


def _inserir_solicitacao_aberta(conexao, id_reserva: int, tipo: str = "reclamacao") -> int:
    return conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, tipo, descricao, status) "
            "VALUES (:id_reserva, :tipo, 'problema no quarto', 'aberta') "
            "RETURNING id_solicitacao"
        ),
        {"id_reserva": id_reserva, "tipo": tipo},
    ).scalar()


@pytest.mark.postgres
def test_tipo_enviar_confirmacao_resolucao_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_confirmacao_resolucao(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text(
            "SELECT tipo FROM trabalho WHERE tipo = 'enviar_confirmacao_resolucao'"
        )
    ).scalar_one()
    assert tipo == "enviar_confirmacao_resolucao"


@pytest.mark.postgres
def test_segundo_trabalho_confirmacao_resolucao_da_mesma_solicitacao_e_recusado(
    conexao,
):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_confirmacao_resolucao(
        conexao, id_hotel, id_reserva, id_solicitacao=7
    )

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_confirmacao_resolucao(
            conexao, id_hotel, id_reserva, id_solicitacao=7
        )

    assert "uq_trabalho_enviar_confirmacao_resolucao_solicitacao" in str(erro.value)


@pytest.mark.postgres
@pytest.mark.parametrize("origem", ["aberta", "em_andamento"])
def test_transicao_solicitacao_para_resolvida_e_aceita(conexao, origem):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    id_usuario = _criar_usuario(conexao, id_hotel)
    id_solicitacao = conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, tipo, descricao, status) "
            "VALUES (:id_reserva, 'reclamacao', 'problema no quarto', :status) "
            "RETURNING id_solicitacao"
        ),
        {"id_reserva": id_reserva, "status": origem},
    ).scalar()

    conexao.execute(
        text(
            "UPDATE solicitacao SET status = 'resolvida',"
            " resolvida_em = now(), id_usuario_responsavel = :uid"
            " WHERE id_solicitacao = :id"
        ),
        {"uid": id_usuario, "id": id_solicitacao},
    )

    status = conexao.execute(
        text("SELECT status FROM solicitacao WHERE id_solicitacao = :id"),
        {"id": id_solicitacao},
    ).scalar()
    assert status == "resolvida"


@pytest.mark.postgres
def test_transicao_solicitacao_resolvida_para_aberta_e_recusada(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    id_usuario = _criar_usuario(conexao, id_hotel)
    id_solicitacao = _inserir_solicitacao_aberta(conexao, id_reserva)
    conexao.execute(
        text(
            "UPDATE solicitacao SET status = 'resolvida',"
            " resolvida_em = now(), id_usuario_responsavel = :uid"
            " WHERE id_solicitacao = :id"
        ),
        {"uid": id_usuario, "id": id_solicitacao},
    )

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "UPDATE solicitacao SET status = 'aberta'"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        )

    assert "Transicao de status invalida" in str(erro.value)


@pytest.mark.postgres
def test_transicao_solicitacao_aberta_para_cancelada_e_recusada(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_solicitacao = _inserir_solicitacao_aberta(conexao, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "UPDATE solicitacao SET status = 'cancelada'"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        )

    assert "Transicao de status invalida" in str(erro.value)


@pytest.mark.postgres
def test_solicitacao_resolvida_sem_responsavel_e_recusada(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_solicitacao = _inserir_solicitacao_aberta(conexao, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "UPDATE solicitacao SET status = 'resolvida',"
                " resolvida_em = now()"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        )

    assert "ck_solicitacao_resolvida_tem_responsavel" in str(erro.value)


def _inserir_item_vendavel(conexao, id_hotel: int, *, nome="Cerveja", preco=12.00):
    return conexao.execute(
        text(
            "INSERT INTO item_vendavel (id_hotel, nome, preco_atual) "
            "VALUES (:id_hotel, :nome, :preco) RETURNING id_item_vendavel"
        ),
        {"id_hotel": id_hotel, "nome": nome, "preco": preco},
    ).scalar()


def _inserir_consumo_completo(
    conexao,
    id_reserva: int,
    *,
    valor=8.50,
    status="pendente",
    id_usuario=None,
    lancado_em=None,
):
    id_solicitacao = conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, tipo, descricao) "
            "VALUES (:id_reserva, 'consumo', 'Agua mineral') "
            "RETURNING id_solicitacao"
        ),
        {"id_reserva": id_reserva},
    ).scalar()
    conexao.execute(
        text(
            "INSERT INTO consumo (id_solicitacao, descricao_item, valor_praticado,"
            " status_lancamento, id_usuario_lancamento, lancado_em) "
            "VALUES (:id, 'Agua mineral', :valor, :status, :uid, :quando)"
        ),
        {
            "id": id_solicitacao,
            "valor": valor,
            "status": status,
            "uid": id_usuario,
            "quando": lancado_em,
        },
    )
    return id_solicitacao


@pytest.mark.postgres
def test_item_vendavel_com_preco_nao_negativo_e_aceito(conexao):
    id_hotel = criar_hotel(conexao)

    id_item = _inserir_item_vendavel(conexao, id_hotel, preco=0)
    outro = _inserir_item_vendavel(conexao, id_hotel, nome="Agua", preco=12.00)

    assert id_item
    assert outro != id_item


@pytest.mark.postgres
def test_item_vendavel_com_preco_negativo_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)

    with pytest.raises(DBAPIError) as erro:
        _inserir_item_vendavel(conexao, id_hotel, preco=-0.01)

    assert "ck_item_vendavel_preco_nao_negativo" in str(erro.value)


@pytest.mark.postgres
def test_segundo_item_ativo_com_mesmo_nome_no_hotel_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    _inserir_item_vendavel(conexao, id_hotel, nome="Cerveja")

    with pytest.raises(DBAPIError) as erro:
        _inserir_item_vendavel(conexao, id_hotel, nome="cerveja")

    assert "uq_item_vendavel_hotel_nome_ativo" in str(erro.value)


@pytest.mark.postgres
def test_consumo_cujo_pai_e_servico_e_recusado(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_solicitacao = conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, tipo, descricao) "
            "VALUES (:id_reserva, 'servico', 'toalha extra') "
            "RETURNING id_solicitacao"
        ),
        {"id_reserva": id_reserva},
    ).scalar()

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "INSERT INTO consumo (id_solicitacao, descricao_item, valor_praticado) "
                "VALUES (:id, 'toalha extra', 0)"
            ),
            {"id": id_solicitacao},
        )

    assert "fn_consumo_pai_tipo_consumo" in str(erro.value) or "tipo consumo" in str(
        erro.value
    ).casefold()


@pytest.mark.postgres
def test_solicitacao_consumo_sem_filho_e_recusada_no_commit(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    conexao.execute(
        text(
            "INSERT INTO solicitacao (id_reserva, tipo, descricao) "
            "VALUES (:id_reserva, 'consumo', 'Agua mineral')"
        ),
        {"id_reserva": id_reserva},
    )

    with pytest.raises(DBAPIError) as erro:
        conexao.commit()

    mensagem = str(erro.value).casefold()
    assert "consumo" in mensagem


@pytest.mark.postgres
def test_pai_consumo_com_filho_na_mesma_transacao_e_aceito(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_solicitacao = _inserir_consumo_completo(conexao, id_reserva)

    conexao.commit()
    status = conexao.execute(
        text("SELECT status_lancamento FROM consumo WHERE id_solicitacao = :id"),
        {"id": id_solicitacao},
    ).scalar()
    assert status == "pendente"


@pytest.mark.postgres
def test_lancado_ou_dispensado_sem_autor_e_recusado(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    id_solicitacao = _inserir_consumo_completo(conexao, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "UPDATE consumo SET status_lancamento = 'lancado'"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        )
    assert "ck_consumo_terminal_tem_autor" in str(erro.value)

    conexao.rollback()
    id_solicitacao = _inserir_consumo_completo(
        conexao, criar_reserva(conexao, criar_hotel(conexao))
    )
    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "UPDATE consumo SET status_lancamento = 'dispensado'"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        )
    assert "ck_consumo_terminal_tem_autor" in str(erro.value)


@pytest.mark.postgres
def test_pendente_para_lancado_e_dispensado_com_autor_e_aceito(conexao):
    id_hotel = criar_hotel(conexao)
    id_usuario = _criar_usuario(conexao, id_hotel)
    id_lancado = _inserir_consumo_completo(
        conexao, criar_reserva(conexao, id_hotel)
    )
    id_dispensado = _inserir_consumo_completo(
        conexao, criar_reserva(conexao, id_hotel)
    )

    conexao.execute(
        text(
            "UPDATE consumo SET status_lancamento = 'lancado',"
            " id_usuario_lancamento = :uid, lancado_em = now()"
            " WHERE id_solicitacao = :id"
        ),
        {"id": id_lancado, "uid": id_usuario},
    )
    conexao.execute(
        text(
            "UPDATE consumo SET status_lancamento = 'dispensado',"
            " id_usuario_lancamento = :uid, lancado_em = now()"
            " WHERE id_solicitacao = :id"
        ),
        {"id": id_dispensado, "uid": id_usuario},
    )

    assert conexao.execute(
        text("SELECT status_lancamento FROM consumo WHERE id_solicitacao = :id"),
        {"id": id_lancado},
    ).scalar() == "lancado"
    assert conexao.execute(
        text("SELECT status_lancamento FROM consumo WHERE id_solicitacao = :id"),
        {"id": id_dispensado},
    ).scalar() == "dispensado"


@pytest.mark.postgres
def test_lancado_nao_volta_para_pendente(conexao):
    id_hotel = criar_hotel(conexao)
    id_usuario = _criar_usuario(conexao, id_hotel)
    id_solicitacao = _inserir_consumo_completo(
        conexao, criar_reserva(conexao, id_hotel)
    )
    conexao.execute(
        text(
            "UPDATE consumo SET status_lancamento = 'lancado',"
            " id_usuario_lancamento = :uid, lancado_em = now()"
            " WHERE id_solicitacao = :id"
        ),
        {"id": id_solicitacao, "uid": id_usuario},
    )

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "UPDATE consumo SET status_lancamento = 'pendente'"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        )

    assert "fn_valida_transicao_lancamento" in str(erro.value) or "transicao" in str(
        erro.value
    ).casefold()


def _inserir_trabalho_enviar_pesquisa_saida(
    conexao, id_hotel: int, id_reserva: int
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'enviar_pesquisa_saida',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": '{"id_reserva": %s, "id_mensagem": 1}' % id_reserva,
        },
    )


def _inserir_trabalho_interpretar_pesquisa_saida(
    conexao, id_hotel: int, id_reserva: int, id_mensagem: int = 1
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'interpretar_pesquisa_saida',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": (
                '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem)
            ),
        },
    )


@pytest.mark.postgres
def test_tipo_enviar_pesquisa_saida_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_enviar_pesquisa_saida(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text("SELECT tipo FROM trabalho WHERE tipo = 'enviar_pesquisa_saida'")
    ).scalar_one()
    assert tipo == "enviar_pesquisa_saida"


@pytest.mark.postgres
def test_segundo_trabalho_de_pesquisa_saida_da_mesma_reserva_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_enviar_pesquisa_saida(conexao, id_hotel, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_enviar_pesquisa_saida(conexao, id_hotel, id_reserva)

    assert "uq_trabalho_enviar_pesquisa_saida_reserva" in str(erro.value)


@pytest.mark.postgres
def test_tipo_interpretar_pesquisa_saida_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_interpretar_pesquisa_saida(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text(
            "SELECT tipo FROM trabalho WHERE tipo = 'interpretar_pesquisa_saida'"
        )
    ).scalar_one()
    assert tipo == "interpretar_pesquisa_saida"


@pytest.mark.postgres
def test_segunda_interpretacao_da_mesma_mensagem_e_recusada(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_interpretar_pesquisa_saida(
        conexao, id_hotel, id_reserva, id_mensagem=7
    )

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_interpretar_pesquisa_saida(
            conexao, id_hotel, id_reserva, id_mensagem=7
        )

    assert "uq_trabalho_interpretar_pesquisa_saida_mensagem" in str(erro.value)


@pytest.mark.postgres
def test_avaliacao_de_checkout_sem_nota_e_recusada(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))

    with pytest.raises(DBAPIError) as erro:
        conexao.execute(
            text(
                "INSERT INTO avaliacao (id_reserva, origem, comentario) "
                "VALUES (:id_reserva, 'checkout', 'ok')"
            ),
            {"id_reserva": id_reserva},
        )

    assert "ck_avaliacao_checkout_tem_nota" in str(erro.value)


@pytest.mark.postgres
def test_avaliacao_de_pulso_com_nota_nula_continua_aceita(conexao):
    id_reserva = criar_reserva(conexao, criar_hotel(conexao))
    _inserir_avaliacao_pulso(conexao, id_reserva)
    origem = conexao.execute(
        text(
            "SELECT origem FROM avaliacao WHERE id_reserva = :id"
        ),
        {"id": id_reserva},
    ).scalar_one()
    assert origem == "pulso_segundo_dia"


def _inserir_trabalho_enviar_lista_pedidos_chat(
    conexao, id_hotel: int, id_reserva: int
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'enviar_lista_pedidos_chat',"
            " CAST(:payload AS jsonb), 'pendente')"
        ),
        {
            "id_hotel": id_hotel,
            "payload": '{"id_reserva": %s, "id_mensagem": 1}' % id_reserva,
        },
    )


@pytest.mark.postgres
def test_tipo_enviar_lista_pedidos_chat_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)

    _inserir_trabalho_enviar_lista_pedidos_chat(conexao, id_hotel, id_reserva)

    tipo = conexao.execute(
        text(
            "SELECT tipo FROM trabalho WHERE tipo = 'enviar_lista_pedidos_chat'"
        )
    ).scalar_one()
    assert tipo == "enviar_lista_pedidos_chat"


@pytest.mark.postgres
def test_segundo_trabalho_de_lista_pedidos_da_mesma_reserva_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)
    id_reserva = criar_reserva(conexao, id_hotel)
    _inserir_trabalho_enviar_lista_pedidos_chat(conexao, id_hotel, id_reserva)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_enviar_lista_pedidos_chat(conexao, id_hotel, id_reserva)

    assert "uq_trabalho_enviar_lista_pedidos_chat_reserva" in str(erro.value)


def _inserir_trabalho_coletar_mercado(
    conexao, id_hotel: int, id_concorrente: int, *, status="pendente"
) -> None:
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:id_hotel, 'coletar_mercado',"
            " CAST(:payload AS jsonb), :status)"
        ),
        {
            "id_hotel": id_hotel,
            "payload": '{"id_concorrente": %s}' % id_concorrente,
            "status": status,
        },
    )


@pytest.mark.postgres
def test_tipo_coletar_mercado_e_aceito_pelo_check(conexao):
    id_hotel = criar_hotel(conexao)
    id_concorrente = _inserir_concorrente(conexao, id_hotel)

    _inserir_trabalho_coletar_mercado(conexao, id_hotel, id_concorrente)

    tipo = conexao.execute(
        text("SELECT tipo FROM trabalho WHERE tipo = 'coletar_mercado'")
    ).scalar_one()
    assert tipo == "coletar_mercado"


@pytest.mark.postgres
def test_segundo_trabalho_aberto_de_coleta_do_mesmo_concorrente_e_recusado(
    conexao,
):
    id_hotel = criar_hotel(conexao)
    id_concorrente = _inserir_concorrente(conexao, id_hotel)
    _inserir_trabalho_coletar_mercado(conexao, id_hotel, id_concorrente)

    with pytest.raises(DBAPIError) as erro:
        _inserir_trabalho_coletar_mercado(conexao, id_hotel, id_concorrente)

    assert "uq_trabalho_coletar_mercado_concorrente_aberto" in str(erro.value)


@pytest.mark.postgres
def test_segundo_trabalho_concluido_de_coleta_do_mesmo_concorrente_passa(
    conexao,
):
    id_hotel = criar_hotel(conexao)
    id_concorrente = _inserir_concorrente(conexao, id_hotel)
    _inserir_trabalho_coletar_mercado(
        conexao, id_hotel, id_concorrente, status="concluido"
    )
    _inserir_trabalho_coletar_mercado(
        conexao, id_hotel, id_concorrente, status="concluido"
    )

    qtd = conexao.execute(
        text(
            "SELECT COUNT(*) FROM trabalho WHERE tipo = 'coletar_mercado'"
        )
    ).scalar_one()
    assert qtd == 2


def _inserir_concorrente(
    conexao, id_hotel: int, *, nome="Hotel Vizinho", url="https://a.exemplo/x", ativo=True
):
    return conexao.execute(
        text(
            "INSERT INTO concorrente (id_hotel, nome, url_fonte, ativo) "
            "VALUES (:id_hotel, :nome, :url, :ativo) RETURNING id_concorrente"
        ),
        {"id_hotel": id_hotel, "nome": nome, "url": url, "ativo": ativo},
    ).scalar()


@pytest.mark.postgres
def test_concorrente_com_url_http_e_aceito(conexao):
    id_hotel = criar_hotel(conexao)

    id_concorrente = _inserir_concorrente(conexao, id_hotel)

    assert id_concorrente


@pytest.mark.postgres
def test_concorrente_sem_esquema_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)

    with pytest.raises(DBAPIError) as erro:
        _inserir_concorrente(conexao, id_hotel, url="www.exemplo.com/x")

    assert "ck_concorrente_url_fonte" in str(erro.value)


@pytest.mark.postgres
def test_concorrente_mailto_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)

    with pytest.raises(DBAPIError) as erro:
        _inserir_concorrente(conexao, id_hotel, url="mailto:x@y.com")

    assert "ck_concorrente_url_fonte" in str(erro.value)


@pytest.mark.postgres
def test_concorrente_com_espaco_no_meio_da_url_e_recusado(conexao):
    id_hotel = criar_hotel(conexao)

    with pytest.raises(DBAPIError) as erro:
        _inserir_concorrente(
            conexao, id_hotel, url="https://a.exemplo/caminho com espaco"
        )

    assert "ck_concorrente_url_fonte" in str(erro.value)


@pytest.mark.postgres
def test_segunda_fonte_igual_no_hotel_e_recusada_mesmo_inativa(conexao):
    id_hotel = criar_hotel(conexao)
    _inserir_concorrente(conexao, id_hotel, url="https://a.exemplo/x", ativo=False)

    with pytest.raises(DBAPIError) as erro:
        _inserir_concorrente(conexao, id_hotel, nome="Outro", url="HTTPS://A.EXEMPLO/X")

    assert "uq_concorrente_hotel_fonte" in str(erro.value)


@pytest.mark.postgres
def test_segunda_fonte_com_espacos_nas_pontas_e_recusada(conexao):
    id_hotel = criar_hotel(conexao)
    _inserir_concorrente(conexao, id_hotel, url="https://a.exemplo/x")

    with pytest.raises(DBAPIError) as erro:
        _inserir_concorrente(conexao, id_hotel, nome="Outro", url="  https://a.exemplo/x  ")

    assert "uq_concorrente_hotel_fonte" in str(erro.value)


@pytest.mark.postgres
def test_dois_hoteis_podem_ter_a_mesma_fonte(conexao):
    hotel_a = criar_hotel(conexao)
    hotel_b = criar_hotel(conexao)

    um = _inserir_concorrente(conexao, hotel_a, url="https://a.exemplo/x")
    outro = _inserir_concorrente(conexao, hotel_b, url="https://a.exemplo/x")

    assert um
    assert outro != um
