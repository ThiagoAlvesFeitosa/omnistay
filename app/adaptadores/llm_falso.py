"""Implementacao falsa de LLMProvider para testes e desenvolvimento."""

from app.portas.llm import (
    FalhaDeClassificacao,
    FalhaDeExtracao,
    ResultadoClassificacao,
    ResultadoExtracao,
)


class LLMFalso:
    def __init__(self) -> None:
        self.chamadas: list[str] = []
        self.chamadas_classificar: list[str] = []
        self.proximo: ResultadoExtracao | None = None
        self.proximo_classificacao: ResultadoClassificacao | None = None
        self.falhar_sempre = False
        self.falhar_classificacao = False
        self.falhas_restantes = 0

    def configurar(self, resultado: ResultadoExtracao) -> None:
        self.proximo = resultado

    def configurar_classificacao(self, resultado: ResultadoClassificacao) -> None:
        self.proximo_classificacao = resultado

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
