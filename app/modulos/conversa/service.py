"""Regras de conversa: agendar coleta, receber webhook e extrair ficha."""

from contextlib import nullcontext

from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.comum.log import obter_logger
from app.comum.telefone import TelefoneInvalido, normalizar
from app.fila import service as fila_service
from app.modulos.conversa import repository as repositorio_padrao
from app.modulos.conversa.classificacao import desfecho_de, validar_classificacao
from app.modulos.conversa.schema import EventoEntrada
from app.modulos.conversa.texto_boas_vindas import montar_texto_boas_vindas
from app.modulos.conversa.texto_coleta import montar_texto_coleta, primeiro_nome
from app.modulos.conversa.texto_lembrete import montar_texto_lembrete
from app.modulos.conversa.texto_pulso import (
    montar_confirmacao_pulso_negativo,
    montar_pergunta_pulso,
    montar_reconhecimento_pulso,
)
from app.modulos.conversa.texto_pesquisa_saida import montar_texto_pesquisa_saida
from app.modulos.conversa.validacao_ficha import refinar_resultado
from app.modulos.propriedade import repository as propriedade_repository
from app.modulos.propriedade import service as propriedade_service
from app.portas.llm import (
    FalhaDeClassificacao,
    FalhaDeConversacao,
    FalhaDeExtracao,
    FalhaDeIdentificacao,
    LLMProvider,
    ResultadoExtracao,
    ResultadoPesquisaSaida,
)
from app.portas.mensageria import FalhaDeEnvio, MensageriaGateway
from app.modulos.conversa.fidelidade import resposta_fiel_ao_catalogo
from app.modulos.conversa.texto_aviso_duvida import montar_aviso_duvida_nao_coberta
from app.modulos.conversa.texto_confirmacao_resolucao import (
    montar_confirmacao_resolucao,
)

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


def agendar_pulso(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    nome_completo: str,
    repositorio=repositorio_padrao,
    enfileirar=fila_service.enfileirar_enviar_pulso,
) -> str:
    texto = montar_pergunta_pulso(nome_completo=nome_completo)
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
            "pulso_ja_agendado id_reserva=%s id_hotel=%s",
            id_reserva,
            id_hotel,
        )
        return "ja_agendado"
    logger.info(
        "pulso_agendado id_reserva=%s id_mensagem=%s id_hotel=%s",
        id_reserva,
        id_mensagem,
        id_hotel,
    )
    return "agendada"


CHAVE_ATRIBUICAO_PESQUISA = "horas_atribuicao_pesquisa_saida"


def agendar_pesquisa_saida(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    nome_completo: str,
    repositorio=repositorio_padrao,
    enfileirar=fila_service.enfileirar_enviar_pesquisa_saida,
) -> str:
    texto = montar_texto_pesquisa_saida(nome_completo=nome_completo)
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
            "pesquisa_saida_ja_agendada id_reserva=%s id_hotel=%s",
            id_reserva,
            id_hotel,
        )
        return "ja_agendada"
    logger.info(
        "pesquisa_saida_agendada id_reserva=%s id_mensagem=%s id_hotel=%s",
        id_reserva,
        id_mensagem,
        id_hotel,
    )
    return "agendada"


