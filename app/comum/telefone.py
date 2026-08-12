"""Normalizacao de telefone brasileiro para uso em mensageria.

Forma canonica: somente digitos com prefixo 55 (sem '+').
Aceita nacional com DDD (10 ou 11 digitos) ou ja prefixado com 55 (12 ou 13).
"""


class TelefoneInvalido(ValueError):
    """Numero que nao pode ser usado como contato de mensageria no MVP."""


def normalizar(valor: str) -> str:
    digitos = "".join(c for c in valor if c.isdigit())
    if digitos.startswith("55") and len(digitos) in (12, 13):
        return digitos
    if len(digitos) in (10, 11):
        return "55" + digitos
    raise TelefoneInvalido(
        "Informe um telefone brasileiro com DDD "
        "(celular com 11 digitos ou fixo com 10)."
    )
