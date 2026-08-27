"""Validacao e gravacao da descricao de tom da assistente."""

import logging

import pytest

from app.modulos.propriedade import service as propriedade
from app.modulos.propriedade.service import TAMANHO_MAXIMO_PERSONALIDADE


class Repo:
    def __init__(self, valores=None):
        self.valores = dict(valores or {})
        self.gravacoes = []

    def ler_parametro(self, conexao, id_hotel, chave):
        return self.valores.get(chave)

    def upsert_parametro(self, conexao, id_hotel, chave, valor):
        self.gravacoes.append((chave, valor))
        self.valores[chave] = valor


def test_grava_texto_com_strip():
    repo = Repo()
    gravado = propriedade.gravar_personalidade_assistente(
        object(),
        id_hotel=1,
        texto="  seja breve  ",
        repositorio=repo,
    )
    assert gravado == "seja breve"
    assert repo.gravacoes == [("personalidade_assistente", "seja breve")]


def test_vazio_e_espacos_viram_voz_padrao():
    repo = Repo(valores={"personalidade_assistente": "antigo"})
    assert (
        propriedade.gravar_personalidade_assistente(
            object(), id_hotel=1, texto="", repositorio=repo
        )
        == ""
    )
    assert (
        propriedade.gravar_personalidade_assistente(
            object(), id_hotel=1, texto="   ", repositorio=repo
        )
        == ""
    )
    assert repo.valores["personalidade_assistente"] == ""


def test_leitura_sem_chave_devolve_vazio():
    assert (
        propriedade.ler_personalidade_assistente(
            object(), id_hotel=1, repositorio=Repo()
        )
        == ""
    )


def test_quinhentos_grava_e_quinhentos_e_um_recusa():
    repo = Repo()
    ok = "x" * TAMANHO_MAXIMO_PERSONALIDADE
    assert (
        propriedade.gravar_personalidade_assistente(
            object(), id_hotel=1, texto=ok, repositorio=repo
        )
        == ok
    )
    with pytest.raises(propriedade.DadosInvalidos) as erro:
        propriedade.gravar_personalidade_assistente(
            object(),
            id_hotel=1,
            texto="y" * (TAMANHO_MAXIMO_PERSONALIDADE + 1),
            repositorio=repo,
        )
    assert "longo" in str(erro.value).lower()
    assert repo.valores["personalidade_assistente"] == ok
    assert len(repo.gravacoes) == 1


def test_quebra_de_linha_e_tabulacao_sao_aceitas():
    repo = Repo()
    texto = "breve\te caloroso\nsegunda linha"
    gravado = propriedade.gravar_personalidade_assistente(
        object(), id_hotel=1, texto=texto, repositorio=repo
    )
    assert gravado == texto


def test_nulo_e_recusado_sem_gravar():
    repo = Repo(valores={"personalidade_assistente": "ok"})
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.gravar_personalidade_assistente(
            object(), id_hotel=1, texto="a\x00b", repositorio=repo
        )
    assert repo.gravacoes == []
    assert repo.valores["personalidade_assistente"] == "ok"


def test_log_de_gravacao_nao_traz_o_tom(caplog):
    repo = Repo()
    marca = "NAO_DEVE_APARECER_NO_LOG_TOM_SECRETO"
    with caplog.at_level(logging.INFO):
        propriedade.gravar_personalidade_assistente(
            object(), id_hotel=1, texto=marca, repositorio=repo
        )
    conjunto = caplog.text
    assert marca not in conjunto
    assert "personalidade_assistente_gravada" in conjunto
    assert "id_hotel=1" in conjunto