def agendar_confirmacao_resolucao(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    id_solicitacao: int,
    tipo: str,
    repositorio=repositorio_padrao,
    enfileirar=fila_service.enfileirar_enviar_confirmacao_resolucao,
) -> str:
    nome = "hospede"
    ler_nome = getattr(repositorio, "ler_nome_titular", None)
    if ler_nome is not None:
        nome = ler_nome(conexao, id_reserva=id_reserva) or "hospede"
    texto = montar_confirmacao_resolucao(nome_completo=nome, tipo=tipo)
    try:
        with _savepoint(conexao):
            id_mensagem = repositorio.inserir_mensagem_enviada_pendente(
                conexao, id_reserva=id_reserva, conteudo=texto
            )
            repositorio.gravar_classificacao_bruta(
                conexao,
                id_mensagem=id_mensagem,
                classificacao={
                    "tipo": "confirmacao_resolucao",
                    "id_solicitacao": id_solicitacao,
                },
            )
            enfileirar(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_solicitacao=id_solicitacao,
                id_mensagem=id_mensagem,
            )
    except IntegrityError:
        logger.info(
            "resolucao_ja_agendada id_solicitacao=%s id_hotel=%s"
            " resultado=ja_agendada",
            id_solicitacao,
            id_hotel,
        )
        return "ja_agendada"
    logger.info(
        "resolucao_confirmacao_agendada id_solicitacao=%s id_mensagem=%s"
        " id_hotel=%s resultado=agendada",
        id_solicitacao,
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
    enfileirar_pesquisa=fila_service.enfileirar_interpretar_pesquisa_saida,
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
        resolver_pesquisa = getattr(
            repositorio, "resolver_reserva_encerrada_pesquisa", None
        )
        if resolver_pesquisa is not None:
            reserva = resolver_pesquisa(
                conexao, id_hotel=id_hotel, telefone_contato=telefone
            )
        destino = "pesquisa"
    if reserva is None:
        resolver_encerrada = getattr(
            repositorio, "resolver_reserva_encerrada", None
        )
        if resolver_encerrada is not None:
            reserva = resolver_encerrada(
                conexao, id_hotel=id_hotel, telefone_contato=telefone
            )
        if reserva is None:
            logger.info(
                "webhook_sem_reserva id_evento=%s id_hotel=%s",
                id_evento,
                id_hotel,
            )
            return {"status": "sem_reserva", "id_evento": id_evento}
        id_mensagem = repositorio.inserir_mensagem_recebida(
            conexao,
            id_reserva=reserva["id_reserva"],
            conteudo=evento.texto,
            id_externo=evento.id_mensagem_canal,
            enviada_em=evento.instante_origem,
        )
        gravar = getattr(repositorio, "gravar_classificacao_bruta", None)
        if gravar is not None:
            gravar(
                conexao,
                id_mensagem=id_mensagem,
                classificacao={
                    "tipo": "pesquisa_saida",
                    "desfecho": "fora_da_janela",
                },
            )
        logger.info(
            "webhook_encerrada_sem_trabalho id_evento=%s id_mensagem=%s"
            " id_reserva=%s",
            id_evento,
            id_mensagem,
            reserva["id_reserva"],
        )
        return {
            "status": "registrada",
            "id_evento": id_evento,
            "id_mensagem": id_mensagem,
            "id_reserva": reserva["id_reserva"],
        }

    id_mensagem = repositorio.inserir_mensagem_recebida(
        conexao,
        id_reserva=reserva["id_reserva"],
        conteudo=evento.texto,
        id_externo=evento.id_mensagem_canal,
        enviada_em=evento.instante_origem,
    )
    try:
        if destino == "pesquisa":
            id_trabalho = enfileirar_pesquisa(
                conexao,
                id_hotel=id_hotel,
                id_reserva=reserva["id_reserva"],
                id_mensagem=id_mensagem,
            )
        else:
            enfileirar_fn = (
                enfileirar if destino == "ficha" else enfileirar_estadia
            )
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


def _json_classificacao(valor):
    if valor is None:
        return None
    if isinstance(valor, dict):
        return valor
    import json

    if isinstance(valor, str):
        return json.loads(valor)
    return dict(valor)


def processar_trabalho_classificar_mensagem(
    conexao: Connection,
    *,
    trabalho: dict,
    llm: LLMProvider,
    repositorio=repositorio_padrao,
    enfileirar_resposta=None,
    enfileirar_pedido=None,
    enfileirar_chamado=None,
    enfileirar_pulso=None,
    completar_janela=None,
) -> None:
    """Classifica mensagem de estadia. Sem envio, sem INSERT de solicitacao."""
    from app.fila import repository as fila_repo
    from app.fila import service as fila_svc

    if enfileirar_resposta is None:
        enfileirar_resposta = fila_svc.enfileirar_responder_duvida
    if enfileirar_pedido is None:
        enfileirar_pedido = fila_svc.enfileirar_registrar_pedido_servico
    if enfileirar_chamado is None:
        enfileirar_chamado = fila_svc.enfileirar_abrir_chamado_reclamacao
    if enfileirar_pulso is None:
        enfileirar_pulso = fila_svc.enfileirar_registrar_resposta_pulso

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])

    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    if completar_janela is not None and mensagem is not None:
        id_solicitacao = completar_janela(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            texto=mensagem.get("conteudo") or "",
        )
        if id_solicitacao:
            repositorio.gravar_classificacao_intencao(
                conexao,
                id_hotel=id_hotel,
                id_mensagem=id_mensagem,
                intencao=None,
                sentimento=None,
                urgencia=None,
                classificacao={
                    "tipo": "classificacao_intencao",
                    "desfecho": "janela_registrada",
                    "id_solicitacao": id_solicitacao,
                },
            )
            fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
            logger.info(
                "janela_registrada id_trabalho=%s id_mensagem=%s id_hotel=%s"
                " id_solicitacao=%s resultado=janela_registrada",
                id_trabalho,
                id_mensagem,
                id_hotel,
                id_solicitacao,
            )
            return

    existente = _json_classificacao(
        mensagem.get("classificacao_bruta") if mensagem else None
    )
    if (
        existente
        and existente.get("tipo") == "classificacao_intencao"
        and existente.get("desfecho")
    ):
        if (
            existente.get("desfecho") == "classificado"
            and (existente.get("intencao") or (mensagem or {}).get("intencao"))
            == "duvida_geral"
            and existente.get("resposta") not in ("automatica", "aviso")
        ):
            _enfileirar_responder_duvida(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
                enfileirar=enfileirar_resposta,
            )
        if (
            existente.get("desfecho") == "classificado"
            and (existente.get("intencao") or (mensagem or {}).get("intencao"))
            == "pedido_de_servico"
            and existente.get("resposta") != "confirmacao_pedido"
        ):
            _enfileirar_pedido_servico(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
                enfileirar=enfileirar_pedido,
            )
        if (
            existente.get("desfecho") == "classificado"
            and (existente.get("intencao") or (mensagem or {}).get("intencao"))
            == "reclamacao_tecnica"
            and existente.get("resposta") != "confirmacao_reclamacao"
        ):
            _enfileirar_chamado_reclamacao(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
                enfileirar=enfileirar_chamado,
            )
        intencao_existente = existente.get("intencao") or (
            (mensagem or {}).get("intencao")
        )
        if (
            pulso_aguardando_resposta(
                conexao, id_reserva=id_reserva, repositorio=repositorio
            )
            and intencao_existente
            not in ("duvida_geral", "pedido_de_servico", "reclamacao_tecnica")
            and existente.get("resposta")
            not in ("reconhecimento_pulso", "confirmacao_pulso_negativo")
        ):
            _enfileirar_resposta_pulso(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
                enfileirar=enfileirar_pulso,
            )
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "classificacao_ja_concluida id_trabalho=%s id_mensagem=%s",
            id_trabalho,
            id_mensagem,
        )
        return

    if mensagem is None or not (mensagem.get("conteudo") or "").strip():
        repositorio.gravar_classificacao_intencao(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            intencao=None,
            sentimento=None,
            urgencia=None,
            classificacao={
                "tipo": "classificacao_intencao",
                "desfecho": "formato_invalido",
                "bruto": {},
            },
        )
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "classificacao_formato_invalido id_mensagem=%s id_trabalho=%s"
            " id_hotel=%s",
            id_mensagem,
            id_trabalho,
            id_hotel,
        )
        _encerrar_pulso_se_aguardando(
            conexao,
            id_reserva=id_reserva,
            comentario=(mensagem or {}).get("conteudo"),
            repositorio=repositorio,
        )
        return

    try:
        resultado = llm.classificar(mensagem["conteudo"])
    except FalhaDeClassificacao as erro:
        repositorio.gravar_classificacao_intencao(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            intencao=None,
            sentimento=None,
            urgencia=None,
            classificacao={
                "tipo": "classificacao_intencao",
                "desfecho": "indisponivel",
            },
        )
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "classificacao_indisponivel id_mensagem=%s id_trabalho=%s"
            " id_hotel=%s codigo=%s",
            id_mensagem,
            id_trabalho,
            id_hotel,
            erro.codigo,
        )
        _encerrar_pulso_se_aguardando(
            conexao,
            id_reserva=id_reserva,
            comentario=mensagem.get("conteudo"),
            repositorio=repositorio,
        )
        return

    valida = validar_classificacao(resultado)
    if valida is None:
        repositorio.gravar_classificacao_intencao(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            intencao=None,
            sentimento=None,
            urgencia=None,
            classificacao={
                "tipo": "classificacao_intencao",
                "desfecho": "formato_invalido",
                "bruto": resultado.bruto,
            },
        )
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "classificacao_formato_invalido id_mensagem=%s id_trabalho=%s"
            " id_hotel=%s",
            id_mensagem,
            id_trabalho,
            id_hotel,
        )
        _encerrar_pulso_se_aguardando(
            conexao,
            id_reserva=id_reserva,
            comentario=mensagem.get("conteudo") if mensagem else None,
            repositorio=repositorio,
        )
        return

    desfecho = desfecho_de(valida.intencao)
    repositorio.gravar_classificacao_intencao(
        conexao,
        id_hotel=id_hotel,
        id_mensagem=id_mensagem,
        intencao=valida.intencao,
        sentimento=valida.sentimento,
        urgencia=valida.urgencia,
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": desfecho,
            "intencao": valida.intencao,
            "sentimento": valida.sentimento,
            "urgencia": valida.urgencia,
            "bruto": resultado.bruto,
        },
    )
    if valida.intencao == "duvida_geral":
        _enfileirar_responder_duvida(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            enfileirar=enfileirar_resposta,
        )
    elif valida.intencao == "pedido_de_servico":
        _enfileirar_pedido_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            enfileirar=enfileirar_pedido,
        )
    elif valida.intencao == "reclamacao_tecnica":
        _enfileirar_chamado_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            enfileirar=enfileirar_chamado,
        )
    elif pulso_aguardando_resposta(
        conexao, id_reserva=id_reserva, repositorio=repositorio
    ):
        _enfileirar_resposta_pulso(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            enfileirar=enfileirar_pulso,
        )
    fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
    logger.info(
        "mensagem_classificada id_mensagem=%s id_reserva=%s id_hotel=%s"
        " desfecho=%s intencao=%s",
        id_mensagem,
        id_reserva,
        id_hotel,
        desfecho,
        valida.intencao,
    )


