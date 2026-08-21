"""Cadastro de concorrentes e coleta agendada. Nao conhece HTTP nem SQL."""

from dataclasses import dataclass
from datetime import UTC, timedelta
from decimal import Decimal
from urllib.parse import urlparse

from sqlalchemy.engine import Connection

from app.comum.log import obter_logger
from app.fila import repository as fila_repository
from app.fila import service as fila_service
from app.modulos.mercado import repository as mercado_repository
from app.modulos.mercado.schema import ConcorrenteResposta, FonteAtivaResposta
from app.portas.fonte_publica import (
    DESFECHO_ENCONTRADO,
    DIRETIVA_AUSENTE,
    DIRETIVA_PERMITE,
    DIRETIVA_RECUSA,
)

logger = obter_logger(__name__)

NOME_MAXIMO = 120
URL_MAXIMA = 400


class DadosInvalidos(ValueError):
    """Entrada rejeitada na borda de negocio, com mensagem para o usuario."""


class ConcorrenteNaoEncontrado(Exception):
    pass


class FonteDuplicada(Exception):
    pass


@dataclass(frozen=True)
class Concorrente:
    id_concorrente: int
    id_hotel: int
    nome: str
    url_fonte: str
    ativo: bool

    def para_resposta(self) -> ConcorrenteResposta:
        return ConcorrenteResposta(
            id_concorrente=self.id_concorrente,
            nome=self.nome,
            url_fonte=self.url_fonte,
            ativo=self.ativo,
        )

    def para_fonte_ativa(self) -> FonteAtivaResposta:
        return FonteAtivaResposta(
            id_concorrente=self.id_concorrente,
            nome=self.nome,
            url_fonte=self.url_fonte,
        )


def _da_linha(linha: dict) -> Concorrente:
    return Concorrente(
        id_concorrente=linha["id_concorrente"],
        id_hotel=linha["id_hotel"],
        nome=linha["nome"],
        url_fonte=linha["url_fonte"],
        ativo=linha["ativo"],
    )


def _validar_nome(nome: str) -> str:
    limpo = nome.strip()
    if not limpo:
        raise DadosInvalidos("Informe o nome.")
    if len(limpo) > NOME_MAXIMO:
        raise DadosInvalidos("O nome deve ter no maximo 120 caracteres.")
    return limpo


def _validar_url(url_fonte: str) -> str:
    limpa = url_fonte.strip()
    if not limpa:
        raise DadosInvalidos("Informe o endereco da fonte.")
    if len(limpa) > URL_MAXIMA:
        raise DadosInvalidos(
            "O endereco da fonte deve ter no maximo 400 caracteres."
        )
    analisada = urlparse(limpa)
    if analisada.scheme not in {"http", "https"} or not analisada.hostname:
        raise DadosInvalidos("Informe um endereco da web publico e completo.")
    if analisada.username or analisada.password:
        raise DadosInvalidos("A fonte nao pode trazer usuario nem senha.")
    return limpa


def criar_concorrente(
    conexao: Connection,
    *,
    id_hotel: int,
    nome: str,
    url_fonte: str,
    repositorio=mercado_repository,
) -> Concorrente:
    nome_limpo = _validar_nome(nome)
    url_limpa = _validar_url(url_fonte)
    if repositorio.existe_fonte(conexao, id_hotel=id_hotel, url_fonte=url_limpa):
        raise FonteDuplicada
    linha = repositorio.inserir(
        conexao, id_hotel=id_hotel, nome=nome_limpo, url_fonte=url_limpa
    )
    criado = _da_linha(linha)
    logger.info(
        "concorrente_criar id_concorrente=%s id_hotel=%s",
        criado.id_concorrente,
        criado.id_hotel,
    )
    return criado


def alterar_concorrente(
    conexao: Connection,
    *,
    id_hotel: int,
    id_concorrente: int,
    nome: str | None = None,
    url_fonte: str | None = None,
    ativo: bool | None = None,
    repositorio=mercado_repository,
) -> Concorrente:
    if nome is None and url_fonte is None and ativo is None:
        raise DadosInvalidos("Informe nome, url_fonte ou ativo.")
    nome_limpo = _validar_nome(nome) if nome is not None else None
    url_limpa = _validar_url(url_fonte) if url_fonte is not None else None
    if url_limpa is not None and repositorio.existe_fonte(
        conexao,
        id_hotel=id_hotel,
        url_fonte=url_limpa,
        exceto_id=id_concorrente,
    ):
        raise FonteDuplicada
    linha = repositorio.atualizar(
        conexao,
        id_hotel=id_hotel,
        id_concorrente=id_concorrente,
        nome=nome_limpo,
        url_fonte=url_limpa,
        ativo=ativo,
    )
    if linha is None:
        raise ConcorrenteNaoEncontrado
    alterado = _da_linha(linha)
    if ativo is False:
        acao = "desativar"
    elif ativo is True:
        acao = "reativar"
    else:
        acao = "editar"
    logger.info(
        "concorrente_%s id_concorrente=%s id_hotel=%s",
        acao,
        alterado.id_concorrente,
        alterado.id_hotel,
    )
    return alterado


def listar_manutencao(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=mercado_repository,
) -> list[Concorrente]:
    return [
        _da_linha(linha)
        for linha in repositorio.listar_manutencao(conexao, id_hotel=id_hotel)
    ]


def listar_fontes_ativas(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=mercado_repository,
) -> list[Concorrente]:
    return [
        Concorrente(
            id_concorrente=linha["id_concorrente"],
            id_hotel=id_hotel,
            nome=linha["nome"],
            url_fonte=linha["url_fonte"],
            ativo=True,
        )
        for linha in repositorio.listar_ativos(conexao, id_hotel=id_hotel)
    ]


