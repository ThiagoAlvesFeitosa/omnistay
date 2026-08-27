"""Adaptador real da porta LLMProvider via generateContent. Sem SDK."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from app.comum.log import obter_logger
from app.portas.llm import (
    CAMPOS_FICHA_CHAVE,
    FalhaDeClassificacao,
    FalhaDeConversacao,
    FalhaDeExtracao,
    FalhaDeIdentificacao,
    ResultadoClassificacao,
    ResultadoExtracao,
    ResultadoIdentificacao,
    ResultadoPesquisaSaida,
    ResultadoResposta,
)

logger = obter_logger(__name__)

_HOST = "generativelanguage.googleapis.com"


class LLMGemini:
    def __init__(
        self,
        *,
        chave: str,
        timeout: float,
        modelo: str,
        cliente: httpx.Client | None = None,
    ) -> None:
        self._chave = chave
        self._timeout = timeout
        self._modelo = modelo
        self._cliente = cliente

    def __repr__(self) -> str:
        return f"LLMGemini(modelo={self._modelo!r})"

    def _cliente_http(self) -> httpx.Client:
        if self._cliente is None:
            self._cliente = httpx.Client(timeout=self._timeout)
        return self._cliente

    def _gerar(self, prompt: str, falha: Callable[[str], Exception], metodo: str) -> dict:
        url = (
            f"https://{_HOST}/v1beta/models/{self._modelo}:generateContent"
        )
        corpo = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        try:
            resposta = self._cliente_http().post(
                url,
                headers={
                    "x-goog-api-key": self._chave,
                    "Content-Type": "application/json",
                },
                json=corpo,
                timeout=self._timeout,
            )
        except httpx.TimeoutException as erro:
            logger.info("llm_falha metodo=%s codigo=llm_tempo_esgotado", metodo)
            raise falha("llm_tempo_esgotado") from erro
        except httpx.HTTPError as erro:
            logger.info("llm_falha metodo=%s codigo=llm_indisponivel", metodo)
            raise falha("llm_indisponivel") from erro

        status = resposta.status_code
        if status in (401, 403):
            logger.info("llm_falha metodo=%s codigo=llm_recusa", metodo)
            raise falha("llm_recusa")
        if status == 429:
            logger.info("llm_falha metodo=%s codigo=llm_quota", metodo)
            raise falha("llm_quota")
        if status >= 400:
            logger.info("llm_falha metodo=%s codigo=llm_indisponivel", metodo)
            raise falha("llm_indisponivel")

        try:
            envelope = resposta.json()
        except ValueError:
            logger.info("llm_falha metodo=%s codigo=llm_formato_invalido", metodo)
            raise falha("llm_formato_invalido") from None

        candidatos = envelope.get("candidates") if isinstance(envelope, dict) else None
        if not candidatos:
            logger.info("llm_falha metodo=%s codigo=llm_formato_invalido", metodo)
            raise falha("llm_formato_invalido")
        partes = ((candidatos[0].get("content") or {}).get("parts") or [])
        if not partes or not isinstance(partes[0], dict) or "text" not in partes[0]:
            logger.info("llm_falha metodo=%s codigo=llm_formato_invalido", metodo)
            raise falha("llm_formato_invalido")
        texto = partes[0]["text"]
        try:
            parseado = json.loads(texto)
        except (json.JSONDecodeError, TypeError):
            logger.info("llm_falha metodo=%s codigo=llm_formato_invalido", metodo)
            raise falha("llm_formato_invalido") from None
        if not isinstance(parseado, dict):
            logger.info("llm_falha metodo=%s codigo=llm_formato_invalido", metodo)
            raise falha("llm_formato_invalido")
        logger.info("llm_chamada metodo=%s status=%s", metodo, status)
        return parseado

    def classificar(self, texto: str) -> ResultadoClassificacao:
        prompt = (
            "Classifique a mensagem do hospede. Responda somente JSON com as "
            "chaves intencao, sentimento e urgencia.\n"
            "intencao: duvida_geral | pedido_de_servico | reclamacao_tecnica | "
            "upsell | solicitacao_de_checkout | fora_de_escopo\n"
            "sentimento: positivo | neutro | negativo\n"
            "urgencia: baixa | media | alta\n"
            f"Mensagem:\n{texto}"
        )
        dados = self._gerar(prompt, FalhaDeClassificacao, "classificar")
        return ResultadoClassificacao(
            intencao=_texto_ou_none(dados.get("intencao")),
            sentimento=_texto_ou_none(dados.get("sentimento")),
            urgencia=_texto_ou_none(dados.get("urgencia")),
            bruto=dados,
        )

    def extrair_ficha(self, texto: str) -> ResultadoExtracao:
        chaves = ", ".join(CAMPOS_FICHA_CHAVE)
        prompt = (
            "Extraia os campos da ficha de hospede. Responda somente JSON com "
            "desfecho (completa | parcial | irreconhecivel) e campos (objeto).\n"
            f"Chaves permitidas: {chaves}. Nunca inclua idade.\n"
            f"Texto:\n{texto}"
        )
        dados = self._gerar(prompt, FalhaDeExtracao, "extrair_ficha")
        campos_brutos = dados.get("campos") or {}
        campos: dict[str, str] = {}
        if isinstance(campos_brutos, dict):
            for chave, valor in campos_brutos.items():
                if chave == "idade" or valor is None:
                    continue
                campos[str(chave)] = str(valor)
        desfecho = _texto_ou_none(dados.get("desfecho")) or "irreconhecivel"
        reconhecidos = tuple(k for k in CAMPOS_FICHA_CHAVE if k in campos)
        return ResultadoExtracao(
            desfecho=desfecho,
            campos=campos,
            campos_reconhecidos=reconhecidos,
        )

    def responder_duvida(self, pergunta: str, itens_ativos: tuple) -> ResultadoResposta:
        fatos = "\n".join(
            f"- {item.titulo}: {item.conteudo}" for item in itens_ativos
        )
        prompt = (
            "Responda a pergunta somente com os fatos abaixo. JSON com coberta "
            "(boolean), texto (string ou null) e trechos_citados (lista de strings "
            "copiados dos fatos). Se nenhum fato cobrir: coberta false, texto null, "
            "trechos_citados [].\n"
            f"Fatos:\n{fatos}\n"
            f"Pergunta:\n{pergunta}"
        )
        dados = self._gerar(prompt, FalhaDeConversacao, "responder_duvida")
        trechos = dados.get("trechos_citados") or ()
        if isinstance(trechos, list):
            citados = tuple(str(t) for t in trechos)
        else:
            citados = ()
        texto = dados.get("texto")
        return ResultadoResposta(
            coberta=bool(dados.get("coberta")),
            texto=None if texto is None else str(texto),
            trechos_citados=citados,
        )

    def identificar_item_vendavel(
        self, texto: str, itens_ativos: tuple
    ) -> ResultadoIdentificacao:
        linhas = []
        for item in itens_ativos:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                linhas.append(f"{item[0]}: {item[1]}")
            else:
                linhas.append(str(item))
        prompt = (
            "Identifique o item vendavel. JSON com desfecho (unico | nenhum | "
            "ambiguo), id_item_vendavel (int ou null) e quantidade (int ou null).\n"
            f"Itens:\n{chr(10).join(linhas)}\n"
            f"Pedido:\n{texto}"
        )
        dados = self._gerar(prompt, FalhaDeIdentificacao, "identificar_item_vendavel")
        return ResultadoIdentificacao(
            desfecho=_texto_ou_none(dados.get("desfecho")) or "nenhum",
            id_item_vendavel=_int_ou_none(dados.get("id_item_vendavel")),
            quantidade=_int_ou_none(dados.get("quantidade")),
        )

    def interpretar_pesquisa_saida(self, texto: str) -> ResultadoPesquisaSaida:
        prompt = (
            "Leia a resposta da pesquisa de saida. JSON com desfecho (completo | "
            "parcial | irreconhecivel), nota (int 1-5 ou null), comentario "
            "(string ou null) e aceite (boolean ou null).\n"
            f"Texto:\n{texto}"
        )
        dados = self._gerar(prompt, FalhaDeExtracao, "interpretar_pesquisa_saida")
        aceite = dados.get("aceite")
        if not isinstance(aceite, bool):
            aceite = None
        comentario = dados.get("comentario")
        return ResultadoPesquisaSaida(
            desfecho=_texto_ou_none(dados.get("desfecho")) or "irreconhecivel",
            nota=_int_ou_none(dados.get("nota")),
            comentario=None if comentario is None else str(comentario),
            aceite=aceite,
        )


def _texto_ou_none(valor: Any) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor
    return str(valor)


def _int_ou_none(valor: Any) -> int | None:
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str):
        try:
            return int(valor)
        except ValueError:
            return None
    return None
