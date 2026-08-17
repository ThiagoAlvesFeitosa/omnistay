"""Elegibilidade da recuperacao de boas-vindas, com relogio controlado."""

from datetime import UTC, datetime, timedelta

from worker import agendador


AGORA = datetime(2026, 8, 18, 0, 5, tzinfo=UTC)


def _reserva(**kwargs):
    base = {
        "id_reserva": 1,
        "id_hotel": 10,
        "checkin_em": AGORA - timedelta(minutes=40),
        "nome_completo": "Maria Silva",
    }
    base.update(kwargs)
    return base


class RepoPrazos:
    def __init__(self, validade="12"):
        self.validade = validade

    def ler_parametro(self, conexao, id_hotel, chave):
        if chave == "horas_validade_boas_vindas":
            return self.validade
        return None


def _preparar(monkeypatch, reservas, *, desfecho="agendada"):
    agenda = []
    monkeypatch.setattr(
        agendador.hospedagem_service,
        "listar_hospedados_sem_boas_vindas",
        lambda conexao: reservas,
    )
    monkeypatch.setattr(
        agendador.conversa_service,
        "agendar_boas_vindas",
        lambda conexao, **kwargs: agenda.append(kwargs) or desfecho,
    )
    return agenda


def test_agenda_apenas_dentro_da_janela(monkeypatch):
    recente = _reserva(id_reserva=1, checkin_em=AGORA - timedelta(minutes=40))
    antiga = _reserva(id_reserva=2, checkin_em=AGORA - timedelta(days=3))
    sem_instante = _reserva(id_reserva=3, checkin_em=None)
    agenda = _preparar(monkeypatch, [recente, antiga, sem_instante])
    n = agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 1
    assert [item["id_reserva"] for item in agenda] == [1]


def test_slot_invalido_nao_agenda_e_permanece_candidata(monkeypatch):
    agenda = _preparar(
        monkeypatch, [_reserva()], desfecho="nao_enviada_slot_ausente"
    )
    n = agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 0
    assert len(agenda) == 1


def test_prazo_ausente_nao_supoe_doze(monkeypatch):
    agenda = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(validade=None),
    )
    assert n == 0
    assert agenda == []


def test_prazo_nao_inteiro_positivo_pula_o_hotel(monkeypatch):
    agenda = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(validade="abc"),
    )
    assert n == 0
    assert agenda == []


def test_segunda_passagem_nao_agenda_de_novo(monkeypatch):
    primeira = _preparar(monkeypatch, [_reserva()])
    n1 = agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
    )
    assert n1 == 1
    segunda = _preparar(monkeypatch, [])
    n2 = agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
    )
    assert n2 == 0
    assert segunda == []
    assert len(primeira) == 1


def test_virada_de_dia_usa_checkin_em_nao_calendario(monkeypatch):
    meia_noite = datetime(2026, 8, 18, 0, 5, tzinfo=UTC)
    recente = _reserva(
        id_reserva=1,
        checkin_em=meia_noite - timedelta(minutes=35),
    )
    fora = _reserva(
        id_reserva=2,
        checkin_em=meia_noite - timedelta(hours=13),
    )
    agenda = _preparar(monkeypatch, [recente, fora])
    n = agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=meia_noite,
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 1
    assert agenda[0]["id_reserva"] == 1


def test_recuperacao_loga_identificadores_sem_conteudo(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(agendador.logger, "info", fake_info)
    _preparar(monkeypatch, [_reserva()])
    agendador.verificar_boas_vindas_pendentes(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
    )
    texto = " ".join(registros)
    assert "boas_vindas_recuperadas" in texto
    assert "id_reserva=1" in texto
    assert "Maria" not in texto
    assert "Silva" not in texto