def _enfileirar_responder_duvida(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    enfileirar,
) -> None:
    try:
        with _savepoint(conexao):
            enfileirar(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
            )
    except IntegrityError:
        logger.info(
            "responder_duvida_ja_enfileirada id_mensagem=%s id_hotel=%s",
            id_mensagem,
            id_hotel,
        )


def _enfileirar_pedido_servico(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    enfileirar,
) -> None:
    try:
        with _savepoint(conexao):
            enfileirar(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
            )
    except IntegrityError:
        logger.info(
            "registrar_pedido_servico_ja_enfileirado id_mensagem=%s id_hotel=%s",
            id_mensagem,
            id_hotel,
        )


def _enfileirar_chamado_reclamacao(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    enfileirar,
) -> None:
    try:
        with _savepoint(conexao):
            enfileirar(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
            )
    except IntegrityError:
        logger.info(
            "abrir_chamado_reclamacao_ja_enfileirado id_mensagem=%s id_hotel=%s",
            id_mensagem,
            id_hotel,
        )


def _enfileirar_resposta_pulso(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    enfileirar,
) -> None:
    try:
        with _savepoint(conexao):
            enfileirar(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
            )
    except IntegrityError:
        logger.info(
            "registrar_resposta_pulso_ja_enfileirado id_mensagem=%s id_hotel=%s",
            id_mensagem,
            id_hotel,
        )


def pulso_aguardando_resposta(
    conexao: Connection,
    *,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> bool:
    ler = getattr(repositorio, "pulso_foi_enviado", None)
    if ler is None:
        return False
    if not ler(conexao, id_reserva=id_reserva):
        return False
    from app.modulos.feedback import service as feedback

    return not feedback.tem_avaliacao_de_pulso(conexao, id_reserva=id_reserva)


def _encerrar_pulso_se_aguardando(
    conexao,
    *,
    id_reserva: int,
    comentario: str | None,
    repositorio,
) -> None:
    if not pulso_aguardando_resposta(
        conexao, id_reserva=id_reserva, repositorio=repositorio
    ):
        return
    from app.modulos.feedback import service as feedback

    feedback.encerrar_pulso(
        conexao, id_reserva=id_reserva, comentario=comentario
    )


def _fechar_pulso_apos_operacional(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    id_mensagem: int,
    repositorio,
) -> None:
    if not pulso_aguardando_resposta(
        conexao, id_reserva=id_reserva, repositorio=repositorio
    ):
        return
    from app.modulos.atendimento import service as atendimento
    from app.modulos.feedback import service as feedback

    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem) or {}
    feedback.encerrar_pulso_em_silencio(
        conexao,
        id_reserva=id_reserva,
        comentario=mensagem.get("conteudo"),
    )
    if mensagem.get("sentimento") != "negativo":
        return
    if atendimento.tem_reclamacao_da_mensagem(
        conexao, id_mensagem=id_mensagem
    ):
        return
    atendimento.abrir_reclamacao(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        descricao=mensagem.get("conteudo") or "",
        numero_quarto=None,
        urgencia=mensagem.get("urgencia"),
        janela_preferencia=None,
    )


TIPOS_OPERACIONAIS_FECHAM_PULSO = frozenset(
    {
        "responder_duvida",
        "registrar_pedido_servico",
        "abrir_chamado_reclamacao",
    }
)


