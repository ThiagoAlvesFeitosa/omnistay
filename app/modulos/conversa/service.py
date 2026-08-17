"""Regras de conversa: agendar coleta, receber webhook e extrair ficha."""

from contextlib import nullcontext

from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.comum.log import obter_logger
from app.comum.telefone import TelefoneInvalido, normalizar
from app.fila import service as fila_service
from app.modulos.conversa import repository as repositorio_padrao
from app.modulos.conversa.schema import EventoEntrada
from app.modulos.conversa.texto_boas_vindas import montar_texto_boas_vindas
from app.modulos.conversa.texto_coleta import montar_texto_coleta
from app.modulos.conversa.texto_lembrete import montar_texto_lembrete
from app.modulos.conversa.validacao_ficha import refinar_resultado
from app.modulos.propriedade import repository as propriedade_repository
from app.modulos.propriedade import service as propriedade_service
from app.portas.llm import FalhaDeExtracao, LLMProvider, ResultadoExtracao
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


def agendar_lembrete(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    nome_completo: str,
    repositorio=repositorio_padrao,
    enfileirar=fila_service.enfileirar_enviar_lembrete,
) -> int:
    texto = montar_texto_lembrete(nome_completo=nome_completo)
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
        "lembrete_agendado id_reserva=%s id_mensagem=%s id_hotel=%s",
        id_reserva,
        id_mensagem,
        id_hotel,
    )
    return id_mensagem


CHAVES_SLOTS_BOAS_VINDAS = (
    ("cafe", "boas_vindas_cafe"),
    ("wifi", "boas_vindas_wifi"),
    ("checkout", "boas_vindas_checkout"),
)


def _savepoint(conexao):
    begin = getattr(conexao, "begin_nested", None)
    if begin is None:
        return nullcontext()
    return begin()


def agendar_boas_vindas(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    nome_completo: str,
    repositorio=repositorio_padrao,
    repositorio_propriedade=propriedade_repository,
    enfileirar=fila_service.enfileirar_enviar_boas_vindas,
) -> str:
    lidos = repositorio_propriedade.ler_parametros(
        conexao,
        id_hotel,
        [chave for _, chave in CHAVES_SLOTS_BOAS_VINDAS],
    )
    valores = {}
    for campo, chave in CHAVES_SLOTS_BOAS_VINDAS:
        try:
            valores[campo] = propriedade_service.validar_texto_de_boas_vindas(
                campo, lidos.get(chave) or ""
            )
        except propriedade_service.DadosInvalidos:
            logger.info(
                "boas_vindas_bloqueadas motivo=slot_invalido chave=%s "
                "id_reserva=%s id_hotel=%s",
                chave,
                id_reserva,
                id_hotel,
            )
            return "nao_enviada_slot_ausente"
    texto = montar_texto_boas_vindas(
        nome_completo=nome_completo,
        cafe=valores["cafe"],
        wifi=valores["wifi"],
        checkout=valores["checkout"],
    )
    try:
        with _savepoint(conexao):
            id_mensagem = repositorio.inserir_mensagem_enviada_pendente(
                conexao, id_reserva=id_reserva, conteudo=texto
            )
            enfileirar(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
            )
    except IntegrityError:
        logger.info(
            "boas_vindas_ja_agendadas id_reserva=%s id_hotel=%s",
            id_reserva,
            id_hotel,
        )
        return "ja_agendada"
    logger.info(
        "boas_vindas_agendadas id_reserva=%s id_mensagem=%s id_hotel=%s",
        id_reserva,
        id_mensagem,
        id_hotel,
    )
    return "agendada"


