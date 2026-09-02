"""Envio da resposta da recepcao — grava e enfileira, sem canal."""

import logging
from datetime import UTC, datetime, timedelta

from app.comum.log import obter_logger
from app.modulos.conversa import service as conversa
from app.portas.mensageria import FalhaDeEnvio

logger = obter_logger("test_enviar_resposta")


class Repo:
    def __init__(self):
        self.mensagens = []
        self.trabalhos = []
        self.proximo = 40
        self.status = "hospedado"

    def ler_reserva_do_hotel(self, conexao, *, id_hotel, id_reserva):
        if id_hotel != 1:
            return None
        return {
            "id_reserva": id_reserva,
            "id_hotel": id_hotel,
            "status": self.status,
            "telefone_contato": "5511999990001",
        }

    def ler_ultima_recebida_em(self, conexao, *, id_hotel, id_reserva):
        return datetime(2026, 9, 2, 17, 50, tzinfo=UTC)

    def ler_ultima_resposta_recepcao(self, conexao, *, id_hotel, id_reserva):
        humanas = [
            m
            for m in self.mensagens
            if (m.get("classificacao_bruta") or {}).get("tipo") == "resposta_recepcao"
        ]
        return humanas[-1] if humanas else None

    def inserir_resposta_recepcao(self, conexao, *, id_reserva, conteudo, agora=None):
        id_m = self.proximo
        self.proximo += 1
        instante = agora or datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
        item = {
            "id_mensagem": id_m,
            "id_reserva": id_reserva,
            "direcao": "enviada",
            "conteudo": conteudo,
            "status_envio": "pendente",
            "enviada_em": instante,
            "classificacao_bruta": {"tipo": "resposta_recepcao"},
            "status_trabalho": "pendente",
        }
        self.mensagens.append(item)
        return dict(item)

    def atualizar_status_envio(self, conexao, *, id_mensagem, status_envio, id_externo=None, agora=None):
        for m in self.mensagens:
            if m["id_mensagem"] == id_mensagem:
                m["status_envio"] = status_envio
                if id_externo is not None:
                    m["id_externo"] = id_externo

    def ler_mensagem(self, conexao, *, id_mensagem):
        for m in self.mensagens:
            if m["id_mensagem"] == id_mensagem:
                return m
        return None

    def ler_telefone_da_reserva(self, conexao, *, id_reserva):
        return "5511999990001"


def test_texto_valido_grava_pendente_e_enfileira(caplog):
    caplog.set_level(logging.INFO)
    repo = Repo()
    enfileirados = []

    def enfileirar(conexao, *, id_hotel, id_reserva, id_mensagem):
        enfileirados.append(id_mensagem)
        return 99

    agora = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
    resultado = conversa.enviar_resposta_recepcao(
        object(),
        id_hotel=1,
        id_reserva=12,
        texto="Sim, temos berco.",
        repositorio=repo,
        enfileirar=enfileirar,
        agora=agora,
    )

    assert resultado["status_envio"] == "pendente"
    assert resultado["origem"] == "recepcao"
    assert resultado["entrega"] == "enviando"
    assert resultado["em"] is not None
    assert enfileirados == [resultado["id_mensagem"]]
    assert "Sim, temos berco." not in caplog.text


def test_worker_com_falha_nao_apaga_mensagem(caplog):
    caplog.set_level(logging.INFO)
    repo = Repo()
    item = repo.inserir_resposta_recepcao(
        object(), id_reserva=12, conteudo="Segredo da resposta"
    )

    class Gateway:
        def enviar_texto_sessao(self, **kwargs):
            raise FalhaDeEnvio("mensageria_indisponivel")

    class FilaRepo:
        def marcar_falha(self, *a, **k):
            return None

        def marcar_concluido(self, *a, **k):
            raise AssertionError("nao deveria concluir")

    class FilaSvc:
        def registrar_falha_de_envio(self, *a, **k):
            return "falha"

    conversa.processar_trabalho_enviar_resposta_recepcao(
        object(),
        trabalho={
            "id_trabalho": 1,
            "id_hotel": 1,
            "tipo": "enviar_resposta_recepcao",
            "payload": {"id_reserva": 12, "id_mensagem": item["id_mensagem"]},
            "tentativas": 4,
        },
        gateway=Gateway(),
        repositorio=repo,
        fila_repo=FilaRepo(),
        fila_svc=FilaSvc(),
    )

    gravada = repo.ler_mensagem(object(), id_mensagem=item["id_mensagem"])
    assert gravada["conteudo"] == "Segredo da resposta"
    assert gravada["status_envio"] == "falha"
    assert "Segredo da resposta" not in caplog.text


def test_texto_identico_em_menos_de_cinco_segundos_e_recusado():
    repo = Repo()
    agora = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
    repo.mensagens.append(
        {
            "conteudo": "Sim, temos berco.",
            "enviada_em": agora - timedelta(seconds=2),
            "classificacao_bruta": {"tipo": "resposta_recepcao"},
        }
    )

    try:
        conversa.enviar_resposta_recepcao(
            object(),
            id_hotel=1,
            id_reserva=12,
            texto="Sim, temos berco.",
            repositorio=repo,
            enfileirar=lambda *a, **k: 1,
            agora=agora,
        )
    except conversa.TextoRepetido:
        assert len(
            [
                m
                for m in repo.mensagens
                if (m.get("classificacao_bruta") or {}).get("tipo") == "resposta_recepcao"
            ]
        ) == 1
        return
    raise AssertionError("esperava TextoRepetido")
