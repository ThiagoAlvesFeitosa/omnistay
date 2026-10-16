"""PUT da ficha no balcao."""

import logging

import pytest
from sqlalchemy import text

from testes.integracao.test_confirmar_saida import _tornar
from testes.integracao.test_reservas import _corpo_valido, _login
from testes.suporte.cpf_ficha import CPF_REPROVADO, CPF_VALIDO, CPF_VALIDO_PONTUADO


NOVE = {
    "nome_completo": "Maria Silva",
    "profissao": "Engenheira",
    "data_nascimento": "1990-05-12",
    "tipo_documento": "rg",
    "numero_documento": "1234567",
    "endereco": "Rua A, 100",
    "cep": "01310-100",
    "cidade": "Sao Paulo",
    "telefone": "11987654321",
}


def _criar_parcial(cliente, ambiente, **kwargs) -> int:
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido(**kwargs)).json()[
        "id_reserva"
    ]
    _tornar(ambiente, id_reserva, "ficha_parcial")
    return id_reserva


@pytest.mark.postgres
def test_put_completa_ficha_parcial_sem_enfileirar(app_sobre_ambiente, caplog):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_parcial(cliente, ambiente, telefone="11987654321")
    with ambiente.conexao() as conexao:
        trabalhos_antes = conexao.execute(text("SELECT COUNT(*) FROM trabalho")).scalar_one()

    caplog.set_level(logging.INFO)
    resposta = cliente.put(f"/reservas/{id_reserva}/ficha", json=NOVE)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["ficha_completa"] is True
    assert corpo["status_reserva"] == "ficha_recebida"
    assert corpo["estado_cadastro"] == "completa"
    assert corpo["cep"] == "01310100"
    assert "idade" not in corpo

    fila = cliente.get("/fila-do-dia").json()["itens"]
    linha = next(item for item in fila if item["id_reserva"] == id_reserva)
    assert linha["estado_cadastro"] != "parcial"

    with ambiente.conexao() as conexao:
        trabalhos = conexao.execute(text("SELECT COUNT(*) FROM trabalho")).scalar_one()
        contato = conexao.execute(
            text("SELECT telefone_contato FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
    assert trabalhos == trabalhos_antes
    assert contato == "5511987654321"

    texto_log = caplog.text
    assert "Maria" not in texto_log
    assert "1234567" not in texto_log
    assert "11987654321" not in texto_log
    assert "5511987654321" not in texto_log


@pytest.mark.postgres
def test_put_em_hospedado_nao_muda_status(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post(
        "/reservas", json=_corpo_valido(telefone="11987654322")
    ).json()["id_reserva"]
    _tornar(ambiente, id_reserva, "ficha_recebida")
    _tornar(ambiente, id_reserva, "hospedado")
    resposta = cliente.put(f"/reservas/{id_reserva}/ficha", json=NOVE)
    assert resposta.status_code == 200
    assert resposta.json()["status_reserva"] == "hospedado"
    assert resposta.json()["ficha_completa"] is True


@pytest.mark.postgres
def test_staff_e_gestao_recusados_no_put(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_parcial(cliente, ambiente, telefone="11987654323")
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.put(f"/reservas/{id_reserva}/ficha", json=NOVE).status_code == 403
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.put(f"/reservas/{id_reserva}/ficha", json=NOVE).status_code == 403


@pytest.mark.postgres
def test_outro_hotel_nao_confirma_existencia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_parcial(cliente, ambiente, telefone="11987654324")
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    assert cliente.put(f"/reservas/{id_reserva}/ficha", json=NOVE).status_code == 404


@pytest.mark.postgres
def test_campo_invalido_nao_grava(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_parcial(cliente, ambiente, telefone="11987654325")
    ruim = {**NOVE, "telefone": "123", "cep": "12"}
    assert cliente.put(f"/reservas/{id_reserva}/ficha", json=ruim).status_code == 422
    lida = cliente.get(f"/reservas/{id_reserva}/ficha").json()
    assert lida["cep"] in (None, "")


@pytest.mark.postgres
def test_dois_hoteis_gravam_o_mesmo_documento(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    primeira = _criar_parcial(cliente, ambiente, telefone="11987654340", nome="Ana")
    assert cliente.put(f"/reservas/{primeira}/ficha", json=NOVE).status_code == 200

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    segunda = cliente.post(
        "/reservas", json=_corpo_valido(telefone="11987654341", nome="Bia")
    ).json()["id_reserva"]
    _tornar(ambiente, segunda, "ficha_parcial")
    corpo_b = {**NOVE, "nome_completo": "Bia Costa", "telefone": "11987654341"}
    resposta = cliente.put(f"/reservas/{segunda}/ficha", json=corpo_b)
    assert resposta.status_code == 200
    assert resposta.json()["numero_documento"] == NOVE["numero_documento"]


@pytest.mark.postgres
def test_hotel_b_nao_le_ficha_do_hotel_a(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    primeira = _criar_parcial(cliente, ambiente, telefone="11987654342", nome="Ana")
    assert cliente.put(f"/reservas/{primeira}/ficha", json=NOVE).status_code == 200

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    assert cliente.get(f"/reservas/{primeira}/ficha").status_code == 404


@pytest.mark.postgres
def test_documento_duplicado_nao_funde(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    primeira = _criar_parcial(cliente, ambiente, telefone="11987654326", nome="Ana")
    assert cliente.put(f"/reservas/{primeira}/ficha", json=NOVE).status_code == 200
    segunda = cliente.post(
        "/reservas", json=_corpo_valido(telefone="11987654327", nome="Bia")
    ).json()["id_reserva"]
    _tornar(ambiente, segunda, "ficha_parcial")
    recusa = cliente.put(f"/reservas/{segunda}/ficha", json=NOVE)
    assert recusa.status_code == 409
    lida = cliente.get(f"/reservas/{segunda}/ficha").json()
    assert lida["numero_documento"] in (None, "")


@pytest.mark.postgres
def test_put_documento_duplicado_nomeia_ficha_desta_casa(
    app_sobre_ambiente, caplog, monkeypatch
):
    cliente, ambiente = app_sobre_ambiente
    primeira = _criar_parcial(cliente, ambiente, telefone="11987654343", nome="Ana")
    corpo_ana = {**NOVE, "nome_completo": "Ana Souza"}
    assert cliente.put(f"/reservas/{primeira}/ficha", json=corpo_ana).status_code == 200

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    da_b = cliente.post(
        "/reservas", json=_corpo_valido(telefone="11987654344", nome="Carla")
    ).json()["id_reserva"]
    _tornar(ambiente, da_b, "ficha_parcial")
    corpo_carla = {**NOVE, "nome_completo": "Carla Mendes", "telefone": "11987654344"}
    assert cliente.put(f"/reservas/{da_b}/ficha", json=corpo_carla).status_code == 200

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    segunda = cliente.post(
        "/reservas", json=_corpo_valido(telefone="11987654345", nome="Bia")
    ).json()["id_reserva"]
    _tornar(ambiente, segunda, "ficha_parcial")

    linhas: list[str] = []

    def _info(msg, *args, **kwargs):
        linhas.append(msg % args if args else str(msg))

    monkeypatch.setattr("app.modulos.hospedagem.service.logger.info", _info)
    caplog.set_level(logging.INFO)
    recusa = cliente.put(f"/reservas/{segunda}/ficha", json=corpo_ana)
    assert recusa.status_code == 409
    detalhe = recusa.json()["detail"]
    assert detalhe["codigo"] == "documento_em_uso"
    assert detalhe["nome"] == "Ana Souza"
    assert detalhe["id_reserva"] == primeira
    assert "Ana Souza" in detalhe["recado"]
    assert NOVE["numero_documento"] not in recusa.text
    assert "Carla" not in recusa.text

    lida = cliente.get(f"/reservas/{segunda}/ficha").json()
    assert lida["numero_documento"] in (None, "")

    texto = "\n".join(linhas) + caplog.text
    assert "ficha_alterada_recusada" in texto
    assert "409" in texto
    assert NOVE["numero_documento"] not in texto
    assert "Carla" not in texto


@pytest.mark.postgres
def test_put_cpf_reprovado_nao_altera_nenhum_campo(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_parcial(cliente, ambiente, telefone="11987654328")
    ruim = {
        **NOVE,
        "tipo_documento": "cpf",
        "numero_documento": CPF_REPROVADO,
        "endereco": "Rua Nova, 9",
    }
    recusa = cliente.put(f"/reservas/{id_reserva}/ficha", json=ruim)
    assert recusa.status_code == 422
    assert CPF_REPROVADO not in recusa.text
    lida = cliente.get(f"/reservas/{id_reserva}/ficha").json()
    assert lida["endereco"] in (None, "")
    assert lida["numero_documento"] in (None, "")


@pytest.mark.postgres
def test_put_cpf_valido_pontuado_persiste_onze_digitos(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_parcial(cliente, ambiente, telefone="11987654329")
    corpo = {
        **NOVE,
        "tipo_documento": "cpf",
        "numero_documento": CPF_VALIDO_PONTUADO,
    }
    resposta = cliente.put(f"/reservas/{id_reserva}/ficha", json=corpo)
    assert resposta.status_code == 200
    assert resposta.json()["numero_documento"] == CPF_VALIDO


@pytest.mark.postgres
def test_put_cpf_reprovado_log_nao_traz_numero(app_sobre_ambiente, caplog, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_parcial(cliente, ambiente, telefone="11987654330")
    linhas: list[str] = []

    def _info(msg, *args, **kwargs):
        linhas.append(msg % args if args else str(msg))

    monkeypatch.setattr(
        "app.modulos.hospedagem.service.logger.info", _info
    )
    caplog.set_level(logging.INFO)
    ruim = {
        **NOVE,
        "tipo_documento": "cpf",
        "numero_documento": CPF_REPROVADO,
    }
    assert cliente.put(f"/reservas/{id_reserva}/ficha", json=ruim).status_code == 422
    texto = "\n".join(linhas) + caplog.text
    assert "ficha_alterada_recusada" in texto
    assert "422" in texto
    assert CPF_REPROVADO not in texto
    assert str(id_reserva) in texto
