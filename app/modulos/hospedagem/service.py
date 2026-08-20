"""Regras de hospedagem: reserva, fila e contagem. Sem HTTP e sem SQL."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.comum.log import obter_logger
from app.comum.telefone import TelefoneInvalido, normalizar
from app.modulos.conversa import service as conversa_service
from app.modulos.hospedagem import repository as repositorio_padrao
from app.modulos.hospedagem.schema import (
    ChegadaResposta,
    FichaTitularResposta,
    ItemFilaDoDia,
    ReservaResposta,
)

logger = obter_logger(__name__)


class DadosInvalidos(ValueError):
    """Entrada rejeitada na borda de negocio, com mensagem para o usuario."""


class ReservaNaoEncontrada(Exception):
    pass


class ChegadaNaoPermitida(Exception):
    def __init__(self, status_atual: str) -> None:
        self.status_atual = status_atual
        super().__init__(status_atual)


class RepositorioDeHospedagem(Protocol):
    def inserir_hospede(self, conexao, *, nome_completo: str, telefone: str) -> int: ...

    def inserir_reserva(
        self,
        conexao,
        *,
        id_hotel: int,
        telefone_contato: str,
        data_checkin_prevista: date,
        data_checkout_prevista: date,
        status: str,
    ) -> int: ...

    def inserir_vinculo_titular(
        self, conexao, *, id_reserva: int, id_hospede: int
    ) -> None: ...

    def listar_fila_do_hotel(self, conexao, *, id_hotel: int) -> list[dict]: ...

    def contar_chegadas_do_dia(self, conexao, *, id_hotel: int) -> int: ...


@dataclass(frozen=True)
class ReservaCriada:
    id_reserva: int
    id_hotel: int
    nome: str
    telefone_contato: str
    data_checkin_prevista: date
    data_checkout_prevista: date
    status: str

    def para_resposta(self) -> ReservaResposta:
        return ReservaResposta(
            id_reserva=self.id_reserva,
            id_hotel=self.id_hotel,
            nome=self.nome,
            telefone_contato=self.telefone_contato,
            data_checkin_prevista=self.data_checkin_prevista,
            data_checkout_prevista=self.data_checkout_prevista,
            status=self.status,
        )


def criar_reserva(
    conexao,
    *,
    id_hotel: int,
    nome: str,
    telefone: str,
    data_checkin_prevista: date,
    data_checkout_prevista: date,
    repositorio: RepositorioDeHospedagem = repositorio_padrao,
    agendar_coleta=conversa_service.agendar_coleta_apos_reserva,
) -> ReservaCriada:
    nome_limpo = nome.strip()
    telefone_bruto = telefone.strip()
    if not nome_limpo:
        raise DadosInvalidos("Informe o nome.")
    if not telefone_bruto:
        raise DadosInvalidos("Informe o telefone de contato.")
    if data_checkout_prevista <= data_checkin_prevista:
        raise DadosInvalidos(
            "A data de saida deve ser posterior a data de entrada."
        )
    try:
        telefone_contato = normalizar(telefone_bruto)
    except TelefoneInvalido as erro:
        raise DadosInvalidos(str(erro)) from erro

    id_hospede = repositorio.inserir_hospede(
        conexao, nome_completo=nome_limpo, telefone=telefone_contato
    )
    id_reserva = repositorio.inserir_reserva(
        conexao,
        id_hotel=id_hotel,
        telefone_contato=telefone_contato,
        data_checkin_prevista=data_checkin_prevista,
        data_checkout_prevista=data_checkout_prevista,
        status="aguardando_cadastro",
    )
    repositorio.inserir_vinculo_titular(
        conexao, id_reserva=id_reserva, id_hospede=id_hospede
    )
    agendar_coleta(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        nome_completo=nome_limpo,
    )
    return ReservaCriada(
        id_reserva=id_reserva,
        id_hotel=id_hotel,
        nome=nome_limpo,
        telefone_contato=telefone_contato,
        data_checkin_prevista=data_checkin_prevista,
        data_checkout_prevista=data_checkout_prevista,
        status="aguardando_cadastro",
    )


def listar_fila_do_dia(
    conexao,
    *,
    id_hotel: int,
    repositorio: RepositorioDeHospedagem = repositorio_padrao,
) -> list[ItemFilaDoDia]:
    linhas = repositorio.listar_fila_do_hotel(conexao, id_hotel=id_hotel)
    return [
        ItemFilaDoDia(
            id_reserva=linha["id_reserva"],
            nome=linha.get("nome_completo"),
            telefone_contato=linha["telefone_contato"],
            data_checkin_prevista=linha["data_checkin_prevista"],
            data_checkout_prevista=linha["data_checkout_prevista"],
            status=linha["status"],
            ficha_completa=linha.get("ficha_completa"),
            chegada_nao_confirmada=bool(linha["chegada_nao_confirmada"]),
            boas_vindas_nao_enviadas=bool(linha.get("boas_vindas_nao_enviadas")),
            precisa_atendimento_humano=bool(
                linha.get("precisa_atendimento_humano")
            ),
            status_envio_coleta=linha.get("status_envio_coleta"),
            estado_cadastro=linha.get("estado_cadastro"),
        )
        for linha in linhas
    ]


def contar_chegadas_do_dia(
    conexao,
    *,
    id_hotel: int,
    repositorio: RepositorioDeHospedagem = repositorio_padrao,
) -> int:
    return repositorio.contar_chegadas_do_dia(conexao, id_hotel=id_hotel)


def consolidar_ficha_titular(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    campos: dict,
    desfecho: str,
    repositorio=repositorio_padrao,
) -> None:
    from app.comum.log import obter_logger

    logger = obter_logger(__name__)
    titular = repositorio.ler_titular_da_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if titular is None:
        raise DadosInvalidos("Reserva ou titular nao encontrado.")
    if titular["status"] != "aguardando_cadastro":
        logger.info(
            "consolidacao_ignorada id_reserva=%s status=%s",
            id_reserva,
            titular["status"],
        )
        return

    limpos = {k: v for k, v in campos.items() if k != "idade"}
    repositorio.atualizar_hospede_titular(
        conexao, id_hospede=titular["id_hospede"], campos=limpos
    )
    completa = desfecho == "completa"
    novo_status = "ficha_recebida" if completa else "ficha_parcial"
    repositorio.marcar_ficha_completa(
        conexao, id_reserva=id_reserva, completa=completa
    )
    repositorio.atualizar_status_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva, status=novo_status
    )
    logger.info(
        "ficha_consolidada id_reserva=%s id_hospede=%s status=%s campos=%s",
        id_reserva,
        titular["id_hospede"],
        novo_status,
        len(limpos),
    )


def ler_ficha_titular(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> FichaTitularResposta:
    titular = repositorio.ler_titular_da_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if titular is None:
        raise DadosInvalidos("Reserva nao encontrada.")
    estado = repositorio.estado_cadastro_da_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    return FichaTitularResposta(
        id_reserva=titular["id_reserva"],
        id_hospede=titular["id_hospede"],
        ficha_completa=bool(titular["ficha_completa"]),
        status_reserva=titular["status"],
        estado_cadastro=estado,
        nome_completo=titular["nome_completo"],
        profissao=titular.get("profissao"),
        data_nascimento=titular.get("data_nascimento"),
        tipo_documento=titular.get("tipo_documento"),
        numero_documento=titular.get("numero_documento"),
        endereco=titular.get("endereco"),
        cep=titular.get("cep"),
        cidade=titular.get("cidade"),
        telefone=titular["telefone"],
    )


def listar_reservas_aguardando_cadastro(
    conexao,
    repositorio=repositorio_padrao,
) -> list[dict]:
    return repositorio.listar_reservas_aguardando_cadastro(conexao)


def marcar_reenvio_realizado(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> None:
    repositorio.marcar_reenvio_realizado(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )


def marcar_sem_cadastro_previo(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> None:
    from app.comum.log import obter_logger

    repositorio.marcar_sem_cadastro_previo(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    obter_logger(__name__).info(
        "sem_cadastro_marcado id_reserva=%s id_hotel=%s",
        id_reserva,
        id_hotel,
    )


def confirmar_chegada(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
    agendar_boas_vindas=conversa_service.agendar_boas_vindas,
) -> ChegadaResposta:
    atualizada = repositorio.confirmar_chegada(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if atualizada is None:
        existente = repositorio.ler_reserva_do_hotel(
            conexao, id_hotel=id_hotel, id_reserva=id_reserva
        )
        if existente is None:
            raise ReservaNaoEncontrada
        logger.info(
            "chegada_recusada id_reserva=%s id_hotel=%s status=%s",
            id_reserva,
            id_hotel,
            existente["status"],
        )
        raise ChegadaNaoPermitida(existente["status"])

    titular = repositorio.ler_titular_da_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    nome = titular["nome_completo"] if titular else "hospede"
    desfecho = agendar_boas_vindas(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        nome_completo=nome,
    )
    logger.info(
        "chegada_confirmada id_reserva=%s id_hotel=%s",
        id_reserva,
        id_hotel,
    )
    return ChegadaResposta(
        id_reserva=id_reserva,
        status=atualizada["status"],
        checkin_em=atualizada["checkin_em"],
        boas_vindas=desfecho,
    )


def listar_hospedados_sem_boas_vindas(
    conexao,
    repositorio=repositorio_padrao,
) -> list[dict]:
    return repositorio.listar_hospedados_sem_boas_vindas(conexao)


def listar_hospedados_sem_pulso(
    conexao,
    repositorio=repositorio_padrao,
) -> list[dict]:
    return repositorio.listar_hospedados_sem_pulso(conexao)
