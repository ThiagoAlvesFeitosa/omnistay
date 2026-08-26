"""Contratos internos de entrada do webhook e da tela de simulacao."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class EventoEntrada:
    id_externo: str
    telefone_origem: str
    texto: str
    tem_texto_utilizavel: bool
    id_mensagem_canal: str | None = None
    instante_origem: datetime | None = None


class TurnoHospedeEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str = ""
    id_externo: str | None = Field(default=None, max_length=80)


class ItemConversaSimulador(BaseModel):
    id_reserva: int
    status: str
    nome_titular: str
    telefone_contato: str


class ListaConversasSimulador(BaseModel):
    modo: str
    conversas: list[ItemConversaSimulador]


class MensagemSimulador(BaseModel):
    id_mensagem: int
    direcao: str
    conteudo: str
    status_envio: str | None
    enviada_em: datetime


class FioConversaSimulador(BaseModel):
    id_reserva: int
    status: str
    nome_titular: str
    telefone_contato: str
    mensagens: list[MensagemSimulador]


class TurnoHospedeResposta(BaseModel):
    status: str
    id_mensagem: int | None = None
    id_reserva: int
