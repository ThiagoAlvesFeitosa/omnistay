"""Montagem pura do texto da lista de pedidos feitos pelo chat."""

from decimal import Decimal

from app.modulos.conversa.texto_coleta import primeiro_nome
from app.modulos.conversa.texto_confirmacao_consumo import _formatar_reais


def montar_texto_lista_pedidos_chat(*, nome_completo: str, itens: list) -> str:
    prenome = primeiro_nome(nome_completo)
    linhas = [
        f"Ola, {prenome}!",
        "",
        "Seguem os pedidos feitos pelo chat:",
    ]
    total = Decimal("0.00")
    for item in itens:
        valor = item["valor_praticado"]
        total += valor
        linhas.append(f"- {item['descricao_item']} ({_formatar_reais(valor)})")
    linhas.extend(
        [
            "",
            f"Total dos pedidos feitos pelo chat: {_formatar_reais(total)}",
            "",
            "Esta lista cobre somente o que voce pediu pelo chat.",
        ]
    )
    return "\n".join(linhas)
