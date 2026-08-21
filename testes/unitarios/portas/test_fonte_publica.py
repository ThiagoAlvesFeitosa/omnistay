"""Protocolo de fonte publica declara diretiva e coleta."""

import inspect

from app.portas.fonte_publica import FontePublica


def test_protocolo_declara_consultar_diretiva_e_coletar_publico():
    diretiva = inspect.signature(FontePublica.consultar_diretiva).parameters
    coletar = inspect.signature(FontePublica.coletar_publico).parameters
    assert "url_fonte" in diretiva
    assert "url_fonte" in coletar
