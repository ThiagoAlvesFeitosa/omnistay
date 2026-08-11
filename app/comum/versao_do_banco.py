"""Versao minima do PostgreSQL exigida pelo esquema.

A decisao fica separada da leitura para poder ser verificada sem manter um servidor
antigo so para o teste. Nao e parametro operacional de propriedade: e dependencia de
plataforma, e por isso vive no codigo e nao em `parametro_hotel`.
"""

VERSAO_MINIMA = 160000


class VersaoDeBancoInsuficiente(RuntimeError):
    pass


def formatar(versao: int) -> str:
    return f"{versao // 10000}.{versao % 10000}"


def exigir_versao_minima(versao_do_servidor: int) -> None:
    if versao_do_servidor >= VERSAO_MINIMA:
        return

    raise VersaoDeBancoInsuficiente(
        f"O esquema exige PostgreSQL {formatar(VERSAO_MINIMA)} ou superior, "
        f"e o servidor informou {formatar(versao_do_servidor)}. "
        "Nenhuma estrutura foi criada."
    )
