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
