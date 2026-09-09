"""Sonda crua da API do Gemini: mostra o codigo HTTP e a mensagem de erro.

Serve para separar causas que hoje chegam ao log com o mesmo codigo
`llm_indisponivel`:

    401 / 403  chave invalida ou sem permissao
    404        nome de modelo inexistente
    429        cota estourada
    503        modelo sobrecarregado (problema do Google, transitorio)

Uso:
    uv run python scripts/testar_gemini.py            testa o modelo do .env
    uv run python scripts/testar_gemini.py --varrer   testa varios e diz qual responde
"""

from __future__ import annotations

import json
import sys

import httpx

from app.config import obter_configuracao

HOST = "generativelanguage.googleapis.com"

# Candidatos, do mais leve ao mais pesado. Modelo leve costuma ter fila menor.
CANDIDATOS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]


def _tentar(chave: str, modelo: str, segundos: float = 25.0) -> tuple[bool, str]:
    """Manda um pedido minimo e devolve (respondeu, descricao)."""
    import time

    inicio = time.perf_counter()
    try:
        r = httpx.post(
            f"https://{HOST}/v1beta/models/{modelo}:generateContent",
            headers={"x-goog-api-key": chave, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "Responda apenas: ok"}]}]},
            timeout=segundos,
        )
    except httpx.TimeoutException:
        return False, f"tempo esgotado (>{segundos:.0f}s)"
    except Exception as erro:
        return False, f"falhou: {erro!r}"

    decorrido = time.perf_counter() - inicio
    if r.status_code >= 400:
        try:
            mensagem = r.json().get("error", {}).get("message", "")[:70]
        except Exception:
            mensagem = r.text[:70]
        return False, f"HTTP {r.status_code} — {mensagem}"
    return True, f"OK em {decorrido:.1f}s"


def varrer() -> int:
    config = obter_configuracao()
    chave = config.gemini_api_key
    if not chave:
        print("GEMINI_API_KEY nao esta definida no .env")
        return 1

    print("Testando modelos, 25s de paciencia para cada um.\n")
    funcionam: list[str] = []
    for modelo in CANDIDATOS:
        print(f"  {modelo:.<32}", end=" ", flush=True)
        ok, descricao = _tentar(chave, modelo)
        print(descricao)
        if ok:
            funcionam.append(modelo)

    print()
    if funcionam:
        print("Modelos respondendo agora:")
        for m in funcionam:
            print(f"  {m}")
        print(f"\nColoque no .env:  LLM_MODELO={funcionam[0]}")
        print("Depois reinicie o worker.")
        return 0

    print("Nenhum modelo respondeu. A conta ou o servico estao indisponiveis agora.")
    print("Espere alguns minutos e rode de novo — 503 e sobrecarga costumam passar.")
    return 1


def main() -> int:
    if "--varrer" in sys.argv:
        return varrer()
    config = obter_configuracao()
    chave = config.gemini_api_key
    modelo = config.llm_modelo

    if not chave:
        print("GEMINI_API_KEY nao esta definida no .env")
        return 1

    print(f"modelo configurado : {modelo}")
    print(f"chave              : {chave[:10]}... ({len(chave)} caracteres)")
    print()

    # 1. A chave funciona? Listar modelos e um pedido barato.
    print("--- 1. a chave e valida? (GET /models)")
    try:
        r = httpx.get(
            f"https://{HOST}/v1beta/models",
            headers={"x-goog-api-key": chave},
            timeout=30,
        )
        print(f"    HTTP {r.status_code}")
        if r.status_code >= 400:
            print(f"    {r.text[:400]}")
            return 1
        nomes = [
            m["name"].replace("models/", "")
            for m in r.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
        print(f"    OK — {len(nomes)} modelos disponiveis para gerar texto")
        if modelo in nomes:
            print(f"    '{modelo}' esta na lista")
        else:
            print(f"    ATENCAO: '{modelo}' NAO esta na lista")
            print(f"    proximos: {[n for n in nomes if 'flash' in n][:6]}")
    except Exception as erro:
        print(f"    falhou antes da resposta: {erro!r}")
        return 1

    # 2. O modelo configurado responde?
    print()
    print(f"--- 2. o modelo responde? (POST /{modelo}:generateContent)")
    corpo = {"contents": [{"parts": [{"text": "Responda apenas: ok"}]}]}
    try:
        r = httpx.post(
            f"https://{HOST}/v1beta/models/{modelo}:generateContent",
            headers={"x-goog-api-key": chave, "Content-Type": "application/json"},
            json=corpo,
            timeout=60,
        )
        print(f"    HTTP {r.status_code}")
        if r.status_code >= 400:
            try:
                erro = r.json().get("error", {})
                print(f"    status  : {erro.get('status')}")
                print(f"    mensagem: {erro.get('message')}")
            except Exception:
                print(f"    corpo   : {r.text[:500]}")
            print()
            print("    Leitura:")
            print("      401/403 -> chave invalida ou sem permissao")
            print("      404     -> nome de modelo errado")
            print("      429     -> cota estourada; espere ou troque de modelo")
            print("      503     -> sobrecarga do Google; tente de novo em minutos")
            return 1
        texto = (
            r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        )
        print(f"    OK — respondeu: {texto[:80]!r}")
    except httpx.TimeoutException:
        print(f"    tempo esgotado (>60s). O modelo pode estar congestionado.")
        return 1
    except Exception as erro:
        print(f"    falhou: {erro!r}")
        print(f"    {json.dumps(corpo)[:200]}")
        return 1

    print()
    print("Gemini respondendo normalmente. Se o sistema ainda falhar, o problema")
    print("esta no prompt ou no tempo limite, nao na conexao.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
