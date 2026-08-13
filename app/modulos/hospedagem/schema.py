"""Contratos de entrada e saida do modulo de hospedagem."""

from datetime import date

from pydantic import BaseModel, Field


class ReservaEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=160)
    telefone: str = Field(min_length=1, max_length=40)
    data_checkin_prevista: date
    data_checkout_prevista: date


class ReservaResposta(BaseModel):
    id_reserva: int
    id_hotel: int
    nome: str
    telefone_contato: str
    data_checkin_prevista: date
    data_checkout_prevista: date
    status: str


class ItemFilaDoDia(BaseModel):
    id_reserva: int
    nome: str | None
    telefone_contato: str
    data_checkin_prevista: date
    data_checkout_prevista: date
    status: str
    ficha_completa: bool | None
    chegada_nao_confirmada: bool
    status_envio_coleta: str | None = None


class FilaDoDiaResposta(BaseModel):
    itens: list[ItemFilaDoDia]


class ContagemChegadasResposta(BaseModel):
    quantidade: int
