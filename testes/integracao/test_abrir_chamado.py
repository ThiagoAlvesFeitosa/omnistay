"""Worker abre chamado de reclamacao e confirma ao hospede."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import SEGREDO, _criar_hospedada
from testes.suporte.reclamacao import (
    TEXTO_COM_HORARIO_NA_ORIGEM,
    TEXTO_COM_QUARTO_SEM_HORARIO,
    TEXTO_SEM_QUARTO,
    TEXTO_SO_HORARIO,
    resultado_reclamacao,
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


def _postar(cliente, id_externo: str, texto: str, telefone="11987654001"):
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
            " ORDER BY id_mensagem DESC LIMIT 1"
        ),
        {"r": id_reserva},
    ).mappings().one()


def _solicitacao(conexao, id_reserva: int):
    return conexao.execute(
        text(
            "SELECT id_solicitacao, tipo, descricao, numero_quarto, status,"
            " janela_preferencia FROM solicitacao WHERE id_reserva = :r"
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


def _passar(conexao, llm=None):
    porta = llm or LLMFalso()
    if llm is None:
        porta.configurar_classificacao(resultado_reclamacao())
    processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=porta)


@pytest.mark.postgres
def test_reclamacao_com_quarto_confirma_e_abre_chamado_sem_consumo(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654001")
    _postar(cliente, "evt-rec-402", TEXTO_COM_QUARTO_SEM_HORARIO, telefone="11987654001")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_reclamacao())
    with ambiente.engine.begin() as conexao:
        _passar(conexao, llm)
        recebida = _recebida(conexao, id_reserva)
        bruto = recebida["classificacao_bruta"]
        enviada = conexao.execute(
            text("SELECT conteudo FROM mensagem WHERE id_mensagem = :id"),
            {"id": bruto["id_mensagem_resposta"]},
        ).scalar_one()
        solicitacao = _solicitacao(conexao, id_reserva)
        contagens = _contagens(conexao, id_reserva)
    assert recebida["conteudo"] == TEXTO_COM_QUARTO_SEM_HORARIO
    assert recebida["intencao"] == "reclamacao_tecnica"
    assert bruto["desfecho"] == "classificado"
    assert bruto["resposta"] == "confirmacao_reclamacao"
    assert "manutencao" in enviada.casefold()
    assert "horario" in enviada.casefold()
    assert "gelando" not in enviada.casefold()
    assert solicitacao["tipo"] == "reclamacao"
    assert solicitacao["descricao"] == TEXTO_COM_QUARTO_SEM_HORARIO
    assert solicitacao["numero_quarto"] == "402"
    assert solicitacao["janela_preferencia"] is None
    assert solicitacao["status"] == "aberta"
    assert contagens["enviadas"] >= 1
    assert contagens["solicitacoes"] == 1
    assert contagens["consumos"] == 0
    assert contagens["status"] == "hospedado"
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is False


@pytest.mark.postgres
def test_origem_com_horario_grava_janela_sem_perguntar(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654002")
    _postar(cliente, "evt-rec-16h", TEXTO_COM_HORARIO_NA_ORIGEM, telefone="11987654002")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_reclamacao())
    with ambiente.engine.begin() as conexao:
        _passar(conexao, llm)
        bruto = _recebida(conexao, id_reserva)["classificacao_bruta"]
        enviada = conexao.execute(
            text("SELECT conteudo FROM mensagem WHERE id_mensagem = :id"),
            {"id": bruto["id_mensagem_resposta"]},
        ).scalar_one()
        janela = _solicitacao(conexao, id_reserva)["janela_preferencia"]
    assert janela == "depois das 16h"
    assert "horario" not in enviada.casefold()


@pytest.mark.postgres
def test_followup_horario_completa_mesmo_chamado_sem_segunda_enviada(cenario):
    cliente, ambiente = cenario
    telefone = "11987654003"
    id_reserva = _criar_hospedada(cliente, ambiente, telefone=telefone)
    _postar(cliente, "evt-rec-orig", TEXTO_COM_QUARTO_SEM_HORARIO, telefone=telefone)
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_reclamacao())
    with ambiente.engine.begin() as conexao:
        _passar(conexao, llm)
        primeira = _contagens(conexao, id_reserva)
        id_solicitacao = _solicitacao(conexao, id_reserva)["id_solicitacao"]
    _postar(cliente, "evt-rec-14h", TEXTO_SO_HORARIO, telefone=telefone)
    with ambiente.engine.begin() as conexao:
        _passar(conexao, llm)
        segunda = _contagens(conexao, id_reserva)
        atual = _solicitacao(conexao, id_reserva)
        follow = _recebida(conexao, id_reserva)
    assert segunda["solicitacoes"] == 1
    assert segunda["enviadas"] == primeira["enviadas"]
    assert atual["id_solicitacao"] == id_solicitacao
    assert atual["janela_preferencia"] == "depois das 14h"
    assert follow["classificacao_bruta"]["desfecho"] == "janela_registrada"


@pytest.mark.postgres
def test_reclamacao_sem_quarto_permanece_visivel(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654004")
    _postar(cliente, "evt-rec-sem", TEXTO_SEM_QUARTO, telefone="11987654004")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_reclamacao())
    with ambiente.engine.begin() as conexao:
        _passar(conexao, llm)
        quarto = _solicitacao(conexao, id_reserva)["numero_quarto"]
        enviadas = _contagens(conexao, id_reserva)["enviadas"]
    assert quarto is None
    assert enviadas >= 1
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    itens = cliente.get("/solicitacoes").json()["itens"]
    item = next(i for i in itens if i["id_reserva"] == id_reserva)
    assert item["numero_quarto"] is None
    assert item["tipo"] == "reclamacao"
    assert item["descricao"] == TEXTO_SEM_QUARTO


@pytest.mark.postgres
def test_segunda_passagem_nao_duplica_chamado(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654005")
    _postar(cliente, "evt-rec-dup", TEXTO_COM_QUARTO_SEM_HORARIO, telefone="11987654005")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_reclamacao())
    with ambiente.engine.begin() as conexao:
        _passar(conexao, llm)
        primeira = _contagens(conexao, id_reserva)
        _passar(conexao, llm)
        segunda = _contagens(conexao, id_reserva)
    assert primeira["solicitacoes"] == 1
    assert segunda["solicitacoes"] == 1
    assert segunda["enviadas"] == primeira["enviadas"]
    assert segunda["consumos"] == 0
