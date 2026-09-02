"""Origem e entrega da conversa da estadia — funcoes puras, sem banco."""

from app.modulos.conversa import origem_e_entrega as oe


def test_recebida_e_hospede():
    assert oe.origem(direcao="recebida", classificacao_bruta=None) == "hospede"


def test_enviada_com_tipo_resposta_recepcao_e_recepcao():
    assert (
        oe.origem(
            direcao="enviada",
            classificacao_bruta={"tipo": "resposta_recepcao"},
        )
        == "recepcao"
    )


def test_demais_enviadas_sao_automaticas():
    assert oe.origem(direcao="enviada", classificacao_bruta={"tipo": "boas_vindas"}) == (
        "automatico"
    )
    assert oe.origem(direcao="enviada", classificacao_bruta=None) == "automatico"


def test_pendente_e_enviando_sem_nova_tentativa():
    entrega, nova = oe.entrega(status_envio="pendente", status_trabalho="pendente")
    assert entrega == "enviando"
    assert nova is False


def test_enviada_ou_entregue_aparece_como_enviada():
    assert oe.entrega(status_envio="enviada", status_trabalho="concluido") == (
        "enviada",
        False,
    )
    assert oe.entrega(status_envio="entregue", status_trabalho="concluido") == (
        "enviada",
        False,
    )


def test_falha_com_trabalho_nao_concluido_marca_nova_tentativa():
    assert oe.entrega(status_envio="falha", status_trabalho="falha") == ("falhou", True)
    assert oe.entrega(status_envio="falha", status_trabalho="pendente") == (
        "falhou",
        True,
    )


def test_falha_com_trabalho_concluido_nao_marca_nova_tentativa():
    assert oe.entrega(status_envio="falha", status_trabalho="concluido") == (
        "falhou",
        False,
    )


def test_recebida_nao_tem_entrega():
    assert oe.entrega(status_envio=None, status_trabalho=None) == (None, None)