def processar_trabalho_responder_duvida(
    conexao: Connection,
    *,
    trabalho: dict,
    llm: LLMProvider,
    catalogo,
    gateway: MensageriaGateway,
    repositorio=repositorio_padrao,
) -> None:
    from app.fila import repository as fila_repo

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])

    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    existente = _json_classificacao(
        mensagem.get("classificacao_bruta") if mensagem else None
    )
    if (
        existente
        and existente.get("resposta") in ("automatica", "aviso")
        and existente.get("id_mensagem_resposta")
    ):
        id_enviada = int(existente["id_mensagem_resposta"])
        enviada = repositorio.ler_mensagem(conexao, id_mensagem=id_enviada)
        if enviada and enviada.get("status_envio") == "pendente":
            _enviar_resposta_sessao(
                conexao,
                trabalho=trabalho,
                gateway=gateway,
                repositorio=repositorio,
                id_enviada=id_enviada,
                corpo=enviada["conteudo"],
                id_reserva=id_reserva,
            )
            return
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "duvida_ja_respondida id_trabalho=%s id_mensagem=%s id_hotel=%s"
            " resultado=%s",
            id_trabalho,
            id_mensagem,
            id_hotel,
            existente.get("resposta"),
        )
        _fechar_pulso_apos_operacional(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            repositorio=repositorio,
        )
        return

    pergunta = (mensagem or {}).get("conteudo") or ""
    itens = catalogo.listar_ativos(id_hotel)
    motivo = "aviso"
    texto_automatico = None
    if not itens:
        motivo = "catalogo_vazio"
    else:
        try:
            resultado = llm.responder_duvida(pergunta, itens)
        except FalhaDeConversacao as erro:
            motivo = "indisponivel"
            logger.info(
                "conversacao_indisponivel id_mensagem=%s id_trabalho=%s"
                " id_hotel=%s codigo=%s resultado=indisponivel",
                id_mensagem,
                id_trabalho,
                id_hotel,
                erro.codigo,
            )
        else:
            if not resultado.coberta:
                motivo = "aviso"
            elif not resposta_fiel_ao_catalogo(
                resultado.texto or "", resultado.trechos_citados, itens
            ):
                motivo = "nao_fiel"
                logger.info(
                    "resposta_nao_fiel id_mensagem=%s id_trabalho=%s"
                    " id_hotel=%s resultado=nao_fiel",
                    id_mensagem,
                    id_trabalho,
                    id_hotel,
                )
            else:
                motivo = "automatica"
                texto_automatico = resultado.texto

    if motivo == "automatica":
        corpo = texto_automatico or ""
        resposta = "automatica"
        desfecho = None
        resultado_log = "automatica"
        evento = "duvida_respondida"
    else:
        nome = "hospede"
        ler_nome = getattr(repositorio, "ler_nome_titular", None)
        if ler_nome is not None:
            nome = ler_nome(conexao, id_reserva=id_reserva) or "hospede"
        corpo = montar_aviso_duvida_nao_coberta(nome_completo=nome)
        resposta = "aviso"
        desfecho = "duvida_nao_coberta"
        resultado_log = "aviso" if motivo in ("aviso", "catalogo_vazio") else motivo
        evento = "duvida_nao_coberta"

    id_enviada = repositorio.inserir_mensagem_enviada_pendente(
        conexao, id_reserva=id_reserva, conteudo=corpo
    )
    repositorio.gravar_resposta_duvida(
        conexao,
        id_hotel=id_hotel,
        id_mensagem=id_mensagem,
        resposta=resposta,
        id_mensagem_resposta=id_enviada,
        desfecho=desfecho,
    )
    if motivo != "indisponivel" and motivo != "nao_fiel":
        logger.info(
            "%s id_mensagem=%s id_reserva=%s id_hotel=%s resultado=%s",
            evento,
            id_mensagem,
            id_reserva,
            id_hotel,
            resultado_log,
        )
    elif motivo == "nao_fiel":
        logger.info(
            "duvida_nao_coberta id_mensagem=%s id_reserva=%s id_hotel=%s"
            " resultado=nao_fiel",
            id_mensagem,
            id_reserva,
            id_hotel,
        )

    _enviar_resposta_sessao(
        conexao,
        trabalho=trabalho,
        gateway=gateway,
        repositorio=repositorio,
        id_enviada=id_enviada,
        corpo=corpo,
        id_reserva=id_reserva,
    )


def _enviar_resposta_sessao(
    conexao,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    repositorio,
    id_enviada: int,
    corpo: str,
    id_reserva: int,
    evento_especifico_falha: str | None = None,
) -> None:
    from app.fila import repository as fila_repo
    from app.fila import service as fila_svc

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho.get("payload") or {}
    if trabalho.get("tipo") in TIPOS_OPERACIONAIS_FECHAM_PULSO:
        origem = payload.get("id_mensagem")
        if origem is not None:
            _fechar_pulso_apos_operacional(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                id_mensagem=int(origem),
                repositorio=repositorio,
            )
    telefone = repositorio.ler_telefone_da_reserva(conexao, id_reserva=id_reserva)
    if not telefone:
        fila_repo.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=(trabalho.get("tentativas") or 0) + 1,
            erro="telefone_ausente",
        )
        marcar_envio_falha(
            conexao, id_mensagem=id_enviada, repositorio=repositorio
        )
        return
    try:
        resultado = gateway.enviar_texto_sessao(
            telefone_destino=telefone,
            corpo=corpo,
            id_mensagem=id_enviada,
            id_reserva=id_reserva,
        )
    except FalhaDeEnvio as erro:
        destino = fila_svc.registrar_falha_de_envio(
            conexao,
            id_trabalho=id_trabalho,
            id_hotel=id_hotel,
            tentativas_atuais=trabalho.get("tentativas") or 0,
            codigo_erro=erro.codigo,
        )
        if destino == "falha":
            marcar_envio_falha(
                conexao, id_mensagem=id_enviada, repositorio=repositorio
            )
        logger.info(
            "envio_tentativa_falhou id_trabalho=%s tipo=%s destino=%s codigo=%s",
            id_trabalho,
            trabalho.get("tipo"),
            destino,
            erro.codigo,
        )
        if evento_especifico_falha:
            origem = (trabalho.get("payload") or {}).get("id_mensagem")
            logger.info(
                "%s id_trabalho=%s id_mensagem=%s id_hotel=%s"
                " resultado=envio_falhou codigo=%s",
                evento_especifico_falha,
                id_trabalho,
                origem,
                id_hotel,
                erro.codigo,
            )
        if (
            trabalho.get("tipo") == "registrar_pedido_servico"
            and evento_especifico_falha != "consumo_envio_falhou"
        ):
            origem = (trabalho.get("payload") or {}).get("id_mensagem")
            logger.info(
                "pedido_envio_falhou id_trabalho=%s id_mensagem=%s id_hotel=%s"
                " resultado=envio_falhou codigo=%s",
                id_trabalho,
                origem,
                id_hotel,
                erro.codigo,
            )
        if trabalho.get("tipo") == "abrir_chamado_reclamacao":
            origem = (trabalho.get("payload") or {}).get("id_mensagem")
            logger.info(
                "chamado_envio_falhou id_trabalho=%s id_mensagem=%s id_hotel=%s"
                " resultado=envio_falhou codigo=%s",
                id_trabalho,
                origem,
                id_hotel,
                erro.codigo,
            )
        if trabalho.get("tipo") == "enviar_confirmacao_resolucao":
            payload = trabalho.get("payload") or {}
            logger.info(
                "resolucao_envio_falhou id_trabalho=%s id_solicitacao=%s"
                " id_hotel=%s resultado=envio_falhou codigo=%s",
                id_trabalho,
                payload.get("id_solicitacao"),
                id_hotel,
                erro.codigo,
            )
        return
    marcar_envio_sucesso(
        conexao,
        id_mensagem=id_enviada,
        id_externo=resultado.id_externo,
        repositorio=repositorio,
    )
    fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)


