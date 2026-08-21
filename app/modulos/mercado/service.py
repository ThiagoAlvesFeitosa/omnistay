"""Cadastro de concorrentes. Nao conhece HTTP nem SQL."""

from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy.engine import Connection

from app.comum.log import obter_logger
from app.modulos.mercado import repository as mercado_repository
from app.modulos.mercado.schema import ConcorrenteResposta, FonteAtivaResposta

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