def tem_mensagem_recebida(
    conexao: Connection,
    *,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> bool:
    return repositorio.tem_mensagem_recebida(conexao, id_reserva=id_reserva)


def instante_coleta_enviada(
    conexao: Connection,
    *,
    id_reserva: int,
    repositorio=repositorio_padrao,
):
    return repositorio.instante_coleta_enviada(conexao, id_reserva=id_reserva)


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
    _processar_trabalho_de_envio(
        conexao,
        trabalho=trabalho,
        enviar=gateway.enviar_coleta,
        repositorio=repositorio,
    )


def processar_trabalho_enviar_lembrete(
    conexao: Connection,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    repositorio=repositorio_padrao,
) -> None:
    _processar_trabalho_de_envio(
        conexao,
        trabalho=trabalho,
        enviar=gateway.enviar_lembrete,
        repositorio=repositorio,
    )


def processar_trabalho_enviar_boas_vindas(
    conexao: Connection,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    repositorio=repositorio_padrao,
    repositorio_propriedade=propriedade_repository,
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
    lidos = repositorio_propriedade.ler_parametros(
        conexao,
        id_hotel,
        [chave for _, chave in CHAVES_SLOTS_BOAS_VINDAS],
    )
    valores = {}
    for campo, chave in CHAVES_SLOTS_BOAS_VINDAS:
        try:
            valores[campo] = propriedade_service.validar_texto_de_boas_vindas(
                campo, lidos.get(chave) or ""
            )
        except propriedade_service.DadosInvalidos:
            fila_svc.registrar_falha_de_envio(
                conexao,
                id_trabalho=id_trabalho,
                id_hotel=id_hotel,
                tentativas_atuais=trabalho["tentativas"],
                codigo_erro="slot_invalido",
            )
            marcar_envio_falha(
                conexao, id_mensagem=id_mensagem, repositorio=repositorio
            )
            logger.info(
                "envio_tentativa_falhou id_trabalho=%s tipo=%s destino=falha "
                "codigo=slot_invalido",
                id_trabalho,
                trabalho.get("tipo"),
            )
            return
    prenome = primeiro_nome_do_conteudo_ou_reserva(mensagem["conteudo"])
    try:
        resultado = gateway.enviar_boas_vindas(
            telefone_destino=telefone,
            variaveis=(
                prenome,
                valores["cafe"],
                valores["wifi"],
                valores["checkout"],
            ),
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
            "envio_tentativa_falhou id_trabalho=%s tipo=%s destino=%s codigo=%s",
            id_trabalho,
            trabalho.get("tipo"),
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
    logger.info(
        "boas_vindas_enviadas id_mensagem=%s id_externo=%s",
        id_mensagem,
        resultado.id_externo,
    )


def _processar_trabalho_de_envio(
    conexao: Connection,
    *,
    trabalho: dict,
    enviar,
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
        resultado = enviar(
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
            "envio_tentativa_falhou id_trabalho=%s tipo=%s destino=%s codigo=%s",
            id_trabalho,
            trabalho.get("tipo"),
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
    if conteudo.startswith("Ola, ") and "!" in conteudo:
        return conteudo[len("Ola, ") : conteudo.index("!")]
    return "hospede"


def receber_evento_entrada(
    conexao: Connection,
    *,
    evento: EventoEntrada,
    id_hotel: int,
    repositorio=repositorio_padrao,
    enfileirar=fila_service.enfileirar_interpretar_ficha,
    enfileirar_estadia=fila_service.enfileirar_classificar_mensagem,
) -> dict:
    """Grava evento (+ mensagem/trabalho se elegivel). Nao chama LLM."""
    payload = {
        "id_externo": evento.id_externo,
        "tem_texto_utilizavel": evento.tem_texto_utilizavel,
    }
    id_evento = repositorio.inserir_evento_webhook(
        conexao, id_externo=evento.id_externo, payload=payload
    )
    if id_evento is None:
        logger.info("webhook_duplicado id_externo=%s", evento.id_externo)
        return {"status": "duplicado"}

    if not evento.tem_texto_utilizavel:
        logger.info(
            "webhook_sem_texto id_evento=%s id_hotel=%s", id_evento, id_hotel
        )
        return {"status": "sem_texto", "id_evento": id_evento}

    try:
        telefone = normalizar(evento.telefone_origem)
    except TelefoneInvalido:
        logger.info("webhook_telefone_invalido id_evento=%s", id_evento)
        return {"status": "telefone_invalido", "id_evento": id_evento}

    reserva = repositorio.resolver_reserva_aguardando_cadastro(
        conexao, id_hotel=id_hotel, telefone_contato=telefone
    )
    destino = "ficha"
    if reserva is None:
        reserva = repositorio.resolver_reserva_hospedada(
            conexao, id_hotel=id_hotel, telefone_contato=telefone
        )
        destino = "estadia"
    if reserva is None:
        logger.info(
            "webhook_sem_reserva id_evento=%s id_hotel=%s", id_evento, id_hotel
        )
        return {"status": "sem_reserva", "id_evento": id_evento}

    id_mensagem = repositorio.inserir_mensagem_recebida(
        conexao,
        id_reserva=reserva["id_reserva"],
        conteudo=evento.texto,
        id_externo=evento.id_mensagem_canal,
        enviada_em=evento.instante_origem,
    )
    enfileirar_fn = enfileirar if destino == "ficha" else enfileirar_estadia
    try:
        id_trabalho = enfileirar_fn(
            conexao,
            id_hotel=id_hotel,
            id_reserva=reserva["id_reserva"],
            id_mensagem=id_mensagem,
            id_evento=id_evento,
        )
    except IntegrityError:
        logger.info(
            "webhook_trabalho_duplicado id_evento=%s id_mensagem=%s",
            id_evento,
            id_mensagem,
        )
        id_trabalho = None
    logger.info(
        "webhook_enfileirado id_evento=%s id_mensagem=%s id_trabalho=%s"
        " id_reserva=%s",
        id_evento,
        id_mensagem,
        id_trabalho,
        reserva["id_reserva"],
    )
    return {
        "status": "enfileirado",
        "id_evento": id_evento,
        "id_mensagem": id_mensagem,
        "id_trabalho": id_trabalho,
        "id_reserva": reserva["id_reserva"],
    }


def extrair_campos_via_llm(
    conexao: Connection,
    *,
    id_mensagem: int,
    llm: LLMProvider,
    repositorio=repositorio_padrao,
) -> ResultadoExtracao:
    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    if mensagem is None:
        raise FalhaDeExtracao("mensagem_ausente")
    bruto = llm.extrair_ficha(mensagem["conteudo"])
    refinado = refinar_resultado(bruto)
    classificacao = {
        "tipo": "extracao_ficha",
        "desfecho": refinado.desfecho,
        "campos_reconhecidos": list(refinado.campos_reconhecidos),
    }
    repositorio.gravar_classificacao_bruta(
        conexao, id_mensagem=id_mensagem, classificacao=classificacao
    )
    logger.info(
        "ficha_extraida id_mensagem=%s desfecho=%s campos=%s",
        id_mensagem,
        refinado.desfecho,
        len(refinado.campos_reconhecidos),
    )
    return refinado


def marcar_falha_extrator(
    conexao: Connection,
    *,
    id_mensagem: int,
    repositorio=repositorio_padrao,
) -> None:
    repositorio.gravar_classificacao_bruta(
        conexao,
        id_mensagem=id_mensagem,
        classificacao={
            "tipo": "extracao_ficha",
            "desfecho": "falha_extrator",
            "campos_reconhecidos": [],
        },
    )
    logger.info("ficha_falha_extrator id_mensagem=%s", id_mensagem)


def processar_trabalho_interpretar_ficha(
    conexao: Connection,
    *,
    trabalho: dict,
    llm: LLMProvider,
    consolidar,
    repositorio=repositorio_padrao,
) -> None:
    """Extrai via LLM e chama consolidar(completa/parcial). Sem import de hospedagem."""
    from app.fila import repository as fila_repo
    from app.fila import service as fila_svc

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])

    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    if mensagem and mensagem.get("classificacao_bruta"):
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "interpretar_ja_concluido id_trabalho=%s id_mensagem=%s",
            id_trabalho,
            id_mensagem,
        )
        return

    try:
        resultado = extrair_campos_via_llm(
            conexao, id_mensagem=id_mensagem, llm=llm, repositorio=repositorio
        )
    except FalhaDeExtracao as erro:
        destino = fila_svc.registrar_falha_de_envio(
            conexao,
            id_trabalho=id_trabalho,
            id_hotel=id_hotel,
            tentativas_atuais=trabalho["tentativas"],
            codigo_erro=erro.codigo,
        )
        if destino == "falha":
            marcar_falha_extrator(
                conexao, id_mensagem=id_mensagem, repositorio=repositorio
            )
        logger.info(
            "interpretar_tentativa_falhou id_trabalho=%s destino=%s codigo=%s",
            id_trabalho,
            destino,
            erro.codigo,
        )
        return

    if resultado.desfecho in ("completa", "parcial"):
        consolidar(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            campos=resultado.campos,
            desfecho=resultado.desfecho,
        )
    fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
