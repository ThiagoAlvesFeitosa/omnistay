"""Webhook de estadia — grava sem classificar."""

import json

import pytest
from sqlalchemy import text

from testes.integracao.test_confirmar_chegada import _tornar
from testes.integracao.test_reservas import _corpo_valido, _login
from testes.suporte.webhook import postar_webhook

SEGREDO = "segredo-teste-webhook-estadia"


@pytest.fixture
def webhook_estadia(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "token-teste")
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    yield cliente, ambiente
    obter_configuracao.cache_clear()


def _criar_hospedada(cliente, ambiente, **kwargs) -> int:
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido(**kwargs)).json()[
        "id_reserva"
    ]
    _tornar(ambiente, id_reserva, "ficha_recebida")
    _tornar(ambiente, id_reserva, "hospedado")
    return id_reserva


def _contagens(ambiente, id_reserva: int) -> dict:
    with ambiente.conexao() as conexao:
        return {
            "recebidas": conexao.execute(
                text(
                    "SELECT COUNT(*) FROM mensagem"
                    " WHERE id_reserva = :r AND direcao = 'recebida'"
                ),
                {"r": id_reserva},
            ).scalar_one(),
            "enviadas_novas": conexao.execute(
                text(
                    "SELECT COUNT(*) FROM mensagem"
                    " WHERE id_reserva = :r AND direcao = 'enviada'"
                    " AND enviada_em > now() - interval '1 minute'"
                    " AND status_envio IS NOT NULL"
                ),
                {"r": id_reserva},
            ).scalar_one(),
            "classificar": conexao.execute(
                text(
                    "SELECT COUNT(*) FROM trabalho"
                    " WHERE tipo = 'classificar_mensagem'"
                    " AND (payload->>'id_reserva')::bigint = :r"
                ),
                {"r": id_reserva},
            ).scalar_one(),
            "eventos": conexao.execute(
                text("SELECT COUNT(*) FROM evento_webhook")
            ).scalar_one(),
            "status": conexao.execute(
                text("SELECT status FROM reserva WHERE id_reserva = :r"),
                {"r": id_reserva},
            ).scalar_one(),
            "intencao": conexao.execute(
                text(
                    "SELECT intencao, sentimento, urgencia FROM mensagem"
                    " WHERE id_reserva = :r AND direcao = 'recebida'"
                    " ORDER BY id_mensagem DESC LIMIT 1"
                ),
                {"r": id_reserva},
            ).mappings().first(),
        }


