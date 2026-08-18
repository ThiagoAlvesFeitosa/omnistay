"""Extracao de janela de preferencia a partir do texto da reclamacao."""

from app.modulos.atendimento.janela import (
    extrair_janela_preferencia,
    parece_resposta_de_horario,
)


def test_extrai_janela_de_relato_com_horario():
    assert (
        extrair_janela_preferencia("o ar nao gela, pode ser depois das 16h")
        == "depois das 16h"
    )
    assert extrair_janela_preferencia("vazamento no banheiro as 14:30") == "14:30"
    assert extrair_janela_preferencia("ar-condicionado quebrado de manha") == "de manha"
    assert extrair_janela_preferencia("pode vir agora") == "agora"


def test_sem_horario_nao_inventa_janela():
    assert extrair_janela_preferencia("o ar nao gela") is None
    assert extrair_janela_preferencia("estou no 402") is None
    assert extrair_janela_preferencia("") is None


def test_parece_resposta_de_horario_so_quando_a_mensagem_inteira_e_horario():
    assert parece_resposta_de_horario("depois das 14h") is True
    assert parece_resposta_de_horario("14h") is True
    assert parece_resposta_de_horario("14:00") is True
    assert parece_resposta_de_horario("de manha") is True
    assert parece_resposta_de_horario("a noite.") is True
    assert parece_resposta_de_horario("agora") is True
    assert parece_resposta_de_horario("o chuveiro tambem vazou") is False
    assert parece_resposta_de_horario("qual o wifi?") is False
    assert parece_resposta_de_horario("o ar nao gela, 14h") is False
    assert parece_resposta_de_horario(" ") is False
