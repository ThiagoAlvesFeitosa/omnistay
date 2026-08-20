"""Texto puro da pesquisa de saida."""

from app.modulos.conversa.texto_pesquisa_saida import montar_texto_pesquisa_saida
from testes.suporte.pesquisa_saida import proibicoes_da_pesquisa


def test_pesquisa_pede_nota_comentario_e_aceite_so_com_prenome():
    texto = montar_texto_pesquisa_saida(nome_completo="Marina Duarte")
    baixo = texto.casefold()
    assert "marina" in baixo
    assert "duarte" not in baixo
    assert "1." in texto
    assert "2." in texto
    assert "3." in texto
    assert "1" in texto and "5" in texto
    assert "opcional" in baixo
    assert "sim" in baixo and "nao" in baixo
    for termo in proibicoes_da_pesquisa():
        assert termo not in baixo
