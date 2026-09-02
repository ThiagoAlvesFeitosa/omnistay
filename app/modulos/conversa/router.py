"""Webhook de entrada — grava e responde; nao interpreta."""

import hashlib
import hmac
import json
from datetime import UTC, datetime

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import obter_configuracao
from app.modulos.acesso.dependencias import Conexao, exigir_operacao
from app.modulos.acesso.service import SessaoAtual
from app.modulos.conversa import service as conversa
from app.modulos.conversa.schema import (
    ConversaEstadiaResposta,
    EventoEntrada,
    FioConversaSimulador,
    ListaConversasSimulador,
    RespostaRecepcaoCriada,
    RespostaRecepcaoEntrada,
    TurnoHospedeEntrada,
    TurnoHospedeResposta,
)

roteador = APIRouter(tags=["webhook"])


def _verificar_assinatura(corpo: bytes, cabecalho: str | None, segredo: str) -> bool:
    if not segredo or not cabecalho:
        return False
    esperado = cabecalho
    if esperado.startswith("sha256="):
        esperado = esperado[len("sha256=") :]
    digest = hmac.new(segredo.encode("utf-8"), corpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, esperado)


def _instante_origem(valor) -> datetime | None:
    if valor is None or valor == "":
        return None
    try:
        return datetime.fromtimestamp(int(valor), UTC)
    except (TypeError, ValueError, OSError):
        return None


def _normalizar_payload(dados: dict) -> EventoEntrada | None:
    """Aceita envelope interno de teste ou campos minimos Meta-like."""
    if "id_externo" in dados:
        return EventoEntrada(
            id_externo=str(dados["id_externo"]),
            telefone_origem=str(dados.get("telefone_origem", "")),
            texto=str(dados.get("texto", "")),
            tem_texto_utilizavel=bool(dados.get("tem_texto_utilizavel", True)),
            id_mensagem_canal=dados.get("id_mensagem_canal"),
            instante_origem=_instante_origem(dados.get("timestamp")),
        )
    # Envelope simplificado estilo WhatsApp Cloud
    try:
        valor = dados["entry"][0]["changes"][0]["value"]
        if valor.get("statuses") and not valor.get("messages"):
            status_item = valor["statuses"][0]
            return EventoEntrada(
                id_externo=str(status_item.get("id", "status")),
                telefone_origem="",
                texto="",
                tem_texto_utilizavel=False,
                id_mensagem_canal=str(status_item.get("id")) if status_item.get("id") else None,
            )
        mensagem = valor["messages"][0]
        id_externo = str(mensagem["id"])
        telefone = str(mensagem.get("from", ""))
        tipo = mensagem.get("type", "text")
        if tipo != "text":
            return EventoEntrada(
                id_externo=id_externo,
                telefone_origem=telefone,
                texto="",
                tem_texto_utilizavel=False,
                id_mensagem_canal=id_externo,
                instante_origem=_instante_origem(mensagem.get("timestamp")),
            )
        texto = mensagem["text"]["body"]
        return EventoEntrada(
            id_externo=id_externo,
            telefone_origem=telefone,
            texto=texto,
            tem_texto_utilizavel=bool(texto.strip()),
            id_mensagem_canal=id_externo,
            instante_origem=_instante_origem(mensagem.get("timestamp")),
        )
    except (KeyError, IndexError, TypeError):
        return None


@roteador.get("/webhook")
def verificar_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
) -> Response:
    cfg = obter_configuracao()
    if hub_mode == "subscribe" and hub_verify_token == cfg.whatsapp_verify_token:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


@roteador.post("/webhook")
async def receber_webhook(request: Request, conexao: Conexao) -> dict:
    cfg = obter_configuracao()
    corpo = await request.body()
    assinatura = request.headers.get("X-Hub-Signature-256")
    # Em teste, aceita tambem X-Omnistay-Signature com o mesmo HMAC.
    if not assinatura:
        assinatura = request.headers.get("X-Omnistay-Signature")
    if not _verificar_assinatura(corpo, assinatura, cfg.whatsapp_app_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="assinatura_invalida",
        )
    try:
        dados = json.loads(corpo.decode("utf-8") or "{}")
    except json.JSONDecodeError as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="json_invalido",
        ) from erro

    evento = _normalizar_payload(dados)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="payload_nao_reconhecido",
        )

    id_hotel = cfg.whatsapp_id_hotel
    if not id_hotel:
        # MVP: usa o menor id_hotel cadastrado se nao houver mapeamento.
        from sqlalchemy import text

        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM hotel ORDER BY id_hotel ASC LIMIT 1")
        ).scalar_one_or_none()
        if not id_hotel:
            return {"ok": True, "status": "sem_hotel"}

    resultado = conversa.receber_evento_entrada(
        conexao, evento=evento, id_hotel=int(id_hotel)
    )
    return {"ok": True, "status": resultado.get("status")}


