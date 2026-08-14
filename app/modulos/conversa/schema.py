"""Contratos internos de entrada do webhook."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventoEntrada:
    id_externo: str
    telefone_origem: str
    texto: str
    tem_texto_utilizavel: bool
    id_mensagem_canal: str | None = None
