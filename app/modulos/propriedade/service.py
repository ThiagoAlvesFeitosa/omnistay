"""Criacao inicial da propriedade e leitura de parametros operacionais."""

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.engine import Connection

from app.modulos.acesso import service as acesso_service
from app.modulos.propriedade import repository as propriedade_repository

DURACOES_PADRAO = {
    "duracao_sessao_recepcao_horas": "12",
    "duracao_sessao_staff_horas": "720",
    "duracao_sessao_gestor_horas": "12",
}

PARAMETROS_COLETA_PADRAO = {
    "tentativas_max_envio_mensagem": "5",
}

PARAMETROS_SILENCIO_PADRAO = {
    "horas_ate_reenvio": "24",
    "horas_corte_antes_checkin": "12",
}

CHAVE_DE_DURACAO_POR_PERFIL = {
    "recepcao": "duracao_sessao_recepcao_horas",
    "staff": "duracao_sessao_staff_horas",
    "gestor": "duracao_sessao_gestor_horas",
}


class InstalacaoJaExiste(Exception):
    pass


class DuracaoNaoConfigurada(Exception):
    pass


@dataclass(frozen=True)
class InstalacaoCriada:
    id_hotel: int
    email_gestor: str


def criar_instalacao_inicial(
    conexao: Connection,
    *,
    nome_hotel: str,
    telefone_whatsapp: str,
    nome_gestor: str,
    email_gestor: str,
    senha_gestor: str,
    repositorio=propriedade_repository,
    servico_de_usuario=acesso_service,
) -> InstalacaoCriada:
    if repositorio.existe_propriedade(conexao):
        raise InstalacaoJaExiste(
            "Ja existe propriedade cadastrada; o bootstrap nao altera nada."
        )

    id_hotel = repositorio.inserir_hotel(conexao, nome_hotel, telefone_whatsapp)
    servico_de_usuario.criar_usuario(
        conexao,
        id_hotel=id_hotel,
        nome=nome_gestor,
        email=email_gestor,
        perfil="gestor",
        senha=senha_gestor,
    )
    for chave, valor in DURACOES_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    repositorio.inserir_parametro(
        conexao, id_hotel, "contato_responsavel_dados", telefone_whatsapp
    )
    for chave, valor in PARAMETROS_COLETA_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    for chave, valor in PARAMETROS_SILENCIO_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)

    return InstalacaoCriada(id_hotel=id_hotel, email_gestor=email_gestor)


def duracao_da_sessao_em_horas(
    conexao: Connection,
    *,
    id_hotel: int,
    perfil: str,
    repositorio=propriedade_repository,
) -> int:
    chave = CHAVE_DE_DURACAO_POR_PERFIL.get(perfil)
    if chave is None:
        raise DuracaoNaoConfigurada(f"Perfil sem chave de duracao: {perfil}")

    valor = repositorio.ler_parametro(conexao, id_hotel, chave)
    if valor is None:
        raise DuracaoNaoConfigurada(
            f"Parametro {chave} ausente para o hotel {id_hotel}"
        )
    return int(valor)
