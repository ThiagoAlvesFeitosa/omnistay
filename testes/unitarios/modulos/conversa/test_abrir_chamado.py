"""Confirmacao de reclamacao tecnica e gravacao na mensagem recebida."""

import pytest
from sqlalchemy import text

from app.modulos.conversa import repository as conversa_repo


@pytest.mark.postgres
def test_gravar_confirmacao_reclamacao_nao_altera_conteudo_nem_eixos(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    outro = ambiente.propriedade_b.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511911112222', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo,"
                " intencao, sentimento, urgencia, classificacao_bruta) "
                "VALUES (:r, 'recebida', 'o ar nao gela', 'reclamacao_tecnica',"
                " 'negativo', 'alta',"
                " CAST(:json AS jsonb)) RETURNING id_mensagem"
            ),
            {
                "r": id_reserva,
                "json": (
                    '{"tipo": "classificacao_intencao", "desfecho": "classificado",'
                    ' "intencao": "reclamacao_tecnica"}'
                ),
            },
        ).scalar_one()
        afetadas = conversa_repo.gravar_confirmacao_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_mensagem=id_mensagem,
            id_mensagem_resposta=50,
            id_solicitacao=7,
        )
        assert afetadas == 1
        linha = conexao.execute(
            text(
                "SELECT conteudo, intencao, urgencia, classificacao_bruta"
                " FROM mensagem WHERE id_mensagem = :id"
            ),
            {"id": id_mensagem},
        ).mappings().one()
        assert linha["conteudo"] == "o ar nao gela"
        assert linha["intencao"] == "reclamacao_tecnica"
        assert linha["urgencia"] == "alta"
        bruto = linha["classificacao_bruta"]
        assert bruto["desfecho"] == "classificado"
        assert bruto["resposta"] == "confirmacao_reclamacao"
        assert bruto["id_mensagem_resposta"] == 50
        assert bruto["id_solicitacao"] == 7
        zero = conversa_repo.gravar_confirmacao_reclamacao(
            conexao,
            id_hotel=outro,
            id_mensagem=id_mensagem,
            id_mensagem_resposta=99,
            id_solicitacao=99,
        )
        assert zero == 0


from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.conversa import service as conversa
from app.modulos.conversa.texto_confirmacao_reclamacao import (
    montar_confirmacao_reclamacao,
)
from testes.suporte.reclamacao import (
    TEXTO_COM_HORARIO_NA_ORIGEM,
    TEXTO_COM_QUARTO_SEM_HORARIO,
    TEXTO_SEM_QUARTO,
)


