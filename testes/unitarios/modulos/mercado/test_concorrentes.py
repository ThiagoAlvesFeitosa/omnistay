"""Cadastro de concorrentes com repositorio falso."""

from dataclasses import dataclass, field

import pytest

from app.modulos.mercado import service as mercado
from testes.suporte.concorrentes import NOME, URL_FONTE


@dataclass
class Repositorio:
    itens: list = field(default_factory=list)
    proximo: int = 1
    inserts: int = 0

    def inserir(self, conexao, *, id_hotel, nome, url_fonte):
        self.inserts += 1
        item = {
            "id_concorrente": self.proximo,
            "id_hotel": id_hotel,
            "nome": nome,
            "url_fonte": url_fonte,
            "ativo": True,
        }
        self.proximo += 1
        self.itens.append(item)
        return dict(item)

    def existe_fonte(self, conexao, *, id_hotel, url_fonte, exceto_id=None):
        alvo = url_fonte.strip().casefold()
        for item in self.itens:
            if (
                item["id_hotel"] == id_hotel
                and item["url_fonte"].strip().casefold() == alvo
                and item["id_concorrente"] != exceto_id
            ):
                return True
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
        for item in self.itens:
            if item["id_concorrente"] == id_concorrente and item["id_hotel"] == id_hotel:
                if nome is not None:
                    item["nome"] = nome
                if url_fonte is not None:
                    item["url_fonte"] = url_fonte
                if ativo is not None:
                    item["ativo"] = ativo
                return dict(item)
        return None

    def listar_manutencao(self, conexao, *, id_hotel):
        return sorted(
            [dict(i) for i in self.itens if i["id_hotel"] == id_hotel],
            key=lambda i: (i["nome"], i["id_concorrente"]),
        )

    def listar_ativos(self, conexao, *, id_hotel):
        return [
            {
                "id_concorrente": i["id_concorrente"],
                "nome": i["nome"],
                "url_fonte": i["url_fonte"],
            }
            for i in sorted(
                (i for i in self.itens if i["id_hotel"] == id_hotel and i["ativo"]),
                key=lambda i: (i["nome"], i["id_concorrente"]),
            )
        ]


def test_criar_grava_ativo_no_hotel_da_sessao():
    repo = Repositorio()
    criado = mercado.criar_concorrente(
        object(), id_hotel=7, nome=NOME, url_fonte=URL_FONTE, repositorio=repo
    )
    assert criado.id_hotel == 7
    assert criado.ativo is True
    assert criado.nome == NOME
    assert criado.url_fonte == URL_FONTE
    assert repo.inserts == 1
    assert repo.itens[0]["id_hotel"] == 7


def test_criar_faz_trim_em_nome_e_url():
    repo = Repositorio()
    criado = mercado.criar_concorrente(
        object(),
        id_hotel=1,
        nome=f"  {NOME}  ",
        url_fonte=f"  {URL_FONTE}  ",
        repositorio=repo,
    )
    assert criado.nome == NOME
    assert criado.url_fonte == URL_FONTE


@pytest.mark.parametrize(
    "nome,url",
    [
        ("   ", URL_FONTE),
        (NOME, "   "),
        (NOME, "www.exemplo.com/hotel"),
        (NOME, "mailto:x@y.com"),
        (NOME, "https://user:senha@www.exemplo.com/hotel"),
        ("A" * 121, URL_FONTE),
    ],
)
def test_criar_recusa_entrada_invalida_sem_insert(nome, url):
    repo = Repositorio()
    with pytest.raises(mercado.DadosInvalidos):
        mercado.criar_concorrente(
            object(), id_hotel=1, nome=nome, url_fonte=url, repositorio=repo
        )
    assert repo.inserts == 0