def _traduzir_simulador(erro: Exception) -> None:
    if isinstance(erro, conversa.ModoRealRecusado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": "modo_real"},
        ) from erro
    if isinstance(erro, conversa.ConversaSimuladorNaoEncontrada):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nao encontrado.",
        ) from erro
    if isinstance(erro, conversa.EntradaSimuladorInvalida):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": erro.codigo},
        ) from erro
    raise erro


@roteador.get("/simulador/conversas", response_model=ListaConversasSimulador)
def listar_conversas_simulador(
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("usar_simulador"))],
) -> ListaConversasSimulador:
    try:
        dados = conversa.listar_conversas_simulador(
            conexao,
            id_hotel=sessao.id_hotel,
            modo=obter_configuracao().mensageria_modo,
        )
    except Exception as erro:
        _traduzir_simulador(erro)
    return ListaConversasSimulador.model_validate(dados)


@roteador.get(
    "/simulador/conversas/{id_reserva}",
    response_model=FioConversaSimulador,
)
def obter_conversa_simulador(
    id_reserva: int,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("usar_simulador"))],
) -> FioConversaSimulador:
    try:
        dados = conversa.obter_conversa_simulador(
            conexao,
            id_hotel=sessao.id_hotel,
            id_reserva=id_reserva,
            modo=obter_configuracao().mensageria_modo,
        )
    except Exception as erro:
        _traduzir_simulador(erro)
    return FioConversaSimulador.model_validate(dados)


@roteador.post("/simulador/conversas/{id_reserva}/mensagens")
def enviar_turno_hospede_simulador(
    id_reserva: int,
    corpo: TurnoHospedeEntrada,
    conexao: Conexao,
    sessao: Annotated[SessaoAtual, Depends(exigir_operacao("usar_simulador"))],
) -> JSONResponse:
    try:
        dados = conversa.enviar_turno_hospede_simulador(
            conexao,
            id_hotel=sessao.id_hotel,
            id_reserva=id_reserva,
            modo=obter_configuracao().mensageria_modo,
            texto=corpo.texto,
            id_externo=corpo.id_externo,
        )
    except Exception as erro:
        _traduzir_simulador(erro)
    resposta = TurnoHospedeResposta(
        status=dados["status"],
        id_mensagem=dados.get("id_mensagem"),
        id_reserva=id_reserva,
    )
    codigo = (
        status.HTTP_200_OK
        if dados.get("status") == "duplicado"
        else status.HTTP_201_CREATED
    )
    return JSONResponse(status_code=codigo, content=resposta.model_dump())


def _traduzir_estadia(erro: Exception) -> None:
    if isinstance(erro, conversa.ReservaNaoEncontrada):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva nao encontrada.",
        ) from erro
    if isinstance(erro, conversa.TextoInvalido):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Texto invalido.",
        ) from erro
    if isinstance(erro, conversa.JanelaCanalFechada):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": erro.codigo},
        ) from erro
    if isinstance(erro, conversa.TextoRepetido):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"codigo": erro.codigo},
        ) from erro
    raise erro


@roteador.get(
    "/reservas/{id_reserva}/conversa",
    response_model=ConversaEstadiaResposta,
)
def obter_conversa_da_estadia(
    id_reserva: int,
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("ler_conversa_da_estadia"))
    ],
) -> ConversaEstadiaResposta:
    try:
        dados = conversa.ler_conversa_da_estadia(
            conexao, id_hotel=sessao.id_hotel, id_reserva=id_reserva
        )
    except Exception as erro:
        _traduzir_estadia(erro)
        raise
    return ConversaEstadiaResposta.model_validate(dados)


@roteador.post(
    "/reservas/{id_reserva}/respostas",
    response_model=RespostaRecepcaoCriada,
    status_code=status.HTTP_201_CREATED,
)
def criar_resposta_da_recepcao(
    id_reserva: int,
    corpo: RespostaRecepcaoEntrada,
    conexao: Conexao,
    sessao: Annotated[
        SessaoAtual, Depends(exigir_operacao("enviar_resposta_recepcao"))
    ],
) -> RespostaRecepcaoCriada:
    try:
        dados = conversa.enviar_resposta_recepcao(
            conexao,
            id_hotel=sessao.id_hotel,
            id_reserva=id_reserva,
            texto=corpo.texto,
        )
    except Exception as erro:
        _traduzir_estadia(erro)
        raise
    return RespostaRecepcaoCriada.model_validate(dados)