CHAVE_PERIODICIDADE = "periodicidade_coleta_mercado"


def _inteiro_positivo(valor: str | None) -> int | None:
    if valor is None:
        return None
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    if numero < 1:
        return None
    return numero


def _preco(valor) -> Decimal | None:
    if valor is None:
        return None
    preco = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    if preco < 0:
        return None
    return preco


def _nota_agregada(valor) -> Decimal | None:
    if valor is None:
        return None
    nota = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    if nota < 0 or nota > 5:
        return None
    return nota


def agendar_coletas_devidas(
    conexao: Connection,
    *,
    agora,
    repositorio_propriedade,
    repositorio=mercado_repository,
    enfileirar=fila_service.enfileirar_coletar_mercado,
) -> int:
    if agora.tzinfo is None:
        agora = agora.replace(tzinfo=UTC)
    fontes = repositorio.listar_ativos_de_todos(conexao)
    cache: dict[int, int | None] = {}
    novos = 0
    for fonte in fontes:
        id_hotel = fonte["id_hotel"]
        if id_hotel not in cache:
            horas = _inteiro_positivo(
                repositorio_propriedade.ler_parametro(
                    conexao, id_hotel, CHAVE_PERIODICIDADE
                )
            )
            if horas is None:
                logger.info("periodicidade_ausente id_hotel=%s", id_hotel)
            cache[id_hotel] = horas
        horas = cache[id_hotel]
        if horas is None:
            continue
        ultima = repositorio.ultima_coleta(
            conexao, id_concorrente=fonte["id_concorrente"]
        )
        if ultima is not None:
            marcado = ultima["coletado_em"]
            if getattr(marcado, "tzinfo", None) is None:
                marcado = marcado.replace(tzinfo=UTC)
            if agora < marcado + timedelta(hours=horas):
                continue
        id_trabalho = enfileirar(
            conexao,
            id_hotel=id_hotel,
            id_concorrente=fonte["id_concorrente"],
        )
        if id_trabalho:
            novos += 1
            logger.info(
                "coleta_enfileirada id_concorrente=%s id_hotel=%s",
                fonte["id_concorrente"],
                id_hotel,
            )
    return novos


def processar_trabalho_coletar_mercado(
    conexao: Connection,
    *,
    trabalho: dict,
    fonte,
    agora=None,
    repositorio=mercado_repository,
) -> None:
    from app.comum import relogio

    instante = agora() if callable(agora) else agora
    if instante is None:
        instante = relogio.agora()
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)

    id_hotel = trabalho["id_hotel"]
    id_concorrente = int(trabalho["payload"]["id_concorrente"])
    id_trabalho = trabalho["id_trabalho"]

    ficha = repositorio.obter_ativo(
        conexao, id_hotel=id_hotel, id_concorrente=id_concorrente
    )
    if ficha is None:
        logger.info(
            "fonte_inativa_omitida id_concorrente=%s id_hotel=%s",
            id_concorrente,
            id_hotel,
        )
        fila_repository.marcar_concluido(conexao, id_trabalho=id_trabalho)
        return

    criado_em = repositorio.criado_em_do_trabalho(
        conexao, id_trabalho=id_trabalho
    )
    if getattr(criado_em, "tzinfo", None) is None:
        criado_em = criado_em.replace(tzinfo=UTC)
    ja = repositorio.ultima_coleta(conexao, id_concorrente=id_concorrente)
    if ja is not None:
        marcado = ja["coletado_em"]
        if getattr(marcado, "tzinfo", None) is None:
            marcado = marcado.replace(tzinfo=UTC)
        if marcado >= criado_em:
            fila_repository.marcar_concluido(conexao, id_trabalho=id_trabalho)
            return

    url_fonte = ficha["url_fonte"]
    diretiva = fonte.consultar_diretiva(url_fonte)
    if diretiva != DIRETIVA_PERMITE:
        codigo = (
            "diretiva_recusada"
            if diretiva == DIRETIVA_RECUSA
            else "diretiva_ausente" if diretiva == DIRETIVA_AUSENTE else "falha"
        )
        repositorio.inserir_coleta(
            conexao,
            id_concorrente=id_concorrente,
            sucesso=False,
            preco=None,
            nota_media=None,
            coletado_em=instante,
        )
        logger.info(
            "coleta_falha id_concorrente=%s id_hotel=%s %s",
            id_concorrente,
            id_hotel,
            codigo,
        )
        fila_repository.marcar_concluido(conexao, id_trabalho=id_trabalho)
        return

    resultado = fonte.coletar_publico(url_fonte)
    preco = _preco(resultado.preco)
    nota = _nota_agregada(resultado.nota_media)
    if resultado.desfecho == DESFECHO_ENCONTRADO and (
        preco is not None or nota is not None
    ):
        repositorio.inserir_coleta(
            conexao,
            id_concorrente=id_concorrente,
            sucesso=True,
            preco=preco,
            nota_media=nota,
            coletado_em=instante,
        )
        logger.info(
            "coleta_sucesso id_concorrente=%s id_hotel=%s",
            id_concorrente,
            id_hotel,
        )
    else:
        codigo = {
            "sem_dado": "sem_dado",
            "indisponivel": "fonte_indisponivel",
            "exige_autenticacao": "exige_autenticacao",
        }.get(resultado.desfecho, "falha")
        repositorio.inserir_coleta(
            conexao,
            id_concorrente=id_concorrente,
            sucesso=False,
            preco=None,
            nota_media=None,
            coletado_em=instante,
        )
        logger.info(
            "coleta_falha id_concorrente=%s id_hotel=%s %s",
            id_concorrente,
            id_hotel,
            codigo,
        )
    fila_repository.marcar_concluido(conexao, id_trabalho=id_trabalho)