def test_criar_fonte_duplicada_mesmo_inativa_recusa_sem_insert():
    repo = Repositorio()
    mercado.criar_concorrente(
        object(), id_hotel=1, nome=NOME, url_fonte=URL_FONTE, repositorio=repo
    )
    repo.itens[0]["ativo"] = False
    with pytest.raises(mercado.FonteDuplicada):
        mercado.criar_concorrente(
            object(),
            id_hotel=1,
            nome="Outro",
            url_fonte=URL_FONTE.upper(),
            repositorio=repo,
        )
    assert repo.inserts == 1


def test_alterar_nome_e_url_mantem_ativo():
    repo = Repositorio()
    criado = mercado.criar_concorrente(
        object(), id_hotel=1, nome=NOME, url_fonte=URL_FONTE, repositorio=repo
    )
    alterado = mercado.alterar_concorrente(
        object(),
        id_hotel=1,
        id_concorrente=criado.id_concorrente,
        nome="Novo nome",
        url_fonte="https://www.exemplo.com/novo",
        repositorio=repo,
    )
    assert alterado.nome == "Novo nome"
    assert alterado.url_fonte == "https://www.exemplo.com/novo"
    assert alterado.ativo is True


def test_desativar_e_reativar():
    repo = Repositorio()
    criado = mercado.criar_concorrente(
        object(), id_hotel=1, nome=NOME, url_fonte=URL_FONTE, repositorio=repo
    )
    inativo = mercado.alterar_concorrente(
        object(),
        id_hotel=1,
        id_concorrente=criado.id_concorrente,
        ativo=False,
        repositorio=repo,
    )
    assert inativo.ativo is False
    reativado = mercado.alterar_concorrente(
        object(),
        id_hotel=1,
        id_concorrente=criado.id_concorrente,
        ativo=True,
        repositorio=repo,
    )
    assert reativado.ativo is True


def test_alterar_corpo_vazio_e_id_inexistente_recusam():
    repo = Repositorio()
    criado = mercado.criar_concorrente(
        object(), id_hotel=1, nome=NOME, url_fonte=URL_FONTE, repositorio=repo
    )
    with pytest.raises(mercado.DadosInvalidos):
        mercado.alterar_concorrente(
            object(),
            id_hotel=1,
            id_concorrente=criado.id_concorrente,
            repositorio=repo,
        )
    with pytest.raises(mercado.ConcorrenteNaoEncontrado):
        mercado.alterar_concorrente(
            object(),
            id_hotel=1,
            id_concorrente=99,
            nome="X",
            repositorio=repo,
        )


def test_alterar_url_para_fonte_de_outro_recusa():
    repo = Repositorio()
    mercado.criar_concorrente(
        object(), id_hotel=1, nome=NOME, url_fonte=URL_FONTE, repositorio=repo
    )
    outro = mercado.criar_concorrente(
        object(),
        id_hotel=1,
        nome="Outro",
        url_fonte="https://www.exemplo.com/outro",
        repositorio=repo,
    )
    with pytest.raises(mercado.FonteDuplicada):
        mercado.alterar_concorrente(
            object(),
            id_hotel=1,
            id_concorrente=outro.id_concorrente,
            url_fonte=URL_FONTE,
            repositorio=repo,
        )


def test_fontes_ativas_omit_inativos_e_vazio_nao_e_erro():
    repo = Repositorio()
    ativo = mercado.criar_concorrente(
        object(), id_hotel=1, nome=NOME, url_fonte=URL_FONTE, repositorio=repo
    )
    outro = mercado.criar_concorrente(
        object(),
        id_hotel=1,
        nome="Outro",
        url_fonte="https://www.exemplo.com/outro",
        repositorio=repo,
    )
    mercado.alterar_concorrente(
        object(),
        id_hotel=1,
        id_concorrente=outro.id_concorrente,
        ativo=False,
        repositorio=repo,
    )
    fontes = mercado.listar_fontes_ativas(object(), id_hotel=1, repositorio=repo)
    assert [f.id_concorrente for f in fontes] == [ativo.id_concorrente]
    assert fontes[0].nome == NOME
    assert "ativo" not in fontes[0].para_fonte_ativa().model_dump()
    assert mercado.listar_fontes_ativas(object(), id_hotel=2, repositorio=repo) == []
