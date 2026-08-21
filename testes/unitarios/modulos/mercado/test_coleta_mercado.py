"""Processador de coleta: sucesso, falha, diretiva e isolamento de canais."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.adaptadores.fonte_falsa import FonteFalsa
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.mercado import service as mercado
from app.portas.fonte_publica import (
    DESFECHO_ENCONTRADO,
    DESFECHO_EXIGE_AUTENTICACAO,
    DESFECHO_INDISPONIVEL,
    DESFECHO_SEM_DADO,
    DIRETIVA_AUSENTE,
    DIRETIVA_RECUSA,
    ResultadoPublico,
)
from testes.suporte.coleta_mercado import (
    IDENTIDADE_COLETOR,
    NOTA_FIXTURE,
    PRECO_FIXTURE,
    URL_FONTE,
)

AGORA = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
TRABALHO = {
    "id_trabalho": 9,
    "id_hotel": 10,
    "payload": {"id_concorrente": 7},
}


class RepoColeta:
    def __init__(self, ficha, ultima=None, criado_em=None):
        self.ficha = ficha
        self.ultima = ultima
        self.criado_em = criado_em or AGORA - timedelta(minutes=1)
        self.inseridas = []

    def obter_ativo(self, conexao, *, id_hotel, id_concorrente):
        return self.ficha

    def ultima_coleta(self, conexao, *, id_concorrente):
        if self.inseridas:
            return self.inseridas[-1]
        return self.ultima

    def inserir_coleta(self, conexao, **kwargs):
        self.inseridas.append(kwargs)
        return kwargs

    def criado_em_do_trabalho(self, conexao, *, id_trabalho):
        return self.criado_em


def _concluir(monkeypatch, fila=None):
    dest = fila if fila is not None else []
    monkeypatch.setattr(
        mercado.fila_repository,
        "marcar_concluido",
        lambda conexao, id_trabalho: dest.append(("concluido", id_trabalho)),
    )
    monkeypatch.setattr(
        mercado.fila_repository,
        "marcar_falha",
        lambda conexao, **kwargs: dest.append(("falha", kwargs)),
    )
    return dest


def test_permite_e_encontrado_grava_sucesso(monkeypatch):
    dest = _concluir(monkeypatch)
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
    )
    fonte = FonteFalsa()
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert len(repo.inseridas) == 1
    assert repo.inseridas[0]["sucesso"] is True
    assert repo.inseridas[0]["preco"] == PRECO_FIXTURE
    assert repo.inseridas[0]["nota_media"] == NOTA_FIXTURE
    assert dest == [("concluido", 9)]
    assert fonte.chamadas_coletar == [URL_FONTE]


def test_fonte_inativa_conclui_sem_inserir(monkeypatch):
    dest = _concluir(monkeypatch)
    repo = RepoColeta(None)
    fonte = FonteFalsa()
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert repo.inseridas == []
    assert fonte.chamadas_coletar == []
    assert dest == [("concluido", 9)]


def test_reclaim_com_coleta_ja_feita_nao_revisita(monkeypatch):
    dest = _concluir(monkeypatch)
    criado = AGORA - timedelta(minutes=5)
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE},
        ultima={"coletado_em": criado + timedelta(minutes=1), "sucesso": True},
        criado_em=criado,
    )
    fonte = FonteFalsa()
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert repo.inseridas == []
    assert fonte.chamadas_coletar == []
    assert dest == [("concluido", 9)]


def test_sem_dado_grava_falha_e_conclui_sem_backoff(monkeypatch):
    dest = _concluir(monkeypatch)
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
    )
    fonte = FonteFalsa()
    fonte.configurar(
        URL_FONTE,
        resultado=ResultadoPublico(desfecho=DESFECHO_SEM_DADO),
    )
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert repo.inseridas[0]["sucesso"] is False
    assert repo.inseridas[0]["preco"] is None
    assert dest == [("concluido", 9)]


def test_indisponivel_e_login_gravam_falha(monkeypatch):
    dest = _concluir(monkeypatch)
    for desfecho in (DESFECHO_INDISPONIVEL, DESFECHO_EXIGE_AUTENTICACAO):
        repo = RepoColeta(
            {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
        )
        fonte = FonteFalsa()
        fonte.configurar(
            URL_FONTE, resultado=ResultadoPublico(desfecho=desfecho)
        )
        mercado.processar_trabalho_coletar_mercado(
            object(),
            trabalho=TRABALHO,
            fonte=fonte,
            agora=AGORA,
            repositorio=repo,
        )
        assert repo.inseridas[0]["sucesso"] is False
    assert dest == [("concluido", 9), ("concluido", 9)]


def test_preco_zero_e_sucesso(monkeypatch):
    _concluir(monkeypatch)
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
    )
    fonte = FonteFalsa()
    fonte.configurar(
        URL_FONTE,
        resultado=ResultadoPublico(
            desfecho=DESFECHO_ENCONTRADO, preco=Decimal("0"), nota_media=None
        ),
    )
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert repo.inseridas[0]["sucesso"] is True
    assert repo.inseridas[0]["preco"] == Decimal("0")


def test_so_nota_ou_so_preco_e_sucesso(monkeypatch):
    _concluir(monkeypatch)
    for resultado in (
        ResultadoPublico(desfecho=DESFECHO_ENCONTRADO, preco=PRECO_FIXTURE),
        ResultadoPublico(desfecho=DESFECHO_ENCONTRADO, nota_media=NOTA_FIXTURE),
    ):
        repo = RepoColeta(
            {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
        )
        fonte = FonteFalsa()
        fonte.configurar(URL_FONTE, resultado=resultado)
        mercado.processar_trabalho_coletar_mercado(
            object(),
            trabalho=TRABALHO,
            fonte=fonte,
            agora=AGORA,
            repositorio=repo,
        )
        assert repo.inseridas[0]["sucesso"] is True


def test_diretiva_recusada_nao_visita_e_grava_falha(monkeypatch):
    _concluir(monkeypatch)
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
    )
    fonte = FonteFalsa()
    fonte.configurar(URL_FONTE, diretiva=DIRETIVA_RECUSA)
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert fonte.chamadas_coletar == []
    assert repo.inseridas[0]["sucesso"] is False


def test_diretiva_ausente_nao_e_permissao(monkeypatch):
    _concluir(monkeypatch)
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
    )
    fonte = FonteFalsa()
    fonte.configurar(URL_FONTE, diretiva=DIRETIVA_AUSENTE)
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert fonte.chamadas_coletar == []
    assert repo.inseridas[0]["sucesso"] is False


def test_identidade_do_coletor_e_registrada(monkeypatch):
    _concluir(monkeypatch)
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
    )
    fonte = FonteFalsa()
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=fonte,
        agora=AGORA,
        repositorio=repo,
    )
    assert fonte.ultima_identidade == IDENTIDADE_COLETOR


def test_processador_nao_chama_mensageria(monkeypatch):
    _concluir(monkeypatch)
    gateway = MensageriaFalsa()
    repo = RepoColeta(
        {"id_concorrente": 7, "id_hotel": 10, "url_fonte": URL_FONTE}
    )
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho=TRABALHO,
        fonte=FonteFalsa(),
        agora=AGORA,
        repositorio=repo,
    )
    assert gateway.envios == []


def test_servico_nao_importa_cliente_http():
    import inspect

    fonte = inspect.getsource(mercado)
    assert "urllib.request" not in fonte
    assert "httpx" not in fonte
