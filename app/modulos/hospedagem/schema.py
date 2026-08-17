"""Contratos de entrada e saida do modulo de hospedagem."""

from datetime import date, datetime

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
    boas_vindas_nao_enviadas: bool = False
    precisa_atendimento_humano: bool = False
    status_envio_coleta: str | None = None
    estado_cadastro: str | None = None


class FilaDoDiaResposta(BaseModel):
    itens: list[ItemFilaDoDia]


class ContagemChegadasResposta(BaseModel):
    quantidade: int


class FichaTitularResposta(BaseModel):
    id_reserva: int
    id_hospede: int
    ficha_completa: bool
    status_reserva: str
    estado_cadastro: str | None
    nome_completo: str
    profissao: str | None = None
    data_nascimento: date | None = None
    tipo_documento: str | None = None
    numero_documento: str | None = None
    endereco: str | None = None
    cep: str | None = None
    cidade: str | None = None
    telefone: str


class ChegadaResposta(BaseModel):
    id_reserva: int
    status: str
    checkin_em: datetime
    boas_vindas: str
