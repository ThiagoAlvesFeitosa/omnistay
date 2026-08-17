"""Validacao e gravacao dos tres slots de entrada."""

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


def test_valor_invalido_nao_grava_nenhum_dos_tres():
    repo = Repo(
        {
            "boas_vindas_cafe": "antigo cafe",
            "boas_vindas_wifi": "antigo wifi",
            "boas_vindas_checkout": "antigo checkout",
        }
    )
    with pytest.raises(propriedade.DadosInvalidos) as erro:
        propriedade.gravar_textos_de_boas_vindas(
            object(),
            id_hotel=1,
            cafe="Cafe ok",
            wifi="Wi-Fi\nok",
            checkout="Checkout ok",
            repositorio=repo,
        )
    assert "wifi" in str(erro.value).lower()
    assert "Wi-Fi" not in str(erro.value)
    assert repo.gravacoes == []
    assert repo.valores["boas_vindas_cafe"] == "antigo cafe"
