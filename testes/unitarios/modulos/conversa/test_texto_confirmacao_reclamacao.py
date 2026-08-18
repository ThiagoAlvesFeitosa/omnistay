"""Recado padrao de confirmacao de reclamacao tecnica."""

from app.modulos.conversa.texto_confirmacao_reclamacao import (
    montar_confirmacao_reclamacao,
)


def test_confirmacao_aciona_manutencao_e_pergunta_horario_quando_pedido():
    texto = montar_confirmacao_reclamacao(
        nome_completo="Maria Silva", perguntar_horario=True
    )
    assert "Maria" in texto
    assert "Silva" not in texto
    assert "receb" in texto.casefold()
    assert "manutencao" in texto.casefold() or "manutenção" in texto.casefold()
    assert "horario" in texto.casefold() or "horário" in texto.casefold()
    assert "minuto" not in texto.casefold()
    assert "hoje" not in texto.casefold()
    assert "cardapio" not in texto.casefold()
    assert "ar-condicionado" not in texto.casefold()
    assert "gela" not in texto.casefold()


def test_confirmacao_nao_pergunta_horario_quando_ja_informado():
    texto = montar_confirmacao_reclamacao(
        nome_completo="Maria Silva", perguntar_horario=False
    )
    assert "manutencao" in texto.casefold() or "manutenção" in texto.casefold()
    assert "horario" not in texto.casefold()
    assert "horário" not in texto.casefold()
    assert "prefer" not in texto.casefold()
