"""Resposta automatica de duvida geral a partir do catalogo."""

import pytest
from sqlalchemy import text

from app.adaptadores.catalogo_falso import CatalogoFalso
from app.adaptadores.llm_falso import LLMFalso
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.conversa import repository as conversa_repo
from app.modulos.conversa import service as conversa
from app.portas.llm import ResultadoResposta
from testes.suporte.resposta_duvida import (
    item_cafe,
    resposta_coberta,
    resposta_nao_coberta,
)


class RepoResponder:
    def __init__(
        self,
        *,
        id_hotel=1,
        pergunta="que horas e o cafe",
        classificacao=None,
        enviadas=None,
    ):
        self.id_hotel = id_hotel
        self.eventos = []
        self.proximo_id = 20
        self.telefone = "5511999999999"
        self.nome = "Maria Silva"
        bruto = classificacao or {
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "duvida_geral",
        }
        self.mensagens = {
            8: {
                "id_mensagem": 8,
                "id_reserva": 1,
                "conteudo": pergunta,
                "classificacao_bruta": dict(bruto),
                "status_envio": None,
            }
        }
        if enviadas:
            self.mensagens.update(enviadas)

    def ler_mensagem(self, conexao, *, id_mensagem):
        achada = self.mensagens.get(id_mensagem)
        return dict(achada) if achada else None

    def inserir_mensagem_enviada_pendente(self, conexao, *, id_reserva, conteudo):
        self.eventos.append("gravar_enviada")
        novo = self.proximo_id
        self.proximo_id += 1
        self.mensagens[novo] = {
            "id_mensagem": novo,
            "id_reserva": id_reserva,
            "conteudo": conteudo,
            "classificacao_bruta": None,
            "status_envio": "pendente",
        }
        return novo

    def gravar_resposta_duvida(
        self,
        conexao,
        *,
        id_hotel,
        id_mensagem,
        resposta,
        id_mensagem_resposta,
        desfecho=None,
    ):
        if id_hotel != self.id_hotel:
            return 0
        self.eventos.append("gravar_json")
        atual = dict(self.mensagens[id_mensagem]["classificacao_bruta"] or {})
        atual["resposta"] = resposta
        atual["id_mensagem_resposta"] = id_mensagem_resposta
        if desfecho is not None:
            atual["desfecho"] = desfecho
        self.mensagens[id_mensagem]["classificacao_bruta"] = atual
        return 1

    def ler_nome_titular(self, conexao, *, id_reserva):
        return self.nome

    def ler_telefone_da_reserva(self, conexao, *, id_reserva):
        return self.telefone

    def atualizar_status_envio(
        self, conexao, *, id_mensagem, status_envio, id_externo=None
    ):
        self.mensagens[id_mensagem]["status_envio"] = status_envio


def _trabalho(*, id_hotel=1, id_trabalho=5):
    return {
        "id_trabalho": id_trabalho,
        "id_hotel": id_hotel,
        "payload": {"id_reserva": 1, "id_mensagem": 8},
        "tentativas": 0,
        "tipo": "responder_duvida",
    }


def _processar(monkeypatch, repo, llm, catalogo, gateway=None, trabalho=None):
    concluidos = []
    falhas = []
    reagendados = []

    def marcar_concluido(conexao, *, id_trabalho):
        concluidos.append(id_trabalho)

    def marcar_falha(conexao, *, id_trabalho, tentativas, erro):
        falhas.append({"id_trabalho": id_trabalho, "erro": erro})

    def reagendar(conexao, **kwargs):
        reagendados.append(kwargs)

    monkeypatch.setattr("app.fila.repository.marcar_concluido", marcar_concluido)
    monkeypatch.setattr("app.fila.repository.marcar_falha", marcar_falha)
    monkeypatch.setattr("app.fila.repository.reagendar", reagendar)
    porta = gateway or MensageriaFalsa()
    conversa.processar_trabalho_responder_duvida(
        object(),
        trabalho=trabalho or _trabalho(id_hotel=repo.id_hotel),
        llm=llm,
        catalogo=catalogo,
        gateway=porta,
        repositorio=repo,
    )
    return concluidos, falhas, reagendados, porta


