"""Texto do lembrete — opcionalidade, recepcao e minimizacao."""

from app.modulos.conversa.texto_lembrete import montar_texto_lembrete


def test_declara_opcionalidade_e_preenchimento_na_recepcao():
    texto = montar_texto_lembrete(nome_completo="Maria Silva")
    assert "Ola, Maria!" in texto
    assert "opcional" in texto
    assert "recepcao" in texto


def test_nao_repete_lista_numerada_nem_dados_do_titular():
    texto = montar_texto_lembrete(nome_completo="Maria Silva")
    assert "1. " not in texto
    assert "Nome completo" not in texto
    assert "Silva" not in texto.split("!")[0]
    assert "5511" not in texto
    assert "RG" not in texto
    assert "Rua " not in texto
