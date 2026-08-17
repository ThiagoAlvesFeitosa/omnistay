"""Classificacao de intencao da estadia."""

import pytest
from sqlalchemy import text

from app.adaptadores.llm_falso import LLMFalso
from app.modulos.conversa import repository as conversa_repo
from app.modulos.conversa import service as conversa
from app.modulos.conversa.classificacao import validar_classificacao
from app.portas.llm import ResultadoClassificacao
from testes.suporte.classificacao import eixos_validos


def test_validar_aceita_taxonomia_fechada():
    eixos = eixos_validos(intencao="pedido_de_servico", sentimento="positivo", urgencia="media")
    valida = validar_classificacao(ResultadoClassificacao(**eixos, bruto={}))
    assert valida is not None
    assert valida.intencao == "pedido_de_servico"


def test_validar_rejeita_eixo_faltando():
    assert (
        validar_classificacao(
            ResultadoClassificacao(
                intencao="duvida_geral", sentimento="neutro", urgencia=None, bruto={}
            )
        )
        is None
    )


def test_validar_rejeita_valor_fora_da_lista():
    assert (
        validar_classificacao(
            ResultadoClassificacao(
                intencao="nao_existe",
                sentimento="neutro",
                urgencia="baixa",
                bruto={"intencao": "nao_existe"},
            )
        )
        is None
    )


class RepoClassificar:
    def __init__(self, conteudo="que horas e o cafe", classificacao=None):
        self.conteudo = conteudo
        self.classificacao = classificacao
        self.eixos = {}
        self.chamadas_gravar = 0

    def ler_mensagem(self, conexao, *, id_mensagem):
        return {
            "id_mensagem": id_mensagem,
            "id_reserva": 1,
            "conteudo": self.conteudo,
            "classificacao_bruta": self.classificacao,
        }

    def gravar_classificacao_intencao(
        self,
        conexao,
        *,
        id_hotel,
        id_mensagem,
        intencao,
        sentimento,
        urgencia,
        classificacao,
    ):
        self.chamadas_gravar += 1
        self.eixos = {
            "intencao": intencao,
            "sentimento": sentimento,
            "urgencia": urgencia,
        }
        self.classificacao = classificacao


def _trabalho():
    return {
        "id_trabalho": 5,
        "id_hotel": 1,
        "payload": {"id_reserva": 1, "id_mensagem": 8, "id_evento": 3},
        "tentativas": 0,
    }


def _processar(monkeypatch, repo, llm, enfileirados=None):
    concluidos = []
    if enfileirados is None:
        enfileirados = []

    def marcar_concluido(conexao, *, id_trabalho):
        concluidos.append(id_trabalho)

    def enfileirar(conexao, *, id_hotel, id_reserva, id_mensagem):
        enfileirados.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "id_mensagem": id_mensagem,
            }
        )
        return 99

    monkeypatch.setattr("app.fila.repository.marcar_concluido", marcar_concluido)
    conversa.processar_trabalho_classificar_mensagem(
        object(),
        trabalho=_trabalho(),
        llm=llm,
        repositorio=repo,
        enfileirar_resposta=enfileirar,
    )
    return concluidos, enfileirados


def test_classificacao_valida_grava_eixos_e_conclui(monkeypatch):
    repo = RepoClassificar()
    llm = LLMFalso()
    concluidos, _ = _processar(monkeypatch, repo, llm)
    assert repo.eixos["intencao"] == "duvida_geral"
    assert repo.classificacao["desfecho"] == "classificado"
    assert repo.classificacao["bruto"]["intencao"] == "duvida_geral"
    assert repo.conteudo == "que horas e o cafe"
    assert concluidos == [5]


def test_duvida_geral_enfileira_responder_sem_catalogo_nem_gateway(monkeypatch):
    repo = RepoClassificar()
    llm = LLMFalso()
    _, enfileirados = _processar(monkeypatch, repo, llm)
    assert enfileirados == [
        {"id_hotel": 1, "id_reserva": 1, "id_mensagem": 8}
    ]
    assert llm.chamadas_responder == []


def test_pedido_e_reclamacao_nao_enfileiram_responder(monkeypatch):
    repo = RepoClassificar(conteudo="toalha extra")
    llm = LLMFalso()
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="pedido_de_servico",
            sentimento="neutro",
            urgencia="baixa",
            bruto={},
        )
    )
    _, enfileirados = _processar(monkeypatch, repo, llm)
    assert enfileirados == []