def processar_trabalho_enviar_confirmacao_resolucao(
    conexao: Connection,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    repositorio=repositorio_padrao,
) -> None:
    from app.fila import repository as fila_repo

    id_trabalho = trabalho["id_trabalho"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])
    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    if mensagem is None:
        fila_repo.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=(trabalho.get("tentativas") or 0) + 1,
            erro="mensagem_ausente",
        )
        return
    if mensagem.get("status_envio") == "enviada":
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        return
    _enviar_resposta_sessao(
        conexao,
        trabalho=trabalho,
        gateway=gateway,
        repositorio=repositorio,
        id_enviada=id_mensagem,
        corpo=mensagem["conteudo"],
        id_reserva=id_reserva,
    )


def processar_trabalho_registrar_pedido(
    conexao: Connection,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    abrir_servico,
    abrir_consumo=None,
    listar_itens_ativos=None,
    identificar=None,
    ler_preco=None,
    repositorio=repositorio_padrao,
) -> None:
    from decimal import Decimal

    from app.fila import repository as fila_repo
    from app.modulos.atendimento.quarto import extrair_numero_quarto
    from app.modulos.conversa.texto_aviso_identificacao import (
        montar_aviso_identificacao,
    )
    from app.modulos.conversa.texto_confirmacao_consumo import (
        montar_confirmacao_consumo,
    )
    from app.modulos.conversa.texto_confirmacao_pedido import (
        montar_confirmacao_pedido,
    )

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])

    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    existente = _json_classificacao(
        mensagem.get("classificacao_bruta") if mensagem else None
    )
    resposta_existente = existente.get("resposta") if existente else None
    if resposta_existente in {
        "confirmacao_pedido",
        "confirmacao_consumo",
        "aviso_identificacao",
    } and (
        resposta_existente == "aviso_identificacao"
        or existente.get("id_solicitacao")
    ):
        id_enviada = int(existente["id_mensagem_resposta"])
        enviada = repositorio.ler_mensagem(conexao, id_mensagem=id_enviada)
        evento = (
            "consumo_ja_registrado"
            if resposta_existente == "confirmacao_consumo"
            else (
                "identificacao_humana"
                if resposta_existente == "aviso_identificacao"
                else "pedido_ja_registrado"
            )
        )
        resultado = (
            "ja_avisado"
            if resposta_existente == "aviso_identificacao"
            else "ja_registrado"
        )
        if enviada and enviada.get("status_envio") == "pendente":
            logger.info(
                "%s id_trabalho=%s id_mensagem=%s id_hotel=%s"
                " id_solicitacao=%s resultado=%s",
                evento,
                id_trabalho,
                id_mensagem,
                id_hotel,
                existente.get("id_solicitacao"),
                resultado,
            )
            _enviar_resposta_sessao(
                conexao,
                trabalho=trabalho,
                gateway=gateway,
                repositorio=repositorio,
                id_enviada=id_enviada,
                corpo=enviada["conteudo"],
                id_reserva=id_reserva,
                evento_especifico_falha=(
                    "consumo_envio_falhou"
                    if resposta_existente == "confirmacao_consumo"
                    else None
                ),
            )
            return
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "%s id_trabalho=%s id_mensagem=%s id_hotel=%s"
            " id_solicitacao=%s resultado=%s",
            evento,
            id_trabalho,
            id_mensagem,
            id_hotel,
            existente.get("id_solicitacao"),
            resultado,
        )
        _fechar_pulso_apos_operacional(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            repositorio=repositorio,
        )
        return

    descricao = (mensagem or {}).get("conteudo") or ""
    numero_quarto = extrair_numero_quarto(descricao)
    urgencia = (mensagem or {}).get("urgencia") or "media"
    nome = "hospede"
    ler_nome = getattr(repositorio, "ler_nome_titular", None)
    if ler_nome is not None:
        nome = ler_nome(conexao, id_reserva=id_reserva) or "hospede"

    def _caminho_servico() -> None:
        corpo = montar_confirmacao_pedido(nome_completo=nome)
        id_enviada = repositorio.inserir_mensagem_enviada_pendente(
            conexao, id_reserva=id_reserva, conteudo=corpo
        )
        id_solicitacao = abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao=descricao,
            numero_quarto=numero_quarto,
            urgencia=urgencia,
        )
        repositorio.gravar_confirmacao_pedido(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            id_mensagem_resposta=id_enviada,
            id_solicitacao=id_solicitacao,
        )
        logger.info(
            "pedido_registrado id_trabalho=%s id_mensagem=%s id_reserva=%s"
            " id_hotel=%s id_solicitacao=%s resultado=registrado",
            id_trabalho,
            id_mensagem,
            id_reserva,
            id_hotel,
            id_solicitacao,
        )
        _enviar_resposta_sessao(
            conexao,
            trabalho=trabalho,
            gateway=gateway,
            repositorio=repositorio,
            id_enviada=id_enviada,
            corpo=corpo,
            id_reserva=id_reserva,
        )

    def _caminho_humano(desfecho: str) -> None:
        corpo = montar_aviso_identificacao(nome_completo=nome)
        id_enviada = repositorio.inserir_mensagem_enviada_pendente(
            conexao, id_reserva=id_reserva, conteudo=corpo
        )
        gravar_aviso = getattr(repositorio, "gravar_aviso_identificacao", None)
        if gravar_aviso is not None:
            gravar_aviso(
                conexao,
                id_hotel=id_hotel,
                id_mensagem=id_mensagem,
                id_mensagem_resposta=id_enviada,
                desfecho=desfecho,
            )
        logger.info(
            "identificacao_humana id_trabalho=%s id_mensagem=%s id_hotel=%s"
            " resultado=%s",
            id_trabalho,
            id_mensagem,
            id_hotel,
            desfecho,
        )
        _enviar_resposta_sessao(
            conexao,
            trabalho=trabalho,
            gateway=gateway,
            repositorio=repositorio,
            id_enviada=id_enviada,
            corpo=corpo,
            id_reserva=id_reserva,
        )

    itens = ()
    if listar_itens_ativos is not None:
        itens = tuple(listar_itens_ativos(conexao, id_hotel=id_hotel) or ())
    ids_validos = {par[0] for par in itens}

    if not itens or identificar is None:
        _caminho_servico()
        return

    try:
        resultado = identificar(descricao, itens)
    except FalhaDeIdentificacao:
        _caminho_humano("identificacao_indisponivel")
        return

    desfecho = getattr(resultado, "desfecho", None)
    if desfecho == "nenhum":
        _caminho_servico()
        return
    if desfecho == "ambiguo":
        _caminho_humano("item_ambiguo")
        return
    if desfecho != "unico":
        _caminho_humano("identificacao_indisponivel")
        return

    id_item = getattr(resultado, "id_item_vendavel", None)
    try:
        quantidade = int(resultado.quantidade)
    except (TypeError, ValueError):
        _caminho_humano("identificacao_indisponivel")
        return
    if id_item not in ids_validos or quantidade < 1:
        _caminho_humano("identificacao_indisponivel")
        return

    preco = None
    if ler_preco is not None:
        preco = ler_preco(
            conexao, id_hotel=id_hotel, id_item_vendavel=id_item
        )
    if preco is None:
        _caminho_humano("identificacao_indisponivel")
        return
    if not isinstance(preco, Decimal):
        preco = Decimal(str(preco))
    valor_praticado = preco * quantidade
    nome_item = next(par[1] for par in itens if par[0] == id_item)

    if abrir_consumo is None:
        _caminho_servico()
        return

    corpo = montar_confirmacao_consumo(
        nome_completo=nome,
        descricao_item=nome_item,
        valor_praticado=valor_praticado,
    )
    id_enviada = repositorio.inserir_mensagem_enviada_pendente(
        conexao, id_reserva=id_reserva, conteudo=corpo
    )
    id_solicitacao = abrir_consumo(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        descricao=descricao,
        descricao_item=nome_item,
        valor_praticado=valor_praticado,
        numero_quarto=numero_quarto,
        urgencia=urgencia,
    )
    gravar_consumo = getattr(repositorio, "gravar_confirmacao_consumo", None)
    if gravar_consumo is not None:
        gravar_consumo(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            id_mensagem_resposta=id_enviada,
            id_solicitacao=id_solicitacao,
            id_item_vendavel=id_item,
            quantidade=quantidade,
        )
    logger.info(
        "consumo_registrado id_trabalho=%s id_mensagem=%s id_reserva=%s"
        " id_hotel=%s id_solicitacao=%s resultado=registrado",
        id_trabalho,
        id_mensagem,
        id_reserva,
        id_hotel,
        id_solicitacao,
    )
    _enviar_resposta_sessao(
        conexao,
        trabalho=trabalho,
        gateway=gateway,
        repositorio=repositorio,
        id_enviada=id_enviada,
        corpo=corpo,
        id_reserva=id_reserva,
        evento_especifico_falha="consumo_envio_falhou",
    )


