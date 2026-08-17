"""Testes da porta falsa de LLM."""

import pytest

from app.adaptadores.llm_falso import LLMFalso
from app.portas.llm import (
    FalhaDeClassificacao,
    FalhaDeConversacao,
    FalhaDeExtracao,
    ResultadoClassificacao,
    ResultadoExtracao,
    ResultadoResposta,
)


def test_extracao_configurada_devolve_desfecho_e_campos():
    porta = LLMFalso()
    porta.configurar(
        ResultadoExtracao(
            desfecho="completa",
            campos={"nome_completo": "Maria Silva"},
            campos_reconhecidos=("nome_completo",),
        )
    )
    resultado = porta.extrair_ficha("1. Maria Silva")
    assert resultado.desfecho == "completa"
    assert resultado.campos["nome_completo"] == "Maria Silva"
    assert "idade" not in resultado.campos
    assert len(porta.chamadas) == 1


def test_modo_falha_levanta_erro_tipado():
    porta = LLMFalso()
    porta.falhar_sempre = True
    with pytest.raises(FalhaDeExtracao) as erro:
        porta.extrair_ficha("qualquer")
    assert erro.value.codigo == "llm_indisponivel"


def test_sem_configuracao_devolve_irreconhecivel():
    porta = LLMFalso()
    assert porta.extrair_ficha("xyz").desfecho == "irreconhecivel"


def test_classificar_sem_config_devolve_duvida_geral():
    porta = LLMFalso()
    resultado = porta.classificar("que horas e o cafe")
    assert resultado.intencao == "duvida_geral"
    assert resultado.sentimento == "neutro"
    assert resultado.urgencia == "baixa"
    assert resultado.bruto["intencao"] == "duvida_geral"
    assert len(porta.chamadas_classificar) == 1
    assert porta.chamadas == []


def test_classificar_configurado_devolve_eixos():
    porta = LLMFalso()
    porta.configurar_classificacao(
        ResultadoClassificacao(
            intencao="reclamacao_tecnica",
            sentimento="negativo",
            urgencia="alta",
            bruto={"cru": "ok"},
        )
    )
    resultado = porta.classificar("ar nao gela")
    assert resultado.intencao == "reclamacao_tecnica"
    assert resultado.bruto == {"cru": "ok"}


def test_falhar_classificacao_nao_quebra_ficha():
    porta = LLMFalso()
    porta.falhar_classificacao = True
    with pytest.raises(FalhaDeClassificacao) as erro:
        porta.classificar("qualquer")
    assert erro.value.codigo == "llm_indisponivel"
    assert porta.extrair_ficha("1. Maria").desfecho == "irreconhecivel"


def test_responder_sem_itens_nao_inventa():
    porta = LLMFalso()
    resultado = porta.responder_duvida("que horas e o cafe", ())
    assert resultado.coberta is False
    assert len(porta.chamadas_responder) == 1
    assert porta.chamadas_classificar == []


def test_responder_com_itens_sem_config_usa_primeiro():
    from testes.suporte.resposta_duvida import item_cafe

    porta = LLMFalso()
    item = item_cafe()
    resultado = porta.responder_duvida("cafe", (item,))
    assert resultado.coberta is True
    assert item.conteudo in (resultado.texto or "")
    assert item.conteudo in resultado.trechos_citados


def test_falhar_conversacao_nao_quebra_classificar_nem_ficha():
    porta = LLMFalso()
    porta.falhar_conversacao = True
    with pytest.raises(FalhaDeConversacao) as erro:
        porta.responder_duvida("cafe", ())
    assert erro.value.codigo == "llm_indisponivel"
    assert porta.classificar("x").intencao == "duvida_geral"
    assert porta.extrair_ficha("1. Maria").desfecho == "irreconhecivel"


def test_configurar_resposta_devolve_o_configurado():
    porta = LLMFalso()
    porta.configurar_resposta(
        ResultadoResposta(coberta=False, texto=None, trechos_citados=())
    )
    from testes.suporte.resposta_duvida import item_cafe

    resultado = porta.responder_duvida("cafe", (item_cafe(),))
    assert resultado.coberta is False
