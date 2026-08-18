"""Criacao inicial da propriedade e leitura de parametros operacionais."""

from dataclasses import dataclass

from sqlalchemy.engine import Connection

from app.comum.log import obter_logger
from app.modulos.acesso import service as acesso_service
from app.modulos.propriedade import repository as propriedade_repository
from app.modulos.propriedade.schema import ItemCatalogoResposta

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

CHAVES_SLOTS_BOAS_VINDAS = {
    "cafe": "boas_vindas_cafe",
    "wifi": "boas_vindas_wifi",
    "checkout": "boas_vindas_checkout",
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