class RepoChamado:
    def __init__(
        self,
        *,
        id_hotel=1,
        conteudo=TEXTO_COM_QUARTO_SEM_HORARIO,
        classificacao=None,
        enviadas=None,
        urgencia="alta",
    ):
        self.id_hotel = id_hotel
        self.eventos = []
        self.proximo_id = 20
        self.telefone = "5511999999999"
        self.nome = "Maria Silva"
        bruto = classificacao or {
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "reclamacao_tecnica",
        }
        self.mensagens = {
            8: {
                "id_mensagem": 8,
                "id_reserva": 1,
                "conteudo": conteudo,
                "urgencia": urgencia,
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

    def gravar_confirmacao_reclamacao(
        self,
        conexao,
        *,
        id_hotel,
        id_mensagem,
        id_mensagem_resposta,
        id_solicitacao,
    ):
        if id_hotel != self.id_hotel:
            return 0
        self.eventos.append("gravar_json")
        atual = dict(self.mensagens[id_mensagem]["classificacao_bruta"] or {})
        atual["resposta"] = "confirmacao_reclamacao"
        atual["id_mensagem_resposta"] = id_mensagem_resposta
        atual["id_solicitacao"] = id_solicitacao
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


class EspiaoAbrirReclamacao:
    def __init__(self, repo, *, id_solicitacao=70, falhar=False):
        self.repo = repo
        self.id_solicitacao = id_solicitacao
        self.falhar = falhar
        self.chamadas = []
        self.enviadas_no_instante = []

    def __call__(self, conexao, **kwargs):
        self.enviadas_no_instante.append(
            sum(1 for evento in self.repo.eventos if evento == "gravar_enviada")
        )
        self.chamadas.append(kwargs)
        if self.falhar:
            raise RuntimeError("falha_ao_abrir")
        return self.id_solicitacao


def _trabalho_chamado(*, id_hotel=1, id_trabalho=5):
    return {
        "id_trabalho": id_trabalho,
        "id_hotel": id_hotel,
        "payload": {"id_reserva": 1, "id_mensagem": 8},
        "tentativas": 0,
        "tipo": "abrir_chamado_reclamacao",
    }


def _processar_chamado(monkeypatch, repo, abrir, gateway=None, trabalho=None):
    concluidos = []
    falhas = []
    reagendados = []

    def marcar_concluido(conexao, *, id_trabalho):
        concluidos.append(id_trabalho)

    def marcar_falha(conexao, *, id_trabalho, tentativas, erro):
        falhas.append({"id_trabalho": id_trabalho, "erro": erro})

    def reagendar(conexao, **kwargs):
        reagendados.append(kwargs)

    def registrar_falha_de_envio(conexao, **kwargs):
        reagendados.append(kwargs)
        return "reagendado"

    monkeypatch.setattr("app.fila.repository.marcar_concluido", marcar_concluido)
    monkeypatch.setattr("app.fila.repository.marcar_falha", marcar_falha)
    monkeypatch.setattr("app.fila.repository.reagendar", reagendar)
    monkeypatch.setattr(
        "app.fila.service.registrar_falha_de_envio", registrar_falha_de_envio
    )
    porta = gateway or MensageriaFalsa()
    conversa.processar_trabalho_abrir_chamado(
        object(),
        trabalho=trabalho or _trabalho_chamado(id_hotel=repo.id_hotel),
        gateway=porta,
        abrir_reclamacao=abrir,
        repositorio=repo,
    )
    return concluidos, falhas, reagendados, porta


def test_chamado_grava_enviada_abre_reclamacao_e_envia_depois(monkeypatch):
    repo = RepoChamado()
    abrir = EspiaoAbrirReclamacao(repo)
    concluidos, falhas, reagendados, gateway = _processar_chamado(
        monkeypatch, repo, abrir
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    enviada = repo.mensagens[json_cls["id_mensagem_resposta"]]
    recado = montar_confirmacao_reclamacao(
        nome_completo="Maria Silva", perguntar_horario=True
    )
    assert repo.eventos[:2] == ["gravar_enviada", "gravar_json"]
    assert abrir.enviadas_no_instante == [1]
    assert abrir.chamadas[0]["descricao"] == TEXTO_COM_QUARTO_SEM_HORARIO
    assert abrir.chamadas[0]["numero_quarto"] == "402"
    assert abrir.chamadas[0]["janela_preferencia"] is None
    assert abrir.chamadas[0]["urgencia"] == "alta"
    assert json_cls["resposta"] == "confirmacao_reclamacao"
    assert json_cls["desfecho"] == "classificado"
    assert json_cls["id_solicitacao"] == 70
    assert enviada["conteudo"] == recado
    assert "horario" in recado.casefold()
    assert gateway.envios[0]["tipo"] == "sessao"
    assert gateway.envios[0]["corpo"] == recado
    assert concluidos == [5]
    assert falhas == []
    assert reagendados == []


def test_enviada_existe_antes_de_abrir_reclamacao_e_recado_nao_promete(monkeypatch):
    repo = RepoChamado()
    abrir = EspiaoAbrirReclamacao(repo)
    _, _, _, gateway = _processar_chamado(monkeypatch, repo, abrir)
    assert abrir.enviadas_no_instante == [1]
    corpo = gateway.envios[0]["corpo"].casefold()
    assert "minuto" not in corpo
    assert "hoje" not in corpo
    assert "cardapio" not in corpo
    assert "gela" not in corpo


def test_abrir_reclamacao_levantando_nao_envia(monkeypatch):
    repo = RepoChamado()
    abrir = EspiaoAbrirReclamacao(repo, falhar=True)
    gateway = MensageriaFalsa()
    with pytest.raises(RuntimeError, match="falha_ao_abrir"):
        _processar_chamado(monkeypatch, repo, abrir, gateway=gateway)
    assert gateway.envios == []
    assert "gravar_json" not in repo.eventos
    assert abrir.enviadas_no_instante == [1]


def test_origem_com_horario_nao_pergunta_de_novo(monkeypatch):
    repo = RepoChamado(conteudo=TEXTO_COM_HORARIO_NA_ORIGEM)
    abrir = EspiaoAbrirReclamacao(repo)
    _, _, _, gateway = _processar_chamado(monkeypatch, repo, abrir)
    assert abrir.chamadas[0]["janela_preferencia"] == "depois das 16h"
    corpo = gateway.envios[0]["corpo"].casefold()
    assert "horario" not in corpo


def test_chamado_sem_quarto_ainda_confirma(monkeypatch):
    repo = RepoChamado(conteudo=TEXTO_SEM_QUARTO)
    abrir = EspiaoAbrirReclamacao(repo)
    _, _, _, gateway = _processar_chamado(monkeypatch, repo, abrir)
    assert abrir.chamadas[0]["numero_quarto"] is None
    assert abrir.chamadas[0]["descricao"] == TEXTO_SEM_QUARTO
    assert gateway.envios[0]["corpo"]
    assert repo.mensagens[8]["classificacao_bruta"]["resposta"] == (
        "confirmacao_reclamacao"
    )


def test_ja_aberto_pendente_so_retenta_envio(monkeypatch):
    recado = montar_confirmacao_reclamacao(
        nome_completo="Maria Silva", perguntar_horario=True
    )
    repo = RepoChamado(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "reclamacao_tecnica",
            "resposta": "confirmacao_reclamacao",
            "id_mensagem_resposta": 20,
            "id_solicitacao": 70,
        },
        enviadas={
            20: {
                "id_mensagem": 20,
                "id_reserva": 1,
                "conteudo": recado,
                "classificacao_bruta": None,
                "status_envio": "pendente",
            }
        },
    )
    abrir = EspiaoAbrirReclamacao(repo)
    concluidos, _, _, gateway = _processar_chamado(monkeypatch, repo, abrir)
    assert abrir.chamadas == []
    assert repo.eventos == []
    assert gateway.envios[0]["corpo"] == recado
    assert concluidos == [5]


def test_ja_aberto_enviada_so_conclui(monkeypatch):
    recado = montar_confirmacao_reclamacao(
        nome_completo="Maria Silva", perguntar_horario=True
    )
    repo = RepoChamado(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "reclamacao_tecnica",
            "resposta": "confirmacao_reclamacao",
            "id_mensagem_resposta": 20,
            "id_solicitacao": 70,
        },
        enviadas={
            20: {
                "id_mensagem": 20,
                "id_reserva": 1,
                "conteudo": recado,
                "classificacao_bruta": None,
                "status_envio": "enviada",
            }
        },
    )
    abrir = EspiaoAbrirReclamacao(repo)
    concluidos, _, _, gateway = _processar_chamado(monkeypatch, repo, abrir)
    assert abrir.chamadas == []
    assert gateway.envios == []
    assert concluidos == [5]


def test_falha_de_envio_preserva_chamado_e_reagenda(monkeypatch):
    repo = RepoChamado()
    abrir = EspiaoAbrirReclamacao(repo)
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    concluidos, falhas, reagendados, _ = _processar_chamado(
        monkeypatch, repo, abrir, gateway=gateway
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    assert json_cls["id_solicitacao"] == 70
    assert json_cls["resposta"] == "confirmacao_reclamacao"
    enviada = repo.mensagens[json_cls["id_mensagem_resposta"]]
    assert enviada["status_envio"] == "pendente"
    assert len(abrir.chamadas) == 1
    assert concluidos == []
    assert falhas == []
    assert reagendados
