"""Validacao e gravacao dos slots de boas-vindas."""

import pytest

from app.modulos.propriedade import service as propriedade


class Repo:
    def __init__(self, valores=None):
        self.valores = dict(valores or {})
        self.gravacoes = []

    def ler_parametros(self, conexao, id_hotel, chaves):
        return {
            chave: self.valores[chave]
            for chave in chaves
            if chave in self.valores
        }

    def upsert_parametro(self, conexao, id_hotel, chave, valor):
        self.gravacoes.append((chave, valor))
        self.valores[chave] = valor


SLOTS_ANTIGOS = {
    "boas_vindas_cafe": "antigo cafe",
    "boas_vindas_wifi": "antigo wifi",
    "boas_vindas_checkout": "antigo checkout",
    "boas_vindas_convite": "antigo convite",
}


def test_validacao_recusa_vazio_espacos_quebra_tab_e_tamanho():
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("cafe", "")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("cafe", "   ")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("cafe", "linha\nquebra")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("cafe", "linha\rquebra")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("cafe", "com\ttab")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("cafe", "a     b")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("cafe", "x" * 256)


def test_validacao_aceita_quatro_espacos_e_faz_strip():
    assert (
        propriedade.validar_texto_de_boas_vindas("wifi", "  senha    hotel  ")
        == "senha    hotel"
    )


def test_validacao_do_convite_reusa_o_mesmo_formato():
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("convite", "")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("convite", "linha\nquebra")
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.validar_texto_de_boas_vindas("convite", "x" * 256)
    assert (
        propriedade.validar_texto_de_boas_vindas(
            "convite", "  Pode perguntar sobre o spa.  "
        )
        == "Pode perguntar sobre o spa."
    )


def test_valor_invalido_nao_grava_nenhum_dos_quatro():
    repo = Repo(SLOTS_ANTIGOS)
    with pytest.raises(propriedade.DadosInvalidos) as erro:
        propriedade.gravar_textos_de_boas_vindas(
            object(),
            id_hotel=1,
            cafe="Cafe ok",
            wifi="Wi-Fi\nok",
            checkout="Checkout ok",
            convite="Pode perguntar sobre o spa.",
            repositorio=repo,
        )
    assert "wifi" in str(erro.value).lower()
    assert "Wi-Fi" not in str(erro.value)
    assert repo.gravacoes == []
    assert repo.valores["boas_vindas_cafe"] == "antigo cafe"
    assert repo.valores["boas_vindas_convite"] == "antigo convite"


def test_convite_invalido_nao_grava_nenhum_dos_quatro():
    repo = Repo(SLOTS_ANTIGOS)
    with pytest.raises(propriedade.DadosInvalidos) as erro:
        propriedade.gravar_textos_de_boas_vindas(
            object(),
            id_hotel=1,
            cafe="Cafe ok",
            wifi="Wi-Fi ok",
            checkout="Checkout ok",
            convite="Pode\nperguntar",
            repositorio=repo,
        )
    assert "convite" in str(erro.value).lower()
    assert "Pode" not in str(erro.value)
    assert repo.gravacoes == []
    assert repo.valores["boas_vindas_convite"] == "antigo convite"


def test_grava_convite_com_strip():
    repo = Repo(SLOTS_ANTIGOS)
    gravados = propriedade.gravar_textos_de_boas_vindas(
        object(),
        id_hotel=1,
        cafe="Cafe ok",
        wifi="Wi-Fi ok",
        checkout="Checkout ok",
        convite="  Pode perguntar sobre o spa.  ",
        repositorio=repo,
    )
    assert gravados["convite"] == "Pode perguntar sobre o spa."
    assert repo.valores["boas_vindas_convite"] == "Pode perguntar sobre o spa."
