"""Montagem do recado curto de boas-vindas."""

import inspect

from app.modulos.conversa.texto_boas_vindas import montar_texto_boas_vindas

CONVITE = "Pode perguntar sobre o spa."
FRASE_ANTIGA = "Quer saber mais alguma coisa da sua estadia?"


def test_texto_confirma_chegada_traz_tres_fatos_e_convite_da_casa():
    texto = montar_texto_boas_vindas(
        nome_completo="Maria Silva",
        cafe="Cafe das 7h as 10h",
        wifi="rede Hotel, senha na recepcao",
        checkout="ate as 12h",
        convite=CONVITE,
    )
    linhas = texto.splitlines()
    assert "chegada" in texto.lower()
    assert "Cafe da manha: Cafe das 7h as 10h" in texto
    assert "Wi-Fi: rede Hotel, senha na recepcao" in texto
    assert "Checkout: ate as 12h" in texto
    assert linhas[-1] == CONVITE
    assert FRASE_ANTIGA not in texto
    assert "Silva" not in texto
    assert "Ola, Maria!" in texto
    for termo in ("oferta", "desconto", "promocao", "promoção"):
        assert termo not in texto.lower()


def test_funcao_nao_recebe_catalogo_aviso_nem_tom():
    parametros = inspect.signature(montar_texto_boas_vindas).parameters
    assert "catalogo" not in parametros
    assert "aviso" not in parametros
    assert "tom" not in parametros
    assert "personalidade" not in parametros
    assert "convite" in parametros


def test_texto_traz_aviso_imediatamente_antes_do_convite():
    texto = montar_texto_boas_vindas(
        nome_completo="Maria Silva",
        cafe="Cafe das 7h as 10h",
        wifi="rede Hotel, senha na recepcao",
        checkout="ate as 12h",
        convite=CONVITE,
    )
    linhas = texto.splitlines()
    baixo = texto.lower()
    assert "assistente virtual" in baixo
    assert "recepcao" in baixo
    assert linhas[-1] == CONVITE
    idx_aviso = next(
        i for i, linha in enumerate(linhas) if "assistente virtual" in linha.lower()
    )
    assert idx_aviso == len(linhas) - 2
    assert FRASE_ANTIGA not in texto
    assert "Silva" not in texto
