"""POST /solicitacoes/{id}/resolucao — fecha o chamado e agenda o recado."""

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.conversa.texto_confirmacao_resolucao import (
    montar_confirmacao_resolucao,
)
from testes.integracao.test_reservas import _login
from testes.integracao.test_solicitacoes import (
    CHAVES_CADASTRAIS,
    _semear_reclamacao,
    _semear_servico,
)
from testes.integracao.test_webhook_estadia import _criar_hospedada
from testes.suporte.resolucao import (
    DETALHE_JA_RESOLVIDA,
    DETALHE_NAO_ENCONTRADA,
    DETALHE_TIPO_CONSUMO,
)
from worker.consumidor import processar_uma_passagem_na_engine


def _ids_solicitacao(cliente) -> set[int]:
    return {i["id_solicitacao"] for i in cliente.get("/solicitacoes").json()["itens"]}


def _solicitacao(ambiente, id_solicitacao: int) -> dict:
    with ambiente.conexao() as conexao:
        return conexao.execute(
            text(
                "SELECT status, resolvida_em, id_usuario_responsavel, tipo"
                " FROM solicitacao WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).mappings().one()


def _trabalhos_resolucao(ambiente, id_solicitacao: int):
    with ambiente.conexao() as conexao:
        return conexao.execute(
            text(
                "SELECT status, payload FROM trabalho"
                " WHERE tipo = 'enviar_confirmacao_resolucao'"
                " AND (payload->>'id_solicitacao')::bigint = :id"
            ),
            {"id": id_solicitacao},
        ).mappings().all()


def _enviadas_resolucao(ambiente, id_reserva: int):
    with ambiente.conexao() as conexao:
        return conexao.execute(
            text(
                "SELECT status_envio, conteudo, classificacao_bruta"
                " FROM mensagem WHERE id_reserva = :r AND direcao = 'enviada'"
                " AND classificacao_bruta->>'tipo' = 'confirmacao_resolucao'"
            ),
            {"r": id_reserva},
        ).mappings().all()


def _status_reserva(ambiente, id_reserva: int) -> str:
    with ambiente.conexao() as conexao:
        return conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :id"),
            {"id": id_reserva},
        ).scalar_one()


@pytest.mark.postgres
def test_staff_resolve_reclamacao_e_item_sai_da_lista(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(
        cliente, ambiente, telefone="11987654101", nome="Maria Silva"
    )
    _semear_reclamacao(ambiente, id_reserva, "ar nao gela", "402", None)
    cliente.cookies.clear()
    staff = ambiente.propriedade_a.usuarios["staff"]
    _login(cliente, staff)
    id_sol = next(iter(_ids_solicitacao(cliente)))
    status_antes = _status_reserva(ambiente, id_reserva)

    resposta = cliente.post(f"/solicitacoes/{id_sol}/resolucao")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["id_solicitacao"] == id_sol
    assert corpo["tipo"] == "reclamacao"
    assert corpo["status"] == "resolvida"
    assert corpo["id_usuario_responsavel"] == staff.id_usuario
    assert corpo["resolvida_em"]
    assert corpo["confirmacao"] == "agendada"
    for chave in CHAVES_CADASTRAIS:
        assert chave not in corpo
    assert "descricao" not in corpo
    assert id_sol not in _ids_solicitacao(cliente)
    assert _status_reserva(ambiente, id_reserva) == status_antes
    trabalhos = _trabalhos_resolucao(ambiente, id_sol)
    assert len(trabalhos) == 1
    assert trabalhos[0]["status"] == "pendente"


@pytest.mark.postgres
def test_worker_entrega_recado_e_chamado_permanece_resolvido(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(
        cliente, ambiente, telefone="11987654102", nome="Maria Silva"
    )
    _semear_reclamacao(ambiente, id_reserva, "ar nao gela", None, None)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    id_sol = next(iter(_ids_solicitacao(cliente)))
    assert cliente.post(f"/solicitacoes/{id_sol}/resolucao").status_code == 200

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    recado = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="reclamacao"
    )
    envio = next(e for e in porta.envios if e["tipo"] == "sessao" and e["corpo"] == recado)
    assert envio["corpo"] == recado
    enviadas = _enviadas_resolucao(ambiente, id_reserva)
    assert len(enviadas) == 1
    assert enviadas[0]["status_envio"] == "enviada"
    assert enviadas[0]["conteudo"] == recado
    linha = _solicitacao(ambiente, id_sol)
    assert linha["status"] == "resolvida"
    assert _trabalhos_resolucao(ambiente, id_sol)[0]["status"] == "concluido"
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert id_sol not in _ids_solicitacao(cliente)


@pytest.mark.postgres
def test_segundo_post_devolve_409_sem_segunda_enviada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654103")
    _semear_servico(ambiente, id_reserva, "toalha extra", None)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    id_sol = next(iter(_ids_solicitacao(cliente)))
    primeira = cliente.post(f"/solicitacoes/{id_sol}/resolucao")
    assert primeira.status_code == 200
    antes = _solicitacao(ambiente, id_sol)
    segunda = cliente.post(f"/solicitacoes/{id_sol}/resolucao")
    assert segunda.status_code == 409
    assert segunda.json()["detail"] == DETALHE_JA_RESOLVIDA
    depois = _solicitacao(ambiente, id_sol)
    assert depois["id_usuario_responsavel"] == antes["id_usuario_responsavel"]
    assert depois["resolvida_em"] == antes["resolvida_em"]
    assert len(_enviadas_resolucao(ambiente, id_reserva)) == 1
    assert len(_trabalhos_resolucao(ambiente, id_sol)) == 1


@pytest.mark.postgres
def test_gestao_recebe_403_e_hotel_b_recebe_404(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654104")
    _semear_reclamacao(ambiente, id_reserva, "chuveiro vazou", None, None)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    id_sol = next(iter(_ids_solicitacao(cliente)))

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    recusa = cliente.post(f"/solicitacoes/{id_sol}/resolucao")
    assert recusa.status_code == 403
    assert _solicitacao(ambiente, id_sol)["status"] == "aberta"
    assert id_sol in _ids_solicitacao(cliente)

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["staff"])
    outro = cliente.post(f"/solicitacoes/{id_sol}/resolucao")
    assert outro.status_code == 404
    assert outro.json()["detail"] == DETALHE_NAO_ENCONTRADA
    assert _solicitacao(ambiente, id_sol)["status"] == "aberta"


@pytest.mark.postgres
def test_falha_ao_agendar_desfaz_e_envio_falho_nao_reabre(
    app_sobre_ambiente, monkeypatch
):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654105")
    _semear_servico(ambiente, id_reserva, "travesseiro extra", None)
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    id_sol = next(iter(_ids_solicitacao(cliente)))

    from app.modulos.conversa import service as conversa_modulo

    original = conversa_modulo.agendar_confirmacao_resolucao

    def abortar(*args, **kwargs):
        raise RuntimeError("falha ao agendar")

    monkeypatch.setattr(
        "app.modulos.atendimento.service.conversa_service.agendar_confirmacao_resolucao",
        abortar,
    )
    with pytest.raises(RuntimeError, match="falha ao agendar"):
        cliente.post(f"/solicitacoes/{id_sol}/resolucao")
    assert id_sol in _ids_solicitacao(cliente)
    assert _solicitacao(ambiente, id_sol)["status"] == "aberta"
    assert _enviadas_resolucao(ambiente, id_reserva) == []

    monkeypatch.setattr(
        "app.modulos.atendimento.service.conversa_service.agendar_confirmacao_resolucao",
        original,
    )
    assert cliente.post(f"/solicitacoes/{id_sol}/resolucao").status_code == 200
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    assert porta.envios == []
    assert _solicitacao(ambiente, id_sol)["status"] == "resolvida"
    assert id_sol not in _ids_solicitacao(cliente)
    assert _trabalhos_resolucao(ambiente, id_sol)[0]["status"] != "concluido"


@pytest.mark.postgres
def test_consumo_recusado_em_andamento_e_encerrado_aceitam(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_consumo = _criar_hospedada(cliente, ambiente, telefone="11987654106")
    id_andamento = _criar_hospedada(cliente, ambiente, telefone="11987654107")
    id_encerrado = _criar_hospedada(cliente, ambiente, telefone="11987654108")
    _semear_servico(ambiente, id_encerrado, "toalha extra", None)

    with ambiente.engine.begin() as conexao:
        id_sol_consumo = conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, tipo, descricao, status)"
                " VALUES (:r, 'consumo', 'frigobar', 'aberta')"
                " RETURNING id_solicitacao"
            ),
            {"r": id_consumo},
        ).scalar_one()
        id_msg = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo)"
                " VALUES (:r, 'recebida', 'ar nao gela') RETURNING id_mensagem"
            ),
            {"r": id_andamento},
        ).scalar_one()
        id_sol_andamento = conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, id_mensagem_origem, tipo,"
                " descricao, status)"
                " VALUES (:r, :m, 'reclamacao', 'ar nao gela', 'em_andamento')"
                " RETURNING id_solicitacao"
            ),
            {"r": id_andamento, "m": id_msg},
        ).scalar_one()
        id_sol_encerrado = conexao.execute(
            text(
                "SELECT id_solicitacao FROM solicitacao WHERE id_reserva = :r"
            ),
            {"r": id_encerrado},
        ).scalar_one()
        conexao.execute(
            text("UPDATE reserva SET status = 'encerrado' WHERE id_reserva = :r"),
            {"r": id_encerrado},
        )

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    consumo = cliente.post(f"/solicitacoes/{id_sol_consumo}/resolucao")
    assert consumo.status_code == 409
    assert consumo.json()["detail"] == DETALHE_TIPO_CONSUMO

    andamento = cliente.post(f"/solicitacoes/{id_sol_andamento}/resolucao")
    assert andamento.status_code == 200
    assert andamento.json()["status"] == "resolvida"

    encerrado = cliente.post(f"/solicitacoes/{id_sol_encerrado}/resolucao")
    assert encerrado.status_code == 200
    assert encerrado.json()["status"] == "resolvida"
