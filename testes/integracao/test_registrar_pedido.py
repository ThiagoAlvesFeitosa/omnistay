"""Worker registra pedido de servico e confirma ao hospede."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import SEGREDO, _criar_hospedada
from testes.suporte.pedido_servico import (
    TEXTO_COM_QUARTO,
    TEXTO_SEM_QUARTO,
    resultado_pedido_servico,
)
from testes.suporte.webhook import postar_webhook
from worker.consumidor import processar_uma_passagem


@pytest.fixture
def cenario(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "token-teste")
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    yield cliente, ambiente
    obter_configuracao.cache_clear()


def _postar(cliente, id_externo: str, texto: str, telefone="11987654321"):
    return postar_webhook(
        cliente,
        {
            "id_externo": id_externo,
            "telefone_origem": telefone,
            "texto": texto,
            "tem_texto_utilizavel": True,
        },
        segredo=SEGREDO,
    )


def _item_fila(cliente, id_reserva: int) -> dict:
    itens = cliente.get("/fila-do-dia").json()["itens"]
    return next(i for i in itens if i["id_reserva"] == id_reserva)


def _recebida(conexao, id_reserva: int):
    return conexao.execute(
        text(
            "SELECT id_mensagem, conteudo, classificacao_bruta, intencao"
            " FROM mensagem"
            " WHERE id_reserva = :r AND direcao = 'recebida'"
        ),
        {"r": id_reserva},
    ).mappings().one()


def _contagens(conexao, id_reserva: int) -> dict:
    return {
        "enviadas": conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
            ),
            {"r": id_reserva},
        ).scalar_one(),
        "solicitacoes": conexao.execute(
            text(
                "SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one(),
        "consumos": conexao.execute(
            text(
                "SELECT COUNT(*) FROM consumo c"
                " JOIN solicitacao s ON s.id_solicitacao = c.id_solicitacao"
                " WHERE s.id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one(),
        "status": conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one(),
    }


@pytest.mark.postgres
def test_pedido_com_quarto_confirma_e_abre_servico_sem_consumo(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987652001")
    _postar(cliente, "evt-ped-402", TEXTO_COM_QUARTO, telefone="11987652001")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_pedido_servico())
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        recebida = _recebida(conexao, id_reserva)
        bruto = recebida["classificacao_bruta"]
        enviada = conexao.execute(
            text("SELECT conteudo FROM mensagem WHERE id_mensagem = :id"),
            {"id": bruto["id_mensagem_resposta"]},
        ).scalar_one()
        solicitacao = conexao.execute(
            text(
                "SELECT tipo, descricao, numero_quarto, status"
                " FROM solicitacao WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).mappings().one()
        contagens = _contagens(conexao, id_reserva)
    assert recebida["conteudo"] == TEXTO_COM_QUARTO
    assert recebida["intencao"] == "pedido_de_servico"
    assert bruto["desfecho"] == "classificado"
    assert bruto["resposta"] == "confirmacao_pedido"
    assert "equipe" in enviada.casefold()
    assert "toalha" not in enviada.casefold()
    assert solicitacao["tipo"] == "servico"
    assert solicitacao["descricao"] == TEXTO_COM_QUARTO
    assert solicitacao["numero_quarto"] == "402"
    assert solicitacao["status"] == "aberta"
    assert contagens["enviadas"] >= 1
    assert contagens["solicitacoes"] == 1
    assert contagens["consumos"] == 0
    assert contagens["status"] == "hospedado"
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is False
    pendentes = cliente.get("/consumos/pendentes")
    assert pendentes.status_code == 200
    assert all(
        i["id_reserva"] != id_reserva for i in pendentes.json()["itens"]
    )


@pytest.mark.postgres
def test_pedido_sem_quarto_permanece_visivel(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987652002")
    _postar(cliente, "evt-ped-sem", TEXTO_SEM_QUARTO, telefone="11987652002")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_pedido_servico())
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        quarto = conexao.execute(
            text(
                "SELECT numero_quarto FROM solicitacao WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        enviadas = conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert quarto is None
    assert enviadas >= 1
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    itens = cliente.get("/solicitacoes").json()["itens"]
    item = next(i for i in itens if i["id_reserva"] == id_reserva)
    assert item["numero_quarto"] is None
    assert item["descricao"] == TEXTO_SEM_QUARTO


@pytest.mark.postgres
def test_segunda_passagem_nao_duplica_pedido(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987652003")
    _postar(cliente, "evt-ped-dup", TEXTO_COM_QUARTO, telefone="11987652003")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_pedido_servico())
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        primeira = _contagens(conexao, id_reserva)
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        segunda = _contagens(conexao, id_reserva)
    assert primeira["solicitacoes"] == 1
    assert segunda["solicitacoes"] == 1
    assert segunda["enviadas"] == primeira["enviadas"]
    assert segunda["consumos"] == 0
