"""Fila do dia da recepcao."""

from datetime import date, timedelta

import pytest

from testes.integracao.test_reservas import _corpo_valido, _login


@pytest.mark.postgres
def test_reserva_aparece_na_fila_do_dia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    _login(cliente, recepcao)

    criada = cliente.post("/reservas", json=_corpo_valido()).json()
    fila = cliente.get("/fila-do-dia")
    assert fila.status_code == 200
    itens = fila.json()["itens"]
    assert len(itens) == 1
    item = itens[0]
    assert item["id_reserva"] == criada["id_reserva"]
    assert item["nome"] == "Maria Silva"
    assert item["telefone_contato"] == "5511987654321"
    assert item["status"] == "aguardando_cadastro"
    assert item["ficha_completa"] is False
    assert item["chegada_nao_confirmada"] is False
    assert item["status_envio_coleta"] == "pendente"
    assert item["estado_cadastro"] == "aguardando"


@pytest.mark.postgres
def test_chegada_passada_sem_confirmacao_e_sinalizada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    ontem = date.today() - timedelta(days=1)
    cliente.post(
        "/reservas",
        json=_corpo_valido(
            data_checkin_prevista=ontem.isoformat(),
            data_checkout_prevista=date.today().isoformat(),
        ),
    )
    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["chegada_nao_confirmada"] is True


@pytest.mark.postgres
def test_fila_isola_hotels(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido(nome="Alpha"))

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido(nome="Beta", telefone="11977776666"))

    fila_b = cliente.get("/fila-do-dia").json()["itens"]
    assert len(fila_b) == 1
    assert fila_b[0]["nome"] == "Beta"

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    fila_a = cliente.get("/fila-do-dia").json()["itens"]
    assert len(fila_a) == 1
    assert fila_a[0]["nome"] == "Alpha"


@pytest.mark.postgres
def test_reserva_futura_nao_aparece_na_fila_do_dia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    hoje = date.today()
    futura = hoje + timedelta(days=30)
    cliente.post(
        "/reservas",
        json=_corpo_valido(
            nome="Dezembro",
            telefone="11933332222",
            data_checkin_prevista=futura.isoformat(),
            data_checkout_prevista=(futura + timedelta(days=2)).isoformat(),
        ),
    )
    cliente.post("/reservas", json=_corpo_valido(nome="Hoje"))

    itens = cliente.get("/fila-do-dia").json()["itens"]
    nomes = [item["nome"] for item in itens]
    assert "Hoje" in nomes
    assert "Dezembro" not in nomes


@pytest.mark.postgres
def test_staff_e_gestor_nao_leem_fila_nominada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido())

    for perfil in ("staff", "gestor"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        assert cliente.get("/fila-do-dia").status_code == 403


@pytest.mark.postgres
def test_fila_distingue_sem_cadastro_previo(app_sobre_ambiente):
    from sqlalchemy import text

    from worker.agendador import verificar_cadastros_pendentes
    from worker.consumidor import processar_uma_passagem_na_engine
    from app.adaptadores.mensageria_falsa import MensageriaFalsa

    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    processar_uma_passagem_na_engine(ambiente.engine, gateway=MensageriaFalsa())
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
    item = next(
        i
        for i in cliente.get("/fila-do-dia").json()["itens"]
        if i["id_reserva"] == id_reserva
    )
    assert item["estado_cadastro"] == "sem_cadastro_previo"
    with ambiente.conexao() as conexao:
        status = conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
    assert status == "sem_cadastro_previo"


@pytest.mark.postgres
def test_fila_distingue_chegada_atrasada_de_boas_vindas_nao_enviadas(
    app_sobre_ambiente,
):
    from sqlalchemy import text

    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    _login(cliente, recepcao)
    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    atrasada = cliente.post(
        "/reservas",
        json=_corpo_valido(
            nome="Atrasada",
            telefone="11911110001",
            data_checkin_prevista=ontem.isoformat(),
            data_checkout_prevista=hoje.isoformat(),
        ),
    ).json()["id_reserva"]
    do_dia = cliente.post(
        "/reservas",
        json=_corpo_valido(nome="DoDia", telefone="11911110002"),
    ).json()["id_reserva"]
    com_pacote = cliente.post(
        "/reservas",
        json=_corpo_valido(nome="ComPacote", telefone="11911110003"),
    ).json()["id_reserva"]
    sem_pacote = cliente.post(
        "/reservas",
        json=_corpo_valido(nome="SemPacote", telefone="11911110004"),
    ).json()["id_reserva"]

    with ambiente.engine.begin() as conexao:
        for id_reserva in (com_pacote, sem_pacote):
            conexao.execute(
                text(
                    "UPDATE reserva SET status = 'ficha_recebida' "
                    "WHERE id_reserva = :id"
                ),
                {"id": id_reserva},
            )
    assert cliente.post(f"/reservas/{com_pacote}/chegada").status_code == 200
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "DELETE FROM parametro_hotel "
                "WHERE id_hotel = :h AND chave = 'boas_vindas_wifi'"
            ),
            {"h": recepcao.id_hotel},
        )
    assert cliente.post(f"/reservas/{sem_pacote}/chegada").status_code == 200

    itens = {i["nome"]: i for i in cliente.get("/fila-do-dia").json()["itens"]}
    assert itens["Atrasada"]["chegada_nao_confirmada"] is True
    assert itens["Atrasada"]["boas_vindas_nao_enviadas"] is False
    assert itens["DoDia"]["chegada_nao_confirmada"] is False
    assert itens["DoDia"]["boas_vindas_nao_enviadas"] is False
    assert itens["ComPacote"]["chegada_nao_confirmada"] is False
    assert itens["ComPacote"]["boas_vindas_nao_enviadas"] is False
    assert itens["SemPacote"]["chegada_nao_confirmada"] is False
    assert itens["SemPacote"]["boas_vindas_nao_enviadas"] is True
    for item in itens.values():
        assert not (
            item["chegada_nao_confirmada"] and item["boas_vindas_nao_enviadas"]
        )
    del atrasada, do_dia
