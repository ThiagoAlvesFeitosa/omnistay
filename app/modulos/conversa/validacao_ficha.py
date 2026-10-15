"""Validacao pura dos campos da ficha — sem idade."""

from datetime import date, datetime

from app.comum.telefone import TelefoneInvalido, normalizar
from app.portas.llm import CAMPOS_FICHA_CHAVE, ResultadoExtracao

TIPOS_DOCUMENTO = frozenset({"rg", "cpf", "passaporte"})


def _data_nascimento(valor: str) -> str | None:
    bruto = valor.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(bruto, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _tipo_documento(valor: str) -> str | None:
    chave = valor.strip().lower()
    if chave in TIPOS_DOCUMENTO:
        return chave
    return None


def _cep(valor: str) -> str | None:
    digitos = "".join(c for c in valor if c.isdigit())
    if len(digitos) == 8:
        return digitos
    return None


def _telefone(valor: str) -> str | None:
    try:
        return normalizar(valor)
    except TelefoneInvalido:
        return None


def _digitos(valor: str) -> str:
    return "".join(c for c in valor if c.isdigit())


def _digito_verificador(base: str, pesos: range) -> str:
    soma = sum(int(digito) * peso for digito, peso in zip(base, pesos))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def _cpf_confere(digitos: str) -> bool:
    if len(digitos) != 11:
        return False
    if len(set(digitos)) == 1:
        return False
    primeiro = _digito_verificador(digitos[:9], range(10, 1, -1))
    segundo = _digito_verificador(digitos[:10], range(11, 1, -1))
    return digitos[9] == primeiro and digitos[10] == segundo


def validar_campos_extraidos(campos: dict[str, str]) -> dict[str, str]:
    """Devolve so campos utilizaveis. Nunca inclui idade."""
    saida: dict[str, str] = {}
    if "idade" in campos:
        # Ignora deliberadamente — idade nao e persistida.
        pass
    for chave in CAMPOS_FICHA_CHAVE:
        if chave not in campos or campos[chave] is None:
            continue
        bruto = str(campos[chave]).strip()
        if not bruto:
            continue
        if chave == "data_nascimento":
            normalizado = _data_nascimento(bruto)
            if normalizado:
                saida[chave] = normalizado
            continue
        if chave == "tipo_documento":
            normalizado = _tipo_documento(bruto)
            if normalizado:
                saida[chave] = normalizado
            continue
        if chave == "cep":
            normalizado = _cep(bruto)
            if normalizado:
                saida[chave] = normalizado
            continue
        if chave == "telefone":
            normalizado = _telefone(bruto)
            if normalizado:
                saida[chave] = normalizado
            continue
        if chave == "numero_documento":
            tipo = saida.get("tipo_documento")
            if tipo is None and campos.get("tipo_documento"):
                tipo = _tipo_documento(str(campos["tipo_documento"]))
            if tipo == "cpf":
                digitos = _digitos(bruto)
                if _cpf_confere(digitos):
                    saida[chave] = digitos
                continue
        saida[chave] = bruto
    return saida


def classificar_desfecho(campos_validos: dict[str, str]) -> str:
    n = len(campos_validos)
    if n == 0:
        return "irreconhecivel"
    if n >= len(CAMPOS_FICHA_CHAVE):
        return "completa"
    return "parcial"


def refinar_resultado(resultado: ResultadoExtracao) -> ResultadoExtracao:
    validos = validar_campos_extraidos(dict(resultado.campos))
    desfecho = classificar_desfecho(validos)
    return ResultadoExtracao(
        desfecho=desfecho,
        campos=validos,
        campos_reconhecidos=tuple(validos.keys()),
    )


def data_nascimento_como_date(valor: str) -> date:
    return date.fromisoformat(valor)
