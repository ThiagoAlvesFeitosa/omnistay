"""Testes da porta falsa de LLM."""

import pytest

from app.adaptadores.llm_falso import LLMFalso
from app.portas.llm import FalhaDeExtracao, ResultadoExtracao


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
