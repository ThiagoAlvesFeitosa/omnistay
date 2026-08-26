"""Consumidor da fila de trabalho."""

from sqlalchemy.engine import Connection, Engine

from app.adaptadores.catalogo_banco import CatalogoBanco
from app.adaptadores.fonte_falsa import FonteFalsa
from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.fabrica_mensageria import construir_mensageria
from app.config import obter_configuracao
from app.comum.log import obter_logger
from app.fila import repository as fila_repository
from app.modulos.atendimento import service as atendimento_service
from app.modulos.conversa import service as conversa_service
from app.modulos.hospedagem import service as hospedagem_service
from app.modulos.mercado import service as mercado_service
from app.modulos.propriedade import service as propriedade_service
from app.portas.fonte_publica import FontePublica
from app.portas.llm import LLMProvider
from app.portas.mensageria import MensageriaGateway

logger = obter_logger(__name__)


def processar_uma_passagem(
    conexao: Connection,
    *,
    gateway: MensageriaGateway,
    llm: LLMProvider | None = None,
    catalogo=None,
    fonte: FontePublica | None = None,
    limite: int = 100,
) -> int:
    """Processa ate `limite` trabalhos elegiveis. Devolve quantos foram claims."""
    porta_llm = llm or LLMFalso()
    porta_catalogo = catalogo
    porta_fonte = fonte or FonteFalsa()
    processados = 0
    while processados < limite:
        trabalho = fila_repository.reclamar_proximo(conexao)
        if trabalho is None:
            break
        logger.info(
            "trabalho_claim id_trabalho=%s tipo=%s",
            trabalho["id_trabalho"],
            trabalho["tipo"],
        )
        if trabalho["tipo"] == "enviar_coleta":
            conversa_service.processar_trabalho_enviar_coleta(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "interpretar_ficha":
            conversa_service.processar_trabalho_interpretar_ficha(
                conexao,
                trabalho=trabalho,
                llm=porta_llm,
                consolidar=hospedagem_service.consolidar_ficha_titular,
            )
        elif trabalho["tipo"] == "enviar_lembrete":
            conversa_service.processar_trabalho_enviar_lembrete(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "enviar_boas_vindas":
            conversa_service.processar_trabalho_enviar_boas_vindas(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "classificar_mensagem":
            conversa_service.processar_trabalho_classificar_mensagem(
                conexao,
                trabalho=trabalho,
                llm=porta_llm,
                completar_janela=atendimento_service.completar_janela_se_resposta,
            )
        elif trabalho["tipo"] == "responder_duvida":
            conversa_service.processar_trabalho_responder_duvida(
                conexao,
                trabalho=trabalho,
                llm=porta_llm,
                catalogo=porta_catalogo or CatalogoBanco(conexao),
                gateway=gateway,
            )
        elif trabalho["tipo"] == "registrar_pedido_servico":
            conversa_service.processar_trabalho_registrar_pedido(
                conexao,
                trabalho=trabalho,
                gateway=gateway,
                abrir_servico=atendimento_service.abrir_servico,
                abrir_consumo=atendimento_service.abrir_consumo,
                listar_itens_ativos=propriedade_service.listar_itens_vendaveis_ativos,
                identificar=porta_llm.identificar_item_vendavel,
                ler_preco=propriedade_service.ler_preco_item_ativo,
            )
        elif trabalho["tipo"] == "abrir_chamado_reclamacao":
            conversa_service.processar_trabalho_abrir_chamado(
                conexao,
                trabalho=trabalho,
                gateway=gateway,
                abrir_reclamacao=atendimento_service.abrir_reclamacao,
            )
        elif trabalho["tipo"] == "enviar_confirmacao_resolucao":
            conversa_service.processar_trabalho_enviar_confirmacao_resolucao(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "enviar_pulso":
            conversa_service.processar_trabalho_enviar_pulso(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "registrar_resposta_pulso":
            conversa_service.processar_trabalho_registrar_resposta_pulso(
                conexao,
                trabalho=trabalho,
                gateway=gateway,
                abrir_reclamacao=atendimento_service.abrir_reclamacao,
            )
        elif trabalho["tipo"] == "enviar_pesquisa_saida":
            conversa_service.processar_trabalho_enviar_pesquisa_saida(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "interpretar_pesquisa_saida":
            conversa_service.processar_trabalho_interpretar_pesquisa_saida(
                conexao,
                trabalho=trabalho,
                llm=porta_llm,
            )
        elif trabalho["tipo"] == "enviar_lista_pedidos_chat":
            conversa_service.processar_trabalho_enviar_lista_pedidos_chat(
                conexao, trabalho=trabalho, gateway=gateway
            )
        elif trabalho["tipo"] == "coletar_mercado":
            mercado_service.processar_trabalho_coletar_mercado(
                conexao, trabalho=trabalho, fonte=porta_fonte
            )
        else:
            fila_repository.marcar_falha(
                conexao,
                id_trabalho=trabalho["id_trabalho"],
                tentativas=trabalho["tentativas"] + 1,
                erro="tipo_desconhecido",
            )
        processados += 1
    return processados


def processar_uma_passagem_na_engine(
    engine: Engine,
    *,
    gateway: MensageriaGateway | None = None,
    llm: LLMProvider | None = None,
    catalogo=None,
    fonte: FontePublica | None = None,
) -> int:
    porta = gateway or construir_mensageria(obter_configuracao())
    with engine.begin() as conexao:
        return processar_uma_passagem(
            conexao, gateway=porta, llm=llm, catalogo=catalogo, fonte=fonte
        )
