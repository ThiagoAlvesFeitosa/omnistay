"""Regras de conversa: agendar coleta e espelhar status de envio."""

from sqlalchemy.engine import Connection

from app.comum.log import obter_logger
from app.fila import service as fila_service
from app.modulos.conversa import repository as repositorio_padrao
from app.modulos.conversa.texto_coleta import montar_texto_coleta
from app.modulos.propriedade import repository as propriedade_repository
from app.portas.mensageria import FalhaDeEnvio, MensageriaGateway

logger = obter_logger(__name__)

CHAVE_CONTATO = "contato_responsavel_dados"


def agendar_coleta_apos_reserva(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    nome_completo: str,
    repositorio=repositorio_padrao,
    repositorio_propriedade=propriedade_repository,
    enfileirar=fila_service.enfileirar_enviar_coleta,
) -> int:
    contato = repositorio_propriedade.ler_parametro(conexao, id_hotel, CHAVE_CONTATO)
    if not contato:
        contato = "recepcao do hotel"
    texto = montar_texto_coleta(
        nome_completo=nome_completo,
        contato_responsavel_dados=contato,
    )
    id_mensagem = repositorio.inserir_mensagem_enviada_pendente(
        conexao, id_reserva=id_reserva, conteudo=texto
    )
    enfileirar(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
    )
    logger.info(
        "coleta_agendada id_reserva=%s id_mensagem=%s id_hotel=%s",
        id_reserva,
        id_mensagem,
        id_hotel,
    )
    return id_mensagem


def marcar_envio_sucesso(
    conexao: Connection,
    *,
    id_mensagem: int,
    id_externo: str | None,
    repositorio=repositorio_padrao,
) -> None:
    repositorio.atualizar_status_envio(
        conexao,
        id_mensagem=id_mensagem,
        status_envio="enviada",
        id_externo=id_externo,
    )
    logger.info(
        "coleta_enviada id_mensagem=%s id_externo=%s",
        id_mensagem,
        id_externo,
    )


def marcar_envio_falha(
    conexao: Connection,
    *,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> None:
    repositorio.atualizar_status_envio(
        conexao, id_mensagem=id_mensagem, status_envio="falha"
    )
    logger.info("coleta_falha id_mensagem=%s", id_mensagem)


def processar_trabalho_enviar_coleta(
    conexao: Connection,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    repositorio=repositorio_padrao,
) -> None:
    from app.fila import repository as fila_repo
    from app.fila import service as fila_svc

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])
    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    if mensagem is None:
        fila_repo.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=trabalho["tentativas"] + 1,
            erro="mensagem_ausente",
        )
        return
    telefone = repositorio.ler_telefone_da_reserva(conexao, id_reserva=id_reserva)
    if not telefone:
        fila_repo.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=trabalho["tentativas"] + 1,
            erro="telefone_ausente",
        )
        marcar_envio_falha(conexao, id_mensagem=id_mensagem, repositorio=repositorio)
        return
    prenome = primeiro_nome_do_conteudo_ou_reserva(mensagem["conteudo"])
    try:
        resultado = gateway.enviar_coleta(
            telefone_destino=telefone,
            primeiro_nome=prenome,
            corpo=mensagem["conteudo"],
            id_mensagem=id_mensagem,
            id_reserva=id_reserva,
        )
    except FalhaDeEnvio as erro:
        destino = fila_svc.registrar_falha_de_envio(
            conexao,
            id_trabalho=id_trabalho,
            id_hotel=id_hotel,
            tentativas_atuais=trabalho["tentativas"],
            codigo_erro=erro.codigo,
        )
        if destino == "falha":
            marcar_envio_falha(
                conexao, id_mensagem=id_mensagem, repositorio=repositorio
            )
        logger.info(
            "coleta_tentativa_falhou id_trabalho=%s destino=%s codigo=%s",
            id_trabalho,
            destino,
            erro.codigo,
        )
        return
    marcar_envio_sucesso(
        conexao,
        id_mensagem=id_mensagem,
        id_externo=resultado.id_externo,
        repositorio=repositorio,
    )
    fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)


def primeiro_nome_do_conteudo_ou_reserva(conteudo: str) -> str:
    # "Ola, Maria!" no inicio do texto montado
    if conteudo.startswith("Ola, ") and "!" in conteudo:
        return conteudo[len("Ola, ") : conteudo.index("!")]
    return "hospede"
