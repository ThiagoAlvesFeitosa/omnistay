"""Varredura do pulso: segundo dia, prazo, reclamacao e isolamento."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text

from worker import agendador
from testes.suporte.pulso import montar_hospedado_para_pulso

AGORA = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


def _reserva(**kwargs):
    base = {
        "id_reserva": 1,
        "id_hotel": 10,
        "checkin_em": datetime(2026, 8, 18, 15, 0, tzinfo=UTC),
        "data_checkout_prevista": date(2026, 8, 21),
        "nome_completo": "Marina Duarte",
    }
    base.update(kwargs)
    return base


class RepoPrazos:
    def __init__(self, por_hotel=None, padrao="24"):
        self.por_hotel = por_hotel or {}
        self.padrao = padrao

    def ler_parametro(self, conexao, id_hotel, chave):
        if chave != agendador.CHAVE_MINIMO_PULSO:
            return None
        if id_hotel in self.por_hotel:
            return self.por_hotel[id_hotel]
        return self.padrao


def _preparar(monkeypatch, reservas, *, reclamacao=None):
    agenda = []
    monkeypatch.setattr(
        agendador.hospedagem_service,
        "listar_hospedados_sem_pulso",
        lambda conexao: reservas,
    )
    monkeypatch.setattr(
        agendador.conversa_service,
        "agendar_pulso",
        lambda conexao, **kwargs: agenda.append(kwargs) or "agendada",
    )
    abertas = reclamacao if reclamacao is not None else set()

    def tem_reclamacao(conexao, *, id_reserva):
        return id_reserva in abertas

    return agenda, tem_reclamacao


def test_agenda_no_dia_seguinte_ao_checkin(monkeypatch):
    agenda, tem = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        tem_reclamacao_aberta=tem,
    )
    assert n == 1
    assert [item["id_reserva"] for item in agenda] == [1]


def test_mesmo_dia_do_checkin_nao_agenda(monkeypatch):
    agenda, tem = _preparar(
        monkeypatch,
        [_reserva(checkin_em=AGORA - timedelta(hours=3))],
    )
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        tem_reclamacao_aberta=tem,
    )
    assert n == 0
    assert agenda == []


def test_reclamacao_aberta_suprime_e_servico_nao(monkeypatch):
    aberta, tem_aberta = _preparar(
        monkeypatch, [_reserva(id_reserva=1)], reclamacao={1}
    )
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        tem_reclamacao_aberta=tem_aberta,
    )
    assert n == 0
    assert aberta == []

    agenda, tem_livre = _preparar(monkeypatch, [_reserva(id_reserva=2)])
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        tem_reclamacao_aberta=tem_livre,
    )
    assert n == 1


def test_uma_noite_no_segundo_dia_nao_agenda(monkeypatch):
    agenda, tem = _preparar(
        monkeypatch,
        [_reserva(data_checkout_prevista=date(2026, 8, 19))],
    )
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        tem_reclamacao_aberta=tem,
    )
    assert n == 0
    assert agenda == []


def test_checkout_amanha_com_minimo_vinte_e_quatro_agenda(monkeypatch):
    agenda, tem = _preparar(
        monkeypatch,
        [_reserva(data_checkout_prevista=date(2026, 8, 20))],
    )
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        tem_reclamacao_aberta=tem,
    )
    assert n == 1


def test_horas_restantes_abaixo_do_minimo_nao_agenda(monkeypatch):
    agenda, tem = _preparar(
        monkeypatch,
        [_reserva(data_checkout_prevista=date(2026, 8, 20))],
    )
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(padrao="48"),
        tem_reclamacao_aberta=tem,
    )
    assert n == 0
    assert agenda == []


def test_dois_hoteis_so_o_minimo_suficiente_agenda(monkeypatch):
    reservas = [
        _reserva(
            id_reserva=1,
            id_hotel=10,
            data_checkout_prevista=date(2026, 8, 20),
        ),
        _reserva(
            id_reserva=2,
            id_hotel=20,
            data_checkout_prevista=date(2026, 8, 20),
        ),
    ]
    agenda, tem = _preparar(monkeypatch, reservas)
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(
            por_hotel={10: "24", 20: "48"},
            padrao="24",
        ),
        tem_reclamacao_aberta=tem,
    )
    assert n == 1
    assert [item["id_reserva"] for item in agenda] == [1]


def test_prazo_ausente_nao_inventa_minimo(monkeypatch):
    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(agendador.logger, "info", fake_info)
    agenda, tem = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(padrao=None),
        tem_reclamacao_aberta=tem,
    )
    texto = " ".join(registros)
    assert n == 0
    assert agenda == []
    assert "prazo_ausente" in texto
    assert "Como esta" not in texto


def test_prazo_invalido_loga_sem_texto_da_pergunta(monkeypatch):
    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(agendador.logger, "info", fake_info)
    agenda, tem = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_pulsos_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(padrao="abc"),
        tem_reclamacao_aberta=tem,
    )
    texto = " ".join(registros)
    assert n == 0
    assert "prazo_ausente" in texto
    assert "estadia" not in texto


@pytest.mark.postgres
def test_varredura_grava_um_trabalho_e_mensagem_pendente(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000401"
        )
        n = agendador.verificar_pulsos_pendentes(conexao)
        tipos = conexao.execute(
            text(
                "SELECT tipo, status FROM trabalho"
                " WHERE (payload->>'id_reserva')::bigint = :r"
                " AND tipo = 'enviar_pulso'"
            ),
            {"r": id_reserva},
        ).mappings().all()
        mensagens = conexao.execute(
            text(
                "SELECT status_envio, conteudo FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
            ),
            {"r": id_reserva},
        ).mappings().all()
    assert n == 1
    assert len(tipos) == 1
    assert tipos[0]["status"] == "pendente"
    assert len(mensagens) == 1
    assert mensagens[0]["status_envio"] == "pendente"
    assert "?" in mensagens[0]["conteudo"]
