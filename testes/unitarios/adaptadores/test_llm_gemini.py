"""Adaptador real: parseia JSON do candidato; nunca abre a rede."""

import json
import logging

import httpx
import pytest

from app.portas.catalogo import ItemCatalogo
from app.portas.llm import (
    FalhaDeClassificacao,
    FalhaDeConversacao,
    FalhaDeExtracao,
    FalhaDeIdentificacao,
)
from testes.suporte.llm import cliente_gemini_falso


def _envelope(objeto: dict) -> dict:
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps(objeto)}]}}]
    }


def _porta(handler, *, chave="k-teste", modelo="gemini-2.0-flash"):
    from app.adaptadores.llm_gemini import LLMGemini

    return LLMGemini(
        chave=chave,
        timeout=15.0,
        modelo=modelo,
        cliente=cliente_gemini_falso(handler),
    )


def test_classificar_devolve_eixos_e_usa_header_de_chave():
    pedidos = []

    def handler(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return httpx.Response(
            200,
            json=_envelope(
                {
                    "intencao": "duvida_geral",
                    "sentimento": "neutro",
                    "urgencia": "baixa",
                }
            ),
        )

    porta = _porta(handler, modelo="gemini-2.0-flash")
    resultado = porta.classificar("que horas e o cafe")

    assert resultado.intencao == "duvida_geral"
    assert resultado.sentimento == "neutro"
    assert resultado.urgencia == "baixa"
    assert resultado.bruto["intencao"] == "duvida_geral"
    assert len(pedidos) == 1
    pedido = pedidos[0]
    assert pedido.method == "POST"
    assert pedido.url.host == "generativelanguage.googleapis.com"
    assert pedido.url.path.endswith("/models/gemini-2.0-flash:generateContent")
    assert "key" not in pedido.url.params
    assert pedido.headers["x-goog-api-key"] == "k-teste"


def test_classificar_com_taxonomia_invalida_devolve_resultado():
    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_envelope(
                {
                    "intencao": "nao_existe",
                    "sentimento": "neutro",
                    "urgencia": "baixa",
                }
            ),
        )

    resultado = _porta(handler).classificar("texto solto")
    assert resultado.intencao == "nao_existe"
    assert resultado.bruto["intencao"] == "nao_existe"


def test_extrair_ficha_devolve_desfecho_e_campos_sem_idade():
    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_envelope(
                {
                    "desfecho": "parcial",
                    "campos": {
                        "nome_completo": "Maria Silva",
                        "cidade": "Recife",
                        "idade": "40",
                    },
                }
            ),
        )

    resultado = _porta(handler).extrair_ficha("sou Maria de Recife")
    assert resultado.desfecho == "parcial"
    assert resultado.campos["nome_completo"] == "Maria Silva"
    assert resultado.campos["cidade"] == "Recife"
    assert "idade" not in resultado.campos


def test_responder_duvida_inclui_itens_no_corpo_e_devolve_resultado():
    pedidos = []

    def handler(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return httpx.Response(
            200,
            json=_envelope(
                {
                    "coberta": True,
                    "texto": "7h as 10h",
                    "trechos_citados": ["7h as 10h"],
                }
            ),
        )

    itens = (
        ItemCatalogo(
            id_catalogo_item=1,
            categoria="horario",
            titulo="Cafe da manha",
            conteudo="7h as 10h",
        ),
    )
    resultado = _porta(handler).responder_duvida("que horas e o cafe", itens)
    assert resultado.coberta is True
    assert resultado.texto == "7h as 10h"
    assert resultado.trechos_citados == ("7h as 10h",)
    corpo = json.loads(pedidos[0].content)
    prompt = corpo["contents"][0]["parts"][0]["text"]
    assert "Cafe da manha" in prompt
    assert "7h as 10h" in prompt


def test_identificar_item_vendavel_parseia_json():
    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_envelope(
                {
                    "desfecho": "unico",
                    "id_item_vendavel": 3,
                    "quantidade": 2,
                }
            ),
        )

    resultado = _porta(handler).identificar_item_vendavel(
        "duas aguas", ((3, "Agua"), (4, "Vinho"))
    )
    assert resultado.desfecho == "unico"
    assert resultado.id_item_vendavel == 3
    assert resultado.quantidade == 2


