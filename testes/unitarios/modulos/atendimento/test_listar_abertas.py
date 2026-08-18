"""Lista operacional de solicitacoes sem dado cadastral."""

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import abrir_reclamacao, abrir_servico, listar_abertas


def _reserva_e_mensagem(conexao, id_hotel: int, conteudo: str, telefone: str):
    id_reserva = conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista) "
            "VALUES (:h, :tel, CURRENT_DATE, CURRENT_DATE + 2) "
            "RETURNING id_reserva"
        ),
        {"h": id_hotel, "tel": telefone},
    ).scalar_one()
    id_mensagem = conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
            "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
        ),
        {"r": id_reserva, "c": conteudo},
    ).scalar_one()
    return id_reserva, id_mensagem


CHAVES_ESPERADAS = {
    "id_solicitacao",
    "id_reserva",
    "tipo",
    "descricao",
    "numero_quarto",
    "urgencia",
    "status",
    "aberta_em",
    "janela_preferencia",
    "destaque_tempo_excedido",
}


@pytest.mark.postgres
def test_listar_abertas_devolve_itens_operacionais_sem_cadastro(ambiente):
    id_a = ambiente.propriedade_a.id_hotel
    id_b = ambiente.propriedade_b.id_hotel
    with ambiente.engine.begin() as conexao:
        reserva_a1, msg_a1 = _reserva_e_mensagem(
            conexao, id_a, "toalha extra no quarto 402", "5511910000001"
        )
        reserva_a2, msg_a2 = _reserva_e_mensagem(
            conexao, id_a, "travesseiro extra", "5511910000002"
        )
        _, msg_b = _reserva_e_mensagem(
            conexao, id_b, "pedido do hotel b", "5511910000003"
        )
        abrir_servico(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_a1,
            id_mensagem=msg_a1,
            descricao="toalha extra no quarto 402",
            numero_quarto="402",
            urgencia="baixa",
        )
        abrir_servico(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_a2,
            id_mensagem=msg_a2,
            descricao="travesseiro extra",
            numero_quarto=None,
            urgencia="media",
        )
        abrir_servico(
            conexao,
            id_hotel=id_b,
            id_reserva=conexao.execute(
                text("SELECT id_reserva FROM mensagem WHERE id_mensagem = :id"),
                {"id": msg_b},
            ).scalar_one(),
            id_mensagem=msg_b,
            descricao="pedido do hotel b",
            numero_quarto=None,
            urgencia="baixa",
        )
        itens_a = listar_abertas(conexao, id_hotel=id_a)
        itens_b = listar_abertas(conexao, id_hotel=id_b)
        itens_inexistente = listar_abertas(conexao, id_hotel=999999)

    assert [i["descricao"] for i in itens_a] == [
        "toalha extra no quarto 402",
        "travesseiro extra",
    ]
    assert itens_a[0]["numero_quarto"] == "402"
    assert itens_a[1]["numero_quarto"] is None
    for item in itens_a:
        assert set(item) == CHAVES_ESPERADAS
        assert "nome" not in item
        assert "telefone" not in item
        assert "documento" not in item
    assert len(itens_b) == 1
    assert itens_b[0]["descricao"] == "pedido do hotel b"
    assert itens_inexistente == []


@pytest.mark.postgres
def test_listar_abertas_inclui_reclamacao_sem_cadastro(ambiente):
    id_a = ambiente.propriedade_a.id_hotel
    id_b = ambiente.propriedade_b.id_hotel
    with ambiente.engine.begin() as conexao:
        reserva_a, msg_a = _reserva_e_mensagem(
            conexao, id_a, "o ar do quarto 402 nao esta gelando", "5511910000011"
        )
        reserva_serv, msg_serv = _reserva_e_mensagem(
            conexao, id_a, "toalha extra", "5511910000012"
        )
        abrir_reclamacao(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_a,
            id_mensagem=msg_a,
            descricao="o ar do quarto 402 nao esta gelando",
            numero_quarto="402",
            urgencia="alta",
            janela_preferencia=None,
        )
        abrir_servico(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_serv,
            id_mensagem=msg_serv,
            descricao="toalha extra",
            numero_quarto=None,
            urgencia="baixa",
        )
        itens_a = listar_abertas(conexao, id_hotel=id_a)
        itens_b = listar_abertas(conexao, id_hotel=id_b)

    reclamacao = next(i for i in itens_a if i["tipo"] == "reclamacao")
    servico = next(i for i in itens_a if i["tipo"] == "servico")
    assert reclamacao["numero_quarto"] == "402"
    assert reclamacao["janela_preferencia"] is None
    assert reclamacao["destaque_tempo_excedido"] is False
    assert servico["janela_preferencia"] is None
    assert servico["destaque_tempo_excedido"] is False
    for item in itens_a:
        assert set(item) == CHAVES_ESPERADAS
        assert "nome" not in item
        assert "telefone" not in item
        assert "documento" not in item
    assert all(i["id_reserva"] != reserva_a for i in itens_b)


