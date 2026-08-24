"""Regra de solicitacao operacional — sem HTTP e sem mensageria."""

from datetime import UTC, timedelta

from sqlalchemy.engine import Connection

from app.comum import relogio as relogio_padrao
from app.comum.log import obter_logger
from app.modulos.atendimento import repository as repositorio_padrao
from app.modulos.atendimento.schema import LancamentoResposta, ResolucaoResposta
from app.modulos.conversa import service as conversa_service
from app.modulos.atendimento.janela import (
    extrair_janela_preferencia,
    parece_resposta_de_horario,
)
from app.modulos.propriedade import repository as propriedade_repository

URGENCIA_PADRAO = "media"
CHAVE_DESTAQUE = "horas_destaque_chamado_aberto"
logger = obter_logger(__name__)


class HotelIncompativel(Exception):
    """A reserva nao pertence ao hotel do trabalho ou da sessao."""


class SolicitacaoNaoEncontrada(Exception):
    """Solicitacao inexistente neste hotel."""


class ResolucaoNaoPermitida(Exception):
    """Estado ou tipo nao admite esta operacao."""

    def __init__(self, detalhe: str, *, status: str, tipo: str):
        super().__init__(detalhe)
        self.detalhe = detalhe
        self.status = status
        self.tipo = tipo


class LancamentoNaoPermitido(Exception):
    """Consumo ja deixou a fila de pendentes."""

    def __init__(self, detalhe: str, *, status_lancamento: str):
        super().__init__(detalhe)
        self.detalhe = detalhe
        self.status_lancamento = status_lancamento


DETALHE_JA_RESOLVIDA = "Esta solicitacao ja foi resolvida."
DETALHE_CANCELADA = "Solicitacao cancelada nao pode ser resolvida."
DETALHE_ESTADO = "O estado atual da solicitacao nao admite resolucao."
DETALHE_JA_LANCADO = "Este consumo ja foi lancado."
DETALHE_JA_DISPENSADO = "Este consumo ja foi dispensado."


def abrir_servico(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    descricao: str,
    numero_quarto: str | None,
    urgencia: str | None,
    repositorio=repositorio_padrao,
) -> int:
    hotel = repositorio.hotel_da_reserva(conexao, id_reserva=id_reserva)
    if hotel != id_hotel:
        raise HotelIncompativel()
    return repositorio.inserir_servico(
        conexao,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        descricao=descricao,
        numero_quarto=numero_quarto,
        urgencia=urgencia or URGENCIA_PADRAO,
    )


def abrir_reclamacao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    descricao: str,
    numero_quarto: str | None,
    urgencia: str | None,
    janela_preferencia: str | None,
    repositorio=repositorio_padrao,
) -> int:
    hotel = repositorio.hotel_da_reserva(conexao, id_reserva=id_reserva)
    if hotel != id_hotel:
        raise HotelIncompativel()
    return repositorio.inserir_reclamacao(
        conexao,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        descricao=descricao,
        numero_quarto=numero_quarto,
        urgencia=urgencia or URGENCIA_PADRAO,
        janela_preferencia=janela_preferencia,
    )


