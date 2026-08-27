"""Criacao inicial da propriedade e leitura de parametros operacionais."""

from dataclasses import dataclass
from decimal import Decimal
import unicodedata

from sqlalchemy.engine import Connection

from app.comum.log import obter_logger
from app.modulos.acesso import service as acesso_service
from app.modulos.propriedade import repository as propriedade_repository
from app.modulos.propriedade.schema import (
    ExecucaoRetencaoResposta,
    ItemCatalogoResposta,
    ItemVendavelResposta,
)

logger = obter_logger(__name__)

CATEGORIAS_CATALOGO = frozenset(
    {"horario", "cardapio", "servico", "programacao", "regra"}
)
TITULO_MAXIMO = 160

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

PARAMETROS_BOAS_VINDAS_PADRAO = {
    "boas_vindas_cafe": "Cafe da manha das 7h as 10h",
    "boas_vindas_wifi": "Wi-Fi: rede do hotel, senha na recepcao",
    "boas_vindas_checkout": "Checkout ate as 12h",
    "horas_validade_boas_vindas": "12",
}

PARAMETROS_CHAMADO_PADRAO = {
    "horas_destaque_chamado_aberto": "2",
}

PARAMETROS_PULSO_PADRAO = {
    "horas_minimas_para_pulso": "24",
}

PARAMETROS_PESQUISA_SAIDA_PADRAO = {
    "horas_atribuicao_pesquisa_saida": "24",
}

PARAMETROS_MERCADO_PADRAO = {
    "periodicidade_coleta_mercado": "24",
}

PARAMETROS_RETENCAO_PADRAO = {
    "meses_retencao_conteudo_livre": "12",
    "anos_retencao_ficha": "5",
}

CHAVES_SLOTS_BOAS_VINDAS = {
    "cafe": "boas_vindas_cafe",
    "wifi": "boas_vindas_wifi",
    "checkout": "boas_vindas_checkout",
}

