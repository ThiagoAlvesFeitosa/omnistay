"""Constantes e montagem de estadia encerrada para testes de retencao.

Uso so em teste. Sem segredo, sem worker, sem canal de mensagem.
As marcas coincidem com `app.comum.retencao` (T013); aqui existem para o
suporte nao depender da implementacao.
"""

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

MARCA_TEXTO = "[anonimizado]"
MARCA_PAYLOAD = {"anonimizado": True}
MARCA_TELEFONE = "anonimizado"

CHAVE_MESES = "meses_retencao_conteudo_livre"
CHAVE_ANOS = "anos_retencao_ficha"
MESES_PADRAO = "12"
ANOS_PADRAO = "5"

AGORA_RETENCAO = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)

__all__ = [
    "CHAVE_MESES",
    "CHAVE_ANOS",
    "MESES_PADRAO",
    "ANOS_PADRAO",
    "MARCA_TEXTO",
    "MARCA_PAYLOAD",
    "MARCA_TELEFONE",
    "AGORA_RETENCAO",
    "gravar_estadia_encerrada",
]


def gravar_estadia_encerrada(
    conexao: Connection,
    id_hotel: int,
    *,
    checkout_em: datetime,
    texto: str,
    comentario: str | None = None,
    descricao: str | None = None,
    numero_quarto: str | None = None,
    janela_preferencia: str | None = None,
    id_externo: str | None = None,
    telefone: str = "5511910000099",
    nome: str = "Titular Retencao",
    intencao: str = "duvida_geral",
    sentimento: str = "neutro",
    urgencia: str = "baixa",
    classificacao_bruta: dict | None = None,
    nota: int = 4,
    incluir_avaliacao: bool = False,
    incluir_consentimento: bool = False,
) -> dict:
    """Insere hóspede, reserva encerrada, mensagem e opcionais da estadia.

    Devolve ids. A reserva percorre a máquina de estados até `encerrado`.
    """
    if checkout_em.tzinfo is None:
        checkout_em = checkout_em.replace(tzinfo=UTC)
    checkin_em = checkout_em - timedelta(days=2)
    entrada = checkin_em.date()
    saida = checkout_em.date()
    if saida <= entrada:
        saida = entrada + timedelta(days=1)

    id_reserva = conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista, status) "
            "VALUES (:h, :tel, :entrada, :saida, 'aguardando_cadastro') "
            "RETURNING id_reserva"
        ),
        {"h": id_hotel, "tel": telefone, "entrada": entrada, "saida": saida},
    ).scalar_one()
    id_hospede = conexao.execute(
        text(
            "INSERT INTO hospede (nome_completo, telefone) "
            "VALUES (:nome, :tel) RETURNING id_hospede"
        ),
        {"nome": nome, "tel": telefone},
    ).scalar_one()
    conexao.execute(
        text(
            "INSERT INTO reserva_hospede (id_reserva, id_hospede, titular,"
            " ficha_completa) VALUES (:r, :h, true, true)"
        ),
        {"r": id_reserva, "h": id_hospede},
    )
    conexao.execute(
        text(
            "UPDATE reserva SET status = 'ficha_recebida' WHERE id_reserva = :r"
        ),
        {"r": id_reserva},
    )
    conexao.execute(
        text(
            "UPDATE reserva SET status = 'hospedado', checkin_em = :c "
            "WHERE id_reserva = :r"
        ),
        {"r": id_reserva, "c": checkin_em},
    )
    conexao.execute(
        text(
            "UPDATE reserva SET status = 'encerrado', checkout_em = :s "
            "WHERE id_reserva = :r"
        ),
        {"r": id_reserva, "s": checkout_em},
    )

    bruto = classificacao_bruta
    if bruto is None:
        bruto = {"eco": texto, "tipo": "classificacao"}
    id_mensagem = conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo, id_externo,"
            " intencao, sentimento, urgencia, classificacao_bruta) "
            "VALUES (:r, 'recebida', :texto, :ext, :intencao, :sentimento,"
            " :urgencia, CAST(:bruto AS jsonb)) RETURNING id_mensagem"
        ),
        {
            "r": id_reserva,
            "texto": texto,
            "ext": id_externo,
            "intencao": intencao,
            "sentimento": sentimento,
            "urgencia": urgencia,
            "bruto": json.dumps(bruto),
        },
    ).scalar_one()

    id_evento = None
    if id_externo:
        id_evento = conexao.execute(
            text(
                "INSERT INTO evento_webhook (id_externo, payload) "
                "VALUES (:ext, CAST(:payload AS jsonb)) RETURNING id_evento"
            ),
            {
                "ext": id_externo,
                "payload": json.dumps({"texto": texto, "id": id_externo}),
            },
        ).scalar_one()

    id_solicitacao = None
    if descricao is not None:
        id_solicitacao = conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, id_mensagem_origem, tipo,"
                " descricao, numero_quarto, janela_preferencia, urgencia,"
                " status) VALUES (:r, :m, 'servico', :d, :quarto, :janela,"
                " 'media', 'aberta') RETURNING id_solicitacao"
            ),
            {
                "r": id_reserva,
                "m": id_mensagem,
                "d": descricao,
                "quarto": numero_quarto,
                "janela": janela_preferencia,
            },
        ).scalar_one()

    id_avaliacao = None
    if incluir_avaliacao or comentario is not None:
        id_avaliacao = conexao.execute(
            text(
                "INSERT INTO avaliacao (id_reserva, origem, nota, comentario) "
                "VALUES (:r, 'checkout', :nota, :c) RETURNING id_avaliacao"
            ),
            {"r": id_reserva, "nota": nota, "c": comentario},
        ).scalar_one()

    if incluir_consentimento:
        conexao.execute(
            text(
                "INSERT INTO consentimento (id_hospede, finalidade, concedido,"
                " origem) VALUES (:h, 'comunicacao_marketing', true, 'painel')"
            ),
            {"h": id_hospede},
        )

    return {
        "id_reserva": id_reserva,
        "id_hospede": id_hospede,
        "id_mensagem": id_mensagem,
        "id_evento": id_evento,
        "id_solicitacao": id_solicitacao,
        "id_avaliacao": id_avaliacao,
    }
