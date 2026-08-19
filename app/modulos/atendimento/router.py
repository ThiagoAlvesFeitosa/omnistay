"""Rotas da fila operacional de solicitacoes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modulos.acesso.dependencias import Conexao, exigir_operacao
from app.modulos.acesso.service import SessaoAtual
from app.modulos.atendimento import service as atendimento
from app.modulos.atendimento.schema import (
    LancamentoResposta,
    ListaConsumosPendentes,
    ListaSolicitacoes,
    ResolucaoResposta,
)

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


@roteador.get("/consumos/pendentes", response_model=ListaConsumosPendentes)
def listar_consumos_pendentes(
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("ler_solicitacao_atribuida"))
    ],
) -> ListaConsumosPendentes:
    itens = atendimento.listar_pendentes(conexao, id_hotel=sessao.id_hotel)
    return ListaConsumosPendentes(itens=itens)


def _mapear_lancamento(operar, conexao, sessao, id_solicitacao: int):
    try:
        return operar(
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
    except atendimento.LancamentoNaoPermitido as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=erro.detalhe,
        ) from erro


@roteador.post(
    "/solicitacoes/{id_solicitacao}/lancamento",
    response_model=LancamentoResposta,
)
def lancar_consumo(
    id_solicitacao: int,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("lancar_consumo"))],
) -> LancamentoResposta:
    return _mapear_lancamento(atendimento.lancar, conexao, sessao, id_solicitacao)


@roteador.post(
    "/solicitacoes/{id_solicitacao}/dispensa",
    response_model=LancamentoResposta,
)
def dispensar_consumo(
    id_solicitacao: int,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("lancar_consumo"))],
) -> LancamentoResposta:
    return _mapear_lancamento(
        atendimento.dispensar, conexao, sessao, id_solicitacao
    )
