from fastapi import FastAPI

from app.comum.log import configurar_log
from app.modulos.acesso.router import roteador as roteador_acesso
from app.modulos.atendimento.router import roteador as roteador_atendimento
from app.modulos.conversa.router import roteador as roteador_conversa
from app.modulos.hospedagem.router import roteador as roteador_hospedagem
from app.modulos.mercado.router import roteador as roteador_mercado
from app.modulos.propriedade.router import roteador as roteador_propriedade
from app.modulos.sistema.router import roteador as roteador_sistema


def criar_aplicacao() -> FastAPI:
    configurar_log()
    aplicacao = FastAPI(title="OmniStay")
    aplicacao.include_router(roteador_sistema)
    aplicacao.include_router(roteador_acesso)
    aplicacao.include_router(roteador_hospedagem)
    aplicacao.include_router(roteador_conversa)
    aplicacao.include_router(roteador_atendimento)
    aplicacao.include_router(roteador_propriedade)
    aplicacao.include_router(roteador_mercado)
    return aplicacao


app = criar_aplicacao()
