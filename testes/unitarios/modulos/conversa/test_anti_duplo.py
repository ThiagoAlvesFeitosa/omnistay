"""Anti-duplo temporal: texto identico em poucos segundos, sem UNIQUE por reserva."""

from datetime import UTC, datetime, timedelta

from app.modulos.conversa import anti_duplo


def test_texto_identico_dentro_de_cinco_segundos_e_duplicata():
    agora = datetime(2026, 9, 2, 18, 0, 5, tzinfo=UTC)
    ultima = {
        "conteudo": "  Sim, temos berco.  ",
        "enviada_em": datetime(2026, 9, 2, 18, 0, 1, tzinfo=UTC),
    }

    assert anti_duplo.e_duplicata(texto="Sim, temos berco.", ultima=ultima, agora=agora)


def test_texto_diferente_nao_e_duplicata():
    agora = datetime(2026, 9, 2, 18, 0, 2, tzinfo=UTC)
    ultima = {
        "conteudo": "Sim, temos berco.",
        "enviada_em": datetime(2026, 9, 2, 18, 0, 1, tzinfo=UTC),
    }

    assert not anti_duplo.e_duplicata(
        texto="E toalha extra?", ultima=ultima, agora=agora
    )


def test_mesmo_texto_depois_de_cinco_segundos_nao_e_duplicata():
    agora = datetime(2026, 9, 2, 18, 0, 7, tzinfo=UTC)
    ultima = {
        "conteudo": "Sim, temos berco.",
        "enviada_em": datetime(2026, 9, 2, 18, 0, 1, tzinfo=UTC),
    }

    assert not anti_duplo.e_duplicata(
        texto="Sim, temos berco.", ultima=ultima, agora=agora
    )


def test_sem_resposta_anterior_nao_e_duplicata():
    agora = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
    assert not anti_duplo.e_duplicata(texto="Ola", ultima=None, agora=agora)


def test_constante_sao_cinco_segundos():
    assert anti_duplo.SEGUNDOS_ANTI_DUPLO == 5
