"""Logs de catalogo registram identificadores, nao o texto do fato."""

from app.modulos.propriedade import service as catalogo


class Repo:
    def __init__(self):
        self.item = {
            "id_catalogo_item": 4,
            "id_hotel": 1,
            "categoria": "horario",
            "titulo": "Cafe secreto",
            "conteudo": "nao deve aparecer no log",
            "ativo": True,
        }

    def inserir_item(self, conexao, *, id_hotel, categoria, titulo, conteudo):
        return dict(self.item)

    def atualizar_item(
        self,
        conexao,
        *,
        id_hotel,
        id_catalogo_item,
        titulo=None,
        conteudo=None,
        ativo=None,
    ):
        if ativo is not None:
            self.item["ativo"] = ativo
        if titulo is not None:
            self.item["titulo"] = titulo
        return dict(self.item)


def _capturar(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(catalogo.logger, "info", fake_info)
    return registros


def _texto_proibido(texto: str) -> None:
    assert "Cafe secreto" not in texto
    assert "nao deve aparecer no log" not in texto


def test_criar_loga_identificadores_sem_texto(monkeypatch):
    registros = _capturar(monkeypatch)
    catalogo.criar_item(
        object(),
        id_hotel=1,
        categoria="horario",
        titulo="Cafe secreto",
        conteudo="nao deve aparecer no log",
        repositorio=Repo(),
    )
    texto = " ".join(registros)
    assert "id_catalogo_item=4" in texto
    assert "id_hotel=1" in texto
    assert "categoria=horario" in texto
    _texto_proibido(texto)


def test_editar_desativar_reativar_sem_texto(monkeypatch):
    repo = Repo()
    registros = _capturar(monkeypatch)
    catalogo.alterar_item(
        object(),
        id_hotel=1,
        id_catalogo_item=4,
        titulo="Cafe secreto",
        repositorio=repo,
    )
    catalogo.alterar_item(
        object(), id_hotel=1, id_catalogo_item=4, ativo=False, repositorio=repo
    )
    catalogo.alterar_item(
        object(), id_hotel=1, id_catalogo_item=4, ativo=True, repositorio=repo
    )
    texto = " ".join(registros)
    assert "catalogo_alterado" in texto
    assert "catalogo_desativado" in texto
    assert "catalogo_reativado" in texto
    assert "id_catalogo_item=4" in texto
    _texto_proibido(texto)
