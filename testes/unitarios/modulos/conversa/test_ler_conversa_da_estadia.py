"""Leitura da conversa da estadia — regras, sem SQL."""

import logging

from app.comum.log import obter_logger
from app.modulos.conversa import service as conversa

logger = obter_logger("test_ler_conversa")


class Repo:
    def __init__(self, mensagens, id_hotel=1):
        self.mensagens = mensagens
        self.id_hotel = id_hotel
        self.consultas = []

    def ler_reserva_do_hotel(self, conexao, *, id_hotel, id_reserva):
        self.consultas.append(("reserva", id_hotel, id_reserva))
        if id_hotel != self.id_hotel:
            return None
        return {"id_reserva": id_reserva, "id_hotel": id_hotel, "status": "encerrado"}

    def listar_conversa_da_estadia(self, conexao, *, id_hotel, id_reserva):
        self.consultas.append(("lista", id_hotel, id_reserva))
        return list(self.mensagens)

    def ler_ultima_recebida_em(self, conexao, *, id_hotel, id_reserva):
        recebidas = [m for m in self.mensagens if m["direcao"] == "recebida"]
        if not recebidas:
            return None
        return recebidas[-1]["enviada_em"]


def test_lista_ordenada_do_hotel_da_sessao():
    from datetime import UTC, datetime

    repo = Repo(
        [
            {
                "id_mensagem": 1,
                "direcao": "recebida",
                "conteudo": "tem berco?",
                "status_envio": None,
                "enviada_em": datetime(2026, 9, 2, 18, 0, tzinfo=UTC),
                "classificacao_bruta": None,
                "status_trabalho": None,
            },
            {
                "id_mensagem": 2,
                "direcao": "enviada",
                "conteudo": "A recepção vai atender.",
                "status_envio": "enviada",
                "enviada_em": datetime(2026, 9, 2, 18, 1, tzinfo=UTC),
                "classificacao_bruta": {"tipo": "aviso_encaminhamento"},
                "status_trabalho": None,
            },
        ]
    )

    resultado = conversa.ler_conversa_da_estadia(
        object(), id_hotel=1, id_reserva=12, repositorio=repo
    )

    assert [m["id_mensagem"] for m in resultado["mensagens"]] == [1, 2]
    assert resultado["mensagens"][0]["origem"] == "hospede"
    assert ("lista", 1, 12) in repo.consultas


def test_reserva_de_outro_hotel_nao_e_encontrada():
    repo = Repo([], id_hotel=1)
    try:
        conversa.ler_conversa_da_estadia(
            object(), id_hotel=2, id_reserva=12, repositorio=repo
        )
    except conversa.ReservaNaoEncontrada:
        return
    raise AssertionError("esperava ReservaNaoEncontrada")


def test_conteudo_nao_vai_a_log(caplog):
    from datetime import UTC, datetime

    caplog.set_level(logging.INFO)
    repo = Repo(
        [
            {
                "id_mensagem": 1,
                "direcao": "recebida",
                "conteudo": "segredo-do-hospede",
                "status_envio": None,
                "enviada_em": datetime(2026, 9, 2, 18, 0, tzinfo=UTC),
                "classificacao_bruta": None,
                "status_trabalho": None,
            }
        ]
    )
    conversa.ler_conversa_da_estadia(
        object(), id_hotel=1, id_reserva=12, repositorio=repo
    )
    assert "segredo-do-hospede" not in caplog.text


def test_reserva_encerrada_continua_legivel():
    from datetime import UTC, datetime

    repo = Repo(
        [
            {
                "id_mensagem": 1,
                "direcao": "recebida",
                "conteudo": "oi",
                "status_envio": None,
                "enviada_em": datetime(2026, 9, 1, tzinfo=UTC),
                "classificacao_bruta": None,
                "status_trabalho": None,
            }
        ]
    )
    resultado = conversa.ler_conversa_da_estadia(
        object(), id_hotel=1, id_reserva=12, repositorio=repo
    )
    assert len(resultado["mensagens"]) == 1