@pytest.mark.postgres
def test_hospedado_grava_mensagem_e_trabalho_pendente(webhook_estadia):
    cliente, ambiente = webhook_estadia
    id_reserva = _criar_hospedada(cliente, ambiente)

    resposta = postar_webhook(
        cliente,
        {
            "id_externo": "evt-est-1",
            "telefone_origem": "11987654321",
            "texto": "que horas e o cafe",
            "tem_texto_utilizavel": True,
        },
        segredo=SEGREDO,
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "enfileirado"

    dados = _contagens(ambiente, id_reserva)
    assert dados["status"] == "hospedado"
    assert dados["recebidas"] == 1
    assert dados["classificar"] == 1
    assert dados["intencao"]["intencao"] is None
    assert dados["intencao"]["sentimento"] is None
    assert dados["intencao"]["urgencia"] is None

    with ambiente.conexao() as conexao:
        conteudo = conexao.execute(
            text(
                "SELECT conteudo FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        status_trabalho = conexao.execute(
            text(
                "SELECT status FROM trabalho WHERE tipo = 'classificar_mensagem'"
            )
        ).scalar_one()
    assert conteudo == "que horas e o cafe"
    assert status_trabalho == "pendente"


@pytest.mark.postgres
def test_ficha_recebida_sem_checkin_nao_abre_conversa(webhook_estadia):
    cliente, ambiente = webhook_estadia
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    _tornar(ambiente, id_reserva, "ficha_recebida")

    resposta = postar_webhook(
        cliente,
        {
            "id_externo": "evt-sem-chegada",
            "telefone_origem": "11987654321",
            "texto": "ja cheguei",
            "tem_texto_utilizavel": True,
        },
        segredo=SEGREDO,
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "sem_reserva"
    dados = _contagens(ambiente, id_reserva)
    assert dados["status"] == "ficha_recebida"
    assert dados["recebidas"] == 0
    assert dados["classificar"] == 0


@pytest.mark.postgres
def test_telefone_de_outro_hotel_nao_grava_na_reserva_alheia(webhook_estadia):
    cliente, ambiente = webhook_estadia
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    id_b = cliente.post(
        "/reservas",
        json=_corpo_valido(telefone="11999999999"),
    ).json()["id_reserva"]
    _tornar(ambiente, id_b, "ficha_recebida")
    _tornar(ambiente, id_b, "hospedado")

    resposta = postar_webhook(
        cliente,
        {
            "id_externo": "evt-hotel-b",
            "telefone_origem": "11999999999",
            "texto": "oi do quarto",
            "tem_texto_utilizavel": True,
        },
        segredo=SEGREDO,
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "sem_reserva"
    with ambiente.conexao() as conexao:
        recebidas_b = conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_b},
        ).scalar_one()
    assert recebidas_b == 0


def _eventos_mensagens_trabalhos(ambiente) -> tuple[int, int, int]:
    with ambiente.conexao() as conexao:
        return (
            conexao.execute(text("SELECT COUNT(*) FROM evento_webhook")).scalar_one(),
            conexao.execute(
                text("SELECT COUNT(*) FROM mensagem WHERE direcao = 'recebida'")
            ).scalar_one(),
            conexao.execute(
                text(
                    "SELECT COUNT(*) FROM trabalho"
                    " WHERE tipo = 'classificar_mensagem'"
                )
            ).scalar_one(),
        )


@pytest.mark.postgres
def test_post_sem_assinatura_e_recusado(webhook_estadia):
    cliente, ambiente = webhook_estadia
    _criar_hospedada(cliente, ambiente)
    antes = _eventos_mensagens_trabalhos(ambiente)
    corpo = json.dumps(
        {
            "id_externo": "evt-sem-sig",
            "telefone_origem": "11987654321",
            "texto": "forjado",
            "tem_texto_utilizavel": True,
        }
    ).encode()
    resposta = cliente.post(
        "/webhook",
        content=corpo,
        headers={"Content-Type": "application/json"},
    )
    assert resposta.status_code == 401
    assert _eventos_mensagens_trabalhos(ambiente) == antes


@pytest.mark.postgres
def test_hmac_invalido_em_hospedado_e_recusado(webhook_estadia):
    cliente, ambiente = webhook_estadia
    _criar_hospedada(cliente, ambiente)
    antes = _eventos_mensagens_trabalhos(ambiente)
    corpo = json.dumps(
        {
            "id_externo": "evt-hmac-ruim",
            "telefone_origem": "11987654321",
            "texto": "forjado",
            "tem_texto_utilizavel": True,
        }
    ).encode()
    resposta = cliente.post(
        "/webhook",
        content=corpo,
        headers={
            "Content-Type": "application/json",
            "X-Omnistay-Signature": "sha256=00",
        },
    )
    assert resposta.status_code == 401
    assert _eventos_mensagens_trabalhos(ambiente) == antes


@pytest.mark.postgres
def test_segredo_vazio_recusa_qualquer_envelope(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "")
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    _criar_hospedada(cliente, ambiente)
    antes = _eventos_mensagens_trabalhos(ambiente)
    resposta = postar_webhook(
        cliente,
        {
            "id_externo": "evt-sem-segredo",
            "telefone_origem": "11987654321",
            "texto": "nao deveria entrar",
            "tem_texto_utilizavel": True,
        },
        segredo="qualquer",
    )
    assert resposta.status_code == 401
    assert _eventos_mensagens_trabalhos(ambiente) == antes
    obter_configuracao.cache_clear()


@pytest.mark.postgres
def test_reenvio_do_mesmo_evento_nao_duplica_estadia(webhook_estadia):
    cliente, ambiente = webhook_estadia
    id_reserva = _criar_hospedada(cliente, ambiente)
    payload = {
        "id_externo": "evt-dup-est",
        "telefone_origem": "11987654321",
        "texto": "toalha extra",
        "tem_texto_utilizavel": True,
    }
    assert postar_webhook(cliente, payload, segredo=SEGREDO).status_code == 200
    segundo = postar_webhook(cliente, payload, segredo=SEGREDO)
    assert segundo.status_code == 200
    assert segundo.json()["status"] == "duplicado"
    dados = _contagens(ambiente, id_reserva)
    assert dados["recebidas"] == 1
    assert dados["classificar"] == 1


@pytest.mark.postgres
def test_worker_nao_consome_classificar_mensagem(webhook_estadia):
    from app.adaptadores.mensageria_falsa import MensageriaFalsa
    from worker.consumidor import processar_uma_passagem

    cliente, ambiente = webhook_estadia
    id_reserva = _criar_hospedada(cliente, ambiente)
    postar_webhook(
        cliente,
        {
            "id_externo": "evt-worker",
            "telefone_origem": "11987654321",
            "texto": "wifi caiu",
            "tem_texto_utilizavel": True,
        },
        segredo=SEGREDO,
    )
    with ambiente.engine.begin() as conexao:
        id_trabalho, status_antes = conexao.execute(
            text(
                "SELECT id_trabalho, status FROM trabalho"
                " WHERE tipo = 'classificar_mensagem'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).one()
        processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        linha = conexao.execute(
            text(
                "SELECT id_trabalho, status, erro_ultima_tentativa"
                " FROM trabalho WHERE id_trabalho = :id"
            ),
            {"id": id_trabalho},
        ).mappings().one()
    assert status_antes == "pendente"
    assert linha["id_trabalho"] == id_trabalho
    assert linha["status"] == "pendente"
    assert linha["erro_ultima_tentativa"] is None


@pytest.mark.postgres
def test_log_e_payload_do_evento_nao_levam_texto(webhook_estadia, caplog):
    import logging

    caplog.set_level(logging.INFO)
    cliente, ambiente = webhook_estadia
    _criar_hospedada(cliente, ambiente)
    texto = "segredo do hospede na estadia"
    postar_webhook(
        cliente,
        {
            "id_externo": "evt-log",
            "telefone_origem": "11987654321",
            "texto": texto,
            "tem_texto_utilizavel": True,
        },
        segredo=SEGREDO,
    )
    cliente.post(
        "/webhook",
        content=b'{"id_externo":"evt-401","texto":"nao vazar"}',
        headers={"Content-Type": "application/json"},
    )
    assert texto not in caplog.text
    assert "nao vazar" not in caplog.text
    with ambiente.conexao() as conexao:
        payload = conexao.execute(
            text(
                "SELECT payload FROM evento_webhook WHERE id_externo = 'evt-log'"
            )
        ).scalar_one()
    bruto = json.dumps(payload)
    assert texto not in bruto
    assert "texto" not in payload


@pytest.mark.postgres
def test_envelope_de_status_nao_vira_mensagem_de_hospede(webhook_estadia):
    cliente, ambiente = webhook_estadia
    id_reserva = _criar_hospedada(cliente, ambiente)
    resposta = postar_webhook(
        cliente,
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {"id": "wamid-status-1", "status": "delivered"}
                                ]
                            }
                        }
                    ]
                }
            ]
        },
        segredo=SEGREDO,
    )
    assert resposta.status_code == 200
    dados = _contagens(ambiente, id_reserva)
    assert dados["recebidas"] == 0
    assert dados["classificar"] == 0

    ilegivel = postar_webhook(cliente, {"foo": 1}, segredo=SEGREDO)
    assert ilegivel.status_code == 400


@pytest.mark.postgres
def test_get_webhook_desafio_de_posse(webhook_estadia):
    cliente, _ = webhook_estadia
    ok = cliente.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "token-teste",
            "hub.challenge": "abc",
        },
    )
    assert ok.status_code == 200
    assert ok.text == "abc"
    ruim = cliente.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "errado",
            "hub.challenge": "abc",
        },
    )
    assert ruim.status_code == 403