def test_indisponivel_encaminha_sem_eixos_e_conclui(monkeypatch):
    repo = RepoClassificar()
    llm = LLMFalso()
    llm.falhar_classificacao = True
    concluidos, enfileirados = _processar(monkeypatch, repo, llm)
    assert repo.eixos["intencao"] is None
    assert repo.classificacao["desfecho"] == "indisponivel"
    assert "bruto" not in repo.classificacao
    assert concluidos == [5]
    assert enfileirados == []


def test_formato_invalido_preserva_bruto(monkeypatch):
    repo = RepoClassificar()
    llm = LLMFalso()
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="nao_existe",
            sentimento="neutro",
            urgencia="baixa",
            bruto={"cru": "lixo"},
        )
    )
    _, enfileirados = _processar(monkeypatch, repo, llm)
    assert repo.eixos["intencao"] is None
    assert repo.classificacao["desfecho"] == "formato_invalido"
    assert repo.classificacao["bruto"] == {"cru": "lixo"}
    assert enfileirados == []


def test_reclamacao_nao_abre_chamado(monkeypatch):
    repo = RepoClassificar(conteudo="ar nao gela")
    llm = LLMFalso()
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="reclamacao_tecnica",
            sentimento="negativo",
            urgencia="alta",
            bruto={},
        )
    )
    _, enfileirados = _processar(monkeypatch, repo, llm)
    assert repo.classificacao["desfecho"] == "classificado"
    assert not hasattr(repo, "solicitacao")
    assert enfileirados == []


def test_upsell_encaminha_humano(monkeypatch):
    repo = RepoClassificar()
    llm = LLMFalso()
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="upsell",
            sentimento="positivo",
            urgencia="baixa",
            bruto={"intencao": "upsell"},
        )
    )
    _, enfileirados = _processar(monkeypatch, repo, llm)
    assert repo.eixos["intencao"] == "upsell"
    assert repo.classificacao["desfecho"] == "encaminhado_humano"
    assert enfileirados == []


def test_ja_classificada_nao_chama_llm(monkeypatch):
    repo = RepoClassificar(
        classificacao={"tipo": "classificacao_intencao", "desfecho": "classificado"}
    )
    llm = LLMFalso()
    _processar(monkeypatch, repo, llm)
    assert llm.chamadas_classificar == []
    assert repo.chamadas_gravar == 0


def test_ja_classificada_duvida_sem_resposta_enfileira(monkeypatch):
    repo = RepoClassificar(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "duvida_geral",
        }
    )
    llm = LLMFalso()
    _, enfileirados = _processar(monkeypatch, repo, llm)
    assert llm.chamadas_classificar == []
    assert enfileirados == [
        {"id_hotel": 1, "id_reserva": 1, "id_mensagem": 8}
    ]


@pytest.mark.postgres
def test_gravar_nao_altera_conteudo_nem_vaza_hotel(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    outro = ambiente.propriedade_b.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511911111111', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'texto original') RETURNING id_mensagem"
            ),
            {"r": id_reserva},
        ).scalar_one()
        afetadas = conversa_repo.gravar_classificacao_intencao(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            intencao="duvida_geral",
            sentimento="neutro",
            urgencia="baixa",
            classificacao={
                "tipo": "classificacao_intencao",
                "desfecho": "classificado",
            },
        )
        assert afetadas == 1
        linha = conexao.execute(
            text(
                "SELECT conteudo, intencao FROM mensagem WHERE id_mensagem = :id"
            ),
            {"id": id_mensagem},
        ).mappings().one()
        assert linha["conteudo"] == "texto original"
        assert linha["intencao"] == "duvida_geral"
        zero = conversa_repo.gravar_classificacao_intencao(
            conexao,
            id_hotel=outro,
            id_mensagem=id_mensagem,
            intencao="upsell",
            sentimento="neutro",
            urgencia="baixa",
            classificacao={
                "tipo": "classificacao_intencao",
                "desfecho": "encaminhado_humano",
            },
        )
        assert zero == 0
        intencao = conexao.execute(
            text("SELECT intencao FROM mensagem WHERE id_mensagem = :id"),
            {"id": id_mensagem},
        ).scalar_one()
        assert intencao == "duvida_geral"