def _catalogo_cafe(id_hotel=1):
    porta = CatalogoFalso()
    porta.configurar(id_hotel, (item_cafe(id_hotel=id_hotel),))
    return porta


def test_duvida_coberta_grava_enviada_antes_de_enviar(monkeypatch):
    repo = RepoResponder()
    llm = LLMFalso()
    llm.configurar_resposta(resposta_coberta())
    catalogo = _catalogo_cafe()
    concluidos, falhas, reagendados, gateway = _processar(
        monkeypatch, repo, llm, catalogo
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    enviada = repo.mensagens[json_cls["id_mensagem_resposta"]]
    assert repo.eventos[:2] == ["gravar_enviada", "gravar_json"]
    assert json_cls["resposta"] == "automatica"
    assert json_cls["desfecho"] == "classificado"
    assert enviada["conteudo"] == "7h as 10h"
    assert gateway.envios[0]["tipo"] == "sessao"
    assert gateway.envios[0]["corpo"] == "7h as 10h"
    assert gateway.envios[0]["id_mensagem"] == json_cls["id_mensagem_resposta"]
    assert concluidos == [5]
    assert falhas == []
    assert reagendados == []
    assert json_cls["desfecho"] != "duvida_nao_coberta"


def test_ja_respondida_pendente_nao_chama_llm_de_novo(monkeypatch):
    repo = RepoResponder(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "duvida_geral",
            "resposta": "automatica",
            "id_mensagem_resposta": 20,
        },
        enviadas={
            20: {
                "id_mensagem": 20,
                "id_reserva": 1,
                "conteudo": "7h as 10h",
                "classificacao_bruta": None,
                "status_envio": "pendente",
            }
        },
    )
    llm = LLMFalso()
    catalogo = _catalogo_cafe()
    concluidos, _, _, gateway = _processar(monkeypatch, repo, llm, catalogo)
    assert llm.chamadas_responder == []
    assert repo.eventos == []
    assert gateway.envios[0]["corpo"] == "7h as 10h"
    assert concluidos == [5]


def test_ja_respondida_enviada_so_conclui(monkeypatch):
    repo = RepoResponder(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "duvida_geral",
            "resposta": "automatica",
            "id_mensagem_resposta": 20,
        },
        enviadas={
            20: {
                "id_mensagem": 20,
                "id_reserva": 1,
                "conteudo": "7h as 10h",
                "classificacao_bruta": None,
                "status_envio": "enviada",
            }
        },
    )
    llm = LLMFalso()
    concluidos, _, _, gateway = _processar(
        monkeypatch, repo, llm, _catalogo_cafe()
    )
    assert llm.chamadas_responder == []
    assert gateway.envios == []
    assert concluidos == [5]


