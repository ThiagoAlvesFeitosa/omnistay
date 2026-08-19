"""Recado padrao de confirmacao de resolucao."""

from app.modulos.conversa.texto_confirmacao_resolucao import (
    montar_confirmacao_resolucao,
)
from testes.suporte.resolucao import proibicoes_do_recado


def test_confirmacao_de_reclamacao_fala_de_problema_atendido():
    texto = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="reclamacao"
    )
    assert "Maria" in texto
    assert "Silva" not in texto
    compacto = texto.casefold()
    assert "problema" in compacto
    assert "atendido" in compacto or "manutencao" in compacto
    for palavra in proibicoes_do_recado():
        assert palavra not in compacto


def test_confirmacao_de_servico_fala_de_pedido_atendido():
    texto = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="servico"
    )
    assert "Maria" in texto
    assert "Silva" not in texto
    compacto = texto.casefold()
    assert "pedido" in compacto
    assert "atendido" in compacto
    for palavra in proibicoes_do_recado():
        assert palavra not in compacto


def test_confirmacao_de_consumo_nao_cita_valor_nem_lancamento():
    texto = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="consumo"
    )
    compacto = texto.casefold()
    assert "pedido" in compacto
    assert "atendido" in compacto
    assert "r$" not in compacto
    assert "lancad" not in compacto
    for palavra in proibicoes_do_recado():
        assert palavra not in compacto
