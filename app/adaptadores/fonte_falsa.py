"""Fonte publica falsa: mapa URL -> diretiva e resultado. Sem rede."""

from decimal import Decimal

from app.portas.fonte_publica import (
    DESFECHO_ENCONTRADO,
    DIRETIVA_PERMITE,
    ResultadoPublico,
)

IDENTIDADE_PADRAO = "OmniStay-Coletor/1.0"
PRECO_PADRAO = Decimal("150.00")
NOTA_PADRAO = Decimal("4.50")


class FonteFalsa:
    """Configuravel por URL. Padrao: diretiva permite e dado encontrado."""

    def __init__(self) -> None:
        self._por_url: dict[str, tuple[str, ResultadoPublico]] = {}
        self.ultima_identidade: str | None = None
        self.chamadas_diretiva: list[str] = []
        self.chamadas_coletar: list[str] = []
        self.padrao_diretiva = DIRETIVA_PERMITE
        self.padrao_resultado = ResultadoPublico(
            desfecho=DESFECHO_ENCONTRADO,
            preco=PRECO_PADRAO,
            nota_media=NOTA_PADRAO,
        )

    def configurar(
        self,
        url_fonte: str,
        *,
        diretiva: str | None = None,
        resultado: ResultadoPublico | None = None,
    ) -> None:
        atual_dir, atual_res = self._por_url.get(
            url_fonte, (self.padrao_diretiva, self.padrao_resultado)
        )
        self._por_url[url_fonte] = (
            diretiva if diretiva is not None else atual_dir,
            resultado if resultado is not None else atual_res,
        )

    def consultar_diretiva(self, url_fonte: str) -> str:
        self.ultima_identidade = IDENTIDADE_PADRAO
        self.chamadas_diretiva.append(url_fonte)
        diretiva, _ = self._por_url.get(
            url_fonte, (self.padrao_diretiva, self.padrao_resultado)
        )
        return diretiva

    def coletar_publico(self, url_fonte: str) -> ResultadoPublico:
        self.ultima_identidade = IDENTIDADE_PADRAO
        self.chamadas_coletar.append(url_fonte)
        _, resultado = self._por_url.get(
            url_fonte, (self.padrao_diretiva, self.padrao_resultado)
        )
        return resultado
