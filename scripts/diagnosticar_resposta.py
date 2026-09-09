"""Diagnostico: mostra exatamente o que o modelo devolve ao responder uma duvida.

Serve para parar de adivinhar quando a resposta automatica e recusada. Chama o
mesmo adaptador que o worker usa, com o mesmo catalogo, e imprime a resposta
crua mais o veredito da verificacao de fidelidade.

Uso:
    uv run python scripts/diagnosticar_resposta.py "que horas abre a piscina?"
    uv run python scripts/diagnosticar_resposta.py "tem berco no quarto?"

Nao grava nada e nao envia mensagem. So consulta.
"""

from __future__ import annotations

import sys

from app.adaptadores.catalogo_banco import CatalogoBanco
from app.adaptadores.fabrica_llm import construir_llm
from app.comum.transacao import transacao
from app.config import obter_configuracao
from app.modulos.conversa.fidelidade import resposta_fiel_ao_catalogo


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: uv run python scripts/diagnosticar_resposta.py "sua pergunta"')
        return 1
    pergunta = sys.argv[1]
    id_hotel = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    config = obter_configuracao()
    print(f"modo do LLM ....: {config.llm_modo}")
    print(f"modelo .........: {config.llm_modelo}")
    print(f"tempo limite ...: {config.llm_timeout_seconds}s")
    print()

    with transacao() as conexao:
        itens = CatalogoBanco(conexao).listar_ativos(id_hotel)
    print(f"itens ativos no catalogo do hotel {id_hotel}: {len(itens)}")
    for item in itens:
        print(f"  [{item.categoria}] {item.titulo}: {item.conteudo[:70]}")
    if not itens:
        print("\nCatalogo vazio. E por isso que nada e respondido.")
        return 1

    print(f"\npergunta: {pergunta}")
    llm = construir_llm(config)
    resultado = llm.responder_duvida(pergunta, itens)

    print("\n--- o que o modelo devolveu ---")
    print(f"coberta ........: {resultado.coberta}")
    print(f"texto ..........: {resultado.texto!r}")
    print(f"trechos citados : {len(resultado.trechos_citados)}")
    for t in resultado.trechos_citados:
        print(f"  - {t!r}")

    print("\n--- verificacao de fidelidade ---")
    if not resultado.coberta:
        print("O MODELO disse que o catalogo nao cobre a pergunta.")
        print("A verificacao nem chega a rodar. O problema esta no prompt ou no")
        print("conteudo do catalogo, nao na checagem.")
        return 0

    fiel = resposta_fiel_ao_catalogo(
        resultado.texto or "", resultado.trechos_citados, itens
    )
    print(f"resposta_fiel_ao_catalogo: {fiel}")
    if not fiel:
        print("\nA verificacao recusou. Confira, para cada trecho acima:")
        print("  1. ele aparece em algum item do catalogo?")
        print("  2. ele aparece dentro do texto da resposta?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
