"""Pesquisa de saida ponta a ponta com portas falsas."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.llm import ResultadoPesquisaSaida
from testes.integracao.test_confirmar_saida import _criar_hospedada
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import SEGREDO
from testes.suporte.pesquisa_saida import proibicoes_da_pesquisa
from testes.suporte.webhook import postar_webhook
from worker.consumidor import processar_uma_passagem


@pytest.mark.postgres
def test_worker_envia_pesquisa_curta_via_falsa(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654201")
    cliente.post(f"/reservas/{id_reserva}/saida")
    porta = MensageriaFalsa()
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=porta, limite=50)
    envios = [e for e in porta.envios if e["tipo"] == "pesquisa_saida"]
    assert len(envios) == 1
    baixo = envios[0]["corpo"].casefold()
    for termo in proibicoes_da_pesquisa():
        assert termo not in baixo
    with ambiente.conexao() as conexao:
        status = conexao.execute(
            text(
                "SELECT status_envio FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
                " ORDER BY id_mensagem DESC LIMIT 1"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert status == "enviada"


@pytest.mark.postgres
def test_resposta_completa_grava_avaliacao_e_consentimento(
    app_sobre_ambiente, monkeypatch
):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "token-teste")
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    try:
        id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654202")
        cliente.post(f"/reservas/{id_reserva}/saida")
        porta = MensageriaFalsa()
        llm = LLMFalso()
        llm.configurar_pesquisa_saida(
            ResultadoPesquisaSaida(
                desfecho="completo", nota=5, comentario="otimo", aceite=True
            )
        )
        with ambiente.engine.begin() as conexao:
            processar_uma_passagem(conexao, gateway=porta, llm=llm, limite=50)
        postar_webhook(
            cliente,
            {
                "id_externo": "ps-ok",
                "telefone_origem": "11987654202",
                "texto": "5 e sim",
                "tem_texto_utilizavel": True,
            },
            segredo=SEGREDO,
        )
        with ambiente.engine.begin() as conexao:
            processar_uma_passagem(conexao, gateway=porta, llm=llm, limite=50)
            avaliacao = conexao.execute(
                text(
                    "SELECT origem, nota FROM avaliacao"
                    " WHERE id_reserva = :r AND origem = 'checkout'"
                ),
                {"r": id_reserva},
            ).mappings().one()
            consentimentos = conexao.execute(
                text(
                    "SELECT COUNT(*) FROM consentimento c"
                    " JOIN reserva_hospede rh ON rh.id_hospede = c.id_hospede"
                    " WHERE rh.id_reserva = :r"
                    " AND c.origem = 'pesquisa_checkout'"
                    " AND c.concedido"
                ),
                {"r": id_reserva},
            ).scalar_one()
            pesquisas = conexao.execute(
                text(
                    "SELECT COUNT(*) FROM trabalho"
                    " WHERE tipo = 'enviar_pesquisa_saida'"
                    " AND (payload->>'id_reserva')::bigint = :r"
                ),
                {"r": id_reserva},
            ).scalar_one()
        assert avaliacao["nota"] == 5
        assert consentimentos == 1
        assert pesquisas == 1
    finally:
        obter_configuracao.cache_clear()
