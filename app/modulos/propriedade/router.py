"""Rotas de catalogo da propriedade."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modulos.acesso.dependencias import Conexao, exigir_operacao
from app.modulos.acesso.service import SessaoAtual
from app.modulos.propriedade import service as catalogo
from app.modulos.propriedade.schema import (
    BoasVindasEntrada,
    BoasVindasResposta,
    CatalogoAtivoResposta,
    ItemCatalogoAtivo,
    ItemCatalogoEntrada,
    ItemCatalogoPatch,
    ItemCatalogoResposta,
    ListaManutencaoResposta,
)

roteador = APIRouter(tags=["propriedade"])


@roteador.post(
    "/catalogo",
    response_model=ItemCatalogoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_item(
    entrada: ItemCatalogoEntrada,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("alterar_catalogo"))],
) -> ItemCatalogoResposta:
    try:
        criado = catalogo.criar_item(
            conexao,
            id_hotel=sessao.id_hotel,
            categoria=entrada.categoria,
            titulo=entrada.titulo,
            conteudo=entrada.conteudo,
        )
    except catalogo.DadosInvalidos as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro
    return criado.para_resposta()


@roteador.get("/catalogo", response_model=ListaManutencaoResposta)
def listar_manutencao(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_catalogo"))],
) -> ListaManutencaoResposta:
    itens = catalogo.listar_manutencao(conexao, id_hotel=sessao.id_hotel)
    return ListaManutencaoResposta(itens=[item.para_resposta() for item in itens])


def _item_ativo(item: catalogo.ItemDeCatalogo) -> ItemCatalogoAtivo:
    return ItemCatalogoAtivo(
        id_catalogo_item=item.id_catalogo_item,
        categoria=item.categoria,
        titulo=item.titulo,
        conteudo=item.conteudo,
    )


@roteador.get("/catalogo/ativo", response_model=CatalogoAtivoResposta)
def listar_ativo(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_catalogo"))],
) -> CatalogoAtivoResposta:
    agrupado = catalogo.ler_catalogo_ativo(conexao, id_hotel=sessao.id_hotel)
    return CatalogoAtivoResposta(
        horario=[_item_ativo(i) for i in agrupado["horario"]],
        cardapio=[_item_ativo(i) for i in agrupado["cardapio"]],
        servico=[_item_ativo(i) for i in agrupado["servico"]],
        programacao=[_item_ativo(i) for i in agrupado["programacao"]],
        regra=[_item_ativo(i) for i in agrupado["regra"]],
    )


@roteador.patch(
    "/catalogo/{id_catalogo_item}",
    response_model=ItemCatalogoResposta,
)
def alterar_item(
    id_catalogo_item: int,
    entrada: ItemCatalogoPatch,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("alterar_catalogo"))],
) -> ItemCatalogoResposta:
    try:
        alterado = catalogo.alterar_item(
            conexao,
            id_hotel=sessao.id_hotel,
            id_catalogo_item=id_catalogo_item,
            titulo=entrada.titulo,
            conteudo=entrada.conteudo,
            ativo=entrada.ativo,
        )
    except catalogo.DadosInvalidos as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro
    except catalogo.ItemNaoEncontrado as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item nao encontrado.",
        ) from erro
    return alterado.para_resposta()


@roteador.get("/propriedade/boas-vindas", response_model=BoasVindasResposta)
def ler_boas_vindas(
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("ler_texto_de_boas_vindas"))
    ],
) -> BoasVindasResposta:
    textos = catalogo.ler_textos_de_boas_vindas(
        conexao, id_hotel=sessao.id_hotel
    )
    return BoasVindasResposta(**textos)


@roteador.put("/propriedade/boas-vindas", response_model=BoasVindasResposta)
def gravar_boas_vindas(
    entrada: BoasVindasEntrada,
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("alterar_texto_de_boas_vindas"))
    ],
) -> BoasVindasResposta:
    try:
        gravados = catalogo.gravar_textos_de_boas_vindas(
            conexao,
            id_hotel=sessao.id_hotel,
            cafe=entrada.cafe,
            wifi=entrada.wifi,
            checkout=entrada.checkout,
        )
    except catalogo.DadosInvalidos as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro
    return BoasVindasResposta(**gravados)
