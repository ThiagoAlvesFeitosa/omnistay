"""Contratos de entrada e saida do cadastro de concorrentes e do painel."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ConcorrenteEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=1, max_length=120)
    url_fonte: str = Field(min_length=1, max_length=400)


class ConcorrentePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=1, max_length=120)
    url_fonte: str | None = Field(default=None, min_length=1, max_length=400)
    ativo: bool | None = None


class ConcorrenteResposta(BaseModel):
    id_concorrente: int
    nome: str
    url_fonte: str
    ativo: bool


class FonteAtivaResposta(BaseModel):
    id_concorrente: int
    nome: str
    url_fonte: str


class ListaManutencaoResposta(BaseModel):
    concorrentes: list[ConcorrenteResposta]


class ListaFontesAtivasResposta(BaseModel):
    fontes: list[FonteAtivaResposta]


class UltimoSucessoResposta(BaseModel):
    preco: Decimal | None
    nota_media: Decimal | None
    coletado_em: datetime


class UltimaFalhaResposta(BaseModel):
    coletado_em: datetime


class ItemPainelResposta(BaseModel):
    id_concorrente: int
    nome: str
    ativo: bool
    situacao: str
    ultimo_sucesso: UltimoSucessoResposta | None
    ultima_falha: UltimaFalhaResposta | None


class PainelMercadoResposta(BaseModel):
    periodicidade_horas: int | None
    concorrentes: list[ItemPainelResposta]


class PontoColetaResposta(BaseModel):
    id_coleta: int
    sucesso: bool
    preco: Decimal | None
    nota_media: Decimal | None
    coletado_em: datetime


class HistoricoMercadoResposta(BaseModel):
    id_concorrente: int
    nome: str
    ativo: bool
    coletas: list[PontoColetaResposta]
