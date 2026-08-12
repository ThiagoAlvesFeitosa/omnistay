"""Regras de usuario e sessao: autenticar, autorizar acesso, administrar funcionarios."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.engine import Connection

from app.comum import relogio, seguranca
from app.comum.log import obter_logger
from app.modulos.acesso import repository as acesso_repository

_logger = obter_logger(__name__)

PERFIS_VALIDOS = frozenset({"recepcao", "staff", "gestor"})
TAMANHO_MINIMO_DA_SENHA = 12
NOME_DO_COOKIE = "omnistay_sessao"


class EmailJaCadastrado(Exception):
    pass


class PerfilInvalido(Exception):
    pass


class SenhaCurtaDemais(Exception):
    pass


class UsuarioNaoEncontrado(Exception):
    pass


class AutoDesativacaoProibida(Exception):
    pass


class CredenciaisInvalidas(Exception):
    pass


class SessaoAusenteOuInvalida(Exception):
    pass


class SessaoNaoEncontrada(Exception):
    pass


@dataclass(frozen=True)
class UsuarioCriado:
    id_usuario: int
    nome: str
    email: str
    perfil: str
    ativo: bool = True


@dataclass(frozen=True)
class SessaoAutenticada:
    token: str
    id_sessao: int
    id_usuario: int
    id_hotel: int
    nome: str
    perfil: str
    dispositivo: str | None
    criada_em: datetime
    expira_em: datetime


@dataclass(frozen=True)
class SessaoAtual:
    id_sessao: int
    id_usuario: int
    id_hotel: int
    nome: str
    perfil: str
    dispositivo: str | None
    criada_em: datetime
    expira_em: datetime


def criar_usuario(
    conexao: Connection,
    *,
    id_hotel: int,
    nome: str,
    email: str,
    perfil: str,
    senha: str,
    repositorio=acesso_repository,
    derivar: Callable[[str], str] = seguranca.derivar_senha,
) -> UsuarioCriado:
    if perfil not in PERFIS_VALIDOS:
        raise PerfilInvalido(f"Perfil fora dos previstos: {perfil}")
    if len(senha) < TAMANHO_MINIMO_DA_SENHA:
        raise SenhaCurtaDemais(
            f"Senha precisa ter ao menos {TAMANHO_MINIMO_DA_SENHA} caracteres"
        )
    if repositorio.buscar_por_email(conexao, email) is not None:
        raise EmailJaCadastrado(email)

    id_usuario = repositorio.inserir_usuario(
        conexao,
        id_hotel=id_hotel,
        nome=nome,
        email=email,
        senha_hash=derivar(senha),
        perfil=perfil,
    )
    return UsuarioCriado(
        id_usuario=id_usuario, nome=nome, email=email, perfil=perfil
    )


def desativar_usuario(
    conexao: Connection,
    *,
    id_usuario: int,
    id_hotel_do_ator: int,
    id_usuario_do_ator: int,
    repositorio=acesso_repository,
    agora: Callable[[], datetime] = relogio.agora,
) -> None:
    if id_usuario == id_usuario_do_ator:
        raise AutoDesativacaoProibida("gestor nao pode desativar a si mesmo")

    alvo = repositorio.buscar_por_id(conexao, id_usuario)
    if alvo is None or alvo.id_hotel != id_hotel_do_ator:
        raise UsuarioNaoEncontrado(id_usuario)

    instante = agora()
    repositorio.desativar_usuario(conexao, id_usuario)
    repositorio.revogar_sessoes_do_usuario(conexao, id_usuario, instante)


def autenticar(
    conexao: Connection,
    *,
    email: str,
    senha: str,
    dispositivo: str | None,
    repositorio=acesso_repository,
    ler_duracao: Callable[..., int] | None = None,
    agora: Callable[[], datetime] = relogio.agora,
    conferir: Callable[[str, str], bool] = seguranca.conferir_senha,
    gerar_token: Callable[[], str] = seguranca.gerar_token,
    hash_do_token: Callable[[str], str] = seguranca.hash_do_token,
    hash_de_referencia: Callable[..., str] = seguranca.hash_de_referencia,
) -> SessaoAutenticada:
    # Import local evita ciclo com propriedade.service, que chama criar_usuario.
    if ler_duracao is None:
        from app.modulos.propriedade import service as propriedade_service

        ler_duracao = propriedade_service.duracao_da_sessao_em_horas

    usuario = repositorio.buscar_por_email(conexao, email)
    if usuario is None:
        # Iguala o tempo de resposta: e-mail inexistente tambem paga a derivacao.
        conferir(senha, hash_de_referencia())
        _logger.info("AUTH_RECUSADA motivo=email_inexistente")
        raise CredenciaisInvalidas()

    if not usuario.ativo or not conferir(senha, usuario.senha_hash):
        _logger.info(
            "AUTH_RECUSADA id_usuario=%s motivo=credencial_ou_inativo",
            usuario.id_usuario,
        )
        raise CredenciaisInvalidas()

    instante = agora()
    horas = ler_duracao(conexao, id_hotel=usuario.id_hotel, perfil=usuario.perfil)
    expira_em = instante + timedelta(hours=horas)
    token = gerar_token()
    id_sessao = repositorio.inserir_sessao(
        conexao,
        id_usuario=usuario.id_usuario,
        token_hash=hash_do_token(token),
        dispositivo=dispositivo,
        criada_em=instante,
        expira_em=expira_em,
    )
    _logger.info(
        "AUTH_OK id_usuario=%s id_sessao=%s perfil=%s",
        usuario.id_usuario,
        id_sessao,
        usuario.perfil,
    )
    return SessaoAutenticada(
        token=token,
        id_sessao=id_sessao,
        id_usuario=usuario.id_usuario,
        id_hotel=usuario.id_hotel,
        nome=usuario.nome,
        perfil=usuario.perfil,
        dispositivo=dispositivo,
        criada_em=instante,
        expira_em=expira_em,
    )


def resolver_sessao(
    conexao: Connection,
    token: str | None,
    *,
    repositorio=acesso_repository,
    agora: Callable[[], datetime] = relogio.agora,
    hash_do_token: Callable[[str], str] = seguranca.hash_do_token,
) -> SessaoAtual:
    if not token:
        raise SessaoAusenteOuInvalida()

    linha = repositorio.buscar_sessao_por_hash(conexao, hash_do_token(token))
    instante = agora()
    if (
        linha is None
        or linha.revogada_em is not None
        or linha.expira_em <= instante
        or not linha.ativo
    ):
        raise SessaoAusenteOuInvalida()

    return SessaoAtual(
        id_sessao=linha.id_sessao,
        id_usuario=linha.id_usuario,
        id_hotel=linha.id_hotel,
        nome=linha.nome,
        perfil=linha.perfil,
        dispositivo=linha.dispositivo,
        criada_em=linha.criada_em,
        expira_em=linha.expira_em,
    )


def encerrar_sessao(
    conexao: Connection,
    token: str | None,
    *,
    repositorio=acesso_repository,
    agora: Callable[[], datetime] = relogio.agora,
    hash_do_token: Callable[[str], str] = seguranca.hash_do_token,
) -> None:
    if not token:
        return
    linha = repositorio.buscar_sessao_por_hash(conexao, hash_do_token(token))
    if linha is None or linha.revogada_em is not None:
        return
    repositorio.revogar_sessao(conexao, linha.id_sessao, agora())
    _logger.info("SESSAO_ENCERRADA id_sessao=%s", linha.id_sessao)


def listar_sessoes_ativas(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=acesso_repository,
    agora: Callable[[], datetime] = relogio.agora,
) -> list:
    return repositorio.listar_sessoes_ativas_do_hotel(conexao, id_hotel, agora())


def revogar_sessao(
    conexao: Connection,
    *,
    id_sessao: int,
    id_hotel_do_ator: int,
    repositorio=acesso_repository,
    agora: Callable[[], datetime] = relogio.agora,
) -> None:
    linha = repositorio.buscar_sessao_por_id(conexao, id_sessao)
    if linha is None or linha.id_hotel != id_hotel_do_ator:
        raise SessaoNaoEncontrada(id_sessao)
    if linha.revogada_em is None:
        repositorio.revogar_sessao(conexao, id_sessao, agora())
        _logger.info("SESSAO_REVOGADA id_sessao=%s", id_sessao)
