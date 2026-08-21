"""Rotas de cadastro de concorrentes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modulos.acesso.dependencias import Conexao, exigir_operacao
from app.modulos.acesso.service import SessaoAtual
from app.modulos.mercado import service as mercado
from app.modulos.mercado.schema import (
    ConcorrenteEntrada,
    ConcorrentePatch,
    ConcorrenteResposta,
    HistoricoMercadoResposta,
    ListaFontesAtivasResposta,
    ListaManutencaoResposta,
    PainelMercadoResposta,
)

roteador = APIRouter(tags=["mercado"])


@roteador.post(
    "/concorrentes",
    response_model=ConcorrenteResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_concorrente(
    entrada: ConcorrenteEntrada,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("alterar_concorrentes"))],
) -> ConcorrenteResposta:
    try:
        criado = mercado.criar_concorrente(
            conexao,
            id_hotel=sessao.id_hotel,
            nome=entrada.nome,
            url_fonte=entrada.url_fonte,
        )
    except mercado.DadosInvalidos as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro
    except mercado.FonteDuplicada as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe concorrente com esta fonte.",
        ) from erro
    return criado.para_resposta()


@roteador.get("/concorrentes", response_model=ListaManutencaoResposta)
def listar_manutencao(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_concorrentes"))],
) -> ListaManutencaoResposta:
    itens = mercado.listar_manutencao(conexao, id_hotel=sessao.id_hotel)
    return ListaManutencaoResposta(
        concorrentes=[item.para_resposta() for item in itens]
    )


@roteador.get("/concorrentes/ativos", response_model=ListaFontesAtivasResposta)
def listar_fontes_ativas(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_concorrentes"))],
) -> ListaFontesAtivasResposta:
    fontes = mercado.listar_fontes_ativas(conexao, id_hotel=sessao.id_hotel)
    return ListaFontesAtivasResposta(
        fontes=[item.para_fonte_ativa() for item in fontes]
    )


@roteador.patch(
    "/concorrentes/{id_concorrente}",
    response_model=ConcorrenteResposta,
)
def alterar_concorrente(
    id_concorrente: int,
    entrada: ConcorrentePatch,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("alterar_concorrentes"))],
) -> ConcorrenteResposta:
    try:
        alterado = mercado.alterar_concorrente(
            conexao,
            id_hotel=sessao.id_hotel,
            id_concorrente=id_concorrente,
            nome=entrada.nome,
            url_fonte=entrada.url_fonte,
            ativo=entrada.ativo,
        )
    except mercado.DadosInvalidos as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro
    except mercado.ConcorrenteNaoEncontrado as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concorrente nao encontrado.",
        ) from erro
    except mercado.FonteDuplicada as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe concorrente com esta fonte.",
        ) from erro
    return alterado.para_resposta()


@roteador.get("/mercado", response_model=PainelMercadoResposta)
def consultar_painel(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_mercado"))],
) -> PainelMercadoResposta:
    painel = mercado.ler_painel(conexao, id_hotel=sessao.id_hotel)
    return painel.para_resposta()


@roteador.get(
    "/mercado/concorrentes/{id_concorrente}",
    response_model=HistoricoMercadoResposta,
)
def consultar_historico(
    id_concorrente: int,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_mercado"))],
) -> HistoricoMercadoResposta:
    try:
        historico = mercado.ler_historico(
            conexao,
            id_hotel=sessao.id_hotel,
            id_concorrente=id_concorrente,
        )
    except mercado.ConcorrenteNaoEncontrado as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concorrente nao encontrado.",
        ) from erro
    return historico.para_resposta()
