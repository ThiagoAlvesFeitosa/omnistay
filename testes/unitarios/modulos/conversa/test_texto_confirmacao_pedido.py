"""Recado padrao de confirmacao de pedido de servico."""

from app.modulos.conversa.texto_confirmacao_pedido import montar_confirmacao_pedido


def test_confirmacao_diz_que_equipe_vai_atender_sem_prazo_nem_catalogo():
    texto = montar_confirmacao_pedido(nome_completo="Maria Silva")
    assert "Maria" in texto
    assert "Silva" not in texto
    assert "pedido" in texto.casefold()
    assert "equipe" in texto.casefold()
    assert "atender" in texto.casefold()
    assert "minuto" not in texto.casefold()
    assert "hoje" not in texto.casefold()
    assert "7h" not in texto
    assert "cardapio" not in texto.casefold()
    assert "horario" not in texto.casefold()
    assert "toalha" not in texto.casefold()
    assert "preferencia" not in texto.casefold()
