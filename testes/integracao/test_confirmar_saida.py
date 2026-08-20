"""Confirmacao de saida pela recepcao."""

from datetime import date, timedelta

import pytest
from sqlalchemy import text

from testes.integracao.test_reservas import _corpo_valido, _login


def _tornar(ambiente, id_reserva: int, status: str) -> None:
    extra = ", checkin_em = now()" if status == "hospedado" else ""
    extra = extra + ", checkout_em = now()" if status == "encerrado" else extra
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                f"UPDATE reserva SET status = :status{extra} "
                "WHERE id_reserva = :id"
            ),
            {"status": status, "id": id_reserva},
        )


def _criar_hospedada(cliente, ambiente, **kwargs) -> int:
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido(**kwargs)).json()[
        "id_reserva"
    ]
    _tornar(ambiente, id_reserva, "ficha_recebida")
    _tornar(ambiente, id_reserva, "hospedado")
    return id_reserva


def _contagens(ambiente, id_reserva: int) -> dict:
    with ambiente.conexao() as conexao:
        return {
            "trabalhos": conexao.execute(
                text(
                    "SELECT COUNT(*) FROM trabalho"
                    " WHERE tipo = 'enviar_pesquisa_saida'"
                    " AND payload->>'id_reserva' = :id"
                ),
                {"id": str(id_reserva)},
            ).scalar_one(),
            "mensagens": conexao.execute(
                text(
                    "SELECT COUNT(*) FROM mensagem WHERE id_reserva = :id"
                    " AND direcao = 'enviada'"
                ),
                {"id": id_reserva},
            ).scalar_one(),
        }


@pytest.mark.postgres
def test_recepcao_confirma_saida_e_agenda_pesquisa_sem_enviar(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente)

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "encerrado"
    assert corpo["pesquisa"] == "agendada"
    assert corpo["lista"] == "ausente"
    assert corpo["checkout_em"]

    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text(
                "SELECT status, checkout_em, data_checkout_prevista "
                "FROM reserva WHERE id_reserva = :id"
            ),
            {"id": id_reserva},
        ).mappings().one()
        envio = conexao.execute(
            text(
                "SELECT status_envio FROM mensagem"
                " WHERE id_reserva = :id AND direcao = 'enviada'"
                " ORDER BY id_mensagem DESC LIMIT 1"
            ),
            {"id": id_reserva},
        ).scalar_one()
    assert linha["status"] == "encerrado"
    assert linha["checkout_em"] is not None
    assert linha["checkout_em"].date() != linha["data_checkout_prevista"] or (
        linha["checkout_em"].hour, linha["checkout_em"].minute
    ) != (0, 0)
    assert envio == "pendente"
    assert _contagens(ambiente, id_reserva)["trabalhos"] == 1
    with ambiente.conexao() as conexao:
        listas = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_lista_pedidos_chat'"
                " AND payload->>'id_reserva' = :id"
            ),
            {"id": str(id_reserva)},
        ).scalar_one()
    assert listas == 0


@pytest.mark.postgres
def test_saida_com_chamado_aberto_permanece_aceita(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente)
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, tipo, descricao)"
                " VALUES (:r, 'reclamacao', 'ar')"
            ),
            {"r": id_reserva},
        )

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "encerrado"


@pytest.mark.postgres
def test_saida_sem_cookie_e_recusada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente)
    cliente.cookies.clear()

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 401


@pytest.mark.postgres
@pytest.mark.parametrize(
    "caminho",
    [
        ("aguardando_cadastro", []),
        ("ficha_recebida", ["ficha_recebida"]),
        ("encerrado", ["ficha_recebida", "hospedado", "encerrado"]),
        ("cancelada", ["cancelada"]),
    ],
)
def test_estado_invalido_recebe_409_sem_gravar(app_sobre_ambiente, caminho):
    status_final, passos = caminho
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    for passo in passos:
        _tornar(ambiente, id_reserva, passo)
    antes = _contagens(ambiente, id_reserva)
    checkout_antes = None
    if status_final == "encerrado":
        with ambiente.conexao() as conexao:
            checkout_antes = conexao.execute(
                text("SELECT checkout_em FROM reserva WHERE id_reserva = :id"),
                {"id": id_reserva},
            ).scalar_one()

    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 409

    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text("SELECT status, checkout_em FROM reserva WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).mappings().one()
    assert linha["status"] == status_final
    if status_final == "encerrado":
        assert linha["checkout_em"] == checkout_antes
    assert _contagens(ambiente, id_reserva) == antes


@pytest.mark.postgres
def test_segundo_clique_nao_cria_segunda_pesquisa(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente)
    primeira = cliente.post(f"/reservas/{id_reserva}/saida")
    assert primeira.status_code == 200
    segunda = cliente.post(f"/reservas/{id_reserva}/saida")
    assert segunda.status_code == 409
    assert _contagens(ambiente, id_reserva)["trabalhos"] == 1


@pytest.mark.postgres
def test_gestor_e_staff_nao_confirmam_saida(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.post(f"/reservas/{id_reserva}/saida").status_code == 403
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.post(f"/reservas/{id_reserva}/saida").status_code == 403


@pytest.mark.postgres
def test_saida_de_outro_hotel_e_404(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    resposta = cliente.post(f"/reservas/{id_reserva}/saida")
    assert resposta.status_code == 404
    with ambiente.conexao() as conexao:
        status_atual = conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).scalar_one()
    assert status_atual == "hospedado"


@pytest.mark.postgres
def test_fila_destaca_saida_vencida_e_some_depois_do_clique(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    ontem = (date.today() - timedelta(days=1)).isoformat()
    hoje = date.today().isoformat()
    id_vencida = _criar_hospedada(
        cliente,
        ambiente,
        telefone="11987654001",
        data_checkin_prevista=(date.today() - timedelta(days=2)).isoformat(),
        data_checkout_prevista=ontem,
    )
    id_hoje = _criar_hospedada(
        cliente,
        ambiente,
        telefone="11987654002",
        data_checkin_prevista=(date.today() - timedelta(days=1)).isoformat(),
        data_checkout_prevista=hoje,
    )
    id_encerrada = _criar_hospedada(
        cliente, ambiente, telefone="11987654003"
    )
    cliente.post(f"/reservas/{id_encerrada}/saida")

    itens = {item["id_reserva"]: item for item in cliente.get("/fila-do-dia").json()["itens"]}
    assert itens[id_vencida]["saida_nao_confirmada"] is True
    assert itens[id_vencida]["chegada_nao_confirmada"] is False
    assert itens[id_hoje]["saida_nao_confirmada"] is False
    assert id_encerrada not in itens

    cliente.post(f"/reservas/{id_vencida}/saida")
    depois = {
        item["id_reserva"]: item
        for item in cliente.get("/fila-do-dia").json()["itens"]
    }
    assert id_vencida not in depois
