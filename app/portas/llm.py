"""Porta de LLM — o dominio depende so desta interface."""

from dataclasses import dataclass, field
from typing import Protocol


class FalhaDeExtracao(Exception):
    """Extrator indisponivel ou erro tipado, sem eco do texto."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


CAMPOS_FICHA_CHAVE = (
    "nome_completo",
    "profissao",
    "data_nascimento",
    "tipo_documento",
    "numero_documento",
    "endereco",
    "cep",
    "cidade",
    "telefone",
)


@dataclass(frozen=True)
class ResultadoExtracao:
    """Campos opcionais da ficha — nunca inclui idade."""

    desfecho: str  # completa | parcial | irreconhecivel
    campos: dict[str, str] = field(default_factory=dict)
    campos_reconhecidos: tuple[str, ...] = ()


class FalhaDeClassificacao(Exception):
    """Classificador indisponivel, recusa ou tempo esgotado — sem eco do texto."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


class FalhaDeConversacao(Exception):
    """Redacao a partir do catalogo indisponivel — sem eco do texto."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


class FalhaDeIdentificacao(Exception):
    """Identificador de item indisponivel, recusa ou tempo esgotado — sem eco do texto."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


@dataclass(frozen=True)
class ResultadoClassificacao:
    """Eixos da mensagem de estadia. Valores podem ser invalidos; o dominio valida."""

    intencao: str | None
    sentimento: str | None
    urgencia: str | None
    bruto: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ResultadoResposta:
    """Redacao de duvida geral. O dominio valida trechos contra o catalogo."""

    coberta: bool
    texto: str | None = None
    trechos_citados: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultadoIdentificacao:
    """Item vendavel reconhecido. O dominio valida id e quantidade; o preco vem do banco."""

    desfecho: str  # unico | nenhum | ambiguo
    id_item_vendavel: int | None = None
    quantidade: int | None = None


@dataclass(frozen=True)
class ResultadoPesquisaSaida:
    """Leitura da pesquisa de saida. O dominio valida nota e nao promove silencio a recusa."""

    desfecho: str  # completo | parcial | irreconhecivel
    nota: int | None = None
    comentario: str | None = None
    aceite: bool | None = None


class LLMProvider(Protocol):
    def extrair_ficha(self, texto: str) -> ResultadoExtracao: ...
    def classificar(self, texto: str) -> ResultadoClassificacao: ...
    def responder_duvida(
        self, pergunta: str, itens_ativos: tuple, tom: str = ""
    ) -> ResultadoResposta: ...
    def identificar_item_vendavel(
        self, texto: str, itens_ativos: tuple
    ) -> ResultadoIdentificacao: ...
    def interpretar_pesquisa_saida(self, texto: str) -> ResultadoPesquisaSaida: ...
