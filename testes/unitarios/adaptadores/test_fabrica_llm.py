"""Fabrica de inteligencia escolhe o adaptador pelo modo."""

import pytest

from testes.suporte.llm import cfg_llm


def test_controlado_devolve_llm_falso():
    from app.adaptadores.fabrica_llm import construir_llm
    from app.adaptadores.llm_falso import LLMFalso
    from app.adaptadores.llm_gemini import LLMGemini

    porta = construir_llm(cfg_llm("controlado"))
    assert isinstance(porta, LLMFalso)
    assert not isinstance(porta, LLMGemini)


def test_real_com_chave_devolve_gemini_sem_rede():
    from app.adaptadores.fabrica_llm import construir_llm
    from app.adaptadores.llm_gemini import LLMGemini

    porta = construir_llm(cfg_llm("real", chave="k-teste"))
    assert isinstance(porta, LLMGemini)


@pytest.mark.parametrize("modo", ["", "teste", "DEMO", "gemini"])
def test_modo_ausente_ou_invalido_falha_alto(modo):
    from app.adaptadores.fabrica_llm import (
        ConfiguracaoDeInteligenciaInvalida,
        construir_llm,
    )

    with pytest.raises(ConfiguracaoDeInteligenciaInvalida) as erro:
        construir_llm(cfg_llm(modo))
    assert erro.value.codigo == "modo_invalido"
    assert "k-teste" not in str(erro.value)


def test_real_sem_chave_falha_alto_sem_cair_no_controlado():
    from app.adaptadores.fabrica_llm import (
        ConfiguracaoDeInteligenciaInvalida,
        construir_llm,
    )
    from app.adaptadores.llm_falso import LLMFalso

    with pytest.raises(ConfiguracaoDeInteligenciaInvalida) as erro:
        construir_llm(cfg_llm("real", chave=""))
    assert erro.value.codigo == "chave_ausente"
    assert not isinstance(getattr(erro.value, "porta", None), LLMFalso)


def test_fabrica_ignora_modo_de_canal():
    from app.adaptadores.fabrica_llm import construir_llm
    from app.adaptadores.llm_falso import LLMFalso
    from app.adaptadores.llm_gemini import LLMGemini

    demo = construir_llm(cfg_llm("controlado", mensageria_modo="demonstracao"))
    real_canal = construir_llm(cfg_llm("controlado", mensageria_modo="real"))
    assert type(demo) is type(real_canal) is LLMFalso

    a = construir_llm(
        cfg_llm("real", chave="k", mensageria_modo="demonstracao")
    )
    b = construir_llm(cfg_llm("real", chave="k", mensageria_modo="real"))
    assert type(a) is type(b) is LLMGemini


def test_excecao_de_chave_ausente_nao_interpola_segredo():
    from app.adaptadores.fabrica_llm import (
        ConfiguracaoDeInteligenciaInvalida,
        construir_llm,
    )

    with pytest.raises(ConfiguracaoDeInteligenciaInvalida) as erro:
        construir_llm(cfg_llm("real", chave=""))
    assert "AQ." not in str(erro.value)
    assert erro.value.codigo == "chave_ausente"


def test_env_example_lista_chave_sem_valor():
    from pathlib import Path

    texto = Path(".env.example").read_text(encoding="utf-8")
    linhas = [
        linha.rstrip()
        for linha in texto.splitlines()
        if linha.startswith("GEMINI_API_KEY=")
    ]
    assert linhas == ["GEMINI_API_KEY="]
    assert "LLM_MODO=" in texto
    assert "LLM_TIMEOUT_SECONDS=" in texto
    assert "LLM_MODELO=" in texto
