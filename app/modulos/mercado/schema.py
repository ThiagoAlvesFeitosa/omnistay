"""Contratos de entrada e saida do cadastro de concorrentes."""

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
