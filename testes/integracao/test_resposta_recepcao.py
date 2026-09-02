"""GET conversa da estadia e POST resposta da recepcao."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from testes.integracao.test_reservas import _corpo_valido, _login
from testes.integracao.test_solicitacoes import _semear_reclamacao
from testes.integracao.test_webhook_estadia import _criar_hospedada
from worker.consumidor import processar_uma_passagem


def _abrir_janela(ambiente, id_reserva: int) -> None:
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'tem berco?')"
            ),
            {"r": id_reserva},
        )


@pytest.mark.postgres
def test_recepcao_le_e_envia_e_worker_entrega(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651001")
    _abrir_janela(ambiente, id_reserva)

    lida = cliente.get(f"/reservas/{id_reserva}/conversa")
    assert lida.status_code == 200
    corpo = lida.json()
    assert corpo["janela"]["aberta"] is True
    origens = {m["origem"] for m in corpo["mensagens"]}
    assert "hospede" in origens

    enviada = cliente.post(
        f"/reservas/{id_reserva}/respostas",
        json={"texto": "Sim, temos berco no quarto."},
    )
    assert enviada.status_code == 201
    item = enviada.json()
    assert item["origem"] == "recepcao"
    assert item["entrega"] == "enviando"
    assert item["conteudo"] == "Sim, temos berco no quarto."

    gateway = MensageriaFalsa()
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=gateway)
    assert any(
        e["tipo"] == "sessao" and e["corpo"] == "Sim, temos berco no quarto."
        for e in gateway.envios
    )
    de_novo = cliente.get(f"/reservas/{id_reserva}/conversa").json()
    humana = next(m for m in de_novo["mensagens"] if m["origem"] == "recepcao")
    assert humana["entrega"] == "enviada"
    assert humana["status_envio"] == "enviada"


@pytest.mark.postgres
def test_staff_e_gestao_recebem_403(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651002")
    _abrir_janela(ambiente, id_reserva)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get(f"/reservas/{id_reserva}/conversa").status_code == 403
    assert (
        cliente.post(
            f"/reservas/{id_reserva}/respostas", json={"texto": "Oi"}
        ).status_code
        == 403
    )
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.get(f"/reservas/{id_reserva}/conversa").status_code == 403
    assert (
        cliente.post(
            f"/reservas/{id_reserva}/respostas", json={"texto": "Oi"}
        ).status_code
        == 403
    )


@pytest.mark.postgres
def test_post_nao_altera_chamado_nem_enfileira_resolucao(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651003")
    _semear_reclamacao(ambiente, id_reserva, "Ar-condicionado parado", "12", None)
    antes = None
    with ambiente.conexao() as conexao:
        antes = conexao.execute(
            text(
                "SELECT id_solicitacao, status FROM solicitacao"
                " WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).mappings().one()
        resolucoes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_confirmacao_resolucao'"
            )
        ).scalar_one()
    assert antes["status"] == "aberta"
    resposta = cliente.post(
        f"/reservas/{id_reserva}/respostas",
        json={"texto": "Ja acionamos a manutencao."},
    )
    assert resposta.status_code == 201
    with ambiente.conexao() as conexao:
        depois = conexao.execute(
            text("SELECT status FROM solicitacao WHERE id_solicitacao = :id"),
            {"id": antes["id_solicitacao"]},
        ).scalar_one()
        resolucoes_depois = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_confirmacao_resolucao'"
            )
        ).scalar_one()
    assert depois == "aberta"
    assert resolucoes_depois == resolucoes


@pytest.mark.postgres
def test_hotel_alheio_devolve_404(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    id_b = cliente.post(
        "/reservas", json=_corpo_valido(nome="Beta", telefone="11977776666")
    ).json()["id_reserva"]
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert cliente.get(f"/reservas/{id_b}/conversa").status_code == 404
    assert (
        cliente.post(
            f"/reservas/{id_b}/respostas", json={"texto": "Oi"}
        ).status_code
        == 404
    )


@pytest.mark.postgres
def test_texto_vazio_ou_longo_devolve_422(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651004")
    _abrir_janela(ambiente, id_reserva)
    assert (
        cliente.post(
            f"/reservas/{id_reserva}/respostas", json={"texto": "   "}
        ).status_code
        == 422
    )
    assert (
        cliente.post(
            f"/reservas/{id_reserva}/respostas", json={"texto": "x" * 4097}
        ).status_code
        == 422
    )


@pytest.mark.postgres
def test_janela_fechada_devolve_409(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651005")
    lida = cliente.get(f"/reservas/{id_reserva}/conversa")
    assert lida.status_code == 200
    assert lida.json()["janela"]["aberta"] is False
    assert lida.json()["janela"]["motivo"] == "nunca_escreveu"
    recusa = cliente.post(
        f"/reservas/{id_reserva}/respostas", json={"texto": "Oi"}
    )
    assert recusa.status_code == 409
    assert recusa.json()["detail"]["codigo"] == "janela_fechada"


@pytest.mark.postgres
def test_chamado_resolvido_nao_fecha_a_janela(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651007")
    _semear_reclamacao(ambiente, id_reserva, "ar nao gela", "12", None)
    id_sol = cliente.get("/solicitacoes").json()["itens"][0]["id_solicitacao"]
    assert cliente.post(f"/solicitacoes/{id_sol}/resolucao").status_code == 200
    lida = cliente.get(f"/reservas/{id_reserva}/conversa")
    assert lida.status_code == 200
    assert lida.json()["janela"]["aberta"] is True
    resposta = cliente.post(
        f"/reservas/{id_reserva}/respostas",
        json={"texto": "Complemento depois do chamado resolvido."},
    )
    assert resposta.status_code == 201


@pytest.mark.postgres
def test_reserva_encerrada_permanece_legivel_e_nao_envia_com_janela_fechada(
    app_sobre_ambiente,
):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651008")
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text("UPDATE reserva SET status = 'encerrado' WHERE id_reserva = :r"),
            {"r": id_reserva},
        )
    lida = cliente.get(f"/reservas/{id_reserva}/conversa")
    assert lida.status_code == 200
    assert lida.json()["janela"]["aberta"] is False
    recusa = cliente.post(
        f"/reservas/{id_reserva}/respostas", json={"texto": "Oi"}
    )
    assert recusa.status_code == 409
    assert recusa.json()["detail"]["codigo"] == "janela_fechada"


@pytest.mark.postgres
def test_texto_repetido_em_menos_de_cinco_segundos(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651006")
    _abrir_janela(ambiente, id_reserva)
    agora = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
    monkeypatch.setattr("app.comum.relogio.agora", lambda: agora)
    primeiro = cliente.post(
        f"/reservas/{id_reserva}/respostas", json={"texto": "Sim, temos berco."}
    )
    assert primeiro.status_code == 201
    segundo = cliente.post(
        f"/reservas/{id_reserva}/respostas", json={"texto": "Sim, temos berco."}
    )
    assert segundo.status_code == 409
    assert segundo.json()["detail"]["codigo"] == "texto_repetido"
    diferente = cliente.post(
        f"/reservas/{id_reserva}/respostas", json={"texto": "E toalha extra?"}
    )
    assert diferente.status_code == 201
    monkeypatch.setattr(
        "app.comum.relogio.agora", lambda: agora + timedelta(seconds=6)
    )
    repetido_depois = cliente.post(
        f"/reservas/{id_reserva}/respostas", json={"texto": "Sim, temos berco."}
    )
    assert repetido_depois.status_code == 201
    with ambiente.conexao() as conexao:
        quantidade = conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
                " AND classificacao_bruta->>'tipo' = 'resposta_recepcao'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        trabalhos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_resposta_recepcao'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert quantidade == 3
    assert trabalhos == 3
