"""Implementacao falsa de LLMProvider para testes e desenvolvimento."""

from app.portas.llm import (
    FalhaDeClassificacao,
    FalhaDeConversacao,
    FalhaDeExtracao,
    FalhaDeIdentificacao,
    ResultadoClassificacao,
    ResultadoExtracao,
    ResultadoIdentificacao,
    ResultadoPesquisaSaida,
    ResultadoResposta,
)


class LLMFalso:
    def __init__(self) -> None:
        self.chamadas: list[str] = []
        self.chamadas_classificar: list[str] = []
        self.chamadas_responder: list[tuple] = []
        self.chamadas_identificar: list[tuple] = []
        self.chamadas_pesquisa_saida: list[str] = []
        self.proximo: ResultadoExtracao | None = None
        self.proximo_classificacao: ResultadoClassificacao | None = None
        self.proximo_resposta: ResultadoResposta | None = None
        self.proximo_identificacao: ResultadoIdentificacao | None = None
        self.proximo_pesquisa_saida: ResultadoPesquisaSaida | None = None
        self.falhar_sempre = False
        self.falhar_classificacao = False
        self.falhar_conversacao = False
        self.falhar_identificacao = False
        self.falhar_pesquisa_saida = False
        self.falhas_restantes = 0

    def configurar(self, resultado: ResultadoExtracao) -> None:
        self.proximo = resultado

    def configurar_classificacao(self, resultado: ResultadoClassificacao) -> None:
        self.proximo_classificacao = resultado

    def configurar_resposta(self, resultado: ResultadoResposta) -> None:
        self.proximo_resposta = resultado

    def configurar_identificacao(self, resultado: ResultadoIdentificacao) -> None:
        self.proximo_identificacao = resultado

    def configurar_pesquisa_saida(self, resultado: ResultadoPesquisaSaida) -> None:
        self.proximo_pesquisa_saida = resultado

    def extrair_ficha(self, texto: str) -> ResultadoExtracao:
        self.chamadas.append(texto)
        if self.falhar_sempre or self.falhas_restantes > 0:
            if self.falhas_restantes > 0:
                self.falhas_restantes -= 1
            raise FalhaDeExtracao("llm_indisponivel")
        if self.proximo is None:
            return ResultadoExtracao(desfecho="irreconhecivel")
        return self.proximo

    def classificar(self, texto: str) -> ResultadoClassificacao:
        self.chamadas_classificar.append(texto)
        if self.falhar_classificacao:
            raise FalhaDeClassificacao("llm_indisponivel")
        if self.proximo_classificacao is None:
            return ResultadoClassificacao(
                intencao="duvida_geral",
                sentimento="neutro",
                urgencia="baixa",
                bruto={
                    "intencao": "duvida_geral",
                    "sentimento": "neutro",
                    "urgencia": "baixa",
                },
            )
        return self.proximo_classificacao

    def responder_duvida(self, pergunta: str, itens_ativos: tuple) -> ResultadoResposta:
        self.chamadas_responder.append((pergunta, itens_ativos))
        if self.falhar_conversacao:
            raise FalhaDeConversacao("llm_indisponivel")
        if self.proximo_resposta is not None:
            return self.proximo_resposta
        if not itens_ativos:
            return ResultadoResposta(coberta=False)
        primeiro = itens_ativos[0]
        trecho = primeiro.conteudo
        return ResultadoResposta(
            coberta=True,
            texto=trecho,
            trechos_citados=(trecho,),
        )

    def identificar_item_vendavel(
        self, texto: str, itens_ativos: tuple
    ) -> ResultadoIdentificacao:
        self.chamadas_identificar.append((texto, itens_ativos))
        if self.falhar_identificacao:
            raise FalhaDeIdentificacao("indisponivel")
        if self.proximo_identificacao is not None:
            return self.proximo_identificacao
        return ResultadoIdentificacao(desfecho="nenhum")

    def interpretar_pesquisa_saida(self, texto: str) -> ResultadoPesquisaSaida:
        self.chamadas_pesquisa_saida.append(texto)
        if self.falhar_pesquisa_saida:
            raise FalhaDeExtracao("llm_indisponivel")
        if self.proximo_pesquisa_saida is not None:
            return self.proximo_pesquisa_saida
        return ResultadoPesquisaSaida(desfecho="irreconhecivel")
