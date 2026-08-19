"""Dispensa de consumo pendente."""

from datetime import UTC, datetime

import pytest

from app.modulos.atendimento import service as atendimento
from testes.suporte.consumo import DETALHE_JA_DISPENSADO, PRECO_ATUAL
from testes.unitarios.modulos.atendimento.test_lancar import Relogio, Repo


def test_dispensar_marca_dispensado_quando_pendente():
    instante = datetime(2026, 8, 19, 10, 0, tzinfo=UTC)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "status_lancamento": "dispensado",
            "id_usuario_lancamento": 3,
            "lancado_em": instante,
            "valor_praticado": PRECO_ATUAL,
        }
    )
    saida = atendimento.dispensar(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        relogio=Relogio(instante),
    )
    assert saida.status_lancamento == "dispensado"
    assert repo.marcacoes[0]["status_destino"] == "dispensado"


def test_ja_terminal_recusa_dispensa():
    repo = Repo(
        resultado=None, existente={"status_lancamento": "dispensado", "tipo": "consumo"}
    )
    with pytest.raises(atendimento.LancamentoNaoPermitido) as erro:
        atendimento.dispensar(
            object(),
            id_hotel=1,
            id_solicitacao=7,
            id_usuario=3,
            repositorio=repo,
        )
    assert erro.value.detalhe == DETALHE_JA_DISPENSADO


def test_dispensar_loga_ids_sem_valor(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(atendimento.logger, "info", fake_info)
    instante = datetime(2026, 8, 19, 10, 0, tzinfo=UTC)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "status_lancamento": "dispensado",
            "id_usuario_lancamento": 3,
            "lancado_em": instante,
            "valor_praticado": PRECO_ATUAL,
        }
    )
    atendimento.dispensar(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        relogio=Relogio(instante),
    )
    texto = " ".join(registros)
    assert "consumo_dispensado" in texto
    assert "id_solicitacao=7" in texto
    assert "12.00" not in texto
    assert "12,00" not in texto
