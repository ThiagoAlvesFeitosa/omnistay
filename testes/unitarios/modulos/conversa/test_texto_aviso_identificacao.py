"""Recado quando a identificacao do item nao fecha sozinha."""

from app.modulos.conversa.texto_aviso_identificacao import montar_aviso_identificacao
from testes.suporte.consumo import proibicoes_do_recado_consumo


def test_aviso_de_identificacao_pede_conferencia_sem_valor():
    texto = montar_aviso_identificacao(nome_completo="Maria Silva")
    assert "Maria" in texto
    assert "Silva" not in texto
    compacto = texto.casefold()
    assert "recepcao" in compacto or "confer" in compacto
    assert "r$" not in compacto
    for palavra in proibicoes_do_recado_consumo():
        assert palavra not in compacto
