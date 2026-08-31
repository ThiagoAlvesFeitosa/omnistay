from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from app.comum.log import configurar_log
from app.modulos.acesso.router import roteador as roteador_acesso
from app.modulos.atendimento.router import roteador as roteador_atendimento
from app.modulos.conversa.router import roteador as roteador_conversa
from app.modulos.hospedagem.router import roteador as roteador_hospedagem
from app.modulos.mercado.router import roteador as roteador_mercado
from app.modulos.propriedade.router import roteador as roteador_propriedade
from app.modulos.sistema.router import roteador as roteador_sistema

_DIST_PADRAO = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def _arquivo_do_painel(dist: Path, resto: str) -> FileResponse:
    if resto:
        alvo = (dist / resto).resolve()
        try:
            alvo.relative_to(dist.resolve())
        except ValueError as erro:
            raise HTTPException(status_code=404) from erro
        if alvo.is_file():
            return FileResponse(alvo)
    index = dist / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404)


def criar_aplicacao(diretorio_estatico: Path | None = None) -> FastAPI:
    configurar_log()
    aplicacao = FastAPI(title="OmniStay")
    aplicacao.include_router(roteador_sistema)
    aplicacao.include_router(roteador_acesso)
    aplicacao.include_router(roteador_hospedagem)
    aplicacao.include_router(roteador_conversa)
    aplicacao.include_router(roteador_atendimento)
    aplicacao.include_router(roteador_propriedade)
    aplicacao.include_router(roteador_mercado)

    @aplicacao.get("/demo", include_in_schema=False)
    @aplicacao.get("/demo/", include_in_schema=False)
    def redirecionar_demo() -> RedirectResponse:
        return RedirectResponse(url="/app/simulador", status_code=307)

    dist = _DIST_PADRAO if diretorio_estatico is None else diretorio_estatico
    if dist.is_dir():

        @aplicacao.get("/app", include_in_schema=False)
        @aplicacao.get("/app/", include_in_schema=False)
        def painel_raiz() -> FileResponse:
            return _arquivo_do_painel(dist, "")

        @aplicacao.get("/app/{resto:path}", include_in_schema=False)
        def painel_resto(resto: str) -> FileResponse:
            return _arquivo_do_painel(dist, resto)

    return aplicacao


app = criar_aplicacao()