def processar_trabalho_abrir_chamado(
    conexao: Connection,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    abrir_reclamacao,
    repositorio=repositorio_padrao,
) -> None:
    from app.fila import repository as fila_repo
    from app.modulos.atendimento.janela import extrair_janela_preferencia
    from app.modulos.atendimento.quarto import extrair_numero_quarto
    from app.modulos.conversa.texto_confirmacao_reclamacao import (
        montar_confirmacao_reclamacao,
    )

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])

    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    existente = _json_classificacao(
        mensagem.get("classificacao_bruta") if mensagem else None
    )
    if (
        existente
        and existente.get("resposta") == "confirmacao_reclamacao"
        and existente.get("id_solicitacao")
    ):
        id_enviada = int(existente["id_mensagem_resposta"])
        enviada = repositorio.ler_mensagem(conexao, id_mensagem=id_enviada)
        if enviada and enviada.get("status_envio") == "pendente":
            logger.info(
                "chamado_ja_aberto id_trabalho=%s id_mensagem=%s"
                " id_hotel=%s id_solicitacao=%s resultado=ja_aberto",
                id_trabalho,
                id_mensagem,
                id_hotel,
                existente.get("id_solicitacao"),
            )
            _enviar_resposta_sessao(
                conexao,
                trabalho=trabalho,
                gateway=gateway,
                repositorio=repositorio,
                id_enviada=id_enviada,
                corpo=enviada["conteudo"],
                id_reserva=id_reserva,
            )
            return
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "chamado_ja_aberto id_trabalho=%s id_mensagem=%s id_hotel=%s"
            " id_solicitacao=%s resultado=ja_aberto",
            id_trabalho,
            id_mensagem,
            id_hotel,
            existente.get("id_solicitacao"),
        )
        _fechar_pulso_apos_operacional(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            repositorio=repositorio,
        )
        return

    descricao = (mensagem or {}).get("conteudo") or ""
    numero_quarto = extrair_numero_quarto(descricao)
    janela = extrair_janela_preferencia(descricao)
    urgencia = (mensagem or {}).get("urgencia") or "media"
    nome = "hospede"
    ler_nome = getattr(repositorio, "ler_nome_titular", None)
    if ler_nome is not None:
        nome = ler_nome(conexao, id_reserva=id_reserva) or "hospede"
    corpo = montar_confirmacao_reclamacao(
        nome_completo=nome, perguntar_horario=janela is None
    )
    id_enviada = repositorio.inserir_mensagem_enviada_pendente(
        conexao, id_reserva=id_reserva, conteudo=corpo
    )
    id_solicitacao = abrir_reclamacao(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        id_mensagem=id_mensagem,
        descricao=descricao,
        numero_quarto=numero_quarto,
        urgencia=urgencia,
        janela_preferencia=janela,
    )
    repositorio.gravar_confirmacao_reclamacao(
        conexao,
        id_hotel=id_hotel,
        id_mensagem=id_mensagem,
        id_mensagem_resposta=id_enviada,
        id_solicitacao=id_solicitacao,
    )
    logger.info(
        "chamado_aberto id_trabalho=%s id_mensagem=%s id_reserva=%s"
        " id_hotel=%s id_solicitacao=%s resultado=aberto",
        id_trabalho,
        id_mensagem,
        id_reserva,
        id_hotel,
        id_solicitacao,
    )
    _enviar_resposta_sessao(
        conexao,
        trabalho=trabalho,
        gateway=gateway,
        repositorio=repositorio,
        id_enviada=id_enviada,
        corpo=corpo,
        id_reserva=id_reserva,
    )


