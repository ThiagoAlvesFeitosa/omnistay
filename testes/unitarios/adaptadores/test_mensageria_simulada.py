"""MensageriaSimulada implementa o Protocol e sucede sem rede."""

import inspect

from app.adaptadores.mensageria_simulada import MensageriaSimulada
from app.portas.mensageria import MensageriaGateway


def test_implementa_os_sete_envios_do_protocolo():
    for nome in (
        "enviar_coleta",
        "enviar_lembrete",
        "enviar_boas_vindas",
        "enviar_texto_sessao",
        "enviar_pulso",
        "enviar_pesquisa_saida",
        "enviar_lista_pedidos_chat",
    ):
        assert hasattr(MensageriaSimulada, nome)
        assert nome in MensageriaGateway.__dict__ or hasattr(
            MensageriaGateway, nome
        )


def test_sucesso_devolve_id_sim_sem_gancho_de_falha():
    porta = MensageriaSimulada()
    assert not hasattr(porta, "falhar_sempre")
    resultado = porta.enviar_coleta(
        telefone_destino="5511999990000",
        primeiro_nome="Marina",
        corpo="ola",
        id_mensagem=41,
        id_reserva=12,
    )
    assert resultado.id_externo == "sim-41"
    boas = porta.enviar_boas_vindas(
        telefone_destino="5511999990000",
        variaveis=("Marina", "7h", "wifi", "12h"),
        corpo="boas",
        id_mensagem=42,
        id_reserva=12,
    )
    assert boas.id_externo == "sim-42"
    sessao = porta.enviar_texto_sessao(
        telefone_destino="5511999990000",
        corpo="ok",
        id_mensagem=43,
        id_reserva=12,
    )
    assert sessao.id_externo == "sim-43"


def test_assinatura_de_coleta_bate_com_o_protocolo():
    parametros = inspect.signature(MensageriaSimulada.enviar_coleta).parameters
    assert {
        "telefone_destino",
        "primeiro_nome",
        "corpo",
        "id_mensagem",
        "id_reserva",
    }.issubset(parametros)
