"""Rotas de sessao e usuario."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.modulos.acesso import dependencias, service as acesso_service
from app.modulos.acesso.dependencias import Conexao, Sessao
from app.modulos.acesso.schema import (
    CredenciaisDeEntrada,
    SessaoAtualResposta,
    SessaoCriada,
    SessaoListada,
    UsuarioEntrada,
    UsuarioResposta,
)
from app.modulos.acesso.service import NOME_DO_COOKIE

roteador = APIRouter(tags=["acesso"])

MENSAGEM_CREDENCIAIS = "Credenciais invalidas."
MENSAGEM_SESSAO = "Sessao ausente ou invalida."


def _definir_cookie(
    resposta: Response, token: str, expira_em: datetime, pedido: Request
) -> None:
    agora = datetime.now(UTC)
    max_age = max(0, int((expira_em - agora).total_seconds()))
    resposta.set_cookie(
        key=NOME_DO_COOKIE,
        value=token,
        httponly=True,
        secure=pedido.url.scheme == "https",
        samesite="strict",
        path="/",
        max_age=max_age,
    )


def _remover_cookie(resposta: Response) -> None:
    resposta.delete_cookie(key=NOME_DO_COOKIE, path="/")


def _dispositivo(entrada: CredenciaisDeEntrada, pedido: Request) -> str | None:
    if entrada.dispositivo:
        return entrada.dispositivo
    agente = pedido.headers.get("user-agent")
    if not agente:
        return None
    return agente[:120]


@roteador.post(
    "/sessoes",
    response_model=SessaoCriada,
    status_code=status.HTTP_201_CREATED,
)
def criar_sessao(
    entrada: CredenciaisDeEntrada,
    pedido: Request,
    resposta: Response,
    conexao: Conexao,
) -> SessaoCriada:
    try:
        autenticada = acesso_service.autenticar(
            conexao,
            email=entrada.email,
            senha=entrada.senha,
            dispositivo=_dispositivo(entrada, pedido),
        )
    except acesso_service.CredenciaisInvalidas as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MENSAGEM_CREDENCIAIS,
        ) from erro

    _definir_cookie(resposta, autenticada.token, autenticada.expira_em, pedido)
    return SessaoCriada(
        id_usuario=autenticada.id_usuario,
        nome=autenticada.nome,
        perfil=autenticada.perfil,
        expira_em=autenticada.expira_em,
    )


@roteador.delete("/sessoes/atual", status_code=status.HTTP_204_NO_CONTENT)
def encerrar_sessao_atual(
    resposta: Response,
    conexao: Conexao,
    omnistay_sessao: Annotated[str | None, Cookie(alias=NOME_DO_COOKIE)] = None,
) -> None:
    acesso_service.encerrar_sessao(conexao, omnistay_sessao)
    _remover_cookie(resposta)


@roteador.get("/sessoes/atual", response_model=SessaoAtualResposta)
def obter_sessao_atual(sessao: Sessao) -> SessaoAtualResposta:
    return SessaoAtualResposta(
        id_sessao=sessao.id_sessao,
        id_usuario=sessao.id_usuario,
        nome=sessao.nome,
        perfil=sessao.perfil,
        dispositivo=sessao.dispositivo,
        expira_em=sessao.expira_em,
    )


@roteador.get("/sessoes", response_model=list[SessaoListada])
def listar_sessoes(
    conexao: Conexao,
    sessao: Annotated[
        acesso_service.SessaoAtual,
        Depends(dependencias.exigir_operacao("listar_sessoes")),
    ],
) -> list[SessaoListada]:
    linhas = acesso_service.listar_sessoes_ativas(conexao, id_hotel=sessao.id_hotel)
    return [
        SessaoListada(
            id_sessao=linha.id_sessao,
            id_usuario=linha.id_usuario,
            nome_usuario=linha.nome_usuario,
            perfil=linha.perfil,
            dispositivo=linha.dispositivo,
            criada_em=linha.criada_em,
            expira_em=linha.expira_em,
        )
        for linha in linhas
    ]


@roteador.delete("/sessoes/{id_sessao}", status_code=status.HTTP_204_NO_CONTENT)
def revogar_sessao(
    id_sessao: int,
    conexao: Conexao,
    sessao: Annotated[
        acesso_service.SessaoAtual,
        Depends(dependencias.exigir_operacao("revogar_sessao")),
    ],
) -> None:
    try:
        acesso_service.revogar_sessao(
            conexao,
            id_sessao=id_sessao,
            id_hotel_do_ator=sessao.id_hotel,
        )
    except acesso_service.SessaoNaoEncontrada as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessao nao encontrada.",
        ) from erro


@roteador.post(
    "/usuarios",
    response_model=UsuarioResposta,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_usuario(
    entrada: UsuarioEntrada,
    conexao: Conexao,
    sessao: Annotated[
        acesso_service.SessaoAtual,
        Depends(dependencias.exigir_operacao("administrar_usuario")),
    ],
) -> UsuarioResposta:
    try:
        criado = acesso_service.criar_usuario(
            conexao,
            id_hotel=sessao.id_hotel,
            nome=entrada.nome,
            email=entrada.email,
            perfil=entrada.perfil,
            senha=entrada.senha,
        )
    except acesso_service.EmailJaCadastrado as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ja cadastrado.",
        ) from erro
    except acesso_service.PerfilInvalido as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro
    except acesso_service.SenhaCurtaDemais as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(erro),
        ) from erro

    return UsuarioResposta(
        id_usuario=criado.id_usuario,
        nome=criado.nome,
        email=criado.email,
        perfil=criado.perfil,
        ativo=criado.ativo,
    )


@roteador.delete("/usuarios/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_usuario(
    id_usuario: int,
    conexao: Conexao,
    sessao: Annotated[
        acesso_service.SessaoAtual,
        Depends(dependencias.exigir_operacao("administrar_usuario")),
    ],
) -> None:
    try:
        acesso_service.desativar_usuario(
            conexao,
            id_usuario=id_usuario,
            id_hotel_do_ator=sessao.id_hotel,
            id_usuario_do_ator=sessao.id_usuario,
        )
    except acesso_service.AutoDesativacaoProibida as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e permitido desativar o proprio usuario.",
        ) from erro
    except acesso_service.UsuarioNaoEncontrado as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        ) from erro