def _ainda_elegivel_para_envio_pulso(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    repositorio_propriedade=propriedade_repository,
) -> bool:
    from datetime import UTC, datetime

    from app.modulos.atendimento import service as atendimento
    from app.modulos.feedback import service as feedback
    from app.modulos.hospedagem import repository as hospedagem_repo
    from worker.agendador import (
        CHAVE_MINIMO_PULSO,
        _inteiro_positivo,
        horas_restantes_de_estadia,
    )

    reserva = hospedagem_repo.ler_reserva_do_hotel(
        conexao, id_hotel=id_hotel, id_reserva=id_reserva
    )
    if reserva is None or reserva.get("status") != "hospedado":
        return False
    if feedback.tem_avaliacao_de_pulso(conexao, id_reserva=id_reserva):
        return False
    if atendimento.tem_reclamacao_aberta(conexao, id_reserva=id_reserva):
        return False
    minimo = _inteiro_positivo(
        repositorio_propriedade.ler_parametro(
            conexao, id_hotel, CHAVE_MINIMO_PULSO
        )
    )
    if minimo is None:
        return False
    checkout = reserva.get("data_checkout_prevista")
    if checkout is None:
        return False
    restante = horas_restantes_de_estadia(checkout, datetime.now(UTC).date())
    return restante >= minimo


def processar_trabalho_enviar_pulso(
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
            tentativas=(trabalho.get("tentativas") or 0) + 1,
            erro="mensagem_ausente",
        )
        return
    if mensagem.get("status_envio") == "enviada":
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        return
    if not _ainda_elegivel_para_envio_pulso(
        conexao,
        id_hotel=id_hotel,
        id_reserva=id_reserva,
        repositorio_propriedade=repositorio_propriedade,
    ):
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "pulso_suprimido_na_janela id_trabalho=%s id_reserva=%s id_hotel=%s",
            id_trabalho,
            id_reserva,
            id_hotel,
        )
        return
    telefone = repositorio.ler_telefone_da_reserva(
        conexao, id_reserva=id_reserva
    )
    if not telefone:
        fila_repo.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=(trabalho.get("tentativas") or 0) + 1,
            erro="telefone_ausente",
        )
        marcar_envio_falha(
            conexao, id_mensagem=id_mensagem, repositorio=repositorio
        )
        return
    nome = "hospede"
    ler_nome = getattr(repositorio, "ler_nome_titular", None)
    if ler_nome is not None:
        nome = ler_nome(conexao, id_reserva=id_reserva) or "hospede"
    try:
        prenome = primeiro_nome(nome)
    except ValueError:
        prenome = "hospede"
    try:
        resultado = gateway.enviar_pulso(
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
            tentativas_atuais=trabalho.get("tentativas") or 0,
            codigo_erro=erro.codigo,
        )
        if destino == "falha":
            marcar_envio_falha(
                conexao, id_mensagem=id_mensagem, repositorio=repositorio
            )
        logger.info(
            "envio_tentativa_falhou id_trabalho=%s tipo=enviar_pulso"
            " destino=%s codigo=%s",
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
    logger.info(
        "pulso_enviado id_trabalho=%s id_mensagem=%s id_reserva=%s id_hotel=%s",
        id_trabalho,
        id_mensagem,
        id_reserva,
        id_hotel,
    )


def processar_trabalho_registrar_resposta_pulso(
    conexao: Connection,
    *,
    trabalho: dict,
    gateway: MensageriaGateway,
    abrir_reclamacao,
    repositorio=repositorio_padrao,
) -> None:
    from app.fila import repository as fila_repo
    from app.modulos.feedback import service as feedback

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])
    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    existente = _json_classificacao(
        mensagem.get("classificacao_bruta") if mensagem else None
    )
    if (
        existente
        and existente.get("resposta")
        in ("reconhecimento_pulso", "confirmacao_pulso_negativo")
        and existente.get("id_mensagem_resposta")
    ):
        id_enviada = int(existente["id_mensagem_resposta"])
        enviada = repositorio.ler_mensagem(conexao, id_mensagem=id_enviada)
        if enviada and enviada.get("status_envio") == "pendente":
            _enviar_resposta_sessao(
                conexao,
                trabalho=trabalho,
                gateway=gateway,
                repositorio=repositorio,
                id_enviada=id_enviada,
                corpo=enviada["conteudo"],
                id_reserva=id_reserva,
            )
            return
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        return

    sentimento = (mensagem or {}).get("sentimento")
    if sentimento == "negativo":
        corpo = montar_confirmacao_pulso_negativo()
        chave_resposta = "confirmacao_pulso_negativo"
    else:
        corpo = montar_reconhecimento_pulso()
        chave_resposta = "reconhecimento_pulso"

    id_enviada = repositorio.inserir_mensagem_enviada_pendente(
        conexao, id_reserva=id_reserva, conteudo=corpo
    )
    id_avaliacao = feedback.encerrar_pulso(
        conexao,
        id_reserva=id_reserva,
        comentario=(mensagem or {}).get("conteudo"),
    )
    id_solicitacao = None
    if sentimento == "negativo":
        id_solicitacao = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao=(mensagem or {}).get("conteudo") or "",
            numero_quarto=None,
            urgencia=(mensagem or {}).get("urgencia"),
            janela_preferencia=None,
        )
    gravar = getattr(repositorio, "gravar_resposta_pulso", None)
    if gravar is not None:
        gravar(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            id_mensagem_resposta=id_enviada,
            resposta=chave_resposta,
            id_solicitacao=id_solicitacao,
            id_avaliacao=id_avaliacao,
        )
    logger.info(
        "resposta_pulso_registrada id_trabalho=%s id_mensagem=%s"
        " id_reserva=%s id_hotel=%s sentimento=%s",
        id_trabalho,
        id_mensagem,
        id_reserva,
        id_hotel,
        sentimento,
    )
    _enviar_resposta_sessao(
        conexao,
        trabalho=trabalho,
        gateway=gateway,
        repositorio=repositorio,
        id_enviada=id_enviada,
        corpo=corpo,
        id_reserva=id_reserva,
    )


