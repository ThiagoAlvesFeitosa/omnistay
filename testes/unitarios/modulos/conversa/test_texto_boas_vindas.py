"""Montagem do recado curto de boas-vindas."""

import inspect

from app.modulos.conversa.texto_boas_vindas import montar_texto_boas_vindas


def test_texto_confirma_chegada_traz_tres_fatos_e_um_convite():
    texto = montar_texto_boas_vindas(
        nome_completo="Maria Silva",
        cafe="Cafe das 7h as 10h",
        wifi="rede Hotel, senha na recepcao",
        checkout="ate as 12h",
    )
    assert "chegada" in texto.lower()
    assert "Cafe da manha: Cafe das 7h as 10h" in texto
    assert "Wi-Fi: rede Hotel, senha na recepcao" in texto
    assert "Checkout: ate as 12h" in texto
    assert texto.count("?") == 1
    assert texto.rstrip().endswith("?") or "?" in texto.splitlines()[-1]
    assert "Silva" not in texto
    assert "Ola, Maria!" in texto
    for termo in ("oferta", "desconto", "promocao", "promoção"):
        assert termo not in texto.lower()


def test_funcao_nao_recebe_catalogo():
    parametros = inspect.signature(montar_texto_boas_vindas).parameters
    assert "catalogo" not in parametros
