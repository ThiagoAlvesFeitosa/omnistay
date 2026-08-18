"""GET /solicitacoes — fila operacional sem ficha cadastral."""

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import abrir_reclamacao, abrir_servico
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import _criar_hospedada

CHAVES_CADASTRAIS = (
    "nome",
    "telefone",
    "documento",
    "nome_completo",
    "cpf",
    "endereco",
)


def _semear_servico(ambiente, id_reserva: int, descricao: str, quarto: str | None):
    with ambiente.engine.begin() as conexao:
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
            ),
            {"r": id_reserva, "c": descricao},
        ).scalar_one()
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao=descricao,
            numero_quarto=quarto,
            urgencia="baixa",
        )


def _semear_reclamacao(
    ambiente, id_reserva: int, descricao: str, quarto: str | None, janela: str | None
):
    with ambiente.engine.begin() as conexao:
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
            ),
            {"r": id_reserva, "c": descricao},
        ).scalar_one()
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao=descricao,
            numero_quarto=quarto,
            urgencia="alta",
            janela_preferencia=janela,
        )


def _chaves_proibidas(corpo: dict) -> list[str]:
    achadas = []
    itens = corpo.get("itens", [])
    for item in itens:
        for chave in item:
            if chave.casefold() in CHAVES_CADASTRAIS:
                achadas.append(chave)
    for chave in corpo:
        if chave.casefold() in CHAVES_CADASTRAIS:
            achadas.append(chave)
    return achadas


@pytest.mark.postgres
def test_staff_recepcao_e_gestao_leem_fila_sem_cadastro(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_a = _criar_hospedada(cliente, ambiente, telefone="11987653001", nome="Maria Silva")
    _semear_servico(ambiente, id_a, "toalha extra no quarto 402", "402")

    formatos = []
    for perfil in ("staff", "recepcao", "gestor"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        resposta = cliente.get("/solicitacoes")
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert _chaves_proibidas(corpo) == []
        item = next(i for i in corpo["itens"] if i["id_reserva"] == id_a)
        assert item["numero_quarto"] == "402"
        assert item["descricao"] == "toalha extra no quarto 402"
        assert item["tipo"] == "servico"
        assert item["janela_preferencia"] is None
        assert item["destaque_tempo_excedido"] is False
        formatos.append(
            {
                "id_solicitacao": item["id_solicitacao"],
                "tipo": item["tipo"],
                "descricao": item["descricao"],
                "numero_quarto": item["numero_quarto"],
            }
        )
    assert formatos[0] == formatos[1] == formatos[2]


@pytest.mark.postgres
def test_staff_do_hotel_b_nao_ve_pedido_do_hotel_a(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_a = _criar_hospedada(cliente, ambiente, telefone="11987653002")
    _semear_servico(ambiente, id_a, "toalha extra", None)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["staff"])
    resposta = cliente.get("/solicitacoes")
    assert resposta.status_code == 200
    ids = [i["id_reserva"] for i in resposta.json()["itens"]]
    assert id_a not in ids


@pytest.mark.postgres
def test_staff_continua_recusado_na_ficha_e_na_fila_do_dia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987653003")
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/fila-do-dia").status_code == 403
    assert cliente.get(f"/reservas/{id_reserva}/ficha").status_code == 403
    assert cliente.get("/solicitacoes").status_code == 200


@pytest.mark.postgres
def test_staff_recepcao_e_gestao_leem_reclamacao_sem_cadastro(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_a = _criar_hospedada(cliente, ambiente, telefone="11987653004", nome="Maria Silva")
    _semear_reclamacao(
        ambiente, id_a, "o ar do quarto 402 nao esta gelando", "402", None
    )

    for perfil in ("staff", "recepcao", "gestor"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        resposta = cliente.get("/solicitacoes")
        assert resposta.status_code == 200
        corpo = resposta.json()
        assert _chaves_proibidas(corpo) == []
        item = next(i for i in corpo["itens"] if i["id_reserva"] == id_a)
        assert item["tipo"] == "reclamacao"
        assert item["numero_quarto"] == "402"
        assert item["janela_preferencia"] is None
        assert item["destaque_tempo_excedido"] is False

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["staff"])
    ids = [i["id_reserva"] for i in cliente.get("/solicitacoes").json()["itens"]]
    assert id_a not in ids


@pytest.mark.postgres
def test_passagem_de_turno_omite_resolvida_nos_tres_perfis(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    primeira = _criar_hospedada(cliente, ambiente, telefone="11987653011")
    segunda = _criar_hospedada(cliente, ambiente, telefone="11987653012")
    _semear_servico(ambiente, primeira, "toalha extra", None)
    _semear_reclamacao(ambiente, segunda, "ar nao gela", None, None)

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    itens = cliente.get("/solicitacoes").json()["itens"]
    id_primeira = next(i["id_solicitacao"] for i in itens if i["id_reserva"] == primeira)
    id_segunda = next(i["id_solicitacao"] for i in itens if i["id_reserva"] == segunda)
    assert cliente.post(f"/solicitacoes/{id_primeira}/resolucao").status_code == 200

    for perfil in ("staff", "recepcao", "gestor"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        corpo = cliente.get("/solicitacoes").json()
        ids = [i["id_solicitacao"] for i in corpo["itens"]]
        assert id_primeira not in ids
        assert id_segunda in ids
        assert _chaves_proibidas(corpo) == []
        item = next(i for i in corpo["itens"] if i["id_solicitacao"] == id_segunda)
        assert "ficha" not in item
        assert item["tipo"] == "reclamacao"

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["staff"])
    ids_b = [i["id_solicitacao"] for i in cliente.get("/solicitacoes").json()["itens"]]
    assert id_primeira not in ids_b
    assert id_segunda not in ids_b