def test_interpretar_pesquisa_saida_parseia_json():
    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_envelope(
                {
                    "desfecho": "completo",
                    "nota": 5,
                    "comentario": "otimo",
                    "aceite": True,
                }
            ),
        )

    resultado = _porta(handler).interpretar_pesquisa_saida("nota 5 e sim")
    assert resultado.desfecho == "completo"
    assert resultado.nota == 5
    assert resultado.comentario == "otimo"
    assert resultado.aceite is True


@pytest.mark.parametrize(
    ("status", "codigo"),
    [(401, "llm_recusa"), (403, "llm_recusa"), (429, "llm_quota"), (503, "llm_indisponivel")],
)
def test_classificar_mapeia_status_http(status, codigo):
    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {}})

    with pytest.raises(FalhaDeClassificacao) as erro:
        _porta(handler).classificar("qualquer")
    assert erro.value.codigo == codigo
    assert "qualquer" not in str(erro.value)


def test_classificar_timeout_vira_tempo_esgotado():
    def handler(_pedido: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("estouro")

    with pytest.raises(FalhaDeClassificacao) as erro:
        _porta(handler).classificar("segredo do hospede")
    assert erro.value.codigo == "llm_tempo_esgotado"
    assert "segredo" not in str(erro.value)


def test_classificar_rede_vira_indisponivel():
    def handler(_pedido: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("recusado")

    with pytest.raises(FalhaDeClassificacao) as erro:
        _porta(handler).classificar("texto")
    assert erro.value.codigo == "llm_indisponivel"


@pytest.mark.parametrize(
    "corpo",
    [b"<<<", json.dumps({"candidates": []}).encode()],
)
def test_classificar_corpo_invalido_vira_formato(corpo):
    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=corpo)

    with pytest.raises(FalhaDeClassificacao) as erro:
        _porta(handler).classificar("texto")
    assert erro.value.codigo == "llm_formato_invalido"


def test_demais_metodos_mapeiam_falha_do_contrato():
    def handler(_pedido: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("estouro")

    porta = _porta(handler)
    with pytest.raises(FalhaDeExtracao) as extracao:
        porta.extrair_ficha("x")
    assert extracao.value.codigo == "llm_tempo_esgotado"
    with pytest.raises(FalhaDeConversacao) as conversa:
        porta.responder_duvida("x", ())
    assert conversa.value.codigo == "llm_tempo_esgotado"
    with pytest.raises(FalhaDeIdentificacao) as identificacao:
        porta.identificar_item_vendavel("x", ())
    assert identificacao.value.codigo == "llm_tempo_esgotado"
    with pytest.raises(FalhaDeExtracao) as pesquisa:
        porta.interpretar_pesquisa_saida("x")
    assert pesquisa.value.codigo == "llm_tempo_esgotado"


def test_log_nao_traz_chave_nem_texto_do_hospede(caplog):
    chave = "secret-test-key"
    marca = "MARCA-HOSPEDE-XYZ"

    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_envelope(
                {
                    "intencao": "duvida_geral",
                    "sentimento": "neutro",
                    "urgencia": "baixa",
                    "eco": marca,
                }
            ),
        )

    with caplog.at_level(logging.DEBUG, logger="app.adaptadores.llm_gemini"):
        _porta(handler, chave=chave).classificar(marca)

    conjunto = " ".join(registro.getMessage() for registro in caplog.records)
    assert chave not in conjunto
    assert marca not in conjunto
    assert "classificar" in conjunto


def test_log_de_quota_nao_traz_chave_nem_texto(caplog):
    chave = "secret-test-key"
    marca = "MARCA-HOSPEDE-XYZ"

    def handler(_pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": marca}})

    with caplog.at_level(logging.DEBUG, logger="app.adaptadores.llm_gemini"):
        with pytest.raises(FalhaDeClassificacao):
            _porta(handler, chave=chave).classificar(marca)

    conjunto = " ".join(registro.getMessage() for registro in caplog.records)
    assert chave not in conjunto
    assert marca not in conjunto
    assert "llm_quota" in conjunto


def test_servico_de_conversa_nao_importa_adaptador_real():
    import inspect

    from app.modulos.conversa import service as servico

    fonte = inspect.getsource(servico)
    assert "llm_gemini" not in fonte
    assert "fabrica_llm" not in fonte
