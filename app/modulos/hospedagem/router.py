"""Rotas de reserva, fila do dia e contagem de chegadas."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modulos.acesso.dependencias import Conexao, exigir_operacao
from app.modulos.acesso.service import SessaoAtual
from app.modulos.hospedagem import service as hospedagem
from app.modulos.hospedagem.schema import (
    ContagemChegadasResposta,
    FichaTitularResposta,
    FilaDoDiaResposta,
    ReservaEntrada,
    ReservaResposta,
)

roteador = APIRouter(tags=["hospedagem"])


@roteador.post(
    "/reservas",
    response_model=ReservaResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_reserva(
    entrada: ReservaEntrada,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("alterar_reserva"))],
) -> ReservaResposta:
    try:
        criada = hospedagem.criar_reserva(
            conexao,
            id_hotel=sessao.id_hotel,
            nome=entrada.nome,
            telefone=entrada.telefone,
            data_checkin_prevista=entrada.data_checkin_prevista,
            data_checkout_prevista=entrada.data_checkout_prevista,
        )
    except hospedagem.DadosInvalidos as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro
    return criada.para_resposta()


@roteador.get("/fila-do-dia", response_model=FilaDoDiaResposta)
def fila_do_dia(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_fila_do_dia"))],
) -> FilaDoDiaResposta:
    itens = hospedagem.listar_fila_do_dia(conexao, id_hotel=sessao.id_hotel)
    return FilaDoDiaResposta(itens=itens)


@roteador.get(
    "/indicadores/chegadas-do-dia",
    response_model=ContagemChegadasResposta,
)
def chegadas_do_dia(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("ler_indicadores"))],
) -> ContagemChegadasResposta:
    quantidade = hospedagem.contar_chegadas_do_dia(conexao, id_hotel=sessao.id_hotel)
    return ContagemChegadasResposta(quantidade=quantidade)


@roteador.get("/reservas/{id_reserva}/ficha", response_model=FichaTitularResposta)
def ler_ficha(
    id_reserva: int,
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("ler_ficha_de_hospede"))
    ],
) -> FichaTitularResposta:
    try:
        return hospedagem.ler_ficha_titular(
            conexao, id_hotel=sessao.id_hotel, id_reserva=id_reserva
        )
    except hospedagem.DadosInvalidos as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(erro),
        ) from erro
