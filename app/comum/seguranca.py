"""Primitivas de seguranca: derivacao de senha e token de sessao.

Duas escolhas de algoritmo, com motivos diferentes:

**Senha usa derivacao lenta** (PBKDF2-HMAC-SHA256 da biblioteca padrao). Senha
escolhida por humano tem entropia baixa, e o custo por tentativa e a unica defesa
contra forca bruta sobre a tabela vazada. Argon2id e bcrypt seriam preferiveis, mas
sao pacotes compilados e a maquina roda Python 3.14 — wheel ausente e risco
registrado desde a F0.1.

**Token de sessao usa hash rapido** (SHA-256). O token tem 256 bits aleatorios e nao
e adivinhavel: pagar derivacao lenta a cada requisicao autenticada seria custo sem
beneficio. Guardar o hash e nao o token atende a exigencia de que vazamento da tabela
de sessoes nao equivalha a vazamento de acesso.

O valor gravado da senha carrega algoritmo, iteracoes e sal, o que permite elevar o
custo depois sem invalidar as senhas ja cadastradas.
"""

import hashlib
import hmac
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode
from functools import lru_cache

from app.config import obter_configuracao

ALGORITMO = "pbkdf2_sha256"

_SEPARADOR = "$"
_BYTES_DE_SAL = 16
_BYTES_DE_TOKEN = 32


def _codificar(bruto: bytes) -> str:
    return urlsafe_b64encode(bruto).decode("ascii").rstrip("=")


def _decodificar(texto: str) -> bytes:
    resto = len(texto) % 4
    return urlsafe_b64decode(texto + "=" * (4 - resto if resto else 0))


def _derivar(senha: str, sal: bytes, iteracoes: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, iteracoes)


def _iteracoes(informadas: int | None) -> int:
    return informadas if informadas is not None else obter_configuracao().senha_iteracoes


def derivar_senha(senha: str, iteracoes: int | None = None) -> str:
    """Devolve o valor a gravar em `usuario.senha_hash`. Nunca a senha."""
    iteracoes_usadas = _iteracoes(iteracoes)
    sal = secrets.token_bytes(_BYTES_DE_SAL)
    derivado = _derivar(senha, sal, iteracoes_usadas)

    return _SEPARADOR.join(
        [ALGORITMO, str(iteracoes_usadas), _codificar(sal), _codificar(derivado)]
    )


def conferir_senha(senha: str, valor_gravado: str) -> bool:
    """Confere a senha contra o valor gravado, em tempo constante.

    Valor gravado malformado e recusado em vez de levantar erro: o chamador esta
    autenticando, e a distincao entre "senha errada" e "linha corrompida" nao pode
    aparecer na resposta.
    """
    try:
        algoritmo, iteracoes, sal, derivado = valor_gravado.split(_SEPARADOR)
        if algoritmo != ALGORITMO:
            return False
        esperado = _decodificar(derivado)
        obtido = _derivar(senha, _decodificar(sal), int(iteracoes))
    except ValueError:
        return False

    return hmac.compare_digest(esperado, obtido)


@lru_cache
def hash_de_referencia(iteracoes: int | None = None) -> str:
    """Valor gravado descartavel, para conferir contra quando o e-mail nao existe.

    Sem isso, e-mail inexistente responderia em milissegundos e senha errada em
    centenas deles — e a diferenca de tempo diria qual dos dois aconteceu.
    """
    return derivar_senha(secrets.token_urlsafe(_BYTES_DE_TOKEN), iteracoes=iteracoes)


def gerar_token() -> str:
    """Token opaco de sessao. Existe em claro apenas no cookie do cliente."""
    return secrets.token_urlsafe(_BYTES_DE_TOKEN)


def hash_do_token(token: str) -> str:
    """SHA-256 em hexadecimal: e o que a coluna `sessao.token_hash` guarda."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
