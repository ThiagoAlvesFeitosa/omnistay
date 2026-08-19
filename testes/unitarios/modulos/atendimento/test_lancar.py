"""Lancamento de consumo pendente."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modulos.atendimento import service as atendimento
from testes.suporte.consumo import DETALHE_JA_DISPENSADO, DETALHE_JA_LANCADO, PRECO_ATUAL


class Relogio:
    def __init__(self, instante):
        self.instante = instante

    def agora(self):
        return self.instante


class Repo:
    def __init__(self, *, resultado=None, existente=None):
        self.resultado = resultado
        self.existente = existente
        self.marcacoes = []

    def marcar_lancamento(
        self, conexao, *, id_hotel, id_solicitacao, id_usuario, lancado_em, status_destino
    ):
        self.marcacoes.append(
            {
                "id_hotel": id_hotel,
                "id_solicitacao": id_solicitacao,
                "id_usuario": id_usuario,
                "lancado_em": lancado_em,
                "status_destino": status_destino,
            }
        )
        return self.resultado

    def ler_consumo_do_hotel(self, conexao, *, id_hotel, id_solicitacao):
        return self.existente


def test_lancar_preenche_autor_quando_pendente():
    instante = datetime(2026, 8, 19, 10, 0, tzinfo=UTC)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "status_lancamento": "lancado",
            "id_usuario_lancamento": 3,
            "lancado_em": instante,
            "valor_praticado": PRECO_ATUAL,
        }
    )
    saida = atendimento.lancar(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        relogio=Relogio(instante),
    )
    assert saida.status_lancamento == "lancado"
    assert saida.id_usuario_lancamento == 3
    assert repo.marcacoes[0]["status_destino"] == "lancado"


def test_ja_terminal_recusa_sem_alterar():
    repo = Repo(
        resultado=None, existente={"status_lancamento": "lancado", "tipo": "consumo"}
    )
    with pytest.raises(atendimento.LancamentoNaoPermitido) as erro:
        atendimento.lancar(
            object(),
            id_hotel=1,
            id_solicitacao=7,
            id_usuario=3,
            repositorio=repo,
        )
    assert erro.value.detalhe == DETALHE_JA_LANCADO


def test_outro_hotel_nao_encontrada():
    repo = Repo(resultado=None, existente=None)
    with pytest.raises(atendimento.SolicitacaoNaoEncontrada):
        atendimento.lancar(
            object(),
            id_hotel=2,
            id_solicitacao=7,
            id_usuario=3,
            repositorio=repo,
        )


def test_lancar_loga_ids_sem_valor(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(atendimento.logger, "info", fake_info)
    instante = datetime(2026, 8, 19, 10, 0, tzinfo=UTC)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "status_lancamento": "lancado",
            "id_usuario_lancamento": 3,
            "lancado_em": instante,
            "valor_praticado": PRECO_ATUAL,
        }
    )
    atendimento.lancar(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        relogio=Relogio(instante),
    )
    texto = " ".join(registros)
    assert "consumo_lancado" in texto
    assert "id_solicitacao=7" in texto
    assert "resultado=lancado" in texto
    assert "12,00" not in texto
    assert "12.00" not in texto
