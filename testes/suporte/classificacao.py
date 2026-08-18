"""Fixtures de eixos da taxonomia.

Duvida geral classificada (`desfecho=classificado`) e o gancho da F3.3:
o worker enfileira `responder_duvida` a partir desses eixos.

Pedido de servico classificado e o gancho da F3.4: o worker enfileira
`registrar_pedido_servico` a partir desses eixos.

Reclamacao tecnica classificada e o gancho da F3.5: o worker enfileira
`abrir_chamado_reclamacao` a partir desses eixos.
"""

from app.portas.llm import ResultadoClassificacao


def eixos_validos(
    *,
    intencao: str = "duvida_geral",
    sentimento: str = "neutro",
    urgencia: str = "baixa",
) -> dict[str, str]:
    return {
        "intencao": intencao,
        "sentimento": sentimento,
        "urgencia": urgencia,
    }


def resultado_valido(
    *,
    intencao: str = "duvida_geral",
    sentimento: str = "neutro",
    urgencia: str = "baixa",
) -> ResultadoClassificacao:
    eixos = eixos_validos(
        intencao=intencao, sentimento=sentimento, urgencia=urgencia
    )
    return ResultadoClassificacao(**eixos, bruto=dict(eixos))


def eixos_validos(
    *,
    intencao: str = "duvida_geral",
    sentimento: str = "neutro",
    urgencia: str = "baixa",
) -> dict[str, str]:
    return {
        "intencao": intencao,
        "sentimento": sentimento,
        "urgencia": urgencia,
    }