CHAVE_PERSONALIDADE_ASSISTENTE = "personalidade_assistente"
TAMANHO_MAXIMO_PERSONALIDADE = 500
PARAMETROS_PERSONALIDADE_PADRAO = {
    CHAVE_PERSONALIDADE_ASSISTENTE: "",
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
    for chave, valor in PARAMETROS_BOAS_VINDAS_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    for chave, valor in PARAMETROS_CHAMADO_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    for chave, valor in PARAMETROS_PULSO_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    for chave, valor in PARAMETROS_PESQUISA_SAIDA_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    for chave, valor in PARAMETROS_MERCADO_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    for chave, valor in PARAMETROS_RETENCAO_PADRAO.items():
        repositorio.inserir_parametro(conexao, id_hotel, chave, valor)
    for chave, valor in PARAMETROS_PERSONALIDADE_PADRAO.items():
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


class DadosInvalidos(ValueError):
    """Entrada rejeitada na borda de negocio, com mensagem para o usuario."""


class ItemNaoEncontrado(Exception):
    pass


class ItemVendavelNaoEncontrado(Exception):
    pass


class ItemVendavelDuplicado(Exception):
    pass


@dataclass(frozen=True)
class ItemDeCatalogo:
    id_catalogo_item: int
    id_hotel: int
    categoria: str
    titulo: str
    conteudo: str
    ativo: bool

    def para_resposta(self) -> ItemCatalogoResposta:
        return ItemCatalogoResposta(
            id_catalogo_item=self.id_catalogo_item,
            categoria=self.categoria,
            titulo=self.titulo,
            conteudo=self.conteudo,
            ativo=self.ativo,
        )


def _item_da_linha(linha: dict) -> ItemDeCatalogo:
    return ItemDeCatalogo(
        id_catalogo_item=linha["id_catalogo_item"],
        id_hotel=linha["id_hotel"],
        categoria=linha["categoria"],
        titulo=linha["titulo"],
        conteudo=linha["conteudo"],
        ativo=linha["ativo"],
    )


def _validar_texto(titulo: str, conteudo: str) -> tuple[str, str]:
    titulo_limpo = titulo.strip()
    conteudo_limpo = conteudo.strip()
    if not titulo_limpo:
        raise DadosInvalidos("Informe o titulo.")
    if not conteudo_limpo:
        raise DadosInvalidos("Informe o conteudo.")
    if len(titulo_limpo) > TITULO_MAXIMO:
        raise DadosInvalidos("O titulo deve ter no maximo 160 caracteres.")
    return titulo_limpo, conteudo_limpo


def criar_item(
    conexao: Connection,
    *,
    id_hotel: int,
    categoria: str,
    titulo: str,
    conteudo: str,
    repositorio=propriedade_repository,
) -> ItemDeCatalogo:
    if categoria not in CATEGORIAS_CATALOGO:
        raise DadosInvalidos("Categoria invalida.")
    titulo_limpo, conteudo_limpo = _validar_texto(titulo, conteudo)
    linha = repositorio.inserir_item(
        conexao,
        id_hotel=id_hotel,
        categoria=categoria,
        titulo=titulo_limpo,
        conteudo=conteudo_limpo,
    )
    item = _item_da_linha(linha)
    logger.info(
        "catalogo_criado id_catalogo_item=%s id_hotel=%s categoria=%s",
        item.id_catalogo_item,
        item.id_hotel,
        item.categoria,
    )
    return item


def alterar_item(
    conexao: Connection,
    *,
    id_hotel: int,
    id_catalogo_item: int,
    titulo: str | None = None,
    conteudo: str | None = None,
    ativo: bool | None = None,
    categoria: str | None = None,
    repositorio=propriedade_repository,
) -> ItemDeCatalogo:
    if categoria is not None:
        raise DadosInvalidos("A categoria nao pode ser alterada.")
    if titulo is None and conteudo is None and ativo is None:
        raise DadosInvalidos("Informe titulo, conteudo ou ativo.")
    titulo_limpo = None
    conteudo_limpo = None
    if titulo is not None:
        titulo_limpo, _ = _validar_texto(titulo, "x")
    if conteudo is not None:
        _, conteudo_limpo = _validar_texto("x", conteudo)
    linha = repositorio.atualizar_item(
        conexao,
        id_hotel=id_hotel,
        id_catalogo_item=id_catalogo_item,
        titulo=titulo_limpo,
        conteudo=conteudo_limpo,
        ativo=ativo,
    )
    if linha is None:
        raise ItemNaoEncontrado
    item = _item_da_linha(linha)
    acao = "catalogo_alterado"
    if ativo is False:
        acao = "catalogo_desativado"
    elif ativo is True:
        acao = "catalogo_reativado"
    logger.info(
        "%s id_catalogo_item=%s id_hotel=%s categoria=%s",
        acao,
        item.id_catalogo_item,
        item.id_hotel,
        item.categoria,
    )
    return item


def listar_manutencao(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=propriedade_repository,
) -> list[ItemDeCatalogo]:
    return [
        _item_da_linha(linha)
        for linha in repositorio.listar_manutencao(conexao, id_hotel=id_hotel)
    ]


def ler_catalogo_ativo(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=propriedade_repository,
) -> dict[str, list[ItemDeCatalogo]]:
    agrupado = {categoria: [] for categoria in CATEGORIAS_CATALOGO}
    for linha in repositorio.listar_ativos(conexao, id_hotel=id_hotel):
        item = _item_da_linha(linha)
        agrupado[item.categoria].append(item)
    return agrupado


def validar_texto_de_boas_vindas(campo: str, valor: str) -> str:
    if valor is None:
        raise DadosInvalidos(f"Informe o {campo}.")
    if "\n" in valor or "\r" in valor:
        raise DadosInvalidos(
            f"O campo {campo} nao pode ter quebra de linha."
        )
    if "\t" in valor:
        raise DadosInvalidos(f"O campo {campo} nao pode ter tabulacao.")
    if "     " in valor:
        raise DadosInvalidos(
            f"O campo {campo} nao pode ter mais de quatro espacos seguidos."
        )
    limpo = valor.strip()
    if not limpo:
        raise DadosInvalidos(f"Informe o {campo}.")
    if len(limpo) > 255:
        raise DadosInvalidos(
            f"O campo {campo} deve ter no maximo 255 caracteres."
        )
    return limpo


def ler_textos_de_boas_vindas(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=propriedade_repository,
) -> dict[str, str | None]:
    lidos = repositorio.ler_parametros(
        conexao, id_hotel, list(CHAVES_SLOTS_BOAS_VINDAS.values())
    )
    return {
        campo: lidos.get(chave)
        for campo, chave in CHAVES_SLOTS_BOAS_VINDAS.items()
    }


def gravar_textos_de_boas_vindas(
    conexao: Connection,
    *,
    id_hotel: int,
    cafe: str,
    wifi: str,
    checkout: str,
    repositorio=propriedade_repository,
) -> dict[str, str]:
    limpos = {
        "cafe": validar_texto_de_boas_vindas("cafe", cafe),
        "wifi": validar_texto_de_boas_vindas("wifi", wifi),
        "checkout": validar_texto_de_boas_vindas("checkout", checkout),
    }
    for campo, chave in CHAVES_SLOTS_BOAS_VINDAS.items():
        repositorio.upsert_parametro(conexao, id_hotel, chave, limpos[campo])
    logger.info("textos_de_boas_vindas_gravados id_hotel=%s", id_hotel)
    return limpos


def validar_personalidade(texto: str) -> str:
    if texto is None:
        raise DadosInvalidos("O texto e longo demais.")
    limpo = texto.strip()
    if len(limpo) > TAMANHO_MAXIMO_PERSONALIDADE:
        raise DadosInvalidos("O texto e longo demais.")
    for caractere in limpo:
        if (
            unicodedata.category(caractere) == "Cc"
            and caractere not in "\n\r\t"
        ):
            raise DadosInvalidos("O texto contem caractere invalido.")
    return limpo


def ler_personalidade_assistente(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=propriedade_repository,
) -> str:
    valor = repositorio.ler_parametro(
        conexao, id_hotel, CHAVE_PERSONALIDADE_ASSISTENTE
    )
    return valor if valor is not None else ""


def gravar_personalidade_assistente(
    conexao: Connection,
    *,
    id_hotel: int,
    texto: str,
    repositorio=propriedade_repository,
) -> str:
    limpo = validar_personalidade(texto)
    repositorio.upsert_parametro(
        conexao, id_hotel, CHAVE_PERSONALIDADE_ASSISTENTE, limpo
    )
    logger.info("personalidade_assistente_gravada id_hotel=%s", id_hotel)
    return limpo


@dataclass(frozen=True)
class ItemVendavel:
    id_item_vendavel: int
    id_hotel: int
    nome: str
    preco_atual: Decimal
    ativo: bool
    atualizado_em: object

    def para_resposta(self) -> ItemVendavelResposta:
        return ItemVendavelResposta(
            id_item_vendavel=self.id_item_vendavel,
            nome=self.nome,
            preco_atual=self.preco_atual,
            ativo=self.ativo,
            atualizado_em=self.atualizado_em,
        )


def _item_vendavel_da_linha(linha: dict) -> ItemVendavel:
    preco = linha["preco_atual"]
    if not isinstance(preco, Decimal):
        preco = Decimal(str(preco))
    return ItemVendavel(
        id_item_vendavel=linha["id_item_vendavel"],
        id_hotel=linha["id_hotel"],
        nome=linha["nome"],
        preco_atual=preco,
        ativo=linha["ativo"],
        atualizado_em=linha["atualizado_em"],
    )


def _validar_nome_e_preco(nome: str, preco_atual: Decimal) -> tuple[str, Decimal]:
    nome_limpo = nome.strip()
    if not nome_limpo:
        raise DadosInvalidos("Informe o nome.")
    if len(nome_limpo) > TITULO_MAXIMO:
        raise DadosInvalidos("O nome deve ter no maximo 160 caracteres.")
    if preco_atual < 0:
        raise DadosInvalidos("O preco nao pode ser negativo.")
    return nome_limpo, preco_atual


def criar_item_vendavel(
    conexao: Connection,
    *,
    id_hotel: int,
    nome: str,
    preco_atual: Decimal,
    repositorio=propriedade_repository,
) -> ItemVendavel:
    nome_limpo, preco = _validar_nome_e_preco(nome, preco_atual)
    if repositorio.existe_nome_ativo(conexao, id_hotel=id_hotel, nome=nome_limpo):
        raise ItemVendavelDuplicado
    linha = repositorio.inserir_item_vendavel(
        conexao, id_hotel=id_hotel, nome=nome_limpo, preco_atual=preco
    )
    item = _item_vendavel_da_linha(linha)
    logger.info(
        "item_vendavel_criado id_item_vendavel=%s id_hotel=%s",
        item.id_item_vendavel,
        item.id_hotel,
    )
    return item


def atualizar_item_vendavel(
    conexao: Connection,
    *,
    id_hotel: int,
    id_item_vendavel: int,
    nome: str | None = None,
    preco_atual: Decimal | None = None,
    ativo: bool | None = None,
    repositorio=propriedade_repository,
) -> ItemVendavel:
    if nome is None and preco_atual is None and ativo is None:
        raise DadosInvalidos("Informe nome, preco_atual ou ativo.")
    nome_limpo = None
    if nome is not None:
        nome_limpo, _ = _validar_nome_e_preco(nome, Decimal("0"))
        if repositorio.existe_nome_ativo(
            conexao,
            id_hotel=id_hotel,
            nome=nome_limpo,
            exceto_id=id_item_vendavel,
        ):
            raise ItemVendavelDuplicado
    if preco_atual is not None and preco_atual < 0:
        raise DadosInvalidos("O preco nao pode ser negativo.")
    linha = repositorio.atualizar_item_vendavel(
        conexao,
        id_hotel=id_hotel,
        id_item_vendavel=id_item_vendavel,
        nome=nome_limpo,
        preco_atual=preco_atual,
        ativo=ativo,
    )
    if linha is None:
        raise ItemVendavelNaoEncontrado
    item = _item_vendavel_da_linha(linha)
    logger.info(
        "item_vendavel_alterado id_item_vendavel=%s id_hotel=%s",
        item.id_item_vendavel,
        item.id_hotel,
    )
    return item


def listar_itens_vendaveis_manutencao(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=propriedade_repository,
) -> list[ItemVendavel]:
    return [
        _item_vendavel_da_linha(linha)
        for linha in repositorio.listar_itens_vendaveis_manutencao(
            conexao, id_hotel=id_hotel
        )
    ]


def listar_itens_vendaveis_ativos(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=propriedade_repository,
) -> tuple[tuple[int, str], ...]:
    return tuple(
        (int(linha["id_item_vendavel"]), linha["nome"])
        for linha in repositorio.listar_itens_vendaveis_ativos(
            conexao, id_hotel=id_hotel
        )
    )


def ler_preco_item_ativo(
    conexao: Connection,
    *,
    id_hotel: int,
    id_item_vendavel: int,
    repositorio=propriedade_repository,
) -> Decimal | None:
    bruto = repositorio.ler_preco_item_ativo(
        conexao, id_hotel=id_hotel, id_item_vendavel=id_item_vendavel
    )
    if bruto is None:
        return None
    if isinstance(bruto, Decimal):
        return bruto
    return Decimal(str(bruto))


def ja_executou_retencao_no_dia(
    conexao: Connection,
    *,
    id_hotel: int,
    agora,
    repositorio=propriedade_repository,
) -> bool:
    return repositorio.ja_executou_retencao_no_dia(
        conexao, id_hotel=id_hotel, agora=agora
    )


def registrar_execucao_retencao(
    conexao: Connection,
    *,
    id_hotel: int,
    executado_em,
    mensagens_anonimizadas: int = 0,
    comentarios_anonimizados: int = 0,
    payloads_anonimizados: int = 0,
    descricoes_anonimizadas: int = 0,
    fichas_apagadas: int = 0,
    prazo_conteudo_ausente: bool = False,
    prazo_ficha_ausente: bool = False,
    repositorio=propriedade_repository,
) -> int | None:
    return repositorio.registrar_execucao_retencao(
        conexao,
        id_hotel=id_hotel,
        executado_em=executado_em,
        mensagens_anonimizadas=mensagens_anonimizadas,
        comentarios_anonimizados=comentarios_anonimizados,
        payloads_anonimizados=payloads_anonimizados,
        descricoes_anonimizadas=descricoes_anonimizadas,
        fichas_apagadas=fichas_apagadas,
        prazo_conteudo_ausente=prazo_conteudo_ausente,
        prazo_ficha_ausente=prazo_ficha_ausente,
    )


def listar_execucoes_retencao(
    conexao: Connection,
    *,
    id_hotel: int,
    repositorio=propriedade_repository,
) -> list[ExecucaoRetencaoResposta]:
    linhas = repositorio.listar_execucoes_retencao(conexao, id_hotel=id_hotel)
    logger.info(
        "comprovante id_hotel=%s acao=comprovante quantidade=%s",
        id_hotel,
        len(linhas),
    )
    return [
        ExecucaoRetencaoResposta(
            id_execucao=int(linha["id_execucao"]),
            executado_em=linha["executado_em"],
            mensagens_anonimizadas=int(linha["mensagens_anonimizadas"]),
            comentarios_anonimizados=int(linha["comentarios_anonimizados"]),
            payloads_anonimizados=int(linha["payloads_anonimizados"]),
            descricoes_anonimizadas=int(linha["descricoes_anonimizadas"]),
            fichas_apagadas=int(linha["fichas_apagadas"]),
            prazo_conteudo_ausente=bool(linha["prazo_conteudo_ausente"]),
            prazo_ficha_ausente=bool(linha["prazo_ficha_ausente"]),
        )
        for linha in linhas
    ]
