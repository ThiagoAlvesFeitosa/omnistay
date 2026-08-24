"""Retencao: conteudo vencido some, volume fica, ficha some no prazo, GET so gestao."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.comum.retencao import MARCA_PAYLOAD, MARCA_TELEFONE, MARCA_TEXTO
from testes.suporte.retencao import AGORA_RETENCAO, gravar_estadia_encerrada
from worker.agendador import verificar_retencao

CHECKOUT_13_MESES = datetime(2025, 7, 24, 12, 0, tzinfo=UTC)
CHECKOUT_11_MESES = datetime(2025, 9, 24, 12, 0, tzinfo=UTC)
CHECKOUT_SEIS_ANOS = datetime(2020, 8, 24, 12, 0, tzinfo=UTC)


def _login(cliente, usuario):
    resposta = cliente.post(
        "/sessoes",
        json={"email": usuario.email, "senha": usuario.senha},
    )
    assert resposta.status_code == 201


def _contar(conexao, tabela: str) -> int:
    return conexao.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar_one()


def _mensagem(conexao, id_mensagem: int) -> dict:
    linha = conexao.execute(
        text(
            "SELECT conteudo, classificacao_bruta, intencao, sentimento, urgencia"
            " FROM mensagem WHERE id_mensagem = :id"
        ),
        {"id": id_mensagem},
    ).mappings().one()
    return dict(linha)


def _payload(conexao, id_evento: int):
    return conexao.execute(
        text("SELECT payload FROM evento_webhook WHERE id_evento = :id"),
        {"id": id_evento},
    ).scalar_one()


def _solicitacao(conexao, id_solicitacao: int) -> dict:
    linha = conexao.execute(
        text(
            "SELECT descricao, tipo, status, urgencia, numero_quarto,"
            " janela_preferencia FROM solicitacao WHERE id_solicitacao = :id"
        ),
        {"id": id_solicitacao},
    ).mappings().one()
    return dict(linha)


def _avaliacao(conexao, id_avaliacao: int) -> dict:
    linha = conexao.execute(
        text(
            "SELECT comentario, nota, origem FROM avaliacao"
            " WHERE id_avaliacao = :id"
        ),
        {"id": id_avaliacao},
    ).mappings().one()
    return dict(linha)


def _execucoes(conexao, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT * FROM execucao_retencao WHERE id_hotel = :h"
            " ORDER BY executado_em DESC"
        ),
        {"h": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


@pytest.mark.postgres
def test_conteudo_vencido_e_marcado_e_linha_permanece(ambiente):
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        ids = gravar_estadia_encerrada(
            conexao,
            hotel,
            checkout_em=CHECKOUT_13_MESES,
            texto="ar condicionado barulhento no 201",
            comentario="gostei do cafe",
            descricao="toalha extra no 201",
            numero_quarto="201",
            janela_preferencia="depois das 16h",
            id_externo="evt-retencao-13m",
        )
        n_msg = _contar(conexao, "mensagem")
        n_sol = _contar(conexao, "solicitacao")
        n_av = _contar(conexao, "avaliacao")
        tipos = dict(
            conexao.execute(
                text("SELECT tipo, COUNT(*) FROM solicitacao GROUP BY tipo")
            ).all()
        )
        notas = dict(
            conexao.execute(
                text("SELECT nota, COUNT(*) FROM avaliacao GROUP BY nota")
            ).all()
        )
        comprovados = verificar_retencao(conexao, agora=AGORA_RETENCAO)
        msg = _mensagem(conexao, ids["id_mensagem"])
        payload = _payload(conexao, ids["id_evento"])
        sol = _solicitacao(conexao, ids["id_solicitacao"])
        av = _avaliacao(conexao, ids["id_avaliacao"])
        execucoes = _execucoes(conexao, hotel)

        assert comprovados >= 1
        assert msg["conteudo"] == MARCA_TEXTO
        assert msg["classificacao_bruta"] is None
        assert msg["intencao"] == "duvida_geral"
        assert payload == MARCA_PAYLOAD
        assert sol["descricao"] == MARCA_TEXTO
        assert sol["status"] == "aberta"
        assert sol["numero_quarto"] == "201"
        assert sol["janela_preferencia"] == "depois das 16h"
        assert av["comentario"] == MARCA_TEXTO
        assert av["nota"] == 4
        assert _contar(conexao, "mensagem") == n_msg
        assert _contar(conexao, "solicitacao") == n_sol
        assert _contar(conexao, "avaliacao") == n_av
        assert dict(
            conexao.execute(
                text("SELECT tipo, COUNT(*) FROM solicitacao GROUP BY tipo")
            ).all()
        ) == tipos
        assert dict(
            conexao.execute(
                text("SELECT nota, COUNT(*) FROM avaliacao GROUP BY nota")
            ).all()
        ) == notas
        assert len(execucoes) == 1
        assert execucoes[0]["mensagens_anonimizadas"] >= 1
        assert execucoes[0]["comentarios_anonimizados"] >= 1
        assert execucoes[0]["payloads_anonimizados"] >= 1
        assert execucoes[0]["descricoes_anonimizadas"] >= 1


@pytest.mark.postgres
def test_descricao_vazia_permanece_vazia_apos_passagem(ambiente):
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        ids = gravar_estadia_encerrada(
            conexao,
            hotel,
            checkout_em=CHECKOUT_13_MESES,
            texto="mensagem com texto",
            descricao="   ",
            id_externo="evt-desc-vazia",
        )
        verificar_retencao(conexao, agora=AGORA_RETENCAO)
        sol = _solicitacao(conexao, ids["id_solicitacao"])
        execucao = _execucoes(conexao, hotel)[0]

        assert sol["descricao"] == "   "
        assert execucao["descricoes_anonimizadas"] == 0


@pytest.mark.postgres
def test_mensagem_enviada_vencida_tambem_e_anonimizada(ambiente):
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        ids = gravar_estadia_encerrada(
            conexao,
            hotel,
            checkout_em=CHECKOUT_13_MESES,
            texto="pedido do hospede",
            id_externo="evt-enviada-13m",
        )
        id_enviada = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
                " status_envio) VALUES (:r, 'enviada',"
                " 'confirmamos o pedido de toalha', 'enviada')"
                " RETURNING id_mensagem"
            ),
            {"r": ids["id_reserva"]},
        ).scalar_one()
        verificar_retencao(conexao, agora=AGORA_RETENCAO)
        enviada = _mensagem(conexao, id_enviada)

        assert enviada["conteudo"] == MARCA_TEXTO


@pytest.mark.postgres
def test_saida_de_onze_meses_permanece_intacta(ambiente):
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        ids = gravar_estadia_encerrada(
            conexao,
            hotel,
            checkout_em=CHECKOUT_11_MESES,
            texto="texto original da estadia recente",
            comentario="comentario original",
            descricao="descricao original",
            id_externo="evt-retencao-11m",
        )
        verificar_retencao(conexao, agora=AGORA_RETENCAO)
        msg = _mensagem(conexao, ids["id_mensagem"])
        assert msg["conteudo"] == "texto original da estadia recente"
        assert msg["classificacao_bruta"] is not None
        assert _solicitacao(conexao, ids["id_solicitacao"])["descricao"] == (
            "descricao original"
        )
        assert _avaliacao(conexao, ids["id_avaliacao"])["comentario"] == (
            "comentario original"
        )
        assert _payload(conexao, ids["id_evento"]) != MARCA_PAYLOAD


@pytest.mark.postgres
def test_ficha_de_seis_anos_some_e_reserva_permanece(ambiente):
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        ids = gravar_estadia_encerrada(
            conexao,
            hotel,
            checkout_em=CHECKOUT_SEIS_ANOS,
            texto="texto antigo",
            comentario="comentario antigo",
            descricao="descricao antiga",
            id_externo="evt-retencao-6a",
            incluir_consentimento=True,
        )
        id_hospede = ids["id_hospede"]
        id_reserva = ids["id_reserva"]
        verificar_retencao(conexao, agora=AGORA_RETENCAO)
        hospede = conexao.execute(
            text("SELECT 1 FROM hospede WHERE id_hospede = :id"),
            {"id": id_hospede},
        ).scalar()
        consentimento = conexao.execute(
            text("SELECT 1 FROM consentimento WHERE id_hospede = :id"),
            {"id": id_hospede},
        ).scalar()
        reserva = conexao.execute(
            text(
                "SELECT id_reserva, telefone_contato FROM reserva"
                " WHERE id_reserva = :id"
            ),
            {"id": id_reserva},
        ).mappings().one()
        execucao = _execucoes(conexao, hotel)[0]

        assert hospede is None
        assert consentimento is None
        assert reserva["id_reserva"] == id_reserva
        assert reserva["telefone_contato"] == MARCA_TELEFONE
        assert execucao["fichas_apagadas"] >= 1


@pytest.mark.postgres
def test_dois_hoteis_so_o_vencido_de_a_e_marcado_e_segunda_passagem_nao_duplica(
    ambiente,
):
    hotel_a = ambiente.propriedade_a.id_hotel
    hotel_b = ambiente.propriedade_b.id_hotel
    with ambiente.engine.begin() as conexao:
        ids_a = gravar_estadia_encerrada(
            conexao,
            hotel_a,
            checkout_em=CHECKOUT_13_MESES,
            texto="segredo do hotel a",
            comentario="comentario a",
            descricao="descricao a",
            id_externo="evt-hotel-a",
        )
        ids_b = gravar_estadia_encerrada(
            conexao,
            hotel_b,
            checkout_em=CHECKOUT_11_MESES,
            texto="texto do hotel b",
            comentario="comentario b",
            descricao="descricao b",
            id_externo="evt-hotel-b",
        )
        verificar_retencao(conexao, agora=AGORA_RETENCAO)
        verificar_retencao(conexao, agora=AGORA_RETENCAO)
        assert _mensagem(conexao, ids_a["id_mensagem"])["conteudo"] == MARCA_TEXTO
        assert _mensagem(conexao, ids_b["id_mensagem"])["conteudo"] == "texto do hotel b"
        assert len(_execucoes(conexao, hotel_a)) == 1
        assert len(_execucoes(conexao, hotel_b)) == 1


@pytest.mark.postgres
def test_chave_de_meses_ausente_nao_marca_conteudo(ambiente):
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        ids = gravar_estadia_encerrada(
            conexao,
            hotel,
            checkout_em=CHECKOUT_13_MESES,
            texto="deve permanecer",
            id_externo="evt-sem-prazo",
        )
        conexao.execute(
            text(
                "DELETE FROM parametro_hotel"
                " WHERE id_hotel = :h AND chave = 'meses_retencao_conteudo_livre'"
            ),
            {"h": hotel},
        )
        verificar_retencao(conexao, agora=AGORA_RETENCAO)
        assert _mensagem(conexao, ids["id_mensagem"])["conteudo"] == "deve permanecer"
        execucao = _execucoes(conexao, hotel)[0]
        assert execucao["prazo_conteudo_ausente"] is True
        assert execucao["mensagens_anonimizadas"] == 0


@pytest.mark.postgres
def test_gestao_le_comprovante_e_outros_perfis_sao_recusados(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    hotel_a = ambiente.propriedade_a.id_hotel

    _login(cliente, ambiente.propriedade_b.usuarios["gestor"])
    vazio = cliente.get("/retencao")
    assert vazio.status_code == 200
    assert vazio.json()["execucoes"] == []

    with ambiente.engine.begin() as conexao:
        gravar_estadia_encerrada(
            conexao,
            hotel_a,
            checkout_em=CHECKOUT_13_MESES,
            texto="pedido de toalha",
            comentario="otimo",
            descricao="toalha",
            id_externo="evt-http-a",
        )
        verificar_retencao(conexao, agora=AGORA_RETENCAO)

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    ok = cliente.get("/retencao")
    assert ok.status_code == 200
    execucoes = ok.json()["execucoes"]
    assert len(execucoes) == 1
    item = execucoes[0]
    assert "id_hotel" not in item
    assert item["mensagens_anonimizadas"] >= 1
    assert "pedido de toalha" not in str(ok.json())

    recusado = cliente.post("/retencao", json={})
    assert recusado.status_code == 405

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["gestor"])
    lista_b = cliente.get("/retencao")
    assert lista_b.status_code == 200
    assert "pedido de toalha" not in str(lista_b.json())
    for execucao_b in lista_b.json()["execucoes"]:
        assert execucao_b["mensagens_anonimizadas"] == 0

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert cliente.get("/retencao").status_code == 403

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/retencao").status_code == 403

    cliente.cookies.clear()
    sem_cookie = cliente.get("/retencao")
    assert sem_cookie.status_code == 401
