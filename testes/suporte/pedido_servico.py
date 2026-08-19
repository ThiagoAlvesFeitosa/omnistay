"""Textos e eixos de pedido de servico (F3.4).

F3.7 faz fork no mesmo trabalho `registrar_pedido_servico`: item vendavel unico
vira consumo faturavel; identificacao `nenhum` (ou lista vazia) permanece o
servico operacional desta fatia — toalha extra, sem preco. F3.6 fecha o pedido
via POST /solicitacoes/{id}/resolucao.
"""

from testes.suporte.classificacao import resultado_valido

TEXTO_COM_QUARTO = "toalha extra no quarto 402"
TEXTO_SEM_QUARTO = "travesseiro extra"


def resultado_pedido_servico():
    return resultado_valido(
        intencao="pedido_de_servico", sentimento="neutro", urgencia="baixa"
    )
