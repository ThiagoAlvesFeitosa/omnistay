"""Disparo de coleta ao cadastrar reserva."""

import pytest
from sqlalchemy import text

from testes.integracao.test_reservas import _corpo_valido, _login


@pytest.mark.postgres
def test_post_reservas_cria_mensagem_e_trabalho_sem_enviar(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    _login(cliente, recepcao)

    resposta = cliente.post("/reservas", json=_corpo_valido())
    assert resposta.status_code == 201
    id_reserva = resposta.json()["id_reserva"]

    with ambiente.conexao() as conexao:
        mensagens = conexao.execute(
            text(
                "SELECT direcao, status_envio, conteudo FROM mensagem "
                "WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).mappings().all()
        trabalhos = conexao.execute(
            text(
                "SELECT tipo, status, payload FROM trabalho "
                "WHERE (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).mappings().all()

    assert len(mensagens) == 1
    assert mensagens[0]["direcao"] == "enviada"
    assert mensagens[0]["status_envio"] == "pendente"
    assert "Ola, Maria!" in mensagens[0]["conteudo"]
    assert len(trabalhos) == 1
    assert trabalhos[0]["tipo"] == "enviar_coleta"
    assert trabalhos[0]["status"] == "pendente"

    fila = cliente.get("/fila-do-dia")
    assert fila.status_code == 200
    item = fila.json()["itens"][0]
    assert item["status_envio_coleta"] == "pendente"


@pytest.mark.postgres
def test_cadastro_recusado_nao_enfileira(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    with ambiente.conexao() as conexao:
        antes_m = conexao.execute(text("SELECT COUNT(*) FROM mensagem")).scalar_one()
        antes_t = conexao.execute(text("SELECT COUNT(*) FROM trabalho")).scalar_one()

    assert (
        cliente.post(
            "/reservas",
            json=_corpo_valido(telefone="123"),
        ).status_code
        == 422
    )

    with ambiente.conexao() as conexao:
        depois_m = conexao.execute(text("SELECT COUNT(*) FROM mensagem")).scalar_one()
        depois_t = conexao.execute(text("SELECT COUNT(*) FROM trabalho")).scalar_one()
    assert depois_m == antes_m
    assert depois_t == antes_t


@pytest.mark.postgres
def test_unicidade_de_coleta_por_reserva(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]

    with ambiente.engine.begin() as conexao:
        with pytest.raises(Exception):
            conexao.execute(
                text(
                    "INSERT INTO trabalho (id_hotel, tipo, payload, status) VALUES ("
                    " :h, 'enviar_coleta', CAST(:p AS jsonb), 'pendente')"
                ),
                {
                    "h": ambiente.propriedade_a.id_hotel,
                    "p": f'{{"id_reserva": {id_reserva}, "id_mensagem": 999}}',
                },
            )
