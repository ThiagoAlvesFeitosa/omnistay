"""Recado padrao de duvida nao coberta."""

from app.modulos.conversa.texto_aviso_duvida import montar_aviso_duvida_nao_coberta


def test_aviso_diz_que_recepcao_vai_atender_sem_fato_de_catalogo():
    texto = montar_aviso_duvida_nao_coberta(nome_completo="Maria Silva")
    assert "Maria" in texto
    assert "Silva" not in texto
    assert "recepcao" in texto.casefold()
    assert "atender" in texto.casefold()
    assert "7h" not in texto
    assert "cardapio" not in texto.casefold()
    assert "wifi" not in texto.casefold()
