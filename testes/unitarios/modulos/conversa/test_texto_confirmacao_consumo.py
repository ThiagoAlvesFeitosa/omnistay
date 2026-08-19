"""Recado padrao quando o pedido vira consumo faturavel."""

from decimal import Decimal

from app.modulos.conversa.texto_confirmacao_consumo import montar_confirmacao_consumo
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL, proibicoes_do_recado_consumo


def test_confirmacao_de_consumo_cita_item_e_valor_sem_proibicoes():
    texto = montar_confirmacao_consumo(
        nome_completo="Maria Silva",
        descricao_item=NOME_ITEM,
        valor_praticado=PRECO_ATUAL,
    )
    assert "Maria" in texto
    assert "Silva" not in texto
    assert NOME_ITEM in texto
    assert "R$ 12,00" in texto
    compacto = texto.casefold()
    assert "atender" in compacto
    for palavra in proibicoes_do_recado_consumo():
        assert palavra not in compacto