@pytest.mark.postgres
def test_listar_abertas_omite_resolvida_e_mantem_outra_aberta(ambiente):
    from datetime import UTC, datetime

    from app.modulos.atendimento import service as atendimento_svc

    id_a = ambiente.propriedade_a.id_hotel
    instante = datetime(2026, 8, 18, 14, 32, tzinfo=UTC)
    with ambiente.engine.begin() as conexao:
        reserva_ok, msg_ok = _reserva_e_mensagem(
            conexao, id_a, "toalha extra", "5511910000301"
        )
        reserva_outra, msg_outra = _reserva_e_mensagem(
            conexao, id_a, "travesseiro extra", "5511910000302"
        )
        id_ok = abrir_servico(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_ok,
            id_mensagem=msg_ok,
            descricao="toalha extra",
            numero_quarto=None,
            urgencia="baixa",
        )
        id_outra = abrir_servico(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_outra,
            id_mensagem=msg_outra,
            descricao="travesseiro extra",
            numero_quarto=None,
            urgencia="baixa",
        )
        class Agendador:
            def __call__(self, *args, **kwargs):
                return "agendada"

        atendimento_svc.resolver(
            conexao,
            id_hotel=id_a,
            id_solicitacao=id_ok,
            id_usuario=ambiente.propriedade_a.usuarios["staff"].id_usuario,
            agendar_confirmacao=Agendador(),
            relogio=type("R", (), {"agora": staticmethod(lambda: instante)})(),
        )
        itens = listar_abertas(conexao, id_hotel=id_a)
    ids = [i["id_solicitacao"] for i in itens]
    assert id_ok not in ids
    assert id_outra in ids


@pytest.mark.postgres
def test_destaque_so_reclamacao_alem_do_prazo(ambiente):
    from datetime import UTC, datetime, timedelta

    id_hotel = ambiente.propriedade_a.id_hotel
    agora = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
    with ambiente.engine.begin() as conexao:
        reserva_velha, msg_velha = _reserva_e_mensagem(
            conexao, id_hotel, "ar antigo", "5511910000021"
        )
        reserva_nova, msg_nova = _reserva_e_mensagem(
            conexao, id_hotel, "ar recente", "5511910000022"
        )
        reserva_serv, msg_serv = _reserva_e_mensagem(
            conexao, id_hotel, "toalha antiga", "5511910000023"
        )
        id_velha = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=reserva_velha,
            id_mensagem=msg_velha,
            descricao="ar antigo",
            numero_quarto=None,
            urgencia="alta",
            janela_preferencia=None,
        )
        id_nova = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=reserva_nova,
            id_mensagem=msg_nova,
            descricao="ar recente",
            numero_quarto=None,
            urgencia="alta",
            janela_preferencia=None,
        )
        id_serv = abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=reserva_serv,
            id_mensagem=msg_serv,
            descricao="toalha antiga",
            numero_quarto=None,
            urgencia="baixa",
        )
        conexao.execute(
            text("UPDATE solicitacao SET aberta_em = :t WHERE id_solicitacao = :id"),
            {"t": agora - timedelta(hours=3), "id": id_velha},
        )
        conexao.execute(
            text("UPDATE solicitacao SET aberta_em = :t WHERE id_solicitacao = :id"),
            {"t": agora - timedelta(hours=1), "id": id_nova},
        )
        conexao.execute(
            text("UPDATE solicitacao SET aberta_em = :t WHERE id_solicitacao = :id"),
            {"t": agora - timedelta(hours=3), "id": id_serv},
        )
        itens = listar_abertas(conexao, id_hotel=id_hotel, agora=agora)
    por_id = {i["id_solicitacao"]: i for i in itens}
    assert por_id[id_velha]["destaque_tempo_excedido"] is True
    assert por_id[id_nova]["destaque_tempo_excedido"] is False
    assert por_id[id_serv]["destaque_tempo_excedido"] is False


@pytest.mark.postgres
def test_destaque_ausente_quando_prazo_nao_e_numero(ambiente):
    from datetime import UTC, datetime, timedelta

    id_hotel = ambiente.propriedade_a.id_hotel
    agora = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
    with ambiente.engine.begin() as conexao:
        reserva, msg = _reserva_e_mensagem(
            conexao, id_hotel, "ar antigo", "5511910000024"
        )
        id_sol = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=reserva,
            id_mensagem=msg,
            descricao="ar antigo",
            numero_quarto=None,
            urgencia="alta",
            janela_preferencia=None,
        )
        conexao.execute(
            text("UPDATE solicitacao SET aberta_em = :t WHERE id_solicitacao = :id"),
            {"t": agora - timedelta(hours=5), "id": id_sol},
        )
        itens = listar_abertas(
            conexao,
            id_hotel=id_hotel,
            agora=agora,
            ler_parametro=lambda *a, **k: None,
        )
    item = next(i for i in itens if i["id_solicitacao"] == id_sol)
    assert item["destaque_tempo_excedido"] is False
