"""Janela de 24h do canal: constante nomeada, relogio injetavel."""

from datetime import UTC, datetime, timedelta

from app.modulos.conversa import janela


def test_janela_aberta_quando_hospede_escreveu_ha_menos_de_24h():
    agora = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
    recente = agora - timedelta(hours=23, minutes=59)

    resultado = janela.avaliar(ultima_recebida_em=recente, agora=agora)

    assert resultado == {"aberta": True, "motivo": None}


def test_janela_fechada_quando_nunca_escreveu():
    agora = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)

    resultado = janela.avaliar(ultima_recebida_em=None, agora=agora)

    assert resultado == {"aberta": False, "motivo": "nunca_escreveu"}


def test_janela_fechada_quando_escreveu_ha_mais_de_24h():
    agora = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
    antiga = agora - timedelta(hours=24, seconds=1)

    resultado = janela.avaliar(ultima_recebida_em=antiga, agora=agora)

    assert resultado == {"aberta": False, "motivo": "sem_mensagem_recente"}


def test_vinte_e_quatro_horas_nao_leem_parametro_hotel():
    assert janela.JANELA_SESSAO_CANAL_HORAS == 24
    assert janela.TAMANHO_MAXIMO_TEXTO_CANAL == 4096
    assert not hasattr(janela, "ler_parametro")
