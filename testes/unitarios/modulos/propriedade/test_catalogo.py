"""Regras do catalogo com repositorio falso."""

from dataclasses import dataclass, field

import pytest

from app.modulos.propriedade import service as catalogo

CATEGORIAS = ("horario", "cardapio", "servico", "programacao", "regra")


@dataclass
class Repositorio:
    itens: list = field(default_factory=list)
    inserts: list = field(default_factory=list)
    proximo: int = 1

    def inserir_item(self, conexao, *, id_hotel, categoria, titulo, conteudo):
        item = {
            "id_catalogo_item": self.proximo,
            "id_hotel": id_hotel,
            "categoria": categoria,
            "titulo": titulo,
            "conteudo": conteudo,
            "ativo": True,
        }
        self.proximo += 1
        self.itens.append(item)
        self.inserts.append(item)
        return item

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
        for item in self.itens:
            if (
                item["id_catalogo_item"] == id_catalogo_item
                and item["id_hotel"] == id_hotel
            ):
                if titulo is not None:
                    item["titulo"] = titulo
                if conteudo is not None:
                    item["conteudo"] = conteudo
                if ativo is not None:
                    item["ativo"] = ativo
                return dict(item)
        return None

    def listar_manutencao(self, conexao, *, id_hotel):
        filtrados = [dict(i) for i in self.itens if i["id_hotel"] == id_hotel]
        return sorted(
            filtrados, key=lambda i: (i["categoria"], i["id_catalogo_item"])
        )

    def listar_ativos(self, conexao, *, id_hotel):
        filtrados = [
            dict(i)
            for i in self.itens
            if i["id_hotel"] == id_hotel and i["ativo"]
        ]
        return sorted(
            filtrados, key=lambda i: (i["categoria"], i["id_catalogo_item"])
        )


def _criar(repo, **kwargs):
    padrao = {
        "id_hotel": 1,
        "categoria": "horario",
        "titulo": "Cafe da manha",
        "conteudo": "7h as 10h",
    }
    padrao.update(kwargs)
    return catalogo.criar_item(object(), repositorio=repo, **padrao)


def test_criar_nas_cinco_categorias_grava_ativo_no_hotel_da_sessao():
    repo = Repositorio()
    for categoria in CATEGORIAS:
        item = _criar(repo, categoria=categoria, titulo=categoria)
        assert item.categoria == categoria
        assert item.ativo is True
        assert item.id_hotel == 1
    assert [i["categoria"] for i in repo.inserts] == list(CATEGORIAS)
    assert all(i["id_hotel"] == 1 for i in repo.inserts)


def test_trim_em_titulo_e_conteudo():
    repo = Repositorio()
    item = _criar(repo, titulo="  Cafe  ", conteudo="  7h  ")
    assert item.titulo == "Cafe"
    assert item.conteudo == "7h"
    assert repo.inserts[0]["titulo"] == "Cafe"
    assert repo.inserts[0]["conteudo"] == "7h"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"titulo": "   "},
        {"conteudo": "   "},
        {"categoria": "spa"},
        {"titulo": "x" * 161},
    ],
)
def test_entrada_invalida_nao_grava(kwargs):
    repo = Repositorio()
    with pytest.raises(catalogo.DadosInvalidos):
        _criar(repo, **kwargs)
    assert repo.inserts == []


def _alterar(repo, id_catalogo_item, **kwargs):
    padrao = {"id_hotel": 1, "id_catalogo_item": id_catalogo_item}
    padrao.update(kwargs)
    return catalogo.alterar_item(object(), repositorio=repo, **padrao)


def test_alterar_titulo_e_conteudo_mantem_ativo():
    repo = Repositorio()
    criado = _criar(repo)
    item = _alterar(
        repo, criado.id_catalogo_item, titulo="Novo", conteudo="Atualizado"
    )
    assert item.titulo == "Novo"
    assert item.conteudo == "Atualizado"
    assert item.ativo is True


def test_desativar_e_reativar():
    repo = Repositorio()
    criado = _criar(repo)
    inativo = _alterar(repo, criado.id_catalogo_item, ativo=False)
    assert inativo.ativo is False
    ativo = _alterar(repo, criado.id_catalogo_item, ativo=True)
    assert ativo.ativo is True


def test_patch_vazio_e_categoria_sao_recusados():
    repo = Repositorio()
    criado = _criar(repo)
    with pytest.raises(catalogo.DadosInvalidos):
        _alterar(repo, criado.id_catalogo_item)
    with pytest.raises(catalogo.DadosInvalidos):
        _alterar(repo, criado.id_catalogo_item, categoria="cardapio")
    assert repo.itens[0]["titulo"] == "Cafe da manha"


def test_alterar_inexistente_levanta_nao_encontrado():
    repo = Repositorio()
    with pytest.raises(catalogo.ItemNaoEncontrado):
        _alterar(repo, 99, titulo="X")


def test_catalogo_ativo_omite_inativos_e_agrupa_cinco_chaves():
    repo = Repositorio()
    for categoria in CATEGORIAS:
        _criar(repo, categoria=categoria, titulo=categoria)
    inativo = _criar(repo, categoria="horario", titulo="Antigo")
    _alterar(repo, inativo.id_catalogo_item, ativo=False)

    agrupado = catalogo.ler_catalogo_ativo(object(), id_hotel=1, repositorio=repo)
    assert set(agrupado.keys()) == set(CATEGORIAS)
    assert all(isinstance(agrupado[c], list) for c in CATEGORIAS)
    ids_ativos = [item.id_catalogo_item for item in agrupado["horario"]]
    assert inativo.id_catalogo_item not in ids_ativos
    assert len(agrupado["horario"]) == 1
    assert len(agrupado["cardapio"]) == 1


def test_catalogo_ativo_vazio_tem_cinco_listas():
    agrupado = catalogo.ler_catalogo_ativo(
        object(), id_hotel=1, repositorio=Repositorio()
    )
    assert set(agrupado.keys()) == set(CATEGORIAS)
    assert all(agrupado[c] == [] for c in CATEGORIAS)
