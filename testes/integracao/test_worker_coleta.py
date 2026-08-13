"""Worker processa envio de coleta com porta falsa."""

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from worker.consumidor import processar_uma_passagem_na_engine
from testes.integracao.test_reservas import _corpo_valido, _login


@pytest.mark.postgres
def test_worker_sucesso_marca_enviada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]

    porta = MensageriaFalsa()
    processados = processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    assert processados >= 1
    assert len(porta.envios) == 1
    assert porta.envios[0]["telefone_destino"] == "5511987654321"
    assert porta.envios[0]["primeiro_nome"] == "Maria"

    with ambiente.conexao() as conexao:
        status_msg = conexao.execute(
            text(
                "SELECT status_envio FROM mensagem WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        status_trab = conexao.execute(
            text(
                "SELECT status FROM trabalho "
                "WHERE (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert status_msg == "enviada"
    assert status_trab == "concluido"

    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["status_envio_coleta"] == "enviada"


@pytest.mark.postgres
def test_falha_nao_apaga_reserva_e_esgota_em_falha(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE parametro_hotel SET valor = '1' "
                "WHERE id_hotel = :h AND chave = 'tentativas_max_envio_mensagem'"
            ),
            {"h": hotel},
        )

    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    criada = cliente.post("/reservas", json=_corpo_valido(nome="Joao")).json()
    id_reserva = criada["id_reserva"]

    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)

    with ambiente.conexao() as conexao:
        reserva = conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        status_msg = conexao.execute(
            text("SELECT status_envio FROM mensagem WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        status_trab = conexao.execute(
            text(
                "SELECT status FROM trabalho "
                "WHERE (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        qtd_msg = conexao.execute(
            text("SELECT COUNT(*) FROM mensagem WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()

    assert reserva == "aguardando_cadastro"
    assert status_msg == "falha"
    assert status_trab == "falha"
    assert qtd_msg == 1
    assert porta.envios == []

    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["id_reserva"] == id_reserva
    assert item["status_envio_coleta"] == "falha"


@pytest.mark.postgres
def test_retry_nao_duplica_mensagem_nem_envio(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post(
        "/reservas", json=_corpo_valido(nome="Ana Costa")
    ).json()["id_reserva"]

    porta = MensageriaFalsa()
    porta.falhas_restantes = 1
    # Primeira passagem: falha e reagenda (proxima_tentativa_em no futuro)
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)

    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE trabalho SET proxima_tentativa_em = NULL "
                "WHERE (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        )

    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)

    assert len(porta.envios) == 1
    with ambiente.conexao() as conexao:
        qtd_msg = conexao.execute(
            text("SELECT COUNT(*) FROM mensagem WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        status_msg = conexao.execute(
            text("SELECT status_envio FROM mensagem WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
    assert qtd_msg == 1
    assert status_msg == "enviada"


@pytest.mark.postgres
def test_conteudo_tem_contato_do_hotel(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    with ambiente.conexao() as conexao:
        conteudo = conexao.execute(
            text("SELECT conteudo FROM mensagem WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        contato = conexao.execute(
            text(
                "SELECT valor FROM parametro_hotel "
                "WHERE id_hotel = :h AND chave = 'contato_responsavel_dados'"
            ),
            {"h": ambiente.propriedade_a.id_hotel},
        ).scalar_one()
    assert contato in conteudo
    assert "Finalidade:" in conteudo
