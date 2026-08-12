"""Comando de bootstrap: primeira propriedade, gestor e parametros.

Nao e rota HTTP. Existe porque o painel exige login, o usuario exige hotel, e
nenhuma tela cria o primeiro hotel — o ovo e a galinha registrado no estado do
projeto.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from dataclasses import dataclass

from app.comum.log import configurar_log, obter_logger
from app.comum.transacao import transacao
from app.modulos.propriedade import service as propriedade_service

_logger = obter_logger(__name__)


@dataclass(frozen=True)
class ResultadoDoBootstrap:
    ok: bool
    mensagem: str
    id_hotel: int | None = None
    email_gestor: str | None = None


def _obter_senha(fornecida: str | None) -> str:
    if fornecida:
        return fornecida
    do_ambiente = os.environ.get("BOOTSTRAP_SENHA_INICIAL")
    if do_ambiente:
        return do_ambiente
    if sys.stdin.isatty():
        senha = getpass.getpass("Senha inicial do gestor: ")
        if senha:
            return senha
    raise SystemExit(
        "Senha inicial nao fornecida. Defina BOOTSTRAP_SENHA_INICIAL "
        "ou execute em terminal interativo."
    )


def executar_bootstrap(
    *,
    nome_hotel: str,
    telefone_whatsapp: str,
    nome_gestor: str,
    email_gestor: str,
    senha: str | None = None,
) -> ResultadoDoBootstrap:
    senha_gestor = _obter_senha(senha)

    try:
        with transacao() as conexao:
            criada = propriedade_service.criar_instalacao_inicial(
                conexao,
                nome_hotel=nome_hotel,
                telefone_whatsapp=telefone_whatsapp,
                nome_gestor=nome_gestor,
                email_gestor=email_gestor,
                senha_gestor=senha_gestor,
            )
    except propriedade_service.InstalacaoJaExiste as erro:
        _logger.info("BOOTSTRAP_JA_EXISTE")
        return ResultadoDoBootstrap(ok=False, mensagem=str(erro))

    _logger.info(
        "BOOTSTRAP_OK id_hotel=%s email_gestor=%s",
        criada.id_hotel,
        criada.email_gestor,
    )
    return ResultadoDoBootstrap(
        ok=True,
        mensagem=(
            f"Propriedade {criada.id_hotel} criada com gestor {criada.email_gestor}."
        ),
        id_hotel=criada.id_hotel,
        email_gestor=criada.email_gestor,
    )


def main(argv: list[str] | None = None) -> int:
    configurar_log()
    parser = argparse.ArgumentParser(
        description="Cria a propriedade inicial, o gestor e os parametros padrao."
    )
    parser.add_argument("--nome-hotel", required=True)
    parser.add_argument("--telefone-whatsapp", required=True)
    parser.add_argument("--nome-gestor", required=True)
    parser.add_argument("--email-gestor", required=True)
    argumentos = parser.parse_args(argv)

    resultado = executar_bootstrap(
        nome_hotel=argumentos.nome_hotel,
        telefone_whatsapp=argumentos.telefone_whatsapp,
        nome_gestor=argumentos.nome_gestor,
        email_gestor=argumentos.email_gestor,
    )
    print(resultado.mensagem)
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
