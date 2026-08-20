"""Lista de pedidos feitos pelo chat no encerramento."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.atendimento.service import (
    abrir_consumo,
    abrir_servico,
    dispensar,
    lancar,
)
from app.modulos.propriedade import service as propriedade
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import _criar_hospedada
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL
from testes.suporte.pedidos_chat import CAMINHO_LISTA, ROTULO, proibicoes_da_lista
from worker.consumidor import processar_uma_passagem_na_engine


def _semear_consumo(
    ambiente,
    id_reserva: int,
    descricao: str,
    quarto: str | None,
    *,
    descricao_item: str = NOME_ITEM,
    valor=PRECO_ATUAL,
):
    with ambiente.engine.begin() as conexao:
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
            ),
            {"r": id_reserva, "c": descricao},
        ).scalar_one()
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        return abrir_consumo(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao=descricao,
            descricao_item=descricao_item,
            valor_praticado=valor,
            numero_quarto=quarto,
            urgencia="baixa",
        )


def _semear_servico(ambiente, id_reserva: int):
    with ambiente.engine.begin() as conexao:
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'toalha extra') RETURNING id_mensagem"
            ),
            {"r": id_reserva},
        ).scalar_one()
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao="toalha extra",
            numero_quarto=None,
            urgencia="baixa",
        )


def _contagens_lista(ambiente, id_reserva: int) -> dict:
    with ambiente.conexao() as conexao:
        return {
            "listas": conexao.execute(
                text(
                    "SELECT COUNT(*) FROM trabalho"
                    " WHERE tipo = 'enviar_lista_pedidos_chat'"
                    " AND payload->>'id_reserva' = :id"
                ),
                {"id": str(id_reserva)},
            ).scalar_one(),
            "pesquisas": conexao.execute(
                text(
                    "SELECT COUNT(*) FROM trabalho"
                    " WHERE tipo = 'enviar_pesquisa_saida'"
                    " AND payload->>'id_reserva' = :id"
                ),
                {"id": str(id_reserva)},
            ).scalar_one(),
        }


@pytest.mark.postgres
def test_saida_com_consumo_agenda_lista_sem_enviar(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658001")
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["pesquisa"] == "agendada"
    assert corpo["lista"] == "agendada"
    assert _contagens_lista(ambiente, id_reserva) == {"listas": 1, "pesquisas": 1}

    with ambiente.conexao() as conexao:
        status = conexao.execute(
            text(
                "SELECT status_envio FROM mensagem"
                " WHERE id_reserva = :id AND direcao = 'enviada'"
                " AND conteudo ILIKE '%pedidos feitos pelo chat%'"
            ),
            {"id": id_reserva},
        ).scalar_one()
    assert status == "pendente"


@pytest.mark.postgres
def test_worker_envia_lista_pela_porta_falsa(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658002")
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post(f"/reservas/{id_reserva}/saida")

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    enviados = [e for e in porta.envios if e["tipo"] == "lista_pedidos_chat"]
    assert len(enviados) == 1
    assert ROTULO in enviados[0]["corpo"].casefold()
    assert NOME_ITEM in enviados[0]["corpo"]


def _semear_misto(ambiente, id_reserva: int) -> None:
    _semear_consumo(
        ambiente, id_reserva, "uma cerveja", "402", descricao_item="Cerveja"
    )
    id_agua = _semear_consumo(
        ambiente,
        id_reserva,
        "uma agua",
        None,
        descricao_item="Agua",
        valor=Decimal("5.00"),
    )
    id_cortesia = _semear_consumo(
        ambiente,
        id_reserva,
        "cortesia da casa",
        None,
        descricao_item="Cortesia",
        valor=Decimal("0.00"),
    )
    _semear_servico(ambiente, id_reserva)
    recepcao = ambiente.propriedade_a.usuarios["recepcao"].id_usuario
    with ambiente.engine.begin() as conexao:
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        lancar(
            conexao,
            id_hotel=id_hotel,
            id_solicitacao=id_agua,
            id_usuario=recepcao,
        )
        dispensar(
            conexao,
            id_hotel=id_hotel,
            id_solicitacao=id_cortesia,
            id_usuario=recepcao,
        )


def _corpo_da_lista(ambiente, id_reserva: int) -> str:
    with ambiente.conexao() as conexao:
        return conexao.execute(
            text(
                "SELECT conteudo FROM mensagem"
                " WHERE id_reserva = :id AND direcao = 'enviada'"
                " AND conteudo ILIKE '%pedidos feitos pelo chat%'"
            ),
            {"id": id_reserva},
        ).scalar_one()


@pytest.mark.postgres
def test_saida_mista_omite_toalha_e_dispensado(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658003")
    _semear_misto(ambiente, id_reserva)
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 200
    assert resposta.json()["lista"] == "agendada"
    corpo = _corpo_da_lista(ambiente, id_reserva)
    baixo = corpo.casefold()
    assert "cerveja" in baixo
    assert "agua" in baixo
    assert "toalha" not in baixo
    assert "cortesia" not in baixo


def _caminho(id_reserva: int) -> str:
    return CAMINHO_LISTA.format(id=id_reserva)


@pytest.mark.postgres
def test_get_devolve_cobraveis_antes_do_envio(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658004")
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post(f"/reservas/{id_reserva}/saida")

    resposta = cliente.get(_caminho(id_reserva))
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["id_reserva"] == id_reserva
    assert len(corpo["itens"]) == 1
    item = corpo["itens"][0]
    assert item["descricao_item"] == NOME_ITEM
    assert Decimal(str(item["valor_praticado"])) == PRECO_ATUAL
    assert Decimal(str(corpo["total"])) == PRECO_ATUAL
    assert "nome" not in item
    assert "telefone" not in item
    assert "status_lancamento" not in item
    assert "status_lancamento" not in corpo


@pytest.mark.postgres
def test_get_sem_consumo_devolve_lista_vazia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658005")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    resposta = cliente.get(_caminho(id_reserva))
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["itens"] == []
    assert Decimal(str(corpo["total"])) == Decimal("0")


@pytest.mark.postgres
def test_saida_sem_consumo_nao_agenda_lista(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658006")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 200
    assert resposta.json()["lista"] == "ausente"
    assert resposta.json()["pesquisa"] == "agendada"
    assert _contagens_lista(ambiente, id_reserva) == {"listas": 0, "pesquisas": 1}


@pytest.mark.postgres
def test_saida_so_dispensado_nao_agenda_lista(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658007")
    id_cortesia = _semear_consumo(
        ambiente,
        id_reserva,
        "cortesia",
        None,
        descricao_item="Cortesia",
        valor=Decimal("0.00"),
    )
    recepcao = ambiente.propriedade_a.usuarios["recepcao"].id_usuario
    with ambiente.engine.begin() as conexao:
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        dispensar(
            conexao,
            id_hotel=id_hotel,
            id_solicitacao=id_cortesia,
            id_usuario=recepcao,
        )
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 200
    assert resposta.json()["lista"] == "ausente"
    assert _contagens_lista(ambiente, id_reserva)["listas"] == 0


@pytest.mark.postgres
def test_valor_na_lista_e_o_praticado_nao_o_preco_atual(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658008")
    with ambiente.engine.begin() as conexao:
        item = propriedade.criar_item_vendavel(
            conexao,
            id_hotel=ambiente.propriedade_a.id_hotel,
            nome=NOME_ITEM,
            preco_atual=PRECO_ATUAL,
        )
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    with ambiente.engine.begin() as conexao:
        propriedade.atualizar_item_vendavel(
            conexao,
            id_hotel=ambiente.propriedade_a.id_hotel,
            id_item_vendavel=item.id_item_vendavel,
            preco_atual=Decimal("20.00"),
        )
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post(f"/reservas/{id_reserva}/saida")

    consulta = cliente.get(_caminho(id_reserva)).json()
    assert Decimal(str(consulta["itens"][0]["valor_praticado"])) == PRECO_ATUAL
    assert "20,00" not in _corpo_da_lista(ambiente, id_reserva)
    assert "12,00" in _corpo_da_lista(ambiente, id_reserva)


@pytest.mark.postgres
def test_corpo_enviado_tem_rotulo_e_pesquisa_nao_incorpora_lista(
    app_sobre_ambiente,
):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658009")
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post(f"/reservas/{id_reserva}/saida")

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    listas = [e for e in porta.envios if e["tipo"] == "lista_pedidos_chat"]
    pesquisas = [e for e in porta.envios if e["tipo"] == "pesquisa_saida"]
    assert len(listas) == 1
    baixo = listas[0]["corpo"].casefold()
    assert ROTULO in baixo
    for termo in proibicoes_da_lista():
        assert termo not in baixo
    assert ROTULO not in pesquisas[0]["corpo"].casefold()


@pytest.mark.postgres
def test_falha_do_worker_mantem_encerrado_e_get_vivo(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658010")
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post(f"/reservas/{id_reserva}/saida")

    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    consulta = cliente.get(_caminho(id_reserva))
    assert consulta.status_code == 200
    assert len(consulta.json()["itens"]) == 1
    with ambiente.conexao() as conexao:
        status = conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).scalar_one()
    assert status == "encerrado"

    porta.falhar_sempre = False
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE trabalho SET proxima_tentativa_em = NULL"
                " WHERE (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        )
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    enviados = [e for e in porta.envios if e["tipo"] == "lista_pedidos_chat"]
    assert len(enviados) == 1


@pytest.mark.postgres
def test_staff_gestao_e_outro_hotel_isolam_a_lista(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987658011")
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    caminho = _caminho(id_reserva)

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get(caminho).status_code == 403

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    leitura = cliente.get(caminho)
    assert leitura.status_code == 200
    assert len(leitura.json()["itens"]) == 1
    assert cliente.post(f"/reservas/{id_reserva}/saida").status_code == 403

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    alheia = cliente.get(caminho)
    assert alheia.status_code == 404
    assert alheia.json()["detail"] == "Reserva nao encontrada."
    saida = cliente.post(f"/reservas/{id_reserva}/saida")
    assert saida.status_code == 404
    assert _contagens_lista(ambiente, id_reserva)["listas"] == 0
