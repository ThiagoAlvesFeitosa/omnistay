"""Agendamento e envio da confirmacao de resolucao."""

from dataclasses import dataclass, field

import pytest
from sqlalchemy.exc import IntegrityError

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.conversa import service as conversa
from app.modulos.conversa.texto_confirmacao_resolucao import (
    montar_confirmacao_resolucao,
)
from testes.suporte.resolucao import proibicoes_do_recado


@dataclass
class RepoMensagem:
    mensagens: dict = field(default_factory=dict)
    proximo: int = 1
    nome: str = "Maria Silva"
    telefone: str = "5511999990001"
    eventos: list = field(default_factory=list)

    def inserir_mensagem_enviada_pendente(self, conexao, *, id_reserva, conteudo):
        id_mensagem = self.proximo
        self.proximo += 1
        self.mensagens[id_mensagem] = {
            "id_mensagem": id_mensagem,
            "id_reserva": id_reserva,
            "conteudo": conteudo,
            "status_envio": "pendente",
            "classificacao_bruta": None,
        }
        self.eventos.append("gravar_enviada")
        return id_mensagem

    def gravar_classificacao_bruta(self, conexao, *, id_mensagem, classificacao):
        self.mensagens[id_mensagem]["classificacao_bruta"] = dict(classificacao)
        self.eventos.append("gravar_json")

    def ler_nome_titular(self, conexao, *, id_reserva):
        return self.nome

    def ler_mensagem(self, conexao, *, id_mensagem):
        return self.mensagens.get(id_mensagem)

    def ler_telefone_da_reserva(self, conexao, *, id_reserva):
        return self.telefone

    def atualizar_status_envio(
        self, conexao, *, id_mensagem, status_envio, id_externo=None
    ):
        self.mensagens[id_mensagem]["status_envio"] = status_envio
        self.mensagens[id_mensagem]["id_externo"] = id_externo
        self.eventos.append(status_envio)


class Fila:
    def __init__(self, falhar=False):
        self.itens = []
        self.falhar = falhar

    def __call__(
        self, conexao, *, id_hotel, id_reserva, id_solicitacao, id_mensagem
    ):
        if self.falhar:
            raise IntegrityError("dup", {}, Exception())
        self.itens.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "id_solicitacao": id_solicitacao,
                "id_mensagem": id_mensagem,
            }
        )
        return len(self.itens)


class Savepoint:
    def __init__(self, repo):
        self.repo = repo

    def __enter__(self):
        self._ids = set(self.repo.mensagens)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            for chave in list(self.repo.mensagens):
                if chave not in self._ids:
                    del self.repo.mensagens[chave]
            self.repo.eventos = [
                e for e in self.repo.eventos if e != "gravar_enviada"
            ]
        return False


class ConexaoComSavepoint:
    def __init__(self, repo):
        self.repo = repo

    def begin_nested(self):
        return Savepoint(self.repo)


def test_agendar_grava_enviada_enfileira_e_nao_envia():
    repo = RepoMensagem()
    fila = Fila()
    gateway = MensageriaFalsa()
    desfecho = conversa.agendar_confirmacao_resolucao(
        object(),
        id_hotel=1,
        id_reserva=42,
        id_solicitacao=7,
        tipo="reclamacao",
        repositorio=repo,
        enfileirar=fila,
    )
    recado = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="reclamacao"
    )
    assert desfecho == "agendada"
    enviada = repo.mensagens[1]
    assert enviada["conteudo"] == recado
    assert enviada["status_envio"] == "pendente"
    assert enviada["classificacao_bruta"] == {
        "tipo": "confirmacao_resolucao",
        "id_solicitacao": 7,
    }
    assert fila.itens == [
        {
            "id_hotel": 1,
            "id_reserva": 42,
            "id_solicitacao": 7,
            "id_mensagem": 1,
        }
    ]
    assert gateway.envios == []
    compacto = recado.casefold()
    for palavra in proibicoes_do_recado():
        assert palavra not in compacto


def test_unique_devolve_ja_agendada_sem_segunda_enviada():
    repo = RepoMensagem()
    conexao = ConexaoComSavepoint(repo)
    conversa.agendar_confirmacao_resolucao(
        conexao,
        id_hotel=1,
        id_reserva=42,
        id_solicitacao=7,
        tipo="servico",
        repositorio=repo,
        enfileirar=Fila(),
    )
    desfecho = conversa.agendar_confirmacao_resolucao(
        conexao,
        id_hotel=1,
        id_reserva=42,
        id_solicitacao=7,
        tipo="servico",
        repositorio=repo,
        enfileirar=Fila(falhar=True),
    )
    assert desfecho == "ja_agendada"
    assert len(repo.mensagens) == 1


