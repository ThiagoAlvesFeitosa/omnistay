"""Simulador de conversa: GET/POST autenticados, modo e isolamento."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_simulada import MensageriaSimulada
from app.modulos.atendimento.service import abrir_reclamacao
from app.portas.llm import ResultadoResposta
from testes.integracao.test_confirmar_chegada import _criar_elegivel
from testes.integracao.test_controlar_silencio import (
    _checkin_longe,
    _criar_com_coleta_enviada,
    _envelhecer_coleta,
)
from testes.integracao.test_lista_pedidos_chat import _semear_consumo
from testes.integracao.test_reservas import _corpo_valido, _login
from testes.integracao.test_webhook_estadia import _criar_hospedada
from testes.suporte.pedido_servico import TEXTO_COM_QUARTO, resultado_pedido_servico
from testes.suporte.pedidos_chat import ROTULO
from testes.suporte.pulso import montar_hospedado_para_pulso
from testes.suporte.simulador import id_externo_sim, modo_demonstracao, modo_real
from worker.agendador import verificar_cadastros_pendentes, verificar_pulsos_pendentes
from worker.consumidor import processar_uma_passagem_na_engine


def _modo(monkeypatch, qual: str) -> None:
    if qual == "real":
        modo_real(monkeypatch)
    else:
        modo_demonstracao(monkeypatch)


def _login_recepcao(cliente, ambiente):
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])


def _post_turno(cliente, id_reserva: int, texto: str, sufixo: str):
    return cliente.post(
        f"/simulador/conversas/{id_reserva}/mensagens",
        json={"texto": texto, "id_externo": id_externo_sim(sufixo)},
    )


def _fio(cliente, id_reserva: int) -> dict:
    resposta = cliente.get(f"/simulador/conversas/{id_reserva}")
    assert resposta.status_code == 200
    return resposta.json()


def _conteudos(fio: dict) -> str:
    return "\n".join(m["conteudo"] for m in fio["mensagens"])


def _contar(ambiente, sql: str, **params):
    with ambiente.conexao() as conexao:
        return conexao.execute(text(sql), params).scalar_one()


def _semear_cafe(ambiente) -> None:
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO catalogo_item (id_hotel, categoria, titulo, conteudo) "
                "VALUES (:h, 'horario', 'Cafe da manha', '7h as 10h')"
            ),
            {"h": ambiente.propriedade_a.id_hotel},
        )


def _passar(ambiente, llm=None) -> int:
    return processar_uma_passagem_na_engine(
        ambiente.engine, gateway=MensageriaSimulada(), llm=llm
    )


@pytest.mark.postgres
def test_get_conversas_sem_cookie_responde_401(app_sobre_ambiente, monkeypatch):
    cliente, _ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    assert cliente.get("/simulador/conversas").status_code == 401


@pytest.mark.postgres
def test_staff_recebe_403_na_lista(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/simulador/conversas").status_code == 403


@pytest.mark.postgres
def test_recepcao_em_modo_real_recebe_409(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "real")
    _login_recepcao(cliente, ambiente)
    resposta = cliente.get("/simulador/conversas")
    assert resposta.status_code == 409
    assert resposta.json()["detail"]["codigo"] == "modo_real"


@pytest.mark.postgres
def test_lista_vazia_e_200_em_demonstracao(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    _login_recepcao(cliente, ambiente)
    resposta = cliente.get("/simulador/conversas")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["modo"] == "demonstracao"
    assert corpo["conversas"] == []


@pytest.mark.postgres
def test_coleta_enviada_aparece_no_fio(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    _login_recepcao(cliente, ambiente)
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    _passar(ambiente)
    fio = _fio(cliente, id_reserva)
    enviadas = [m for m in fio["mensagens"] if m["direcao"] == "enviada"]
    assert enviadas[0]["status_envio"] == "enviada"
    assert "Ola, Maria" in enviadas[0]["conteudo"]


@pytest.mark.postgres
def test_boas_vindas_enviadas_aparecem_no_fio(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_elegivel(cliente, ambiente)
    assert cliente.post(f"/reservas/{id_reserva}/chegada").status_code == 200
    _passar(ambiente)
    assert "chegada esta confirmada" in _conteudos(_fio(cliente, id_reserva))


@pytest.mark.postgres
def test_lembrete_enviado_aparece_no_fio(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_com_coleta_enviada(cliente, ambiente, **_checkin_longe())
    _envelhecer_coleta(ambiente.engine, id_reserva)
    with ambiente.engine.begin() as conexao:
        verificar_cadastros_pendentes(conexao)
    _passar(ambiente)
    assert "cadastro antecipado" in _conteudos(_fio(cliente, id_reserva))


@pytest.mark.postgres
def test_pulso_enviado_aparece_no_fio(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=ambiente.propriedade_a.id_hotel, telefone="5511910000601"
        )
        verificar_pulsos_pendentes(conexao)
    _passar(ambiente)
    _login_recepcao(cliente, ambiente)
    assert "Como esta sendo sua estadia" in _conteudos(_fio(cliente, id_reserva))


@pytest.mark.postgres
def test_pesquisa_de_saida_enviada_aparece_no_fio(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656001")
    assert cliente.post(f"/reservas/{id_reserva}/saida").status_code == 200
    _passar(ambiente)
    assert "Sua estadia encerrou" in _conteudos(_fio(cliente, id_reserva))


@pytest.mark.postgres
def test_lista_de_pedidos_enviada_aparece_no_fio(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656002")
    _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    _login_recepcao(cliente, ambiente)
    assert cliente.post(f"/reservas/{id_reserva}/saida").status_code == 200
    _passar(ambiente)
    assert ROTULO in _conteudos(_fio(cliente, id_reserva)).casefold()


@pytest.mark.postgres
def test_post_sem_cookie_responde_401(app_sobre_ambiente, monkeypatch):
    cliente, _ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    assert _post_turno(cliente, 1, "oi", "s-401").status_code == 401


@pytest.mark.postgres
def test_staff_recebe_403_no_post(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert _post_turno(cliente, 1, "oi", "s-403").status_code == 403


@pytest.mark.postgres
def test_post_em_modo_real_responde_409(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "real")
    _login_recepcao(cliente, ambiente)
    resposta = _post_turno(cliente, 1, "oi", "s-409")
    assert resposta.status_code == 409
    assert resposta.json()["detail"]["codigo"] == "modo_real"


@pytest.mark.postgres
def test_texto_vazio_responde_400(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    _login_recepcao(cliente, ambiente)
    resposta = cliente.post(
        "/simulador/conversas/1/mensagens",
        json={"texto": "", "id_externo": id_externo_sim("vazio")},
    )
    assert resposta.status_code == 400
    assert resposta.json()["detail"]["codigo"] == "texto_vazio"


@pytest.mark.postgres
def test_id_externo_ausente_responde_400(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    _login_recepcao(cliente, ambiente)
    resposta = cliente.post(
        "/simulador/conversas/1/mensagens",
        json={"texto": "oi"},
    )
    assert resposta.status_code == 400
    assert resposta.json()["detail"]["codigo"] == "id_externo_ausente"


@pytest.mark.postgres
def test_reserva_de_outro_hotel_no_post_responde_404(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_a = _criar_hospedada(cliente, ambiente, telefone="11987656003")
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    assert _post_turno(cliente, id_a, "oi", "hotel-b").status_code == 404


@pytest.mark.postgres
def test_duvida_coberta_aparece_no_fio_depois_do_worker(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656004")
    _semear_cafe(ambiente)
    criada = _post_turno(cliente, id_reserva, "que horas e o cafe", "duvida")
    assert criada.status_code == 201
    _passar(ambiente)
    assert "7h as 10h" in _conteudos(_fio(cliente, id_reserva))


@pytest.mark.postgres
def test_pedido_confirma_no_fio_e_chamado_so_depois_do_worker(
    app_sobre_ambiente, monkeypatch
):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656005")
    assert _post_turno(cliente, id_reserva, TEXTO_COM_QUARTO, "pedido").status_code == 201
    assert (
        _contar(
            ambiente,
            "SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r",
            r=id_reserva,
        )
        == 0
    )
    llm = LLMFalso()
    llm.configurar_classificacao(resultado_pedido_servico())
    _passar(ambiente, llm=llm)
    assert "equipe ja foi avisada" in _conteudos(_fio(cliente, id_reserva)).casefold()
    assert (
        _contar(
            ambiente,
            "SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r",
            r=id_reserva,
        )
        == 1
    )


@pytest.mark.postgres
def test_ficha_enfileira_interpretar_e_duplicata_nao_repete_mensagem(
    app_sobre_ambiente, monkeypatch
):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    _login_recepcao(cliente, ambiente)
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    primeira = _post_turno(cliente, id_reserva, "ficha completa", "ficha")
    segunda = _post_turno(cliente, id_reserva, "ficha completa", "ficha")
    assert primeira.status_code == 201
    assert segunda.status_code == 200
    tipos = _contar(
        ambiente,
        "SELECT COUNT(*) FROM trabalho"
        " WHERE tipo = 'interpretar_ficha'"
        " AND (payload->>'id_reserva')::bigint = :r",
        r=id_reserva,
    )
    classificar = _contar(
        ambiente,
        "SELECT COUNT(*) FROM trabalho"
        " WHERE tipo = 'classificar_mensagem'"
        " AND (payload->>'id_reserva')::bigint = :r",
        r=id_reserva,
    )
    recebidas = _contar(
        ambiente,
        "SELECT COUNT(*) FROM mensagem"
        " WHERE id_reserva = :r AND direcao = 'recebida'",
        r=id_reserva,
    )
    assert tipos == 1
    assert classificar == 0
    assert recebidas == 1


@pytest.mark.postgres
def test_pergunta_fora_do_catalogo_nao_inventa_resposta(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656006")
    _semear_cafe(ambiente)
    assert _post_turno(cliente, id_reserva, "qual o cardapio", "fora").status_code == 201
    llm = LLMFalso()
    llm.configurar_resposta(ResultadoResposta(coberta=False))
    _passar(ambiente, llm=llm)
    texto = _conteudos(_fio(cliente, id_reserva))
    assert "7h as 10h" not in texto
    assert "recepcao" in texto.casefold()
    _login_recepcao(cliente, ambiente)
    itens = cliente.get("/fila-do-dia").json()["itens"]
    item = next(i for i in itens if i["id_reserva"] == id_reserva)
    assert item["precisa_atendimento_humano"] is True


@pytest.mark.postgres
def test_pulso_e_suprimido_quando_ha_reclamacao_aberta(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=ambiente.propriedade_a.id_hotel, telefone="5511910000602"
        )
        id_msg = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'ar quebrado') RETURNING id_mensagem"
            ),
            {"r": id_reserva},
        ).scalar_one()
        abrir_reclamacao(
            conexao,
            id_hotel=ambiente.propriedade_a.id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_msg,
            descricao="ar quebrado",
            numero_quarto="101",
            urgencia="media",
            janela_preferencia=None,
        )
        verificar_pulsos_pendentes(conexao)
    _login_recepcao(cliente, ambiente)
    assert "Como esta sendo sua estadia" not in _conteudos(_fio(cliente, id_reserva))
    assert (
        _contar(
            ambiente,
            "SELECT COUNT(*) FROM trabalho"
            " WHERE tipo = 'enviar_pulso'"
            " AND (payload->>'id_reserva')::bigint = :r",
            r=id_reserva,
        )
        == 0
    )


@pytest.mark.postgres
def test_tres_metodos_em_modo_real_nao_gravam_mensagem(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987656007")
    antes = _contar(ambiente, "SELECT COUNT(*) FROM mensagem")
    _modo(monkeypatch, "real")
    _login_recepcao(cliente, ambiente)
    assert cliente.get("/simulador/conversas").status_code == 409
    assert cliente.get(f"/simulador/conversas/{id_reserva}").status_code == 409
    assert _post_turno(cliente, id_reserva, "oi", "real-post").status_code == 409
    depois = _contar(ambiente, "SELECT COUNT(*) FROM mensagem")
    assert depois == antes


@pytest.mark.postgres
def test_hotel_b_nao_ve_conversa_de_a(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    _modo(monkeypatch, "demonstracao")
    id_a = _criar_hospedada(cliente, ambiente, telefone="11987656008")
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    lista = cliente.get("/simulador/conversas")
    assert lista.status_code == 200
    ids = [c["id_reserva"] for c in lista.json()["conversas"]]
    assert id_a not in ids
    assert cliente.get(f"/simulador/conversas/{id_a}").status_code == 404
    assert _post_turno(cliente, id_a, "oi", "vazou").status_code == 404
