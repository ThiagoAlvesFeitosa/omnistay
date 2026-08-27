"""IA real (fabrica + aviso): regressao humana e recado de boas-vindas."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from testes.integracao.test_classificar_mensagem import _item_fila, _postar
from testes.integracao.test_confirmar_chegada import _criar_elegivel
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import SEGREDO, _criar_hospedada
from worker.consumidor import processar_uma_passagem, processar_uma_passagem_na_engine


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


@pytest.mark.postgres
def test_falso_com_falha_de_classificacao_grava_desfecho_humano_e_conclui(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987650091")
    _postar(cliente, "evt-ia-real-ancora", "preciso de ajuda", telefone="11987650091")
    llm = LLMFalso()
    llm.falhar_classificacao = True
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        eixos = conexao.execute(
            text(
                "SELECT intencao, classificacao_bruta FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).mappings().one()
        status = conexao.execute(
            text(
                "SELECT status FROM trabalho"
                " WHERE tipo = 'classificar_mensagem'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert eixos["intencao"] is None
    assert eixos["classificacao_bruta"]["desfecho"] == "indisponivel"
    assert status == "concluido"
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True


@pytest.mark.postgres
def test_boas_vindas_traz_aviso_e_coleta_nao_traz(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_elegivel(cliente, ambiente, telefone="11987650092")
    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 200

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)

    with ambiente.conexao() as conexao:
        mensagens = conexao.execute(
            text("SELECT conteudo FROM mensagem WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalars().all()

    boas = [m for m in mensagens if "chegada esta confirmada" in m]
    coletas = [m for m in mensagens if "dados cadastrais" in m]
    assert len(boas) == 1
    assert "assistente virtual" in boas[0].lower()
    assert "recepcao" in boas[0].lower()
    assert boas[0].count("?") == 1
    assert len(coletas) == 1
    assert "assistente virtual" not in coletas[0].lower()

    envio = next(e for e in porta.envios if e["tipo"] == "boas_vindas")
    assert len(envio["variaveis"]) == 4
