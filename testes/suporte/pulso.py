"""Constantes e montagem de estadia para testes do pulso do segundo dia."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

CHAVE_MINIMO_PULSO = "horas_minimas_para_pulso"
VALOR_PADRAO_MINIMO = "24"


def proibicoes_da_pergunta() -> tuple[str, ...]:
    return ("extrato", "conta", "oferta", "consentimento", "marketing")


def proibicoes_do_reconhecimento() -> tuple[str, ...]:
    return ("gostando", "que bom")


def proibicoes_da_confirmacao_negativa() -> tuple[str, ...]:
    return ("que horas", "horario", "horário", "extrato", "conta", "prazo")


def montar_hospedado_para_pulso(
    conexao: Connection,
    *,
    id_hotel: int,
    nome: str = "Marina Duarte",
    telefone: str = "5511910000001",
    checkin_em: datetime | None = None,
    noites: int = 3,
) -> int:
    """Reserva hospedada com titular. Padrao: check-in ontem UTC, saida daqui a `noites` dias."""
    if checkin_em is None:
        checkin_em = datetime.now(UTC) - timedelta(days=1, hours=3)
    if checkin_em.tzinfo is None:
        checkin_em = checkin_em.replace(tzinfo=UTC)
    entrada = checkin_em.date()
    saida = entrada + timedelta(days=noites)
    id_reserva = conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista, status, checkin_em) "
            "VALUES (:h, :tel, :entrada, :saida, 'aguardando_cadastro', NULL) "
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
    return id_reserva


def gravar_pulso_enviado(
    conexao: Connection,
    *,
    id_hotel: int,
    id_reserva: int,
    conteudo: str = "Como esta sendo sua estadia?",
) -> int:
    id_mensagem = conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo, status_envio,"
            " enviada_em) VALUES (:r, 'enviada', :c, 'enviada', now())"
            " RETURNING id_mensagem"
        ),
        {"r": id_reserva, "c": conteudo},
    ).scalar_one()
    conexao.execute(
        text(
            "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
            "VALUES (:h, 'enviar_pulso', CAST(:p AS jsonb), 'concluido')"
        ),
        {
            "h": id_hotel,
            "p": '{"id_reserva": %s, "id_mensagem": %s}'
            % (id_reserva, id_mensagem),
        },
    )
    return id_mensagem