def test_nao_coberta_envia_aviso_e_desfecho_humano(monkeypatch):
    repo = RepoResponder()
    llm = LLMFalso()
    llm.configurar_resposta(resposta_nao_coberta())
    catalogo = _catalogo_cafe()
    concluidos, falhas, reagendados, gateway = _processar(
        monkeypatch, repo, llm, catalogo
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    enviada = repo.mensagens[json_cls["id_mensagem_resposta"]]
    assert repo.eventos[:2] == ["gravar_enviada", "gravar_json"]
    assert json_cls["resposta"] == "aviso"
    assert json_cls["desfecho"] == "duvida_nao_coberta"
    assert "recepcao" in enviada["conteudo"].casefold()
    assert "7h as 10h" not in enviada["conteudo"]
    assert gateway.envios[0]["corpo"] == enviada["conteudo"]
    assert concluidos == [5]
    assert falhas == []
    assert reagendados == []


def test_redacao_infiel_nao_envia_texto_do_modelo(monkeypatch):
    catalogo = _catalogo_cafe()
    casos = (
        ResultadoResposta(
            coberta=True,
            texto="piscina olimpica 6h",
            trechos_citados=("piscina olimpica 6h",),
        ),
        ResultadoResposta(coberta=True, texto="7h as 10h", trechos_citados=()),
    )
    for resultado in casos:
        repo = RepoResponder()
        llm = LLMFalso()
        llm.configurar_resposta(resultado)
        _, _, _, gateway = _processar(monkeypatch, repo, llm, catalogo)
        corpo = gateway.envios[0]["corpo"]
        json_cls = repo.mensagens[8]["classificacao_bruta"]
        assert corpo != resultado.texto
        assert "piscina" not in corpo.casefold()
        assert "recepcao" in corpo.casefold()
        assert json_cls["desfecho"] == "duvida_nao_coberta"
        assert json_cls["resposta"] == "aviso"


def test_catalogo_de_outro_hotel_nao_responde(monkeypatch):
    repo = RepoResponder(id_hotel=2)
    llm = LLMFalso()
    catalogo = CatalogoFalso()
    catalogo.configurar(1, (item_cafe(),))
    _, _, _, gateway = _processar(monkeypatch, repo, llm, catalogo)
    corpo = gateway.envios[0]["corpo"]
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    assert llm.chamadas_responder == []
    assert "7h as 10h" not in corpo
    assert "Cafe da manha" not in corpo
    assert json_cls["desfecho"] == "duvida_nao_coberta"


def test_catalogo_vazio_nao_chama_llm(monkeypatch):
    repo = RepoResponder()
    llm = LLMFalso()
    catalogo = CatalogoFalso()
    concluidos, falhas, reagendados, gateway = _processar(
        monkeypatch, repo, llm, catalogo
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    assert llm.chamadas_responder == []
    assert json_cls["desfecho"] == "duvida_nao_coberta"
    assert json_cls["resposta"] == "aviso"
    assert "recepcao" in gateway.envios[0]["corpo"].casefold()
    assert concluidos == [5]
    assert falhas == []
    assert reagendados == []


def test_falha_de_conversacao_escala_sem_backoff_de_llm(monkeypatch):
    repo = RepoResponder()
    llm = LLMFalso()
    llm.falhar_conversacao = True
    catalogo = _catalogo_cafe()
    concluidos, falhas, reagendados, gateway = _processar(
        monkeypatch, repo, llm, catalogo
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    assert json_cls["desfecho"] == "duvida_nao_coberta"
    assert json_cls["resposta"] == "aviso"
    assert "recepcao" in gateway.envios[0]["corpo"].casefold()
    assert concluidos == [5]
    assert falhas == []
    assert reagendados == []


@pytest.mark.postgres
def test_gravar_resposta_nao_altera_conteudo_nem_eixos(ambiente):
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
                "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
                " intencao, sentimento, urgencia, classificacao_bruta) "
                "VALUES (:r, 'recebida', 'texto original', 'duvida_geral',"
                " 'neutro', 'baixa',"
                " CAST(:c AS jsonb)) RETURNING id_mensagem"
            ),
            {
                "r": id_reserva,
                "c": '{"tipo": "classificacao_intencao", "desfecho": "classificado"}',
            },
        ).scalar_one()
        afetadas = conversa_repo.gravar_resposta_duvida(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            resposta="automatica",
            id_mensagem_resposta=99,
        )
        assert afetadas == 1
        linha = conexao.execute(
            text(
                "SELECT conteudo, intencao, classificacao_bruta"
                " FROM mensagem WHERE id_mensagem = :id"
            ),
            {"id": id_mensagem},
        ).mappings().one()
        assert linha["conteudo"] == "texto original"
        assert linha["intencao"] == "duvida_geral"
        assert linha["classificacao_bruta"]["resposta"] == "automatica"
        assert linha["classificacao_bruta"]["id_mensagem_resposta"] == 99
        assert linha["classificacao_bruta"]["desfecho"] == "classificado"
        zero = conversa_repo.gravar_resposta_duvida(
            conexao,
            id_hotel=outro,
            id_mensagem=id_mensagem,
            resposta="aviso",
            id_mensagem_resposta=100,
            desfecho="duvida_nao_coberta",
        )
        assert zero == 0
