"""Instante corrente, em um lugar so.

Existe para ser substituido nos testes: verificar que uma sessao de trinta dias
continua valida e que uma vencida e recusada, sem esperar de verdade e sem gravar
uma expiracao no passado para exercitar um caminho diferente do de producao.
"""

from datetime import UTC, datetime


def agora() -> datetime:
    return datetime.now(UTC)
