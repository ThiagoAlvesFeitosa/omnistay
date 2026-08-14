"""Regras do verificador de silencio, com relogio e dependencias falsas."""

from datetime import UTC, date, datetime, timedelta

from worker import agendador


T0 = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
CHECKIN_LONGE = date(2026, 8, 20)


def _reserva(**kwargs):
    base = {
        "id_reserva": 1,
        "id_hotel": 10,
        "data_checkin_prevista": CHECKIN_LONGE,
        "reenvio_realizado": False,
        "nome_completo": "Maria Silva",
    }
    base.update(kwargs)
    return base


class RepoPrazos:
    def __init__(self, ate="24", corte="12"):
        self.ate = ate
        self.corte = corte

    def ler_parametro(self, conexao, id_hotel, chave):
        return {
            "horas_ate_reenvio": self.ate,
            "horas_corte_antes_checkin": self.corte,
        }.get(chave)


def _preparar(monkeypatch, reservas, *, tem_resposta=False, coleta_em=T0, agenda=None):
    agenda = agenda if agenda is not None else []
    marcados = []
    reenvios = []
    monkeypatch.setattr(
        agendador.hospedagem_service,
        "listar_reservas_aguardando_cadastro",
        lambda conexao: reservas,
    )
    monkeypatch.setattr(
        agendador.conversa_service,
        "tem_mensagem_recebida",
        lambda conexao, id_reserva: tem_resposta,
    )
    monkeypatch.setattr(
        agendador.conversa_service,
        "instante_coleta_enviada",
        lambda conexao, id_reserva: coleta_em,
    )
    monkeypatch.setattr(
        agendador.conversa_service,
        "agendar_lembrete",
        lambda conexao, **kwargs: agenda.append(kwargs) or 99,
    )
    monkeypatch.setattr(
        agendador.hospedagem_service,
        "marcar_reenvio_realizado",
        lambda conexao, **kwargs: reenvios.append(kwargs),
    )
    monkeypatch.setattr(
        agendador.hospedagem_service,
        "marcar_sem_cadastro_previo",
        lambda conexao, **kwargs: marcados.append(kwargs),
    )
    return agenda, reenvios, marcados


def test_apos_prazo_agenda_um_lembrete(monkeypatch):
    agenda, reenvios, marcados = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=T0 + timedelta(hours=25),
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 1
    assert len(agenda) == 1
    assert reenvios[0]["id_reserva"] == 1
    assert marcados == []


def test_segunda_verificacao_nao_agenda_outro(monkeypatch):
    agenda, _, _ = _preparar(
        monkeypatch, [_reserva(reenvio_realizado=True)]
    )
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=T0 + timedelta(hours=48),
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 0
    assert agenda == []


def test_silencio_menor_que_o_prazo_nao_agenda(monkeypatch):
    agenda, _, _ = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=T0 + timedelta(hours=2),
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 0
    assert agenda == []


def test_coleta_ainda_nao_enviada_nao_agenda(monkeypatch):
    agenda, _, marcados = _preparar(monkeypatch, [_reserva()], coleta_em=None)
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=T0 + timedelta(hours=25),
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 0
    assert agenda == []
    assert marcados == []


def test_corte_atingido_marca_e_nao_agenda(monkeypatch):
    agenda, _, marcados = _preparar(
        monkeypatch,
        [_reserva(data_checkin_prevista=date(2026, 8, 3))],
    )
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=datetime(2026, 8, 2, 18, 0, tzinfo=UTC),
        repositorio_propriedade=RepoPrazos(corte="12"),
    )
    assert n == 1
    assert agenda == []
    assert marcados[0]["id_reserva"] == 1


def test_data_de_entrada_vencida_marca(monkeypatch):
    _, _, marcados = _preparar(
        monkeypatch,
        [_reserva(data_checkin_prevista=date(2026, 7, 1))],
    )
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 1
    assert marcados


def test_resposta_nao_agenda_nem_marca(monkeypatch):
    agenda, _, marcados = _preparar(
        monkeypatch, [_reserva()], tem_resposta=True
    )
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=T0 + timedelta(hours=25),
        repositorio_propriedade=RepoPrazos(),
    )
    assert n == 0
    assert agenda == []
    assert marcados == []


def test_prazo_ausente_nao_usa_numero_magico(monkeypatch):
    agenda, _, marcados = _preparar(monkeypatch, [_reserva()])

    class Vazio:
        def ler_parametro(self, conexao, id_hotel, chave):
            return None

    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=T0 + timedelta(hours=100),
        repositorio_propriedade=Vazio(),
    )
    assert n == 0
    assert agenda == []
    assert marcados == []


def test_prazo_menor_dispara_antes(monkeypatch):
    agenda, _, _ = _preparar(monkeypatch, [_reserva()])
    n = agendador.verificar_cadastros_pendentes(
        object(),
        agora=T0 + timedelta(hours=2),
        repositorio_propriedade=RepoPrazos(ate="1"),
    )
    assert n == 1
    assert len(agenda) == 1
