"""Contratos de saida da fila de solicitacoes."""

from datetime import datetime
from decimal import Decimal

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
    valor_praticado: Decimal | None = None
    status_lancamento: str | None = None


class ListaSolicitacoes(BaseModel):
    itens: list[ItemSolicitacao]


class ResolucaoResposta(BaseModel):
    id_solicitacao: int
    tipo: str
    status: str
    resolvida_em: datetime
    id_usuario_responsavel: int
    confirmacao: str


class ItemConsumoPendente(BaseModel):
    id_solicitacao: int
    id_reserva: int
    descricao: str
    descricao_item: str
    numero_quarto: str | None
    valor_praticado: Decimal
    status_lancamento: str
    aberta_em: datetime
    resolvida_em: datetime | None


class ListaConsumosPendentes(BaseModel):
    itens: list[ItemConsumoPendente]


class LancamentoResposta(BaseModel):
    id_solicitacao: int
    status_lancamento: str
    id_usuario_lancamento: int
    lancado_em: datetime
