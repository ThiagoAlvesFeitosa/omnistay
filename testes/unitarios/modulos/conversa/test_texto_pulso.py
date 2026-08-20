"""Textos puros do pulso do segundo dia."""

from app.modulos.conversa.texto_pulso import (
    montar_confirmacao_pulso_negativo,
    montar_pergunta_pulso,
    montar_reconhecimento_pulso,
)
from testes.suporte.pulso import (
    proibicoes_da_confirmacao_negativa,
    proibicoes_da_pergunta,
    proibicoes_do_reconhecimento,
)


def test_pergunta_usa_so_o_primeiro_nome_e_nao_oferta():
    texto = montar_pergunta_pulso(nome_completo="Marina Duarte")
    assert "?" in texto
    assert "Marina" in texto
    assert "Duarte" not in texto
    baixo = texto.casefold()
    for termo in proibicoes_da_pergunta():
        assert termo not in baixo
    assert "\n" not in texto
    assert "\t" not in texto
    assert "    " not in texto
    assert texto.strip()


def test_reconhecimento_nao_afirma_satisfacao():
    texto = montar_reconhecimento_pulso()
    baixo = texto.casefold()
    for termo in proibicoes_do_reconhecimento():
        assert termo not in baixo
    assert montar_reconhecimento_pulso() == texto


def test_confirmacao_negativa_diz_o_proximo_passo_sem_horario():
    texto = montar_confirmacao_pulso_negativo()
    baixo = texto.casefold()
    assert "recepcao" in baixo or "alguem" in baixo or "alguém" in baixo
    for termo in proibicoes_da_confirmacao_negativa():
        assert termo not in baixo
