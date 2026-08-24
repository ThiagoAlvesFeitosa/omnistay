"""Contratos de entrada e saida do catalogo da propriedade."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ItemCatalogoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categoria: str = Field(min_length=1, max_length=40)
    titulo: str = Field(min_length=1, max_length=160)
    conteudo: str = Field(min_length=1)


class ItemCatalogoPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, min_length=1, max_length=160)
    conteudo: str | None = Field(default=None, min_length=1)
    ativo: bool | None = None


class ItemCatalogoResposta(BaseModel):
    id_catalogo_item: int
    categoria: str
    titulo: str
    conteudo: str
    ativo: bool


class ItemCatalogoAtivo(BaseModel):
    id_catalogo_item: int
    categoria: str
    titulo: str
    conteudo: str


class ListaManutencaoResposta(BaseModel):
    itens: list[ItemCatalogoResposta]


class CatalogoAtivoResposta(BaseModel):
    horario: list[ItemCatalogoAtivo]
    cardapio: list[ItemCatalogoAtivo]
    servico: list[ItemCatalogoAtivo]
    programacao: list[ItemCatalogoAtivo]
    regra: list[ItemCatalogoAtivo]


class BoasVindasEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cafe: str = Field(min_length=1, max_length=255)
    wifi: str = Field(min_length=1, max_length=255)
    checkout: str = Field(min_length=1, max_length=255)


class BoasVindasResposta(BaseModel):
    cafe: str | None = None
    wifi: str | None = None
    checkout: str | None = None


class ItemVendavelEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=1, max_length=160)
    preco_atual: Decimal = Field(ge=0)


class ItemVendavelPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=1, max_length=160)
    preco_atual: Decimal | None = Field(default=None, ge=0)
    ativo: bool | None = None


class ItemVendavelResposta(BaseModel):
    id_item_vendavel: int
    nome: str
    preco_atual: Decimal
    ativo: bool
    atualizado_em: datetime


class ListaItensVendaveisResposta(BaseModel):
    itens: list[ItemVendavelResposta]


class ExecucaoRetencaoResposta(BaseModel):
    id_execucao: int
    executado_em: datetime
    mensagens_anonimizadas: int
    comentarios_anonimizados: int
    payloads_anonimizados: int
    descricoes_anonimizadas: int
    fichas_apagadas: int
    prazo_conteudo_ausente: bool
    prazo_ficha_ausente: bool


class ListaRetencaoResposta(BaseModel):
    execucoes: list[ExecucaoRetencaoResposta]
