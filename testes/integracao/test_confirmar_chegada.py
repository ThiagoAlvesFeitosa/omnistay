"""Confirmacao de chegada pela recepcao."""

from datetime import date, timedelta

import pytest
from sqlalchemy import text

from testes.integracao.test_reservas import _corpo_valido, _login


def _tornar(ambiente, id_reserva: int, status: str) -> None:
    extra = ", checkin_em = now()" if status == "hospedado" else ""
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                f"UPDATE reserva SET status = :status{extra} "
                "WHERE id_reserva = :id"
            ),
            {"status": status, "id": id_reserva},
        )


def _criar_elegivel(cliente, ambiente, **kwargs) -> int:
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido(**kwargs)).json()[
        "id_reserva"
    ]
    _tornar(ambiente, id_reserva, "ficha_recebida")
    return id_reserva


@pytest.mark.postgres
def test_recepcao_confirma_chegada_de_ficha_recebida(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_elegivel(cliente, ambiente)

    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "hospedado"
    assert corpo["checkin_em"]
    assert corpo["id_reserva"] == id_reserva

    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text(
                "SELECT status, checkin_em, data_checkin_prevista "
                "FROM reserva WHERE id_reserva = :id"
            ),
            {"id": id_reserva},
        ).mappings().one()
    assert linha["status"] == "hospedado"
    assert linha["checkin_em"] is not None
    assert linha["checkin_em"].date() != linha["data_checkin_prevista"] or (
        linha["checkin_em"].hour, linha["checkin_em"].minute
    ) != (0, 0)


@pytest.mark.postgres
def test_chegada_sem_cookie_e_recusada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_elegivel(cliente, ambiente)
    cliente.cookies.clear()

    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 401


def _contagens(ambiente, id_reserva: int) -> tuple[int, int]:
    with ambiente.conexao() as conexao:
        trabalhos = conexao.execute(
            text("SELECT COUNT(*) FROM trabalho WHERE payload->>'id_reserva' = :id"),
            {"id": str(id_reserva)},
        ).scalar_one()
        mensagens = conexao.execute(
            text("SELECT COUNT(*) FROM mensagem WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).scalar_one()
    return trabalhos, mensagens


@pytest.mark.postgres
@pytest.mark.parametrize(
    "caminho",
    [
        ("encerrado", ["ficha_recebida", "hospedado", "encerrado"]),
        ("cancelada", ["cancelada"]),
        ("hospedado", ["ficha_recebida", "hospedado"]),
        ("aguardando_cadastro", []),
    ],
)
def test_estado_invalido_recebe_409_sem_gravar(app_sobre_ambiente, caminho):
    status_final, passos = caminho
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    for passo in passos:
        _tornar(ambiente, id_reserva, passo)
    antes_t, antes_m = _contagens(ambiente, id_reserva)
    checkin_antes = None
    if status_final == "hospedado":
        with ambiente.conexao() as conexao:
            checkin_antes = conexao.execute(
                text("SELECT checkin_em FROM reserva WHERE id_reserva = :id"),
                {"id": id_reserva},
            ).scalar_one()

    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 409

    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text("SELECT status, checkin_em FROM reserva WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).mappings().one()
    assert linha["status"] == status_final
    if status_final == "hospedado":
        assert linha["checkin_em"] == checkin_antes
    depois_t, depois_m = _contagens(ambiente, id_reserva)
    assert (depois_t, depois_m) == (antes_t, antes_m)


@pytest.mark.postgres
@pytest.mark.parametrize("origem", ["ficha_parcial", "sem_cadastro_previo"])
def test_ficha_incompleta_nao_bloqueia_chegada(app_sobre_ambiente, origem):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    _tornar(ambiente, id_reserva, origem)

    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "hospedado"


@pytest.mark.postgres
def test_confirmacao_remove_destaque_de_chegada_nao_confirmada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    ontem = date.today() - timedelta(days=1)
    id_reserva = _criar_elegivel(
        cliente,
        ambiente,
        data_checkin_prevista=ontem.isoformat(),
        data_checkout_prevista=date.today().isoformat(),
    )
    item = next(
        i
        for i in cliente.get("/fila-do-dia").json()["itens"]
        if i["id_reserva"] == id_reserva
    )
    assert item["chegada_nao_confirmada"] is True

    assert cliente.post(f"/reservas/{id_reserva}/chegada").status_code == 200
    item = next(
        i
        for i in cliente.get("/fila-do-dia").json()["itens"]
        if i["id_reserva"] == id_reserva
    )
    assert item["chegada_nao_confirmada"] is False


@pytest.mark.postgres
def test_gestao_e_staff_recebem_403_na_chegada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_elegivel(cliente, ambiente)
    for perfil in ("gestor", "staff"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
        assert resposta.status_code == 403
    with ambiente.conexao() as conexao:
        status = conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).scalar_one()
    assert status == "ficha_recebida"


@pytest.mark.postgres
def test_recepcao_de_outro_hotel_recebe_404(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_elegivel(cliente, ambiente)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 404
    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text("SELECT status, checkin_em FROM reserva WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).mappings().one()
        trabalhos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho "
                "WHERE tipo = 'enviar_boas_vindas' "
                "AND (payload->>'id_reserva')::bigint = :id"
            ),
            {"id": id_reserva},
        ).scalar_one()
    assert linha["status"] == "ficha_recebida"
    assert linha["checkin_em"] is None
    assert trabalhos == 0