def _trabalho():
    return {
        "id_trabalho": 5,
        "id_hotel": 1,
        "tipo": "enviar_confirmacao_resolucao",
        "payload": {"id_reserva": 42, "id_solicitacao": 7, "id_mensagem": 1},
        "tentativas": 0,
    }


def _processar(monkeypatch, repo, *, gateway=None, trabalho=None):
    concluidos = []
    falhas = []
    reagendados = []

    def marcar_concluido(conexao, *, id_trabalho):
        concluidos.append(id_trabalho)

    def marcar_falha(conexao, *, id_trabalho, tentativas, erro):
        falhas.append({"id_trabalho": id_trabalho, "erro": erro})

    def registrar_falha_de_envio(conexao, **kwargs):
        reagendados.append(kwargs)
        return "reagendado"

    def resolver_proibido(*args, **kwargs):
        raise AssertionError("processador nao resolve solicitacao")

    monkeypatch.setattr("app.fila.repository.marcar_concluido", marcar_concluido)
    monkeypatch.setattr("app.fila.repository.marcar_falha", marcar_falha)
    monkeypatch.setattr(
        "app.fila.service.registrar_falha_de_envio", registrar_falha_de_envio
    )
    monkeypatch.setattr(
        "app.modulos.atendimento.service.resolver", resolver_proibido
    )
    porta = gateway or MensageriaFalsa()
    conversa.processar_trabalho_enviar_confirmacao_resolucao(
        object(),
        trabalho=trabalho or _trabalho(),
        gateway=porta,
        repositorio=repo,
    )
    return concluidos, falhas, reagendados, porta


def test_processador_envia_conteudo_gravado_sem_alterar_solicitacao(monkeypatch):
    recado = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="reclamacao"
    )
    repo = RepoMensagem()
    repo.mensagens[1] = {
        "id_mensagem": 1,
        "id_reserva": 42,
        "conteudo": recado,
        "status_envio": "pendente",
        "classificacao_bruta": {
            "tipo": "confirmacao_resolucao",
            "id_solicitacao": 7,
        },
    }
    concluidos, falhas, reagendados, gateway = _processar(monkeypatch, repo)
    assert gateway.envios[0]["tipo"] == "sessao"
    assert gateway.envios[0]["corpo"] == recado
    assert gateway.envios[0]["id_mensagem"] == 1
    assert repo.mensagens[1]["status_envio"] == "enviada"
    assert concluidos == [5]
    assert falhas == []
    assert reagendados == []
    assert "gravar_enviada" not in repo.eventos


def test_falha_de_envio_nao_reabre_e_nao_conclui(monkeypatch):
    recado = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="servico"
    )
    repo = RepoMensagem()
    repo.mensagens[1] = {
        "id_mensagem": 1,
        "id_reserva": 42,
        "conteudo": recado,
        "status_envio": "pendente",
        "classificacao_bruta": {
            "tipo": "confirmacao_resolucao",
            "id_solicitacao": 7,
        },
    }
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    concluidos, _, reagendados, _ = _processar(
        monkeypatch, repo, gateway=gateway
    )
    assert concluidos == []
    assert reagendados
    assert repo.mensagens[1]["status_envio"] == "pendente"


def test_ja_enviada_conclui_sem_segundo_envio(monkeypatch):
    recado = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="reclamacao"
    )
    repo = RepoMensagem()
    repo.mensagens[1] = {
        "id_mensagem": 1,
        "id_reserva": 42,
        "conteudo": recado,
        "status_envio": "enviada",
        "classificacao_bruta": {
            "tipo": "confirmacao_resolucao",
            "id_solicitacao": 7,
        },
    }
    concluidos, _, _, gateway = _processar(monkeypatch, repo)
    assert gateway.envios == []
    assert concluidos == [5]
    assert "gravar_enviada" not in repo.eventos


def test_pendente_retenta_envio(monkeypatch):
    recado = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="servico"
    )
    repo = RepoMensagem()
    repo.mensagens[1] = {
        "id_mensagem": 1,
        "id_reserva": 42,
        "conteudo": recado,
        "status_envio": "pendente",
        "classificacao_bruta": {
            "tipo": "confirmacao_resolucao",
            "id_solicitacao": 7,
        },
    }
    _, _, _, gateway = _processar(monkeypatch, repo)
    assert len(gateway.envios) == 1
    assert gateway.envios[0]["corpo"] == recado
