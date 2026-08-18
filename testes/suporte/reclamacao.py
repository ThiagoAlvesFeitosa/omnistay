"""Textos e eixos de reclamacao tecnica (F3.5).

F3.6 fecha o chamado via POST /solicitacoes/{id}/resolucao.
"""

from testes.suporte.classificacao import resultado_valido

TEXTO_COM_QUARTO_SEM_HORARIO = "o ar do quarto 402 nao esta gelando"
TEXTO_COM_HORARIO_NA_ORIGEM = "o chuveiro vazou, pode ser depois das 16h"
TEXTO_SEM_QUARTO = "o ar nao esta gelando"
TEXTO_SO_HORARIO = "depois das 14h"


def resultado_reclamacao(*, sentimento: str = "negativo"):
    return resultado_valido(
        intencao="reclamacao_tecnica", sentimento=sentimento, urgencia="alta"
    )
