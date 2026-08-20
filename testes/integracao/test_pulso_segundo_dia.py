"""Pulso do segundo dia ponta a ponta, com portas falsas."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.llm import ResultadoClassificacao
from testes.integracao.test_reservas import _login
from testes.suporte.pulso import gravar_pulso_enviado, montar_hospedado_para_pulso
from worker.agendador import verificar_pulsos_pendentes
from worker.consumidor import processar_uma_passagem_na_engine


def _trabalhos(conexao, id_reserva: int, tipo: str):
    return conexao.execute(
        text(
            "SELECT status FROM trabalho"
            " WHERE tipo = :t AND (payload->>'id_reserva')::bigint = :r"
        ),
        {"t": tipo, "r": id_reserva},
    ).scalars().all()


@pytest.mark.postgres
def test_varredura_nao_chama_a_porta_e_uma_passagem_envia_pulso(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    porta = MensageriaFalsa()
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000501"
        )
        verificar_pulsos_pendentes(conexao)
    assert porta.envios == []

    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    envio = next(e for e in porta.envios if e["tipo"] == "pulso")
    assert envio["id_reserva"] == id_reserva
    with ambiente.conexao() as conexao:
        assert _trabalhos(conexao, id_reserva, "enviar_pulso") == ["concluido"]
        status = conexao.execute(
            text(
                "SELECT status_envio FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        assert status == "enviada"


@pytest.mark.postgres
def test_segunda_varredura_e_silencio_nao_geram_segundo_pulso(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000502"
        )
        assert verificar_pulsos_pendentes(conexao) == 1
        assert verificar_pulsos_pendentes(conexao) == 0
        pulsos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_pulso'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        lembretes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_lembrete'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        respostas = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'registrar_resposta_pulso'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert pulsos == 1
    assert lembretes == 0
    assert respostas == 0


@pytest.mark.postgres
def test_classificar_enfileira_resposta_de_pulso_e_processador_abre_chamado(
    app_sobre_ambiente,
):
    cliente, ambiente = app_sobre_ambiente
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="fora_de_escopo",
            sentimento="negativo",
            urgencia="media",
            bruto={
                "intencao": "fora_de_escopo",
                "sentimento": "negativo",
                "urgencia": "media",
            },
        )
    )
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000503"
        )
        gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'nada esta bom') RETURNING id_mensagem"
            ),
            {"r": id_reserva},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'classificar_mensagem', CAST(:p AS jsonb), 'pendente')"
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
            ),
            {"m": id_mensagem},
        ).scalars().all()
        assert "registrar_resposta_pulso" in tipos
        assert "abrir_chamado_reclamacao" not in tipos

    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta, llm=llm)
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    itens = cliente.get("/solicitacoes").json()["itens"]
    reclamacoes = [
        i for i in itens if i["id_reserva"] == id_reserva and i["tipo"] == "reclamacao"
    ]
    assert len(reclamacoes) == 1
    sessao = [e for e in porta.envios if e["tipo"] == "sessao"]
    assert len(sessao) == 1
    assert "que horas" not in sessao[0]["corpo"].casefold()


@pytest.mark.postgres
def test_pedido_com_pulso_aguardando_fecha_sem_reconhecimento(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000504"
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
    corpos = [e["corpo"] for e in porta.envios]
    assert len(corpos) == 1
    assert "obrigado" not in corpos[0].casefold()
    with ambiente.conexao() as conexao:
        origens = conexao.execute(
            text("SELECT origem FROM avaliacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalars().all()
        assert origens == ["pulso_segundo_dia"]


@pytest.mark.postgres
def test_hotel_b_nao_herda_reclamacao_nem_pulso_de_a(ambiente):
    id_a = ambiente.propriedade_a.id_hotel
    id_b = ambiente.propriedade_b.id_hotel
    with ambiente.engine.begin() as conexao:
        reserva_a = montar_hospedado_para_pulso(
            conexao, id_hotel=id_a, telefone="5511910000505"
        )
        reserva_b = montar_hospedado_para_pulso(
            conexao, id_hotel=id_b, telefone="5511910000506"
        )
        id_msg = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'ar quebrado') RETURNING id_mensagem"
            ),
            {"r": reserva_a},
        ).scalar_one()
        from app.modulos.atendimento.service import abrir_reclamacao

        abrir_reclamacao(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_a,
            id_mensagem=id_msg,
            descricao="ar quebrado",
            numero_quarto="101",
            urgencia="media",
            janela_preferencia=None,
        )
        n = verificar_pulsos_pendentes(conexao)
        pulsos_a = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_pulso'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": reserva_a},
        ).scalar_one()
        pulsos_b = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_pulso'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": reserva_b},
        ).scalar_one()
    assert n == 1
    assert pulsos_a == 0
    assert pulsos_b == 1
