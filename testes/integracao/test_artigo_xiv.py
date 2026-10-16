"""Artigo XIV no esquema migrado (head)."""

import pytest

from testes.suporte.artigo_xiv import EXCECOES, inventario_do_banco, tabelas_sem_dono


@pytest.mark.postgres
def test_hospede_nao_reprova_no_head(ambiente):
    with ambiente.conexao() as conexao:
        reprovadas = tabelas_sem_dono(inventario_do_banco(conexao))
    assert "hospede" not in reprovadas


@pytest.mark.postgres
def test_evento_webhook_continua_excecao(ambiente):
    assert "evento_webhook" in EXCECOES
    with ambiente.conexao() as conexao:
        reprovadas = tabelas_sem_dono(inventario_do_banco(conexao))
    assert "evento_webhook" not in reprovadas
