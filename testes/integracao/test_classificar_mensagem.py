"""Worker classifica mensagem de estadia e sinaliza a fila."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.llm import ResultadoClassificacao
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import SEGREDO, _criar_hospedada
from testes.suporte.webhook import postar_webhook
from worker.consumidor import processar_uma_passagem


@pytest.fixture
def cenario(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "token-teste")
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    yield cliente, ambiente
    obter_configuracao.cache_clear()


def _postar(cliente, id_externo: str, texto: str, telefone="11987654321"):
    return postar_webhook(
        cliente,
        {
            "id_externo": id_externo,
            "telefone_origem": telefone,
            "texto": texto,
            "tem_texto_utilizavel": True,
        },
        segredo=SEGREDO,
    )


def _item_fila(cliente, id_reserva: int) -> dict:
    itens = cliente.get("/fila-do-dia").json()["itens"]
    return next(i for i in itens if i["id_reserva"] == id_reserva)


@pytest.mark.postgres
def test_classificacao_valida_nao_liga_sinal_nem_altera_conteudo(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente)
    _postar(cliente, "evt-cls-1", "que horas e o cafe")
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO catalogo_item (id_hotel, categoria, titulo, conteudo) "
                "VALUES (:h, 'horario', 'Cafe da manha', '7h as 10h')"
            ),
            {"h": ambiente.propriedade_a.id_hotel},
        )
        antes = conexao.execute(
            text(
                "SELECT conteudo FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        depois = conexao.execute(
            text(
                "SELECT conteudo, intencao, classificacao_bruta"
                " FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).mappings().one()
        enviada = conexao.execute(
            text(
                "SELECT conteudo FROM mensagem WHERE id_mensagem = :id"
            ),
            {"id": depois["classificacao_bruta"]["id_mensagem_resposta"]},
        ).scalar_one()
        solicitacoes = conexao.execute(text("SELECT COUNT(*) FROM solicitacao")).scalar_one()
    assert antes == depois["conteudo"] == "que horas e o cafe"
    assert depois["intencao"] == "duvida_geral"
    assert depois["classificacao_bruta"]["resposta"] == "automatica"
    assert "7h as 10h" in enviada
    assert solicitacoes == 0
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is False


@pytest.mark.postgres
def test_indisponivel_liga_sinal_na_fila(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987650002")
    _postar(cliente, "evt-cls-indisp", "preciso de ajuda", telefone="11987650002")
    llm = LLMFalso()
    llm.falhar_classificacao = True
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        eixos = conexao.execute(
            text(
                "SELECT intencao, classificacao_bruta FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).mappings().one()
    assert eixos["intencao"] is None
    assert eixos["classificacao_bruta"]["desfecho"] == "indisponivel"
    assert "resposta" not in eixos["classificacao_bruta"]
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True
    for perfil in ("staff", "gestor"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        assert cliente.get("/fila-do-dia").status_code == 403


@pytest.mark.postgres
def test_formato_invalido_preserva_bruto_e_sinal(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987650003")
    _postar(cliente, "evt-cls-inv", "texto solto", telefone="11987650003")
    llm = LLMFalso()
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="nao_existe",
            sentimento="neutro",
            urgencia="baixa",
            bruto={"cru": "xyz"},
        )
    )
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        bruto = conexao.execute(
            text(
                "SELECT classificacao_bruta FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert bruto["desfecho"] == "formato_invalido"
    assert bruto["bruto"] == {"cru": "xyz"}
    assert "resposta" not in bruto
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True


@pytest.mark.postgres
def test_upsell_liga_sinal_reclamacao_nao_cria_solicitacao(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987650004")
    _postar(cliente, "evt-cls-up", "tem spa", telefone="11987650004")
    llm = LLMFalso()
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="upsell",
            sentimento="positivo",
            urgencia="baixa",
            bruto={},
        )
    )
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        status = conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        bruto = conexao.execute(
            text(
                "SELECT classificacao_bruta FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        solicitacoes = conexao.execute(text("SELECT COUNT(*) FROM solicitacao")).scalar_one()
    assert status == "hospedado"
    assert solicitacoes == 0
    assert "resposta" not in bruto
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True


@pytest.mark.postgres
def test_classificacao_nao_vaza_entre_hoteis(cenario):
    cliente, ambiente = cenario
    id_a = _criar_hospedada(cliente, ambiente, telefone="11987650005")
    _postar(cliente, "evt-cls-a", "ajuda", telefone="11987650005")
    llm = LLMFalso()
    llm.falhar_classificacao = True
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    ids_b = [i["id_reserva"] for i in cliente.get("/fila-do-dia").json()["itens"]]
    assert id_a not in ids_b
