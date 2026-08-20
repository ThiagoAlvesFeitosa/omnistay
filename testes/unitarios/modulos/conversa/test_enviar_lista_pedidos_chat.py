"""Envio da lista de pedidos feitos pelo chat: falha retoma o mesmo trabalho."""

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.atendimento.service import abrir_consumo
from app.modulos.conversa import service as conversa
from app.modulos.hospedagem import service as hospedagem
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL
from testes.suporte.pulso import montar_hospedado_para_pulso


def _semear_consumo(conexao, *, id_hotel: int, id_reserva: int) -> None:
    id_mensagem = conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
            "VALUES (:r, 'recebida', 'uma cerveja') RETURNING id_mensagem"
        ),
        {"r": id_reserva},
    ).scalar_one()
    abrir_consumo(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        descricao="uma cerveja",
        descricao_item=NOME_ITEM,
        valor_praticado=PRECO_ATUAL,
        numero_quarto="402",
        urgencia="baixa",
    )


def _trabalho_pendente(conexao, id_reserva: int) -> dict:
    linha = conexao.execute(
        text(
            "SELECT id_trabalho, id_hotel, tipo, payload, status, tentativas"
            " FROM trabalho"
            " WHERE tipo = 'enviar_lista_pedidos_chat'"
            " AND (payload->>'id_reserva')::bigint = :r"
        ),
        {"r": id_reserva},
    ).mappings().one()
    return dict(linha)


@pytest.mark.postgres
def test_falha_de_envio_nao_reabre_hospedado_nem_apaga_lista(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001401"
        )
        _semear_consumo(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        hospedagem.confirmar_saida(
            conexao, id_hotel=id_hotel, id_reserva=id_reserva
        )
        trabalho = _trabalho_pendente(conexao, id_reserva)
        conversa.processar_trabalho_enviar_lista_pedidos_chat(
            conexao, trabalho=trabalho, gateway=porta
        )
        linha = conexao.execute(
            text(
                "SELECT r.status, t.status AS trabalho, t.id_trabalho"
                " FROM reserva r"
                " JOIN trabalho t ON (t.payload->>'id_reserva')::bigint = r.id_reserva"
                " WHERE r.id_reserva = :r AND t.tipo = 'enviar_lista_pedidos_chat'"
            ),
            {"r": id_reserva},
        ).mappings().one()
        itens = hospedagem.consultar_pedidos_feitos_pelo_chat(
            conexao, id_hotel=id_hotel, id_reserva=id_reserva
        )
    assert linha["status"] == "encerrado"
    assert linha["trabalho"] in ("pendente", "processando")
    assert porta.envios == []
    assert len(itens.itens) == 1


@pytest.mark.postgres
def test_reprocessar_lista_chama_a_porta_de_novo_no_mesmo_id(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    porta = MensageriaFalsa()
    porta.falhas_restantes = 1
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001402"
        )
        _semear_consumo(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        hospedagem.confirmar_saida(
            conexao, id_hotel=id_hotel, id_reserva=id_reserva
        )
        primeiro = _trabalho_pendente(conexao, id_reserva)
        conversa.processar_trabalho_enviar_lista_pedidos_chat(
            conexao, trabalho=primeiro, gateway=porta
        )
        segundo = _trabalho_pendente(conexao, id_reserva)
        conversa.processar_trabalho_enviar_lista_pedidos_chat(
            conexao, trabalho=segundo, gateway=porta
        )
        status = conexao.execute(
            text("SELECT status FROM trabalho WHERE id_trabalho = :id"),
            {"id": primeiro["id_trabalho"]},
        ).scalar_one()
    assert segundo["id_trabalho"] == primeiro["id_trabalho"]
    assert status == "concluido"
    assert len([e for e in porta.envios if e["tipo"] == "lista_pedidos_chat"]) == 1
