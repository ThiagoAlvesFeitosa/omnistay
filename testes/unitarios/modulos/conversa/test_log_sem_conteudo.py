"""Logs de conversa nao carregam conteudo nem telefone."""

import logging

from app.modulos.conversa import service as conversa


def test_marcar_sucesso_loga_so_identificadores(caplog):
    class Repo:
        def atualizar_status_envio(self, conexao, *, id_mensagem, status_envio, id_externo=None):
            return None

    with caplog.at_level(logging.INFO):
        conversa.marcar_envio_sucesso(
            object(), id_mensagem=7, id_externo="fake-7", repositorio=Repo()
        )
    texto = " ".join(r.message for r in caplog.records)
    assert "id_mensagem=7" in texto
    assert "Ola," not in texto
    assert "5511" not in texto
