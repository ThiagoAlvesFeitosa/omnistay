"""Logs de concorrentes registram identificadores, nao nome nem URL."""

from app.modulos.mercado import service as mercado
from testes.suporte.concorrentes import NOME, URL_FONTE


class Repo:
    def __init__(self):
        self.item = {
            "id_concorrente": 4,
            "id_hotel": 1,
            "nome": NOME,
            "url_fonte": URL_FONTE,
            "ativo": True,
        }

    def inserir(self, conexao, *, id_hotel, nome, url_fonte):
        return dict(self.item)

    def existe_fonte(self, conexao, *, id_hotel, url_fonte, exceto_id=None):
        return False

    def atualizar(
        self,
        conexao,
        *,
        id_hotel,
        id_concorrente,
        nome=None,
        url_fonte=None,
        ativo=None,
    ):
        if ativo is not None:
            self.item["ativo"] = ativo
        if nome is not None:
            self.item["nome"] = nome
        return dict(self.item)


def _capturar(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(mercado.logger, "info", fake_info)
    return registros


def _proibido(texto: str) -> None:
    assert NOME not in texto
    assert URL_FONTE not in texto
    assert "exemplo.com" not in texto


def test_criar_loga_identificadores_sem_nome_nem_url(monkeypatch):
    registros = _capturar(monkeypatch)
    mercado.criar_concorrente(
        object(),
        id_hotel=1,
        nome=NOME,
        url_fonte=URL_FONTE,
        repositorio=Repo(),
    )
    texto = " ".join(registros)
    assert "id_concorrente=4" in texto
    assert "id_hotel=1" in texto
    _proibido(texto)


def test_editar_desativar_reativar_sem_nome_nem_url(monkeypatch):
    repo = Repo()
    registros = _capturar(monkeypatch)
    mercado.alterar_concorrente(
        object(), id_hotel=1, id_concorrente=4, nome=NOME, repositorio=repo
    )
    mercado.alterar_concorrente(
        object(), id_hotel=1, id_concorrente=4, ativo=False, repositorio=repo
    )
    mercado.alterar_concorrente(
        object(), id_hotel=1, id_concorrente=4, ativo=True, repositorio=repo
    )
    texto = " ".join(registros)
    assert "concorrente_editar" in texto
    assert "concorrente_desativar" in texto
    assert "concorrente_reativar" in texto
    assert "id_concorrente=4" in texto
    _proibido(texto)


def test_coleta_loga_identificadores_sem_url_preco_nem_nota(monkeypatch):
    from datetime import UTC, datetime
    from app.adaptadores.fonte_falsa import FonteFalsa
    from testes.suporte.coleta_mercado import PRECO_FIXTURE

    class RepoColeta:
        def obter_ativo(self, conexao, *, id_hotel, id_concorrente):
            return {
                "id_concorrente": 4,
                "id_hotel": 1,
                "url_fonte": URL_FONTE,
            }

        def ultima_coleta(self, conexao, *, id_concorrente):
            return None

        def inserir_coleta(self, conexao, **kwargs):
            return kwargs

        def criado_em_do_trabalho(self, conexao, *, id_trabalho):
            return datetime(2026, 8, 21, tzinfo=UTC)

    registros = _capturar(monkeypatch)
    monkeypatch.setattr(
        mercado.fila_repository,
        "marcar_concluido",
        lambda conexao, id_trabalho: None,
    )
    mercado.processar_trabalho_coletar_mercado(
        object(),
        trabalho={
            "id_trabalho": 1,
            "id_hotel": 1,
            "payload": {"id_concorrente": 4},
        },
        fonte=FonteFalsa(),
        agora=datetime(2026, 8, 21, 12, tzinfo=UTC),
        repositorio=RepoColeta(),
    )
    texto = " ".join(registros)
    assert "id_concorrente=4" in texto
    assert "id_hotel=1" in texto
    assert "coleta_sucesso" in texto
    _proibido(texto)
    assert str(PRECO_FIXTURE) not in texto
    assert "4.50" not in texto


def test_painel_e_historico_logam_ids_sem_preco_nota_nem_url(monkeypatch):
    from datetime import UTC, datetime, timedelta
    from testes.suporte.coleta_mercado import PRECO_FIXTURE as PRECO

    coletado = datetime(2026, 8, 21, 11, tzinfo=UTC)
    sucesso = {
        "id_coleta": 1,
        "id_concorrente": 4,
        "preco": PRECO,
        "nota_media": None,
        "sucesso": True,
        "coletado_em": coletado,
    }

    class RepoPainel:
        def listar_manutencao(self, conexao, *, id_hotel):
            return [self.item]

        def ultimos_sucessos(self, conexao, *, id_hotel):
            return {4: sucesso}

        def ultimas_linhas(self, conexao, *, id_hotel):
            return {4: sucesso}

        def obter(self, conexao, *, id_hotel, id_concorrente):
            return self.item

        def listar_serie(self, conexao, *, id_hotel, id_concorrente):
            return [sucesso]

    repo = RepoPainel()
    repo.item = {
        "id_concorrente": 4,
        "id_hotel": 1,
        "nome": NOME,
        "url_fonte": URL_FONTE,
        "ativo": True,
    }
    registros = _capturar(monkeypatch)
    mercado.ler_painel(
        object(),
        id_hotel=1,
        agora=coletado + timedelta(hours=1),
        repositorio=repo,
        ler_parametro=lambda conexao, id_hotel, chave: "24",
    )
    mercado.ler_historico(
        object(), id_hotel=1, id_concorrente=4, repositorio=repo
    )
    texto = " ".join(registros)
    assert "painel" in texto
    assert "historico" in texto
    assert "id_hotel=1" in texto
    assert "id_concorrente=4" in texto
    _proibido(texto)
    assert str(PRECO) not in texto
    assert "4.50" not in texto
