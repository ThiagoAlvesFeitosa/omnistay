"""O dominio de conversa nao escolhe o adaptador de mensageria."""

from pathlib import Path


def test_servico_de_conversa_nao_importa_adaptadores_de_mensageria():
    caminho = Path("app/modulos/conversa/service.py")
    texto = caminho.read_text(encoding="utf-8")
    for nome in (
        "mensageria_simulada",
        "mensageria_whatsapp",
        "mensageria_falsa",
    ):
        assert nome not in texto