def tem_reclamacao_aberta(
    conexao: Connection,
    *,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> bool:
    return repositorio.tem_reclamacao_aberta(conexao, id_reserva=id_reserva)


def tem_reclamacao_da_mensagem(
    conexao: Connection,
    *,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> bool:
    return repositorio.tem_reclamacao_da_mensagem(
        conexao, id_mensagem=id_mensagem
    )


def abrir_consumo(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    descricao: str,
    descricao_item: str,
    valor_praticado,
    numero_quarto: str | None,
    urgencia: str | None,
    repositorio=repositorio_padrao,
) -> int:
    hotel = repositorio.hotel_da_reserva(conexao, id_reserva=id_reserva)
    if hotel != id_hotel:
        raise HotelIncompativel()
    return repositorio.inserir_consumo(
        conexao,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        descricao=descricao,
        descricao_item=descricao_item,
        valor_praticado=valor_praticado,
        numero_quarto=numero_quarto,
        urgencia=urgencia or URGENCIA_PADRAO,
    )


def completar_janela_se_resposta(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    texto: str,
    repositorio=repositorio_padrao,
) -> int | None:
    if not parece_resposta_de_horario(texto):
        return None
    hotel = repositorio.hotel_da_reserva(conexao, id_reserva=id_reserva)
    if hotel != id_hotel:
        return None
    janela = extrair_janela_preferencia(texto)
    if janela is None:
        return None
    return repositorio.completar_janela_aberta(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        janela=janela,
    )


def _horas_de_destaque(valor: str | None) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _destaque_excedido(*, tipo: str, aberta_em, agora, horas: float | None) -> bool:
    if horas is None or tipo != "reclamacao" or aberta_em is None:
        return False
    instante = aberta_em
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)
    return agora - instante >= timedelta(hours=horas)


def listar_abertas(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=repositorio_padrao,
    agora=None,
    ler_parametro=None,
    relogio=relogio_padrao,
) -> list[dict]:
    instante = agora if agora is not None else relogio.agora()
    leitor = ler_parametro or propriedade_repository.ler_parametro
    bruto = leitor(conexao, id_hotel, CHAVE_DESTAQUE)
    horas = _horas_de_destaque(bruto)
    if horas is None:
        logger.info(
            "prazo_ausente id_hotel=%s chave=%s resultado=prazo_ausente",
            id_hotel,
            CHAVE_DESTAQUE,
        )
    itens = []
    for item in repositorio.listar_abertas(conexao, id_hotel=id_hotel):
        itens.append(
            {
                "id_solicitacao": item["id_solicitacao"],
                "id_reserva": item["id_reserva"],
                "tipo": item["tipo"],
                "descricao": item["descricao"],
                "numero_quarto": item["numero_quarto"],
                "urgencia": item["urgencia"],
                "status": item["status"],
                "aberta_em": item["aberta_em"],
                "janela_preferencia": item.get("janela_preferencia"),
                "valor_praticado": item.get("valor_praticado"),
                "status_lancamento": item.get("status_lancamento"),
                "destaque_tempo_excedido": _destaque_excedido(
                    tipo=item["tipo"],
                    aberta_em=item["aberta_em"],
                    agora=instante,
                    horas=horas,
                ),
            }
        )
    return itens


def _detalhe_de_recusa(*, status: str, tipo: str) -> str:
    if status == "resolvida":
        return DETALHE_JA_RESOLVIDA
    if status == "cancelada":
        return DETALHE_CANCELADA
    return DETALHE_ESTADO


def _resultado_de_recusa(*, status: str, tipo: str) -> str:
    if status == "resolvida":
        return "ja_resolvida"
    return "estado_incompativel"


def resolver(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
    id_usuario: int,
    repositorio=repositorio_padrao,
    agendar_confirmacao=None,
    relogio=relogio_padrao,
) -> ResolucaoResposta:
    instante = relogio.agora()
    atualizada = repositorio.marcar_resolvida(
        conexao,
        id_hotel=id_hotel,
        id_solicitacao=id_solicitacao,
        id_usuario=id_usuario,
        resolvida_em=instante,
    )
    if atualizada is None:
        existente = repositorio.ler_do_hotel(
            conexao, id_hotel=id_hotel, id_solicitacao=id_solicitacao
        )
        if existente is None:
            logger.info(
                "resolucao_recusada id_solicitacao=%s id_hotel=%s"
                " resultado=nao_encontrada",
                id_solicitacao,
                id_hotel,
            )
            raise SolicitacaoNaoEncontrada
        logger.info(
            "resolucao_recusada id_solicitacao=%s id_hotel=%s resultado=%s",
            id_solicitacao,
            id_hotel,
            _resultado_de_recusa(
                status=existente["status"], tipo=existente["tipo"]
            ),
        )
        raise ResolucaoNaoPermitida(
            _detalhe_de_recusa(
                status=existente["status"], tipo=existente["tipo"]
            ),
            status=existente["status"],
            tipo=existente["tipo"],
        )

    agendar = agendar_confirmacao or conversa_service.agendar_confirmacao_resolucao
    desfecho = agendar(
        conexao,
        id_hotel=id_hotel,
        id_reserva=atualizada["id_reserva"],
        id_solicitacao=atualizada["id_solicitacao"],
        tipo=atualizada["tipo"],
    )
    logger.info(
        "chamado_resolvido id_solicitacao=%s id_hotel=%s id_usuario=%s"
        " resultado=resolvido",
        atualizada["id_solicitacao"],
        id_hotel,
        id_usuario,
    )
    return ResolucaoResposta(
        id_solicitacao=atualizada["id_solicitacao"],
        tipo=atualizada["tipo"],
        status=atualizada["status"],
        resolvida_em=atualizada["resolvida_em"],
        id_usuario_responsavel=atualizada["id_usuario_responsavel"],
        confirmacao=desfecho,
    )


def listar_pendentes(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=repositorio_padrao,
) -> list[dict]:
    itens = []
    for item in repositorio.listar_pendentes(conexao, id_hotel=id_hotel):
        itens.append(
            {
                "id_solicitacao": item["id_solicitacao"],
                "id_reserva": item["id_reserva"],
                "descricao": item["descricao"],
                "descricao_item": item["descricao_item"],
                "numero_quarto": item["numero_quarto"],
                "valor_praticado": item["valor_praticado"],
                "status_lancamento": item["status_lancamento"],
                "aberta_em": item["aberta_em"],
                "resolvida_em": item.get("resolvida_em"),
            }
        )
    return itens


def listar_pedidos_feitos_pelo_chat(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> list[dict]:
    itens = []
    for item in repositorio.listar_pedidos_feitos_pelo_chat(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    ):
        itens.append(
            {
                "id_solicitacao": item["id_solicitacao"],
                "descricao_item": item["descricao_item"],
                "valor_praticado": item["valor_praticado"],
            }
        )
    return itens


def _aplicar_lancamento(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
    id_usuario: int,
    status_destino: str,
    evento: str,
    repositorio,
    relogio,
) -> LancamentoResposta:
    instante = relogio.agora()
    atualizada = repositorio.marcar_lancamento(
        conexao,
        id_hotel=id_hotel,
        id_solicitacao=id_solicitacao,
        id_usuario=id_usuario,
        lancado_em=instante,
        status_destino=status_destino,
    )
    if atualizada is None:
        existente = repositorio.ler_consumo_do_hotel(
            conexao, id_hotel=id_hotel, id_solicitacao=id_solicitacao
        )
        if existente is None:
            logger.info(
                "%s id_solicitacao=%s id_hotel=%s resultado=nao_encontrada",
                evento,
                id_solicitacao,
                id_hotel,
            )
            raise SolicitacaoNaoEncontrada
        status = existente["status_lancamento"]
        detalhe = (
            DETALHE_JA_LANCADO if status == "lancado" else DETALHE_JA_DISPENSADO
        )
        logger.info(
            "%s id_solicitacao=%s id_hotel=%s resultado=ja_terminal",
            evento,
            id_solicitacao,
            id_hotel,
        )
        raise LancamentoNaoPermitido(detalhe, status_lancamento=status)
    logger.info(
        "%s id_solicitacao=%s id_hotel=%s id_usuario=%s resultado=%s",
        evento,
        atualizada["id_solicitacao"],
        id_hotel,
        id_usuario,
        status_destino,
    )
    return LancamentoResposta(
        id_solicitacao=atualizada["id_solicitacao"],
        status_lancamento=atualizada["status_lancamento"],
        id_usuario_lancamento=atualizada["id_usuario_lancamento"],
        lancado_em=atualizada["lancado_em"],
    )


def lancar(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
    id_usuario: int,
    repositorio=repositorio_padrao,
    relogio=relogio_padrao,
) -> LancamentoResposta:
    return _aplicar_lancamento(
        conexao,
        id_hotel=id_hotel,
        id_solicitacao=id_solicitacao,
        id_usuario=id_usuario,
        status_destino="lancado",
        evento="consumo_lancado",
        repositorio=repositorio,
        relogio=relogio,
    )


def dispensar(
    conexao: Connection,
    *,
    id_hotel: int,
    id_solicitacao: int,
    id_usuario: int,
    repositorio=repositorio_padrao,
    relogio=relogio_padrao,
) -> LancamentoResposta:
    return _aplicar_lancamento(
        conexao,
        id_hotel=id_hotel,
        id_solicitacao=id_solicitacao,
        id_usuario=id_usuario,
        status_destino="dispensado",
        evento="consumo_dispensado",
        repositorio=repositorio,
        relogio=relogio,
    )


def anonimizar_descricoes_vencidas(
    conexao: Connection,
    *,
    id_hotel: int,
    agora,
    meses: int,
    repositorio=repositorio_padrao,
) -> int:
    from app.comum.retencao import MARCA_TEXTO

    return repositorio.anonimizar_descricoes_vencidas(
        conexao,
        id_hotel=id_hotel,
        agora=agora,
        meses=meses,
        marca=MARCA_TEXTO,
    )
