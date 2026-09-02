"""Regras de hospedagem: reserva, fila e contagem. Sem HTTP e sem SQL."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.comum.log import obter_logger
from app.comum.telefone import TelefoneInvalido, normalizar
from app.modulos.atendimento import service as atendimento_service
from app.modulos.conversa import service as conversa_service
from app.modulos.conversa.validacao_ficha import (
    classificar_desfecho,
    validar_campos_extraidos,
)
from app.modulos.hospedagem import repository as repositorio_padrao
from app.modulos.hospedagem.schema import (
    ChegadaResposta,
    ConsentimentoResposta,
    FichaTitularResposta,
    ItemFilaDoDia,
    ItemPedidoFeitoPeloChat,
    ListaPedidosFeitosPeloChat,
    ReservaResposta,
    SaidaResposta,
)
from app.portas.llm import CAMPOS_FICHA_CHAVE

logger = obter_logger(__name__)


class DadosInvalidos(ValueError):
    """Entrada rejeitada na borda de negocio, com mensagem para o usuario."""


class ReservaNaoEncontrada(Exception):
    pass


class ChegadaNaoPermitida(Exception):
    def __init__(self, status_atual: str) -> None:
        self.status_atual = status_atual
        super().__init__(status_atual)


class SaidaNaoPermitida(Exception):
    def __init__(self, status_atual: str) -> None:
        self.status_atual = status_atual
        super().__init__(status_atual)


class HospedeNaoEncontrado(Exception):
    pass


class DocumentoEmUso(Exception):
    pass


STATUS_CICLO_FICHA = frozenset(
    {"aguardando_cadastro", "ficha_parcial", "ficha_recebida"}
)


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

    def contar_hospedados(self, conexao, *, id_hotel: int) -> int: ...


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
            saida_nao_confirmada=bool(linha.get("saida_nao_confirmada")),
            pesquisa_saida_leitura_humana=bool(
                linha.get("pesquisa_saida_leitura_humana")
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


def contar_hospedados(
    conexao,
    *,
    id_hotel: int,
    repositorio: RepositorioDeHospedagem = repositorio_padrao,
) -> int:
    return repositorio.contar_hospedados(conexao, id_hotel=id_hotel)


def ler_indicadores(
    conexao,
    *,
    id_hotel: int,
    repositorio: RepositorioDeHospedagem = repositorio_padrao,
    atendimento=atendimento_service,
):
    from app.modulos.hospedagem.schema import IndicadoresResposta

    logger.info("indicadores id_hotel=%s acao=indicadores", id_hotel)
    consumo = atendimento.somar_consumo_pendente(conexao, id_hotel=id_hotel)
    return IndicadoresResposta(
        chegadas_hoje=contar_chegadas_do_dia(
            conexao, id_hotel=id_hotel, repositorio=repositorio
        ),
        hospedados=contar_hospedados(
            conexao, id_hotel=id_hotel, repositorio=repositorio
        ),
        chamados_abertos=atendimento.contar_chamados_abertos(
            conexao, id_hotel=id_hotel
        ),
        consumo_a_lancar=Decimal(str(consumo or 0)),
    )


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


def _texto_campo(valor) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor.isoformat()
    texto = str(valor).strip()
    return texto or None


def completar_ficha_titular(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    campos: dict,
    repositorio=repositorio_padrao,
) -> FichaTitularResposta:
    titular = repositorio.ler_titular_da_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if titular is None:
        raise ReservaNaoEncontrada

    informados: dict[str, str] = {}
    gravados: dict[str, str | None] = {}
    for chave in CAMPOS_FICHA_CHAVE:
        texto = _texto_campo(campos.get(chave))
        if texto is None:
            gravados[chave] = None
            continue
        informados[chave] = texto

    if not informados.get("nome_completo"):
        raise DadosInvalidos("Informe o nome.")
    if not informados.get("telefone"):
        raise DadosInvalidos("Informe o telefone.")

    validos = validar_campos_extraidos(informados)
    invalidos = [chave for chave in informados if chave not in validos]
    if invalidos:
        raise DadosInvalidos(f"Campo {invalidos[0]} invalido.")

    for chave, valor in validos.items():
        gravados[chave] = valor

    desfecho = classificar_desfecho(validos)
    completa = desfecho == "completa"
    novo_status = "ficha_recebida" if completa else "ficha_parcial"

    try:
        repositorio.atualizar_hospede_titular(
            conexao, id_hospede=titular["id_hospede"], campos=gravados
        )
    except IntegrityError as erro:
        logger.info(
            "ficha_alterada_recusada id_reserva=%s id_hospede=%s codigo=409",
            id_reserva,
            titular["id_hospede"],
        )
        if "uq_hospede_documento" in str(erro.orig or erro):
            raise DocumentoEmUso from erro
        raise

    repositorio.marcar_ficha_completa(
        conexao, id_reserva=id_reserva, completa=completa
    )
    status_final = titular["status"]
    if titular["status"] in STATUS_CICLO_FICHA:
        repositorio.atualizar_status_reserva(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            status=novo_status,
        )
        status_final = novo_status

    logger.info(
        "ficha_alterada_balcao id_reserva=%s id_hospede=%s status=%s campos=%s",
        id_reserva,
        titular["id_hospede"],
        status_final,
        len(validos),
    )
    return ler_ficha_titular(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        repositorio=repositorio,
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


def listar_rotulos_para_simulador(
    conexao,
    *,
    id_hotel: int,
    repositorio=repositorio_padrao,
) -> list[dict]:
    return repositorio.listar_rotulos_para_simulador(conexao, id_hotel=id_hotel)


def obter_rotulo_para_simulador(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> dict | None:
    return repositorio.obter_rotulo_para_simulador(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
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


def confirmar_saida(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
    agendar_pesquisa_saida=conversa_service.agendar_pesquisa_saida,
    listar_pedidos=atendimento_service.listar_pedidos_feitos_pelo_chat,
    agendar_lista=conversa_service.agendar_lista_pedidos_chat,
) -> SaidaResposta:
    atualizada = repositorio.confirmar_saida(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if atualizada is None:
        existente = repositorio.ler_reserva_do_hotel(
            conexao, id_hotel=id_hotel, id_reserva=id_reserva
        )
        if existente is None:
            raise ReservaNaoEncontrada
        logger.info(
            "saida_recusada id_reserva=%s id_hotel=%s status=%s",
            id_reserva,
            id_hotel,
            existente["status"],
        )
        raise SaidaNaoPermitida(existente["status"])

    titular = repositorio.ler_titular_da_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    nome = titular["nome_completo"] if titular else "hospede"
    desfecho = agendar_pesquisa_saida(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        nome_completo=nome,
    )
    itens = listar_pedidos(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    desfecho_lista = "ausente"
    if itens:
        desfecho_lista = agendar_lista(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            nome_completo=nome,
            itens=itens,
        )
    else:
        logger.info(
            "lista_pedidos_ausente id_reserva=%s id_hotel=%s",
            id_reserva,
            id_hotel,
        )
    logger.info(
        "saida_confirmada id_reserva=%s id_hotel=%s",
        id_reserva,
        id_hotel,
    )
    return SaidaResposta(
        id_reserva=id_reserva,
        status=atualizada["status"],
        checkout_em=atualizada["checkout_em"],
        pesquisa=desfecho,
        lista=desfecho_lista,
    )


def consultar_pedidos_feitos_pelo_chat(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
    listar_pedidos=atendimento_service.listar_pedidos_feitos_pelo_chat,
) -> ListaPedidosFeitosPeloChat:
    existente = repositorio.ler_reserva_do_hotel(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if existente is None:
        raise ReservaNaoEncontrada
    itens = listar_pedidos(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    total = sum(
        (item["valor_praticado"] for item in itens),
        Decimal("0.00"),
    )
    return ListaPedidosFeitosPeloChat(
        id_reserva=id_reserva,
        itens=[
            ItemPedidoFeitoPeloChat(
                id_solicitacao=item["id_solicitacao"],
                descricao_item=item["descricao_item"],
                valor_praticado=item["valor_praticado"],
            )
            for item in itens
        ],
        total=total,
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


FINALIDADE_MARKETING = "comunicacao_marketing"
ORIGENS_PAINEL = frozenset({"painel", "solicitacao_titular"})


def registrar_consentimento_pesquisa(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    concedido: bool | None,
    repositorio=repositorio_padrao,
) -> dict | None:
    if concedido is None:
        return None
    id_hospede = repositorio.id_titular_da_reserva(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if id_hospede is None:
        logger.info(
            "consentimento_pesquisa_sem_titular id_reserva=%s id_hotel=%s",
            id_reserva,
            id_hotel,
        )
        return None
    gravado = repositorio.inserir_consentimento(
        conexao,
        id_hospede=id_hospede,
        concedido=bool(concedido),
        origem="pesquisa_checkout",
    )
    logger.info(
        "consentimento_pesquisa_registrado id_hospede=%s id_reserva=%s"
        " concedido=%s",
        id_hospede,
        id_reserva,
        bool(concedido),
    )
    return gravado


def consultar_consentimento_vigente(
    conexao,
    *,
    id_hotel: int,
    id_hospede: int,
    em: datetime | None = None,
    repositorio=repositorio_padrao,
) -> ConsentimentoResposta:
    if not repositorio.hospede_do_hotel(
        conexao, id_hotel=id_hotel, id_hospede=id_hospede
    ):
        raise HospedeNaoEncontrado
    instante = em or datetime.now(UTC)
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)
    linha = repositorio.ler_consentimento_vigente(
        conexao, id_hospede=id_hospede, em=instante
    )
    if linha is None:
        return ConsentimentoResposta(
            id_hospede=id_hospede,
            finalidade=FINALIDADE_MARKETING,
            concedido=False,
            momento=None,
            origem=None,
            em=instante,
        )
    return ConsentimentoResposta(
        id_hospede=id_hospede,
        finalidade=linha["finalidade"],
        concedido=bool(linha["concedido"]),
        momento=linha["momento"],
        origem=linha["origem"],
        em=instante,
    )


def registrar_consentimento_painel(
    conexao,
    *,
    id_hotel: int,
    id_hospede: int,
    concedido: bool,
    origem: str,
    repositorio=repositorio_padrao,
) -> ConsentimentoResposta:
    if origem not in ORIGENS_PAINEL:
        raise DadosInvalidos("Origem de consentimento invalida.")
    if not repositorio.hospede_do_hotel(
        conexao, id_hotel=id_hotel, id_hospede=id_hospede
    ):
        raise HospedeNaoEncontrado
    gravado = repositorio.inserir_consentimento(
        conexao,
        id_hospede=id_hospede,
        concedido=concedido,
        origem=origem,
    )
    logger.info(
        "consentimento_painel_registrado id_hospede=%s origem=%s concedido=%s",
        id_hospede,
        origem,
        concedido,
    )
    return ConsentimentoResposta(
        id_hospede=id_hospede,
        finalidade=gravado["finalidade"],
        concedido=bool(gravado["concedido"]),
        momento=gravado["momento"],
        origem=gravado["origem"],
        em=gravado["momento"],
    )


def apagar_fichas_vencidas(
    conexao,
    *,
    id_hotel: int,
    agora,
    anos: int,
    repositorio=repositorio_padrao,
) -> int:
    from app.comum.retencao import MARCA_TELEFONE

    return repositorio.apagar_fichas_vencidas(
        conexao,
        id_hotel=id_hotel,
        agora=agora,
        anos=anos,
        marca_telefone=MARCA_TELEFONE,
    )
