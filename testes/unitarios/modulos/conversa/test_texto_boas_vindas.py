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


def test_texto_traz_aviso_de_assistente_virtual():
    texto = montar_texto_boas_vindas(
        nome_completo="Maria Silva",
        cafe="Cafe das 7h as 10h",
        wifi="rede Hotel, senha na recepcao",
        checkout="ate as 12h",
    )
    baixo = texto.lower()
    assert "assistente virtual" in baixo
    assert "recepcao" in baixo
    assert texto.count("?") == 1
    linhas = texto.splitlines()
    assert "?" in linhas[-1]
    idx_aviso = next(
        i for i, linha in enumerate(linhas) if "assistente virtual" in linha.lower()
    )
    idx_convite = next(i for i, linha in enumerate(linhas) if "?" in linha)
    assert idx_aviso < idx_convite
    assert "Cafe da manha: Cafe das 7h as 10h" in texto
    assert "Wi-Fi: rede Hotel, senha na recepcao" in texto
    assert "Checkout: ate as 12h" in texto
    assert "Silva" not in texto
    parametros = inspect.signature(montar_texto_boas_vindas).parameters
    assert "aviso" not in parametros
