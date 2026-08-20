"""Interpretacao da pesquisa de saida — nota, aceite e desvio humano."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.modulos.conversa import service as conversa
from app.modulos.hospedagem import service as hospedagem
from app.portas.llm import ResultadoPesquisaSaida
from testes.suporte.pulso import montar_hospedado_para_pulso


def _preparar_resposta(conexao, *, id_hotel: int, telefone: str) -> tuple[int, dict]:
    id_reserva = montar_hospedado_para_pulso(
        conexao, id_hotel=id_hotel, telefone=telefone
    )
    hospedagem.confirmar_saida(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    id_mensagem = conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo)"
            " VALUES (:r, 'recebida', 'resposta') RETURNING id_mensagem"
        ),
        {"r": id_reserva},
    ).scalar_one()
    from app.fila import service as fila_service

    id_trabalho = fila_service.enfileirar_interpretar_pesquisa_saida(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )
    trabalho = conexao.execute(
        text(
            "SELECT id_trabalho, id_hotel, tipo, payload, status, tentativas"
            " FROM trabalho WHERE id_trabalho = :id"
        ),
        {"id": id_trabalho},
    ).mappings().one()
    return id_reserva, dict(trabalho)


@pytest.mark.postgres
def test_completo_grava_nota_e_aceite(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.configurar_pesquisa_saida(
        ResultadoPesquisaSaida(desfecho="completo", nota=5, comentario="ok", aceite=True)
    )
    with ambiente.engine.begin() as conexao:
        id_reserva, trabalho = _preparar_resposta(
            conexao, id_hotel=id_hotel, telefone="5511910001401"
        )
        conversa.processar_trabalho_interpretar_pesquisa_saida(
            conexao, trabalho=trabalho, llm=llm
        )
        nota = conexao.execute(
            text(
                "SELECT nota FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        consentimentos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM consentimento c"
                " JOIN reserva_hospede rh ON rh.id_hospede = c.id_hospede"
                " WHERE rh.id_reserva = :r AND c.origem = 'pesquisa_checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        desfecho = conexao.execute(
            text(
                "SELECT classificacao_bruta->>'desfecho' FROM mensagem"
                " WHERE id_mensagem = :id"
            ),
            {"id": trabalho["payload"]["id_mensagem"]},
        ).scalar_one()
        lembretes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert nota == 5
    assert consentimentos == 1
    assert desfecho == "completo"
    assert lembretes == 0


@pytest.mark.postgres
def test_so_nota_nao_inventa_consentimento(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.configurar_pesquisa_saida(
        ResultadoPesquisaSaida(desfecho="parcial", nota=4, aceite=None)
    )
    with ambiente.engine.begin() as conexao:
        id_reserva, trabalho = _preparar_resposta(
            conexao, id_hotel=id_hotel, telefone="5511910001402"
        )
        conversa.processar_trabalho_interpretar_pesquisa_saida(
            conexao, trabalho=trabalho, llm=llm
        )
        consentimentos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM consentimento c"
                " JOIN reserva_hospede rh ON rh.id_hospede = c.id_hospede"
                " WHERE rh.id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        nota = conexao.execute(
            text(
                "SELECT nota FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert nota == 4
    assert consentimentos == 0


@pytest.mark.postgres
def test_nota_fora_da_faixa_e_descartada(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.configurar_pesquisa_saida(
        ResultadoPesquisaSaida(desfecho="completo", nota=9, aceite=True)
    )
    with ambiente.engine.begin() as conexao:
        id_reserva, trabalho = _preparar_resposta(
            conexao, id_hotel=id_hotel, telefone="5511910001403"
        )
        conversa.processar_trabalho_interpretar_pesquisa_saida(
            conexao, trabalho=trabalho, llm=llm
        )
        avaliacoes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        consentimentos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM consentimento c"
                " JOIN reserva_hospede rh ON rh.id_hospede = c.id_hospede"
                " WHERE rh.id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert avaliacoes == 0
    assert consentimentos == 1


@pytest.mark.postgres
def test_irreconhecivel_sinaliza_humano_sem_inventar(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.configurar_pesquisa_saida(
        ResultadoPesquisaSaida(desfecho="irreconhecivel")
    )
    with ambiente.engine.begin() as conexao:
        id_reserva, trabalho = _preparar_resposta(
            conexao, id_hotel=id_hotel, telefone="5511910001404"
        )
        conversa.processar_trabalho_interpretar_pesquisa_saida(
            conexao, trabalho=trabalho, llm=llm
        )
        flag = conexao.execute(
            text(
                "SELECT pesquisa_saida_leitura_humana FROM vw_fila_do_dia"
                " WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        avaliacoes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        status = conexao.execute(
            text("SELECT status FROM trabalho WHERE id_trabalho = :id"),
            {"id": trabalho["id_trabalho"]},
        ).scalar_one()
    assert flag is True
    assert avaliacoes == 0
    assert status == "concluido"


@pytest.mark.postgres
def test_prazo_ausente_sinaliza_humano_e_nao_inventa(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "DELETE FROM parametro_hotel"
                " WHERE id_hotel = :h AND chave = 'horas_atribuicao_pesquisa_saida'"
            ),
            {"h": id_hotel},
        )
        id_reserva, trabalho = _preparar_resposta(
            conexao, id_hotel=id_hotel, telefone="5511910001405"
        )
        conversa.processar_trabalho_interpretar_pesquisa_saida(
            conexao, trabalho=trabalho, llm=llm
        )
        desfecho = conexao.execute(
            text(
                "SELECT classificacao_bruta->>'desfecho' FROM mensagem"
                " WHERE id_mensagem = :id"
            ),
            {"id": trabalho["payload"]["id_mensagem"]},
        ).scalar_one()
        avaliacoes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO parametro_hotel (id_hotel, chave, valor)"
                " VALUES (:h, 'horas_atribuicao_pesquisa_saida', '24')"
            ),
            {"h": id_hotel},
        )
    assert desfecho == "prazo_ausente"
    assert avaliacoes == 0
    assert llm.chamadas_pesquisa_saida == []


@pytest.mark.postgres
def test_janela_vencida_conclui_sem_humano(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    llm = LLMFalso()
    llm.configurar_pesquisa_saida(
        ResultadoPesquisaSaida(desfecho="completo", nota=5, aceite=True)
    )
    with ambiente.engine.begin() as conexao:
        id_reserva, trabalho = _preparar_resposta(
            conexao, id_hotel=id_hotel, telefone="5511910001406"
        )
        conversa.processar_trabalho_interpretar_pesquisa_saida(
            conexao,
            trabalho=trabalho,
            llm=llm,
            agora=datetime.now(UTC) + timedelta(hours=25),
        )
        flag = conexao.execute(
            text(
                "SELECT pesquisa_saida_leitura_humana FROM vw_fila_do_dia"
                " WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        ).scalar_one_or_none()
        avaliacoes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert flag is None
    assert avaliacoes == 0
    assert llm.chamadas_pesquisa_saida == []
