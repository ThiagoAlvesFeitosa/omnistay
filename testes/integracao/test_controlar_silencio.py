"""F1.4 — controlar o silencio: lembrete unico, corte e cancelamento."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from worker.agendador import verificar_cadastros_pendentes
from worker.consumidor import processar_uma_passagem_na_engine
from testes.integracao.test_interpretar_ficha import _post_webhook
from testes.integracao.test_reservas import _corpo_valido, _login

SEGREDO = "segredo-teste-webhook"


def _checkin_longe():
    hoje = date.today()
    return {
        "data_checkin_prevista": (hoje + timedelta(days=10)).isoformat(),
        "data_checkout_prevista": (hoje + timedelta(days=13)).isoformat(),
    }


def _criar_com_coleta_enviada(cliente, ambiente, **corpo):
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido(**corpo)).json()[
        "id_reserva"
    ]
    processar_uma_passagem_na_engine(ambiente.engine, gateway=MensageriaFalsa())
    return id_reserva


def _envelhecer_coleta(engine, id_reserva, horas=25):
    with engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE mensagem SET enviada_em = :quando"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
                " AND status_envio = 'enviada'"
            ),
            {
                "r": id_reserva,
                "quando": datetime.now(UTC) - timedelta(hours=horas),
            },
        )


def _contar(engine, sql, **params):
    with engine.connect() as conexao:
        return conexao.execute(text(sql), params).scalar_one()


@pytest.mark.postgres
def test_silencio_dispara_um_unico_lembrete(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente, **_checkin_longe())
    _envelhecer_coleta(ambiente.engine, id_reserva)

    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)

    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 1
    )
    assert (
        _contar(
            ambiente.engine,
            "SELECT reenvio_realizado FROM reserva WHERE id_reserva = :r",
            r=id_reserva,
        )
        is True
    )

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    lembretes = [e for e in porta.envios if e.get("tipo") == "lembrete"]
    assert len(lembretes) == 1
    assert "opcional" in lembretes[0]["corpo"]
    assert "recepcao" in lembretes[0]["corpo"]
    assert lembretes[0]["primeiro_nome"] == "Maria"

    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 1
    )
    assert (
        _contar(
            ambiente.engine,
            "SELECT status FROM reserva WHERE id_reserva = :r",
            r=id_reserva,
        )
        == "aguardando_cadastro"
    )


@pytest.mark.postgres
def test_corte_marca_sem_cadastro_e_aparece_na_fila(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)

    status = _contar(
        ambiente.engine,
        "SELECT status FROM reserva WHERE id_reserva = :r",
        r=id_reserva,
    )
    assert status == "sem_cadastro_previo"
    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 0
    )
    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["id_reserva"] == id_reserva
    assert item["estado_cadastro"] == "sem_cadastro_previo"
    assert item["status"] == "sem_cadastro_previo"


@pytest.mark.postgres
def test_sem_cadastro_previo_permite_transicao_para_hospedado(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
        conexao.execute(
            text(
                "UPDATE reserva SET status = 'hospedado', checkin_em = now()"
                " WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        )
    assert (
        _contar(
            ambiente.engine,
            "SELECT status FROM reserva WHERE id_reserva = :r",
            r=id_reserva,
        )
        == "hospedado"
    )


@pytest.mark.postgres
def test_resposta_antes_do_prazo_cancela_lembrete(
    app_sobre_ambiente, monkeypatch
):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente, **_checkin_longe())
    assert (
        _post_webhook(
            cliente,
            {
                "id_externo": "evt-cancela-silencio",
                "telefone_origem": "11987654321",
                "texto": "resposta qualquer",
                "tem_texto_utilizavel": True,
            },
        ).status_code
        == 200
    )
    _envelhecer_coleta(ambiente.engine, id_reserva)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 0
    )
    assert (
        _contar(
            ambiente.engine,
            "SELECT status FROM reserva WHERE id_reserva = :r",
            r=id_reserva,
        )
        == "aguardando_cadastro"
    )


@pytest.mark.postgres
def test_coleta_nao_enviada_nao_gera_lembrete(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post(
        "/reservas", json=_corpo_valido(**_checkin_longe())
    ).json()["id_reserva"]
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE mensagem SET status_envio = 'falha'"
                " WHERE id_reserva = :r"
            ),
            {"r": id_reserva},
        )
        verificar_cadastros_pendentes(conexao)
    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 0
    )


@pytest.mark.postgres
def test_alterar_prazo_muda_o_momento_do_lembrete(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE parametro_hotel SET valor = '48'"
                " WHERE id_hotel = :h AND chave = 'horas_ate_reenvio'"
            ),
            {"h": hotel},
        )
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente, **_checkin_longe())
    _envelhecer_coleta(ambiente.engine, id_reserva, horas=25)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 0
    )
    _envelhecer_coleta(ambiente.engine, id_reserva, horas=49)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM trabalho WHERE tipo = 'enviar_lembrete'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 1
    )


@pytest.mark.postgres
def test_retry_do_lembrete_nao_cria_segunda_mensagem(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente, **_checkin_longe())
    _envelhecer_coleta(ambiente.engine, id_reserva)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)

    porta = MensageriaFalsa()
    porta.falhas_restantes = 1
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE trabalho SET proxima_tentativa_em = NULL"
                " WHERE tipo = 'enviar_lembrete'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        )
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    assert len([e for e in porta.envios if e.get("tipo") == "lembrete"]) == 1
    assert (
        _contar(
            ambiente.engine,
            "SELECT count(*) FROM mensagem WHERE id_reserva = :r"
            " AND direcao = 'enviada'",
            r=id_reserva,
        )
        == 2
    )


@pytest.mark.postgres
def test_resposta_apos_lembrete_impede_marcacao_na_corte(
    app_sobre_ambiente, monkeypatch
):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente, **_checkin_longe())
    _envelhecer_coleta(ambiente.engine, id_reserva)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
    assert (
        _post_webhook(
            cliente,
            {
                "id_externo": "evt-depois-lembrete",
                "telefone_origem": "11987654321",
                "texto": "cheguei atrasado",
                "tem_texto_utilizavel": True,
            },
        ).status_code
        == 200
    )
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE parametro_hotel SET valor = '99999'"
                " WHERE id_hotel = :h AND chave = 'horas_corte_antes_checkin'"
            ),
            {"h": ambiente.propriedade_a.id_hotel},
        )
        verificar_cadastros_pendentes(conexao)
    assert (
        _contar(
            ambiente.engine,
            "SELECT status FROM reserva WHERE id_reserva = :r",
            r=id_reserva,
        )
        != "sem_cadastro_previo"
    )
