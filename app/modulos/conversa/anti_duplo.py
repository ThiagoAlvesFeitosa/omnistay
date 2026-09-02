"""Anti-duplo de gesto: texto identico em poucos segundos.

Idempotencia do trabalho mora no UNIQUE por id_mensagem. Varias respostas
por reserva sao legitimas — por isso nao ha UNIQUE por reserva.
"""

from datetime import datetime, timedelta

from app.comum.relogio import agora as agora_do_sistema

SEGUNDOS_ANTI_DUPLO = 5


def e_duplicata(
    *,
    texto: str,
    ultima: dict | None,
    agora: datetime | None = None,
) -> bool:
    if ultima is None:
        return False
    if (texto or "").strip() != (ultima.get("conteudo") or "").strip():
        return False
    instante = agora or agora_do_sistema()
    enviada_em = ultima["enviada_em"]
    return instante - enviada_em < timedelta(seconds=SEGUNDOS_ANTI_DUPLO)
