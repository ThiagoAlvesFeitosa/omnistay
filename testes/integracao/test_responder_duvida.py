"""Worker responde duvida geral a partir do catalogo da propriedade."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.llm import ResultadoResposta
from testes.integracao.test_reservas import _corpo_valido, _login
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


def _semear_item(conexao, id_hotel: int, *, titulo="Cafe da manha", conteudo="7h as 10h"):
    return conexao.execute(
        text(
            "INSERT INTO catalogo_item (id_hotel, categoria, titulo, conteudo) "
            "VALUES (:h, 'horario', :t, :c) RETURNING id_catalogo_item"
        ),
        {"h": id_hotel, "t": titulo, "c": conteudo},
    ).scalar_one()


def _recebida(conexao, id_reserva: int):
    return conexao.execute(
        text(
            "SELECT id_mensagem, conteudo, classificacao_bruta"
            " FROM mensagem"
            " WHERE id_reserva = :r AND direcao = 'recebida'"
        ),
        {"r": id_reserva},
    ).mappings().one()


def _corpo_enviada(conexao, id_mensagem: int) -> str:
    return conexao.execute(
        text("SELECT conteudo FROM mensagem WHERE id_mensagem = :id"),
        {"id": id_mensagem},
    ).scalar_one()


@pytest.mark.postgres
def test_nao_coberta_avisa_e_abre_chamado_na_fila(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651001")
    _postar(cliente, "evt-rd-nc", "que horas e o cafe", telefone="11987651001")
    llm = LLMFalso()
    llm.configurar_resposta(ResultadoResposta(coberta=False))
    with ambiente.engine.begin() as conexao:
        _semear_item(
            conexao,
            ambiente.propriedade_a.id_hotel,
            titulo="Estacionamento",
            conteudo="pago na saida",
        )
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        recebida = _recebida(conexao, id_reserva)
        enviada = _corpo_enviada(
            conexao, recebida["classificacao_bruta"]["id_mensagem_resposta"]
        )
        solicitacoes = conexao.execute(text("SELECT COUNT(*) FROM solicitacao")).scalar_one()
    assert recebida["classificacao_bruta"]["desfecho"] == "duvida_nao_coberta"
    assert recebida["classificacao_bruta"]["resposta"] == "aviso"
    assert "recepcao" in enviada.casefold()
    assert "7h" not in enviada
    assert "cardapio" not in enviada.casefold()
    assert solicitacoes == 0
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True


@pytest.mark.postgres
def test_redacao_infiel_nao_chega_ao_hospede(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651002")
    _postar(cliente, "evt-rd-infiel", "que horas e o cafe", telefone="11987651002")
    llm = LLMFalso()
    llm.configurar_resposta(
        ResultadoResposta(
            coberta=True,
            texto="piscina olimpica 6h",
            trechos_citados=("piscina olimpica 6h",),
        )
    )
    with ambiente.engine.begin() as conexao:
        _semear_item(conexao, ambiente.propriedade_a.id_hotel)
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        recebida = _recebida(conexao, id_reserva)
        enviada = _corpo_enviada(
            conexao, recebida["classificacao_bruta"]["id_mensagem_resposta"]
        )
    assert "piscina" not in enviada.casefold()
    assert "recepcao" in enviada.casefold()
    assert recebida["classificacao_bruta"]["desfecho"] == "duvida_nao_coberta"
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True


@pytest.mark.postgres
def test_fato_do_hotel_a_nao_responde_o_hotel_b(cenario):
    cliente, ambiente = cenario
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    id_b = cliente.post(
        "/reservas",
        json=_corpo_valido(telefone="11987651003", nome="Beta Silva"),
    ).json()["id_reserva"]
    from testes.integracao.test_confirmar_chegada import _tornar

    _tornar(ambiente, id_b, "ficha_recebida")
    _tornar(ambiente, id_b, "hospedado")
    with ambiente.engine.begin() as conexao:
        _semear_item(conexao, ambiente.propriedade_a.id_hotel)
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
                " intencao, sentimento, urgencia, classificacao_bruta) "
                "VALUES (:r, 'recebida', 'que horas e o cafe', 'duvida_geral',"
                " 'neutro', 'baixa', CAST(:c AS jsonb)) RETURNING id_mensagem"
            ),
            {
                "r": id_b,
                "c": (
                    '{"tipo": "classificacao_intencao",'
                    ' "desfecho": "classificado",'
                    ' "intencao": "duvida_geral"}'
                ),
            },
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'responder_duvida', CAST(:p AS jsonb), 'pendente')"
            ),
            {
                "h": ambiente.propriedade_b.id_hotel,
                "p": '{"id_reserva": %s, "id_mensagem": %s}' % (id_b, id_mensagem),
            },
        )
        enviadas_a_antes = conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem m"
                " JOIN reserva r ON r.id_reserva = m.id_reserva"
                " WHERE r.id_hotel = :h AND m.direcao = 'enviada'"
            ),
            {"h": ambiente.propriedade_a.id_hotel},
        ).scalar_one()
        processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        recebida = _recebida(conexao, id_b)
        enviada = _corpo_enviada(
            conexao, recebida["classificacao_bruta"]["id_mensagem_resposta"]
        )
        enviadas_a_depois = conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem m"
                " JOIN reserva r ON r.id_reserva = m.id_reserva"
                " WHERE r.id_hotel = :h AND m.direcao = 'enviada'"
            ),
            {"h": ambiente.propriedade_a.id_hotel},
        ).scalar_one()
    assert "7h as 10h" not in enviada
    assert recebida["classificacao_bruta"]["desfecho"] == "duvida_nao_coberta"
    assert enviadas_a_depois == enviadas_a_antes
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    assert _item_fila(cliente, id_b)["precisa_atendimento_humano"] is True
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    ids_a = [i["id_reserva"] for i in cliente.get("/fila-do-dia").json()["itens"]]
    assert id_b not in ids_a


@pytest.mark.postgres
def test_conversacao_indisponivel_sinal_permanece_na_fila(cenario):
    cliente, ambiente = cenario
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987651004")
    _postar(cliente, "evt-rd-llm", "que horas e o cafe", telefone="11987651004")
    llm = LLMFalso()
    llm.falhar_conversacao = True
    with ambiente.engine.begin() as conexao:
        _semear_item(conexao, ambiente.propriedade_a.id_hotel)
        processar_uma_passagem(conexao, gateway=MensageriaFalsa(), llm=llm)
        status = conexao.execute(
            text(
                "SELECT status FROM trabalho"
                " WHERE tipo = 'responder_duvida'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        recebida = _recebida(conexao, id_reserva)
    assert status == "concluido"
    assert recebida["classificacao_bruta"]["desfecho"] == "duvida_nao_coberta"
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_reserva)["precisa_atendimento_humano"] is True


@pytest.mark.postgres
def test_item_desativado_nao_cobre_e_reativado_cobre(cenario):
    cliente, ambiente = cenario
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_item = cliente.post(
        "/catalogo",
        json={
            "categoria": "horario",
            "titulo": "Cafe da manha",
            "conteudo": "7h as 10h",
        },
    ).json()["id_catalogo_item"]
    assert cliente.patch(f"/catalogo/{id_item}", json={"ativo": False}).status_code == 200

    id_inativo = _criar_hospedada(cliente, ambiente, telefone="11987651005")
    _postar(cliente, "evt-rd-off", "que horas e o cafe", telefone="11987651005")
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        aviso = _recebida(conexao, id_inativo)
        corpo_aviso = _corpo_enviada(
            conexao, aviso["classificacao_bruta"]["id_mensagem_resposta"]
        )
    assert aviso["classificacao_bruta"]["desfecho"] == "duvida_nao_coberta"
    assert "7h as 10h" not in corpo_aviso

    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert cliente.patch(f"/catalogo/{id_item}", json={"ativo": True}).status_code == 200
    id_ativo = _criar_hospedada(cliente, ambiente, telefone="11987651006")
    _postar(cliente, "evt-rd-on", "que horas e o cafe", telefone="11987651006")
    with ambiente.engine.begin() as conexao:
        processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        coberta = _recebida(conexao, id_ativo)
        corpo = _corpo_enviada(
            conexao, coberta["classificacao_bruta"]["id_mensagem_resposta"]
        )
    assert coberta["classificacao_bruta"]["resposta"] == "automatica"
    assert "7h as 10h" in corpo
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert _item_fila(cliente, id_ativo)["precisa_atendimento_humano"] is False
