"""Porta falsa de mensageria — envio em sessao."""

import pytest

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.mensageria import FalhaDeEnvio


def test_enviar_texto_sessao_registra_corpo():
    porta = MensageriaFalsa()
    resultado = porta.enviar_texto_sessao(
        telefone_destino="5511999999999",
        corpo="Cafe das 7h as 10h",
        id_mensagem=3,
        id_reserva=2,
    )
    assert resultado.id_externo == "fake-3"
    assert porta.envios[0]["tipo"] == "sessao"
    assert porta.envios[0]["corpo"] == "Cafe das 7h as 10h"


def test_enviar_texto_sessao_falha_tipada():
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with pytest.raises(FalhaDeEnvio) as erro:
        porta.enviar_texto_sessao(
            telefone_destino="5511999999999",
            corpo="segredo",
            id_mensagem=1,
            id_reserva=1,
        )
    assert erro.value.codigo == "mensageria_indisponivel"


def test_enviar_pulso_registra_tipo_distinto():
    porta = MensageriaFalsa()
    resultado = porta.enviar_pulso(
        telefone_destino="5511999999999",
        primeiro_nome="Marina",
        corpo="Como esta sendo sua estadia?",
        id_mensagem=9,
        id_reserva=4,
    )
    assert resultado.id_externo == "fake-9"
    assert porta.envios[0]["tipo"] == "pulso"
    assert porta.envios[0]["tipo"] != "boas_vindas"
    assert porta.envios[0]["tipo"] != "sessao"


def test_enviar_pulso_falha_sem_eco_do_corpo():
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with pytest.raises(FalhaDeEnvio) as erro:
        porta.enviar_pulso(
            telefone_destino="5511999999999",
            primeiro_nome="Marina",
            corpo="segredo do pulso",
            id_mensagem=1,
            id_reserva=1,
        )
    assert erro.value.codigo == "mensageria_indisponivel"
    assert "segredo" not in str(erro.value)


def test_enviar_pesquisa_saida_registra_tipo_distinto():
    porta = MensageriaFalsa()
    resultado = porta.enviar_pesquisa_saida(
        telefone_destino="5511999999999",
        primeiro_nome="Marina",
        corpo="De 1 a 5, que nota voce da?",
        id_mensagem=12,
        id_reserva=5,
    )
    assert resultado.id_externo == "fake-12"
    assert porta.envios[0]["tipo"] == "pesquisa_saida"
    assert porta.envios[0]["tipo"] != "pulso"
    assert porta.envios[0]["tipo"] != "boas_vindas"
    assert porta.envios[0]["tipo"] != "sessao"


def test_enviar_pesquisa_saida_falha_sem_eco_do_corpo():
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with pytest.raises(FalhaDeEnvio) as erro:
        porta.enviar_pesquisa_saida(
            telefone_destino="5511999999999",
            primeiro_nome="Marina",
            corpo="segredo da pesquisa",
            id_mensagem=1,
            id_reserva=1,
        )
    assert erro.value.codigo == "mensageria_indisponivel"
    assert "segredo" not in str(erro.value)
