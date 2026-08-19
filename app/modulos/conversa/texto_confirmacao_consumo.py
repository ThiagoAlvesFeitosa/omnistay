"""Recado padrao quando o pedido identificado vira consumo."""

from decimal import Decimal, ROUND_HALF_UP

from app.modulos.conversa.texto_coleta import primeiro_nome


def _formatar_reais(valor: Decimal) -> str:
    quantizado = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    partes = f"{quantizado:.2f}".split(".")
    return f"R$ {partes[0]},{partes[1]}"


def montar_confirmacao_consumo(
    *,
    nome_completo: str,
    descricao_item: str,
    valor_praticado: Decimal,
) -> str:
    prenome = primeiro_nome(nome_completo)
    valor = _formatar_reais(valor_praticado)
    return (
        f"Ola, {prenome}!\n\n"
        f"Recebemos seu pedido de {descricao_item} ({valor}). "
        "A equipe ja foi avisada e vai atender."
    )
