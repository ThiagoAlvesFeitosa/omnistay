"""Implementacao falsa de LLMProvider para testes e desenvolvimento."""

from app.portas.llm import FalhaDeExtracao, ResultadoExtracao


class LLMFalso:
    def __init__(self) -> None:
        self.chamadas: list[str] = []
        self.proximo: ResultadoExtracao | None = None
        self.falhar_sempre = False
        self.falhas_restantes = 0

    def configurar(self, resultado: ResultadoExtracao) -> None:
        self.proximo = resultado

    def extrair_ficha(self, texto: str) -> ResultadoExtracao:
        self.chamadas.append(texto)
        if self.falhar_sempre or self.falhas_restantes > 0:
            if self.falhas_restantes > 0:
                self.falhas_restantes -= 1
            raise FalhaDeExtracao("llm_indisponivel")
        if self.proximo is None:
            return ResultadoExtracao(desfecho="irreconhecivel")
        return self.proximo
