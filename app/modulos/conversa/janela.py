"""Janela de 24 horas do canal — constante do canal, nao da propriedade."""

from datetime import datetime, timedelta

from app.comum.relogio import agora as agora_do_sistema

JANELA_SESSAO_CANAL_HORAS = 24
TAMANHO_MAXIMO_TEXTO_CANAL = 4096


def avaliar(
    *,
    ultima_recebida_em: datetime | None,
    agora: datetime | None = None,
) -> dict:
    instante = agora or agora_do_sistema()
    if ultima_recebida_em is None:
        return {"aberta": False, "motivo": "nunca_escreveu"}
    limite = instante - timedelta(hours=JANELA_SESSAO_CANAL_HORAS)
    if ultima_recebida_em >= limite:
        return {"aberta": True, "motivo": None}
    return {"aberta": False, "motivo": "sem_mensagem_recente"}
