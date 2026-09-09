"""Apaga dados de teste, mantendo a estrutura do banco.

Dois modos:

  PADRAO — apaga so o que e do hospede: reservas, fichas, conversas, chamados,
  consumos, avaliacoes e a fila de trabalho. Preserva hotel, usuarios, catalogo,
  itens vendaveis, textos de boas-vindas, concorrentes e sua sessao aberta.
  E o que voce quer entre um teste e outro.

      uv run python scripts/zerar_demo.py --confirmar

  TUDO — apaga tambem hotel, usuarios e configuracao. Depois dele e preciso
  rodar o bootstrap e o semear_demo de novo.

      uv run python scripts/zerar_demo.py --tudo --confirmar
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine, text

from app.config import obter_configuracao


# O que e do hospede e nasce de novo a cada teste.
DO_HOSPEDE = [
    "trabalho",
    "avaliacao",
    "consumo",
    "solicitacao",
    "mensagem",
    "evento_webhook",
    "consentimento",
    "reserva_hospede",
    "reserva",
    "hospede",
]

# O que e configuracao da casa e voce nao quer redigitar.
PRESERVADAS = [
    "hotel",
    "usuario",
    "sessao",
    "parametro_hotel",
    "catalogo_item",
    "item_vendavel",
    "concorrente",
    "coleta_mercado",
    "execucao_retencao",
]


def main() -> int:
    p = argparse.ArgumentParser(description="Apaga dados de teste do banco.")
    p.add_argument(
        "--tudo",
        action="store_true",
        help="apaga tambem hotel, usuarios e configuracao (exige bootstrap depois)",
    )
    p.add_argument(
        "--confirmar",
        action="store_true",
        help="obrigatorio: confirma que voce quer apagar",
    )
    a = p.parse_args()

    url = obter_configuracao().database_url
    onde = url.split("@")[-1].split("?")[0]

    if not a.confirmar:
        if a.tudo:
            print(f"Isto apaga TODOS os dados de: {onde}")
            print("Inclusive hotel, usuarios e catalogo. Voce teria que refazer")
            print("o bootstrap e o semear_demo.")
        else:
            print(f"Isto apaga os dados de HOSPEDE de: {onde}")
            print("Some: " + ", ".join(DO_HOSPEDE))
            print("Fica:  " + ", ".join(PRESERVADAS))
        print("\nSe e isso mesmo, rode de novo com --confirmar")
        return 1

    motor = create_engine(url)
    with motor.begin() as conexao:
        existentes = {
            linha[0]
            for linha in conexao.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                )
            )
        }
        if not existentes:
            print("Nenhuma tabela encontrada. As migracoes ja rodaram?")
            return 1

        alvos = sorted(existentes) if a.tudo else [
            t for t in DO_HOSPEDE if t in existentes
        ]
        if not alvos:
            print("Nada a apagar.")
            return 0

        conexao.execute(text(f"TRUNCATE {', '.join(alvos)} RESTART IDENTITY CASCADE"))

    print(f"Banco: {onde}")
    print(f"Apagadas {len(alvos)} tabelas: {', '.join(alvos)}")

    if a.tudo:
        print("\nProximo passo: rodar o bootstrap e depois o semear_demo.")
    else:
        nao_tocadas = sorted(t for t in PRESERVADAS if t in existentes)
        print(f"Preservadas: {', '.join(nao_tocadas)}")
        print("\nO catalogo, os usuarios e os textos continuam la.")
        print("Cadastre uma reserva nova no painel e recomece a jornada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
