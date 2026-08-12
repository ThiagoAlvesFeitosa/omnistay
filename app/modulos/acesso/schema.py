"""Contratos de entrada e saida do modulo de acesso. Senha e token nunca saem."""

from datetime import datetime

from pydantic import BaseModel, Field


class CredenciaisDeEntrada(BaseModel):
    email: str = Field(min_length=3, max_length=160)
    senha: str = Field(min_length=1)
    dispositivo: str | None = Field(default=None, max_length=120)


class SessaoCriada(BaseModel):
    id_usuario: int
    nome: str
    perfil: str
    expira_em: datetime


class SessaoAtualResposta(BaseModel):
    id_sessao: int
    id_usuario: int
    nome: str
    perfil: str
    dispositivo: str | None
    expira_em: datetime


class SessaoListada(BaseModel):
    id_sessao: int
    id_usuario: int
    nome_usuario: str
    perfil: str
    dispositivo: str | None
    criada_em: datetime
    expira_em: datetime


class UsuarioEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=160)
    perfil: str
    senha: str = Field(min_length=12)


class UsuarioResposta(BaseModel):
    id_usuario: int
    nome: str
    email: str
    perfil: str
    ativo: bool