def processar_trabalho_enviar_pesquisa_saida(
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
            tentativas=(trabalho.get("tentativas") or 0) + 1,
            erro="mensagem_ausente",
        )
        return
    if mensagem.get("status_envio") == "enviada":
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        return
    telefone = repositorio.ler_telefone_da_reserva(
        conexao, id_reserva=id_reserva
    )
    if not telefone:
        fila_repo.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=(trabalho.get("tentativas") or 0) + 1,
            erro="telefone_ausente",
        )
        marcar_envio_falha(
            conexao, id_mensagem=id_mensagem, repositorio=repositorio
        )
        return
    nome = "hospede"
    ler_nome = getattr(repositorio, "ler_nome_titular", None)
    if ler_nome is not None:
        nome = ler_nome(conexao, id_reserva=id_reserva) or "hospede"
    try:
        prenome = primeiro_nome(nome)
    except ValueError:
        prenome = "hospede"
    try:
        resultado = gateway.enviar_pesquisa_saida(
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
            tentativas_atuais=trabalho.get("tentativas") or 0,
            codigo_erro=erro.codigo,
        )
        if destino == "falha":
            marcar_envio_falha(
                conexao, id_mensagem=id_mensagem, repositorio=repositorio
            )
        logger.info(
            "envio_tentativa_falhou id_trabalho=%s tipo=enviar_pesquisa_saida"
            " destino=%s codigo=%s",
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
    logger.info(
        "pesquisa_saida_enviada id_trabalho=%s id_mensagem=%s"
        " id_reserva=%s id_hotel=%s",
        id_trabalho,
        id_mensagem,
        id_reserva,
        id_hotel,
    )


def _prazo_atribuicao_em_horas(valor: str | None) -> int | None:
    if valor is None:
        return None
    try:
        horas = int(valor)
    except (TypeError, ValueError):
        return None
    if horas < 1:
        return None
    return horas


def _nota_valida(nota) -> int | None:
    try:
        numero = int(nota)
    except (TypeError, ValueError):
        return None
    if numero < 1 or numero > 5:
        return None
    return numero


def processar_trabalho_interpretar_pesquisa_saida(
    conexao: Connection,
    *,
    trabalho: dict,
    llm,
    repositorio=repositorio_padrao,
    repositorio_propriedade=propriedade_repository,
    agora=None,
) -> None:
    from datetime import UTC, timedelta

    from app.comum import relogio as relogio_padrao
    from app.fila import repository as fila_repo
    from app.modulos.feedback import service as feedback
    from app.modulos.hospedagem import service as hospedagem

    id_trabalho = trabalho["id_trabalho"]
    id_hotel = trabalho["id_hotel"]
    payload = trabalho["payload"]
    id_mensagem = int(payload["id_mensagem"])
    id_reserva = int(payload["id_reserva"])
    instante = agora if agora is not None else relogio_padrao.agora()
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)

    def _concluir(desfecho: str) -> None:
        repositorio.gravar_classificacao_bruta(
            conexao,
            id_mensagem=id_mensagem,
            classificacao={"tipo": "pesquisa_saida", "desfecho": desfecho},
        )
        fila_repo.marcar_concluido(conexao, id_trabalho=id_trabalho)
        logger.info(
            "pesquisa_saida_interpretada id_trabalho=%s id_mensagem=%s"
            " id_reserva=%s desfecho=%s",
            id_trabalho,
            id_mensagem,
            id_reserva,
            desfecho,
        )

    mensagem = repositorio.ler_mensagem(conexao, id_mensagem=id_mensagem)
    if mensagem is None:
        fila_repo.marcar_falha(
            conexao,
            id_trabalho=id_trabalho,
            tentativas=(trabalho.get("tentativas") or 0) + 1,
            erro="mensagem_ausente",
        )
        return
    reserva = repositorio.ler_checkout_da_reserva(
        conexao, id_reserva=id_reserva
    )
    checkout_em = (reserva or {}).get("checkout_em")
    valor = repositorio_propriedade.ler_parametro(
        conexao, id_hotel, CHAVE_ATRIBUICAO_PESQUISA
    )
    horas = _prazo_atribuicao_em_horas(valor)
    if horas is None:
        logger.info(
            "prazo_ausente id_trabalho=%s id_reserva=%s id_hotel=%s",
            id_trabalho,
            id_reserva,
            id_hotel,
        )
        _concluir("prazo_ausente")
        return
    if checkout_em is not None:
        if checkout_em.tzinfo is None:
            checkout_em = checkout_em.replace(tzinfo=UTC)
        if instante - checkout_em > timedelta(hours=horas):
            _concluir("fora_da_janela")
            return
    try:
        bruto = llm.interpretar_pesquisa_saida(mensagem["conteudo"])
    except FalhaDeExtracao:
        _concluir("indisponivel")
        return
    desfecho_porta = getattr(bruto, "desfecho", None)
    if desfecho_porta == "irreconhecivel":
        _concluir("irreconhecivel")
        return
    if desfecho_porta not in ("completo", "parcial"):
        _concluir("formato_invalido")
        return
    nota = _nota_valida(getattr(bruto, "nota", None))
    comentario = getattr(bruto, "comentario", None)
    aceite = getattr(bruto, "aceite", None)
    if aceite is not None and not isinstance(aceite, bool):
        aceite = None
    if nota is not None:
        feedback.gravar_avaliacao_checkout(
            conexao,
            id_reserva=id_reserva,
            nota=nota,
            comentario=comentario,
        )
    if isinstance(aceite, bool):
        hospedagem.registrar_consentimento_pesquisa(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            concedido=aceite,
        )
    if nota is not None and isinstance(aceite, bool):
        _concluir("completo")
        return
    if nota is not None or isinstance(aceite, bool) or comentario:
        _concluir("parcial")
        return
    _concluir("formato_invalido")
