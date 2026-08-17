"""Taxonomia de intencao da estadia — funcao pura, sem SQL e sem HTTP."""

from dataclasses import dataclass

from app.portas.llm import ResultadoClassificacao

INTENCOES = frozenset(
    {
        "duvida_geral",
        "pedido_de_servico",
        "reclamacao_tecnica",
        "upsell",
        "solicitacao_de_checkout",
        "fora_de_escopo",
    }
)
INTENCOES_CLASSIFICADAS = frozenset(
    {"duvida_geral", "pedido_de_servico", "reclamacao_tecnica"}
)
INTENCOES_HUMANAS = frozenset(
    {"upsell", "solicitacao_de_checkout", "fora_de_escopo"}
)
SENTIMENTOS = frozenset({"positivo", "neutro", "negativo"})
URGENCIAS = frozenset({"baixa", "media", "alta"})


@dataclass(frozen=True)
class ClassificacaoValida:
    intencao: str
    sentimento: str
    urgencia: str


def validar_classificacao(
    resultado: ResultadoClassificacao,
) -> ClassificacaoValida | None:
    intencao = resultado.intencao
    sentimento = resultado.sentimento
    urgencia = resultado.urgencia
    if not intencao or not sentimento or not urgencia:
        return None
    if intencao not in INTENCOES:
        return None
    if sentimento not in SENTIMENTOS:
        return None
    if urgencia not in URGENCIAS:
        return None
    return ClassificacaoValida(
        intencao=intencao, sentimento=sentimento, urgencia=urgencia
    )


def desfecho_de(intencao: str) -> str:
    if intencao in INTENCOES_HUMANAS:
        return "encaminhado_humano"
    return "classificado"
