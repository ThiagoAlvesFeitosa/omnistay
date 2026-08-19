"""Resolucao de solicitacao — regras com repositorio falso e postgres."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.modulos.atendimento import service as atendimento
from app.modulos.atendimento.service import abrir_reclamacao, abrir_servico, listar_abertas


class Relogio:
    def __init__(self, instante):
        self.instante = instante

    def agora(self):
        return self.instante


class Repo:
    def __init__(self, *, resultado=None, existente=None):
        self.resultado = resultado
        self.existente = existente
        self.marcacoes = []
        self.leituras = []

    def marcar_resolvida(
        self, conexao, *, id_hotel, id_solicitacao, id_usuario, resolvida_em
    ):
        self.marcacoes.append(
            {
                "id_hotel": id_hotel,
                "id_solicitacao": id_solicitacao,
                "id_usuario": id_usuario,
                "resolvida_em": resolvida_em,
            }
        )
        return self.resultado

    def ler_do_hotel(self, conexao, *, id_hotel, id_solicitacao):
        self.leituras.append(
            {"id_hotel": id_hotel, "id_solicitacao": id_solicitacao}
        )
        return self.existente


class Agendador:
    def __init__(self):
        self.chamadas = []

    def __call__(self, conexao, *, id_hotel, id_reserva, id_solicitacao, tipo):
        self.chamadas.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "id_solicitacao": id_solicitacao,
                "tipo": tipo,
            }
        )
        return "agendada"


def test_resolver_grava_snapshot_e_agenda_depois_do_update():
    instante = datetime(2026, 8, 18, 14, 32, tzinfo=UTC)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "id_reserva": 42,
            "tipo": "reclamacao",
            "status": "resolvida",
            "resolvida_em": instante,
            "id_usuario_responsavel": 3,
        }
    )
    agendador = Agendador()

    saida = atendimento.resolver(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        agendar_confirmacao=agendador,
        relogio=Relogio(instante),
    )

    assert repo.marcacoes == [
        {
            "id_hotel": 1,
            "id_solicitacao": 7,
            "id_usuario": 3,
            "resolvida_em": instante,
        }
    ]
    assert saida.status == "resolvida"
    assert saida.id_usuario_responsavel == 3
    assert saida.resolvida_em == instante
    assert saida.tipo == "reclamacao"
    assert agendador.chamadas == [
        {
            "id_hotel": 1,
            "id_reserva": 42,
            "id_solicitacao": 7,
            "tipo": "reclamacao",
        }
    ]


def test_resolver_consumo_agenda_recado_de_pedido_atendido():
    instante = datetime(2026, 8, 18, 14, 32, tzinfo=UTC)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "id_reserva": 42,
            "tipo": "consumo",
            "status": "resolvida",
            "resolvida_em": instante,
            "id_usuario_responsavel": 3,
        }
    )
    agendador = Agendador()

    saida = atendimento.resolver(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        agendar_confirmacao=agendador,
        relogio=Relogio(instante),
    )

    assert saida.tipo == "consumo"
    assert saida.status == "resolvida"
    assert agendador.chamadas[0]["tipo"] == "consumo"


def test_inexistente_no_hotel_nao_agenda():
    repo = Repo(resultado=None, existente=None)
    agendador = Agendador()

    with pytest.raises(atendimento.SolicitacaoNaoEncontrada):
        atendimento.resolver(
            object(),
            id_hotel=1,
            id_solicitacao=99,
            id_usuario=3,
            repositorio=repo,
            agendar_confirmacao=agendador,
        )

    assert agendador.chamadas == []


@pytest.mark.parametrize(
    "existente",
    [
        {"status": "resolvida", "tipo": "reclamacao"},
        {"status": "cancelada", "tipo": "servico"},
    ],
)
def test_recusa_nao_agenda(existente):
    repo = Repo(resultado=None, existente=existente)
    agendador = Agendador()

    with pytest.raises(atendimento.ResolucaoNaoPermitida):
        atendimento.resolver(
            object(),
            id_hotel=1,
            id_solicitacao=7,
            id_usuario=3,
            repositorio=repo,
            agendar_confirmacao=agendador,
        )

    assert agendador.chamadas == []


def test_segunda_chamada_recusa_e_nao_agenda_de_novo():
    instante = datetime(2026, 8, 18, 14, 32, tzinfo=UTC)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "id_reserva": 42,
            "tipo": "servico",
            "status": "resolvida",
            "resolvida_em": instante,
            "id_usuario_responsavel": 3,
        }
    )
    agendador = Agendador()
    atendimento.resolver(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        agendar_confirmacao=agendador,
        relogio=Relogio(instante),
    )
    repo.resultado = None
    repo.existente = {"status": "resolvida", "tipo": "servico"}

    with pytest.raises(atendimento.ResolucaoNaoPermitida):
        atendimento.resolver(
            object(),
            id_hotel=1,
            id_solicitacao=7,
            id_usuario=3,
            repositorio=repo,
            agendar_confirmacao=agendador,
            relogio=Relogio(instante),
        )

    assert len(agendador.chamadas) == 1


def test_resolver_loga_identificadores_sem_descricao(monkeypatch):
    instante = datetime(2026, 8, 18, 14, 32, tzinfo=UTC)
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(atendimento.logger, "info", fake_info)
    repo = Repo(
        resultado={
            "id_solicitacao": 7,
            "id_reserva": 42,
            "tipo": "reclamacao",
            "status": "resolvida",
            "resolvida_em": instante,
            "id_usuario_responsavel": 3,
        }
    )
    atendimento.resolver(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=repo,
        agendar_confirmacao=Agendador(),
        relogio=Relogio(instante),
    )
    repo.resultado = None
    repo.existente = {"status": "resolvida", "tipo": "reclamacao"}
    with pytest.raises(atendimento.ResolucaoNaoPermitida):
        atendimento.resolver(
            object(),
            id_hotel=1,
            id_solicitacao=7,
            id_usuario=3,
            repositorio=repo,
            agendar_confirmacao=Agendador(),
        )

    texto = " ".join(registros)
    assert "chamado_resolvido" in texto
    assert "resolucao_recusada" in texto
    assert "id_solicitacao=7" in texto
    assert "id_hotel=1" in texto
    assert "resultado=resolvido" in texto
    assert "resultado=ja_resolvida" in texto
    assert "ar nao gela" not in texto
    assert "Maria" not in texto


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


@pytest.mark.postgres
def test_resolver_persiste_e_some_da_lista(ambiente):
    id_a = ambiente.propriedade_a.id_hotel
    id_b = ambiente.propriedade_b.id_hotel
    instante = datetime(2026, 8, 18, 14, 32, tzinfo=UTC)
    agendador = Agendador()
    with ambiente.engine.begin() as conexao:
        reserva_a, msg_a = _reserva_e_mensagem(
            conexao, id_a, "ar nao gela", "5511910000101"
        )
        reserva_b, msg_b = _reserva_e_mensagem(
            conexao, id_b, "pedido do hotel b", "5511910000102"
        )
        id_sol = abrir_reclamacao(
            conexao,
            id_hotel=id_a,
            id_reserva=reserva_a,
            id_mensagem=msg_a,
            descricao="ar nao gela",
            numero_quarto="402",
            urgencia="alta",
            janela_preferencia=None,
        )
        abrir_servico(
            conexao,
            id_hotel=id_b,
            id_reserva=reserva_b,
            id_mensagem=msg_b,
            descricao="pedido do hotel b",
            numero_quarto=None,
            urgencia="baixa",
        )
        staff = ambiente.propriedade_a.usuarios["staff"]
        saida = atendimento.resolver(
            conexao,
            id_hotel=id_a,
            id_solicitacao=id_sol,
            id_usuario=staff.id_usuario,
            agendar_confirmacao=agendador,
            relogio=Relogio(instante),
        )
        abertas_a = listar_abertas(conexao, id_hotel=id_a)
        abertas_b = listar_abertas(conexao, id_hotel=id_b)

    assert saida.status == "resolvida"
    assert saida.id_usuario_responsavel == staff.id_usuario
    assert saida.resolvida_em == instante
    assert agendador.chamadas == [
        {
            "id_hotel": id_a,
            "id_reserva": reserva_a,
            "id_solicitacao": id_sol,
            "tipo": "reclamacao",
        }
    ]
    assert all(i["id_solicitacao"] != id_sol for i in abertas_a)
    assert any(i["descricao"] == "pedido do hotel b" for i in abertas_b)
