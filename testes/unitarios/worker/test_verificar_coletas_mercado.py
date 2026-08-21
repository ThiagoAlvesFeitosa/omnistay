"""Varredura de coletas de mercado: vencimento, inativo e periodicidade."""

from datetime import UTC, datetime, timedelta

from worker import agendador
from testes.suporte.coleta_mercado import CHAVE_PERIODICIDADE, URL_FONTE

AGORA = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)


class RepoPrazos:
    def __init__(self, por_hotel=None, padrao="24"):
        self.por_hotel = por_hotel or {}
        self.padrao = padrao
        self.leituras = []

    def ler_parametro(self, conexao, id_hotel, chave):
        self.leituras.append((id_hotel, chave))
        if chave != CHAVE_PERIODICIDADE:
            return None
        if id_hotel in self.por_hotel:
            return self.por_hotel[id_hotel]
        return self.padrao


class RepoFontes:
    def __init__(self, fontes, ultimas=None):
        self.fontes = fontes
        self.ultimas = ultimas or {}

    def listar_ativos_de_todos(self, conexao):
        return list(self.fontes)

    def ultima_coleta(self, conexao, *, id_concorrente):
        return self.ultimas.get(id_concorrente)


def _enfileirar(fila):
    def _fn(conexao, *, id_hotel, id_concorrente):
        fila.append({"id_hotel": id_hotel, "id_concorrente": id_concorrente})
        return len(fila)

    return _fn


def test_fonte_ativa_nunca_coletada_enfileira():
    fila = []
    n = agendador.verificar_coletas_mercado(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        repositorio_mercado=RepoFontes(
            [{"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}]
        ),
        enfileirar=_enfileirar(fila),
    )
    assert n == 1
    assert fila == [{"id_hotel": 10, "id_concorrente": 7}]


def test_fonte_inativa_nao_aparece_na_varredura():
    fila = []
    n = agendador.verificar_coletas_mercado(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        repositorio_mercado=RepoFontes([]),
        enfileirar=_enfileirar(fila),
    )
    assert n == 0
    assert fila == []


def test_janela_ainda_aberta_nao_enfileira():
    fila = []
    n = agendador.verificar_coletas_mercado(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        repositorio_mercado=RepoFontes(
            [{"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}],
            ultimas={
                7: {"coletado_em": AGORA - timedelta(hours=12), "sucesso": True}
            },
        ),
        enfileirar=_enfileirar(fila),
    )
    assert n == 0


def test_janela_vencida_enfileira_de_novo():
    fila = []
    n = agendador.verificar_coletas_mercado(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(),
        repositorio_mercado=RepoFontes(
            [{"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}],
            ultimas={
                7: {"coletado_em": AGORA - timedelta(hours=24), "sucesso": False}
            },
        ),
        enfileirar=_enfileirar(fila),
    )
    assert n == 1


def test_periodicidade_ausente_nao_enfileira_nem_inventa_padrao(monkeypatch):
    from app.modulos.mercado import service as mercado

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(mercado.logger, "info", fake_info)
    fila = []
    n = agendador.verificar_coletas_mercado(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(padrao=None),
        repositorio_mercado=RepoFontes(
            [{"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}]
        ),
        enfileirar=_enfileirar(fila),
    )
    assert n == 0
    assert fila == []
    texto = " ".join(registros)
    assert "periodicidade_ausente" in texto
    assert "id_hotel=10" in texto


def test_dois_hoteis_respeitam_periodicidades_distintas():
    fila = []
    n = agendador.verificar_coletas_mercado(
        object(),
        agora=AGORA,
        repositorio_propriedade=RepoPrazos(por_hotel={1: "12", 2: "48"}, padrao=None),
        repositorio_mercado=RepoFontes(
            [
                {"id_concorrente": 1, "id_hotel": 1, "url_fonte": URL_FONTE},
                {"id_concorrente": 2, "id_hotel": 2, "url_fonte": URL_FONTE},
            ],
            ultimas={
                1: {"coletado_em": AGORA - timedelta(hours=13)},
                2: {"coletado_em": AGORA - timedelta(hours=24)},
            },
        ),
        enfileirar=_enfileirar(fila),
    )
    assert n == 1
    assert fila == [{"id_hotel": 1, "id_concorrente": 1}]
