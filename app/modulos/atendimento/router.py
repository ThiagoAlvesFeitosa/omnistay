"""Rotas da fila operacional de solicitacoes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modulos.acesso.dependencias import Conexao, exigir_operacao
from app.modulos.acesso.service import SessaoAtual
from app.modulos.atendimento import service as atendimento
from app.modulos.atendimento.schema import ListaSolicitacoes, ResolucaoResposta

roteador = APIRouter(tags=["atendimento"])


@roteador.get("/solicitacoes", response_model=ListaSolicitacoes)
def listar_solicitacoes(
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("ler_solicitacao_atribuida"))
    ],
) -> ListaSolicitacoes:
    itens = atendimento.listar_abertas(conexao, id_hotel=sessao.id_hotel)
    return ListaSolicitacoes(itens=itens)


@roteador.post(
    "/solicitacoes/{id_solicitacao}/resolucao",
    response_model=ResolucaoResposta,
)
def resolver_solicitacao(
    id_solicitacao: int,
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("resolver_solicitacao"))
    ],
) -> ResolucaoResposta:
    try:
        return atendimento.resolver(
            conexao,
            id_hotel=sessao.id_hotel,
            id_solicitacao=id_solicitacao,
            id_usuario=sessao.id_usuario,
        )
    except atendimento.SolicitacaoNaoEncontrada as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitacao nao encontrada.",
        ) from erro
    except atendimento.ResolucaoNaoPermitida as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=erro.detalhe,
        ) from erro
