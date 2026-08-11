from fastapi import FastAPI

from app.comum.log import configurar_log
from app.modulos.sistema.router import roteador as roteador_sistema


def criar_aplicacao() -> FastAPI:
    configurar_log()
    aplicacao = FastAPI(title="OmniStay")
    aplicacao.include_router(roteador_sistema)
    return aplicacao


app = criar_aplicacao()
