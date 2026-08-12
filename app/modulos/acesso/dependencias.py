"""Dependencias FastAPI: sessao atual e exigencia de operacao."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.engine import Connection

from app.comum.transacao import transacao
from app.modulos.acesso import politica, service as acesso_service
from app.modulos.acesso.service import NOME_DO_COOKIE, SessaoAtual


def obter_conexao() -> Iterator[Connection]:
    with transacao() as conexao:
        yield conexao


Conexao = Annotated[Connection, Depends(obter_conexao)]


def sessao_atual(
    conexao: Conexao,
    omnistay_sessao: Annotated[str | None, Cookie(alias=NOME_DO_COOKIE)] = None,
) -> SessaoAtual:
    try:
        return acesso_service.resolver_sessao(conexao, omnistay_sessao)
    except acesso_service.SessaoAusenteOuInvalida as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao ausente ou invalida.",
        ) from erro


Sessao = Annotated[SessaoAtual, Depends(sessao_atual)]


def exigir_operacao(operacao: str):
    def dependencia(sessao: Sessao) -> SessaoAtual:
        if not politica.permitido(sessao.perfil, operacao):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissao para esta operacao.",
            )
        return sessao

    return dependencia
