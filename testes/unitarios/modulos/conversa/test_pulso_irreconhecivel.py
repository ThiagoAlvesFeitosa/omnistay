"""Falha de classificacao na janela do pulso encerra sem chamado."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from testes.suporte.pulso import gravar_pulso_enviado, montar_hospedado_para_pulso
from worker.consumidor import processar_uma_passagem_na_engine


@pytest.mark.postgres
def test_classificacao_indisponivel_encerra_pulso_sem_chamado(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.falhar_classificacao = True
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000801"
        )
        gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'asdf') RETURNING id_mensagem"
            ),
            {"r": id_reserva},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'classificar_mensagem', CAST(:p AS jsonb),"
                " 'pendente')"
            ),
            {
                "h": id_hotel,
                "p": (
                    '{"id_reserva": %s, "id_mensagem": %s, "id_evento": 1}'
                    % (id_reserva, id_mensagem)
                ),
            },
        )

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta, llm=llm)
    with ambiente.conexao() as conexao:
        tipos = conexao.execute(
            text(
                "SELECT tipo FROM trabalho"
                " WHERE (payload->>'id_mensagem')::bigint = :m"
                " OR (payload->>'id_reserva')::bigint = :r"
            ),
            {"m": id_mensagem, "r": id_reserva},
        ).scalars().all()
        assert "registrar_resposta_pulso" not in tipos
        assert "abrir_chamado_reclamacao" not in tipos
        n_sol = conexao.execute(
            text("SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        n_av = conexao.execute(
            text(
                "SELECT COUNT(*) FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'pulso_segundo_dia'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        desfecho = conexao.execute(
            text(
                "SELECT classificacao_bruta->>'desfecho' FROM mensagem"
                " WHERE id_mensagem = :id"
            ),
            {"id": id_mensagem},
        ).scalar_one()
    assert n_sol == 0
    assert n_av == 1
    assert desfecho == "indisponivel"
    assert porta.envios == []
