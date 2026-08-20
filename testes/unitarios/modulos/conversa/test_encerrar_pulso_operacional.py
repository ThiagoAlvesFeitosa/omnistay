"""Gancho operacional fecha o pulso sem segundo recado."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.llm import ResultadoResposta
from testes.suporte.pulso import gravar_pulso_enviado, montar_hospedado_para_pulso
from worker.consumidor import processar_uma_passagem_na_engine


@pytest.mark.postgres
def test_pedido_com_pulso_grava_avaliacao_sem_reconhecimento(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000701"
        )
        gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
                " intencao, sentimento, urgencia, classificacao_bruta) "
                "VALUES (:r, 'recebida', 'toalha extra', 'pedido_de_servico',"
                " 'neutro', 'baixa',"
                " CAST(:j AS jsonb)) RETURNING id_mensagem"
            ),
            {
                "r": id_reserva,
                "j": (
                    '{"tipo": "classificacao_intencao", "desfecho": "classificado",'
                    ' "intencao": "pedido_de_servico"}'
                ),
            },
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'registrar_pedido_servico', CAST(:p AS jsonb),"
                " 'pendente')"
            ),
            {
                "h": id_hotel,
                "p": '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem),
            },
        )

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    assert len(porta.envios) == 1
    assert "obrigado" not in porta.envios[0]["corpo"].casefold()
    with ambiente.conexao() as conexao:
        n_av = conexao.execute(
            text("SELECT COUNT(*) FROM avaliacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        tipos = conexao.execute(
            text("SELECT tipo FROM solicitacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalars().all()
    assert n_av == 1
    assert tipos == ["servico"]


@pytest.mark.postgres
def test_reclamacao_tecnica_com_pulso_abre_um_so_chamado(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000702"
        )
        gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
                " intencao, sentimento, urgencia, classificacao_bruta) "
                "VALUES (:r, 'recebida', 'ar quebrado', 'reclamacao_tecnica',"
                " 'negativo', 'alta',"
                " CAST(:j AS jsonb)) RETURNING id_mensagem"
            ),
            {
                "r": id_reserva,
                "j": (
                    '{"tipo": "classificacao_intencao", "desfecho": "classificado",'
                    ' "intencao": "reclamacao_tecnica"}'
                ),
            },
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'abrir_chamado_reclamacao', CAST(:p AS jsonb),"
                " 'pendente')"
            ),
            {
                "h": id_hotel,
                "p": '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem),
            },
        )

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    assert len(porta.envios) == 1
    with ambiente.conexao() as conexao:
        tipos = conexao.execute(
            text("SELECT tipo FROM solicitacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalars().all()
        n_av = conexao.execute(
            text("SELECT COUNT(*) FROM avaliacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
    assert tipos == ["reclamacao"]
    assert n_av == 1


@pytest.mark.postgres
def test_duvida_coberta_com_pulso_nao_manda_obrigado(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.configurar_resposta(
        ResultadoResposta(coberta=True, texto="Cafe das 7h as 10h", trechos_citados=("Cafe das 7h as 10h",))
    )
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO catalogo_item (id_hotel, categoria, titulo, conteudo) "
                "VALUES (:h, 'horario', 'Cafe', 'Cafe das 7h as 10h')"
            ),
            {"h": id_hotel},
        )
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000703"
        )
        gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
                " intencao, sentimento, urgencia, classificacao_bruta) "
                "VALUES (:r, 'recebida', 'que horas e o cafe', 'duvida_geral',"
                " 'neutro', 'baixa',"
                " CAST(:j AS jsonb)) RETURNING id_mensagem"
            ),
            {
                "r": id_reserva,
                "j": (
                    '{"tipo": "classificacao_intencao", "desfecho": "classificado",'
                    ' "intencao": "duvida_geral"}'
                ),
            },
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'responder_duvida', CAST(:p AS jsonb), 'pendente')"
            ),
            {
                "h": id_hotel,
                "p": '{"id_reserva": %s, "id_mensagem": %s}'
                % (id_reserva, id_mensagem),
            },
        )

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta, llm=llm)
    assert len(porta.envios) == 1
    assert "obrigado" not in porta.envios[0]["corpo"].casefold()
    with ambiente.conexao() as conexao:
        assert (
            conexao.execute(
                text("SELECT COUNT(*) FROM avaliacao WHERE id_reserva = :r"),
                {"r": id_reserva},
            ).scalar_one()
            == 1
        )
