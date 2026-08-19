"""Worker registra consumo faturavel a partir de pedido identificado."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.propriedade import service as propriedade
from app.portas.llm import FalhaDeIdentificacao, ResultadoIdentificacao
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import SEGREDO, _criar_hospedada
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL, TEXTO_PEDIDO_CERVEJA
from testes.suporte.pedido_servico import resultado_pedido_servico
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


def _semear_item(ambiente, *, preco=PRECO_ATUAL, nome=NOME_ITEM) -> int:
    with ambiente.engine.begin() as conexao:
        item = propriedade.criar_item_vendavel(
            conexao,
            id_hotel=ambiente.propriedade_a.id_hotel,
            nome=nome,
            preco_atual=preco,
        )
        return item.id_item_vendavel


@pytest.mark.postgres
def test_pedido_identificado_nasce_consumo_pendente_com_valor(cenario):
    cliente, ambiente = cenario
    id_item = _semear_item(ambiente)
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656001")
    _postar(cliente, "evt-cer-1", TEXTO_PEDIDO_CERVEJA, telefone="11987656001")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_pedido_servico())
    llm.configurar_identificacao(
        ResultadoIdentificacao(
            desfecho="unico", id_item_vendavel=id_item, quantidade=1
        )
    )
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        consumo = conexao.execute(
            text(
                "SELECT s.tipo, c.valor_praticado, c.status_lancamento,"
                " m.classificacao_bruta, e.conteudo, r.status"
                " FROM consumo c"
                " JOIN solicitacao s ON s.id_solicitacao = c.id_solicitacao"
                " JOIN mensagem m ON m.id_mensagem = s.id_mensagem_origem"
                " JOIN mensagem e ON e.id_mensagem ="
                " (m.classificacao_bruta->>'id_mensagem_resposta')::bigint"
                " JOIN reserva r ON r.id_reserva = s.id_reserva"
                " WHERE s.id_reserva = :r"
            ),
            {"r": id_reserva},
        ).mappings().one()
    assert consumo["tipo"] == "consumo"
    assert Decimal(str(consumo["valor_praticado"])) == PRECO_ATUAL
    assert consumo["status_lancamento"] == "pendente"
    assert consumo["classificacao_bruta"]["resposta"] == "confirmacao_consumo"
    assert "R$ 12,00" in consumo["conteudo"]
    assert consumo["status"] == "hospedado"
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    itens = cliente.get("/fila-do-dia").json()["itens"]
    item = next(i for i in itens if i["id_reserva"] == id_reserva)
    assert item["precisa_atendimento_humano"] is False


@pytest.mark.postgres
def test_reajuste_nao_reescreve_consumo_ja_gravado(cenario):
    cliente, ambiente = cenario
    id_item = _semear_item(ambiente)
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656002")
    _postar(cliente, "evt-cer-2", TEXTO_PEDIDO_CERVEJA, telefone="11987656002")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_pedido_servico())
    llm.configurar_identificacao(
        ResultadoIdentificacao(
            desfecho="unico", id_item_vendavel=id_item, quantidade=1
        )
    )
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        propriedade.atualizar_item_vendavel(
            conexao,
            id_hotel=ambiente.propriedade_a.id_hotel,
            id_item_vendavel=id_item,
            preco_atual=Decimal("20.00"),
        )
        primeiro = conexao.execute(
            text(
                "SELECT valor_praticado FROM consumo c"
                " JOIN solicitacao s ON s.id_solicitacao = c.id_solicitacao"
                " WHERE s.id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert Decimal(str(primeiro)) == PRECO_ATUAL
    id_reserva2 = _criar_hospedada(cliente, ambiente, telefone="11987656003")
    _postar(cliente, "evt-cer-3", TEXTO_PEDIDO_CERVEJA, telefone="11987656003")
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        segundo = conexao.execute(
            text(
                "SELECT valor_praticado FROM consumo c"
                " JOIN solicitacao s ON s.id_solicitacao = c.id_solicitacao"
                " WHERE s.id_reserva = :r"
            ),
            {"r": id_reserva2},
        ).scalar_one()
    assert Decimal(str(segundo)) == Decimal("20.00")


@pytest.mark.postgres
def test_identificacao_ambigua_escala_sem_consumo(cenario):
    cliente, ambiente = cenario
    _semear_item(ambiente)
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656004")
    _postar(cliente, "evt-cer-4", TEXTO_PEDIDO_CERVEJA, telefone="11987656004")
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_pedido_servico())
    llm.configurar_identificacao(ResultadoIdentificacao(desfecho="ambiguo"))
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        consumos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM consumo c"
                " JOIN solicitacao s ON s.id_solicitacao = c.id_solicitacao"
                " WHERE s.id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        enviada = conexao.execute(
            text(
                "SELECT conteudo FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
                " ORDER BY id_mensagem DESC LIMIT 1"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert consumos == 0
    assert "R$" not in enviada
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    itens = cliente.get("/fila-do-dia").json()["itens"]
    item = next(i for i in itens if i["id_reserva"] == id_reserva)
    assert item["precisa_atendimento_humano"] is True
