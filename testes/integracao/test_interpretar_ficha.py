"""Worker interpreta ficha com LLM falso."""

import hashlib
import hmac
import json

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.llm import CAMPOS_FICHA_CHAVE, ResultadoExtracao
from worker.consumidor import processar_uma_passagem_na_engine
from testes.integracao.test_reservas import _corpo_valido, _login

SEGREDO = "segredo-teste-webhook"


def _assinar(corpo: bytes) -> str:
    digest = hmac.new(SEGREDO.encode(), corpo, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post_webhook(cliente, payload: dict):
    corpo = json.dumps(payload).encode("utf-8")
    return cliente.post(
        "/webhook",
        content=corpo,
        headers={
            "Content-Type": "application/json",
            "X-Omnistay-Signature": _assinar(corpo),
        },
    )


def _campos_completos() -> dict[str, str]:
    return {
        "nome_completo": "Maria Silva",
        "profissao": "Engenheira",
        "data_nascimento": "1990-05-12",
        "tipo_documento": "rg",
        "numero_documento": "1234567",
        "endereco": "Rua A, 100",
        "cep": "01310100",
        "cidade": "Sao Paulo",
        "telefone": "5511987654321",
    }


@pytest.fixture
def cenario(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    # Consome envio da coleta para nao misturar com interpretar
    processar_uma_passagem_na_engine(ambiente.engine, gateway=MensageriaFalsa())
    return cliente, ambiente, id_reserva


@pytest.mark.postgres
def test_caminho_completo_consolida_ficha(cenario):
    cliente, ambiente, id_reserva = cenario
    assert (
        _post_webhook(
            cliente,
            {
                "id_externo": "evt-completo",
                "telefone_origem": "11987654321",
                "texto": "ficha completa",
                "tem_texto_utilizavel": True,
            },
        ).status_code
        == 200
    )

    llm = LLMFalso()
    campos = _campos_completos()
    llm.configurar(
        ResultadoExtracao(
            desfecho="completa",
            campos=campos,
            campos_reconhecidos=tuple(CAMPOS_FICHA_CHAVE),
        )
    )
    processar_uma_passagem_na_engine(
        ambiente.engine, gateway=MensageriaFalsa(), llm=llm
    )

    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["status"] == "ficha_recebida"
    assert item["estado_cadastro"] == "completa"
    assert item["ficha_completa"] is True

    ficha = cliente.get(f"/reservas/{id_reserva}/ficha")
    assert ficha.status_code == 200
    corpo = ficha.json()
    assert corpo["data_nascimento"] == "1990-05-12"
    assert "idade" not in corpo

    with ambiente.conexao() as conexao:
        saidas = conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        coletas = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'enviar_coleta'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert saidas == 1
    assert coletas == 1


@pytest.mark.postgres
def test_parcial_nao_cobra_campos(cenario):
    cliente, ambiente, id_reserva = cenario
    _post_webhook(
        cliente,
        {
            "id_externo": "evt-parcial",
            "telefone_origem": "11987654321",
            "texto": "parcial",
            "tem_texto_utilizavel": True,
        },
    )
    llm = LLMFalso()
    llm.configurar(
        ResultadoExtracao(
            desfecho="parcial",
            campos={"nome_completo": "Maria Silva", "cidade": "Sao Paulo"},
            campos_reconhecidos=("nome_completo", "cidade"),
        )
    )
    processar_uma_passagem_na_engine(
        ambiente.engine, gateway=MensageriaFalsa(), llm=llm
    )
    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["status"] == "ficha_parcial"
    assert item["estado_cadastro"] == "parcial"
    assert item["ficha_completa"] is False

    with ambiente.conexao() as conexao:
        assert (
            conexao.execute(
                text(
                    "SELECT COUNT(*) FROM trabalho WHERE tipo = 'enviar_coleta'"
                    " AND (payload->>'id_reserva')::bigint = :r"
                ),
                {"r": id_reserva},
            ).scalar_one()
            == 1
        )


@pytest.mark.postgres
def test_irreconhecivel_sinaliza_leitura_humana(cenario):
    cliente, ambiente, id_reserva = cenario
    _post_webhook(
        cliente,
        {
            "id_externo": "evt-irr",
            "telefone_origem": "11987654321",
            "texto": "asdf qwer",
            "tem_texto_utilizavel": True,
        },
    )
    llm = LLMFalso()
    llm.configurar(ResultadoExtracao(desfecho="irreconhecivel"))
    processar_uma_passagem_na_engine(
        ambiente.engine, gateway=MensageriaFalsa(), llm=llm
    )
    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["status"] == "aguardando_cadastro"
    assert item["estado_cadastro"] == "leitura_humana"

    with ambiente.conexao() as conexao:
        conteudo = conexao.execute(
            text(
                "SELECT conteudo FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert conteudo == "asdf qwer"


@pytest.mark.postgres
def test_falha_extrator_esgota_em_leitura_humana(cenario):
    cliente, ambiente, id_reserva = cenario
    hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE parametro_hotel SET valor = '1'"
                " WHERE id_hotel = :h AND chave = 'tentativas_max_envio_mensagem'"
            ),
            {"h": hotel},
        )
    _post_webhook(
        cliente,
        {
            "id_externo": "evt-falha",
            "telefone_origem": "11987654321",
            "texto": "texto",
            "tem_texto_utilizavel": True,
        },
    )
    llm = LLMFalso()
    llm.falhar_sempre = True
    processar_uma_passagem_na_engine(
        ambiente.engine, gateway=MensageriaFalsa(), llm=llm
    )
    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["estado_cadastro"] == "leitura_humana"
    with ambiente.conexao() as conexao:
        desfecho = conexao.execute(
            text(
                "SELECT classificacao_bruta->>'desfecho' FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        assert desfecho == "falha_extrator"


@pytest.mark.postgres
def test_operacional_nao_le_ficha(cenario):
    cliente, ambiente, id_reserva = cenario
    cliente.post("/sair")
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get(f"/reservas/{id_reserva}/ficha").status_code == 403


@pytest.mark.postgres
def test_midia_sem_texto_nao_inventa_ficha(cenario):
    cliente, ambiente, id_reserva = cenario
    resposta = _post_webhook(
        cliente,
        {
            "id_externo": "evt-midia",
            "telefone_origem": "11987654321",
            "texto": "",
            "tem_texto_utilizavel": False,
        },
    )
    assert resposta.json()["status"] == "sem_texto"
    with ambiente.conexao() as conexao:
        assert (
            conexao.execute(
                text(
                    "SELECT COUNT(*) FROM mensagem"
                    " WHERE id_reserva = :r AND direcao = 'recebida'"
                ),
                {"r": id_reserva},
            ).scalar_one()
            == 0
        )
