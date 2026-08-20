"""Processador de resposta ao pulso: negativo, positivo e neutro."""

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.atendimento.service import abrir_reclamacao
from app.modulos.conversa import service as conversa
from app.modulos.conversa.texto_pulso import (
    montar_confirmacao_pulso_negativo,
    montar_reconhecimento_pulso,
)
from testes.suporte.pulso import gravar_pulso_enviado, montar_hospedado_para_pulso


def _trabalho(id_hotel, id_reserva, id_mensagem):
    return {
        "id_trabalho": 9,
        "id_hotel": id_hotel,
        "payload": {"id_reserva": id_reserva, "id_mensagem": id_mensagem},
        "tentativas": 0,
        "tipo": "registrar_resposta_pulso",
    }


def _receber(conexao, id_reserva, texto, sentimento):
    return conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
            " intencao, sentimento, urgencia, classificacao_bruta) "
            "VALUES (:r, 'recebida', :c, 'fora_de_escopo', :s, 'baixa',"
            " CAST(:j AS jsonb)) RETURNING id_mensagem"
        ),
        {
            "r": id_reserva,
            "c": texto,
            "s": sentimento,
            "j": (
                '{"tipo": "classificacao_intencao", "desfecho":'
                ' "encaminhado_humano", "intencao": "fora_de_escopo",'
                ' "sentimento": "%s"}' % sentimento
            ),
        },
    ).scalar_one()


@pytest.mark.postgres
def test_negativo_confirma_antes_de_abrir_um_chamado(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    porta = MensageriaFalsa()
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000601"
        )
        gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        id_mensagem = _receber(conexao, id_reserva, "horrivel", "negativo")
        conversa.processar_trabalho_registrar_resposta_pulso(
            conexao,
            trabalho=_trabalho(id_hotel, id_reserva, id_mensagem),
            gateway=porta,
            abrir_reclamacao=abrir_reclamacao,
        )
        enviadas = conexao.execute(
            text(
                "SELECT id_mensagem, conteudo, status_envio FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
                " ORDER BY id_mensagem"
            ),
            {"r": id_reserva},
        ).mappings().all()
        solicitacoes = conexao.execute(
            text(
                "SELECT tipo FROM solicitacao WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalars().all()
        avaliacoes = conexao.execute(
            text("SELECT nota FROM avaliacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalars().all()
        origem = conexao.execute(
            text(
                "SELECT id_mensagem_origem FROM solicitacao WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    confirmacao = [
        m
        for m in enviadas
        if m["conteudo"] == montar_confirmacao_pulso_negativo()
    ]
    assert len(confirmacao) == 1
    assert origem == id_mensagem
    assert confirmacao[0]["id_mensagem"] != id_mensagem
    assert solicitacoes == ["reclamacao"]
    assert avaliacoes == [None]
    assert "que horas" not in confirmacao[0]["conteudo"].casefold()
    assert porta.envios[0]["tipo"] == "sessao"


@pytest.mark.postgres
def test_positivo_e_neutro_usam_o_mesmo_reconhecimento_sem_chamado(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    reconhecido = montar_reconhecimento_pulso()
    corpos = []
    for sentimento, tel in (("positivo", "5511910000602"), ("neutro", "5511910000603")):
        porta = MensageriaFalsa()
        with ambiente.engine.begin() as conexao:
            id_reserva = montar_hospedado_para_pulso(
                conexao, id_hotel=id_hotel, telefone=tel
            )
            gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
            id_mensagem = _receber(conexao, id_reserva, "ok", sentimento)
            conversa.processar_trabalho_registrar_resposta_pulso(
                conexao,
                trabalho=_trabalho(id_hotel, id_reserva, id_mensagem),
                gateway=porta,
                abrir_reclamacao=abrir_reclamacao,
            )
            n_sol = conexao.execute(
                text("SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r"),
                {"r": id_reserva},
            ).scalar_one()
            n_av = conexao.execute(
                text("SELECT COUNT(*) FROM avaliacao WHERE id_reserva = :r"),
                {"r": id_reserva},
            ).scalar_one()
            assert n_sol == 0
            assert n_av == 1
            corpos.append(porta.envios[0]["corpo"])
    assert corpos[0] == corpos[1] == reconhecido
