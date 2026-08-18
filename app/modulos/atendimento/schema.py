"""Contratos de saida da fila de solicitacoes."""

from datetime import datetime

from pydantic import BaseModel


class ItemSolicitacao(BaseModel):
    id_solicitacao: int
    id_reserva: int
    tipo: str
    descricao: str
    numero_quarto: str | None
    urgencia: str
    status: str
    aberta_em: datetime
    janela_preferencia: str | None
    destaque_tempo_excedido: bool


class ListaSolicitacoes(BaseModel):
    itens: list[ItemSolicitacao]


class ResolucaoResposta(BaseModel):
    id_solicitacao: int
    tipo: str
    status: str
    resolvida_em: datetime
    id_usuario_responsavel: int
    confirmacao: str
