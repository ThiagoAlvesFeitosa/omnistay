"""Textos e eixos de pedido de servico (F3.4).

F3.6 fecha o pedido via POST /solicitacoes/{id}/resolucao.
"""

from testes.suporte.classificacao import resultado_valido

TEXTO_COM_QUARTO = "toalha extra no quarto 402"
TEXTO_SEM_QUARTO = "travesseiro extra"


def resultado_pedido_servico():
    return resultado_valido(
        intencao="pedido_de_servico", sentimento="neutro", urgencia="baixa"
    )
