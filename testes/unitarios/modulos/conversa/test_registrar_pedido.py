"""Confirmacao de pedido de servico e gravacao na mensagem recebida."""

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.conversa import repository as conversa_repo
from app.modulos.conversa import service as conversa
from app.modulos.conversa.texto_confirmacao_pedido import montar_confirmacao_pedido
from testes.suporte.pedido_servico import TEXTO_COM_QUARTO, TEXTO_SEM_QUARTO


@pytest.mark.postgres
def test_gravar_confirmacao_nao_altera_conteudo_nem_eixos(ambiente):
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
                "VALUES (:r, 'recebida', 'toalha extra', 'pedido_de_servico',"
                " 'neutro', 'baixa',"
                " CAST(:json AS jsonb)) RETURNING id_mensagem"
            ),
            {
                "r": id_reserva,
                "json": (
                    '{"tipo": "classificacao_intencao", "desfecho": "classificado",'
                    ' "intencao": "pedido_de_servico"}'
                ),
            },
        ).scalar_one()
        afetadas = conversa_repo.gravar_confirmacao_pedido(
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
        assert linha["conteudo"] == "toalha extra"
        assert linha["intencao"] == "pedido_de_servico"
        assert linha["urgencia"] == "baixa"
        bruto = linha["classificacao_bruta"]
        assert bruto["desfecho"] == "classificado"
        assert bruto["resposta"] == "confirmacao_pedido"
        assert bruto["id_mensagem_resposta"] == 50
        assert bruto["id_solicitacao"] == 7
        zero = conversa_repo.gravar_confirmacao_pedido(
            conexao,
            id_hotel=outro,
            id_mensagem=id_mensagem,
            id_mensagem_resposta=99,
            id_solicitacao=99,
        )
        assert zero == 0


class RepoPedido:
    def __init__(
        self,
        *,
        id_hotel=1,
        conteudo=TEXTO_COM_QUARTO,
        classificacao=None,
        enviadas=None,
        urgencia="baixa",
    ):
        self.id_hotel = id_hotel
        self.eventos = []
        self.proximo_id = 20
        self.telefone = "5511999999999"
        self.nome = "Maria Silva"
        bruto = classificacao or {
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "pedido_de_servico",
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

    def gravar_confirmacao_pedido(
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
        atual["resposta"] = "confirmacao_pedido"
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


class EspiaoAbrir:
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


def _trabalho(*, id_hotel=1, id_trabalho=5):
    return {
        "id_trabalho": id_trabalho,
        "id_hotel": id_hotel,
        "payload": {"id_reserva": 1, "id_mensagem": 8},
        "tentativas": 0,
        "tipo": "registrar_pedido_servico",
    }


def _processar(monkeypatch, repo, abrir, gateway=None, trabalho=None):
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
    conversa.processar_trabalho_registrar_pedido(
        object(),
        trabalho=trabalho or _trabalho(id_hotel=repo.id_hotel),
        gateway=porta,
        abrir_servico=abrir,
        repositorio=repo,
    )
    return concluidos, falhas, reagendados, porta


def test_pedido_grava_enviada_abre_servico_e_envia_depois(monkeypatch):
    repo = RepoPedido()
    abrir = EspiaoAbrir(repo)
    concluidos, falhas, reagendados, gateway = _processar(monkeypatch, repo, abrir)
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    enviada = repo.mensagens[json_cls["id_mensagem_resposta"]]
    recado = montar_confirmacao_pedido(nome_completo="Maria Silva")
    assert repo.eventos[:2] == ["gravar_enviada", "gravar_json"]
    assert abrir.enviadas_no_instante == [1]
    assert abrir.chamadas[0]["descricao"] == TEXTO_COM_QUARTO
    assert abrir.chamadas[0]["numero_quarto"] == "402"
    assert abrir.chamadas[0]["urgencia"] == "baixa"
    assert json_cls["resposta"] == "confirmacao_pedido"
    assert json_cls["desfecho"] == "classificado"
    assert json_cls["id_solicitacao"] == 70
    assert enviada["conteudo"] == recado
    assert gateway.envios[0]["tipo"] == "sessao"
    assert gateway.envios[0]["corpo"] == recado
    assert gateway.envios[0]["id_mensagem"] == json_cls["id_mensagem_resposta"]
    assert concluidos == [5]
    assert falhas == []
    assert reagendados == []


def test_enviada_existe_antes_de_abrir_servico_e_recado_nao_promete(monkeypatch):
    repo = RepoPedido()
    abrir = EspiaoAbrir(repo)
    _, _, _, gateway = _processar(monkeypatch, repo, abrir)
    assert abrir.enviadas_no_instante == [1]
    corpo = gateway.envios[0]["corpo"].casefold()
    assert "minuto" not in corpo
    assert "hoje" not in corpo
    assert "7h" not in corpo
    assert "cardapio" not in corpo
    assert "toalha" not in corpo


def test_abrir_servico_levantando_nao_envia(monkeypatch):
    repo = RepoPedido()
    abrir = EspiaoAbrir(repo, falhar=True)
    gateway = MensageriaFalsa()
    with pytest.raises(RuntimeError, match="falha_ao_abrir"):
        _processar(monkeypatch, repo, abrir, gateway=gateway)
    assert gateway.envios == []
    assert "gravar_json" not in repo.eventos
    assert abrir.enviadas_no_instante == [1]


def test_pedido_sem_quarto_ainda_confirma(monkeypatch):
    repo = RepoPedido(conteudo=TEXTO_SEM_QUARTO)
    abrir = EspiaoAbrir(repo)
    _, _, _, gateway = _processar(monkeypatch, repo, abrir)
    assert abrir.chamadas[0]["numero_quarto"] is None
    assert abrir.chamadas[0]["descricao"] == TEXTO_SEM_QUARTO
    assert gateway.envios[0]["corpo"]
    assert repo.mensagens[8]["classificacao_bruta"]["resposta"] == "confirmacao_pedido"


def test_ja_registrado_pendente_so_retenta_envio(monkeypatch):
    recado = montar_confirmacao_pedido(nome_completo="Maria Silva")
    repo = RepoPedido(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "pedido_de_servico",
            "resposta": "confirmacao_pedido",
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
    abrir = EspiaoAbrir(repo)
    concluidos, _, _, gateway = _processar(monkeypatch, repo, abrir)
    assert abrir.chamadas == []
    assert repo.eventos == []
    assert gateway.envios[0]["corpo"] == recado
    assert concluidos == [5]


def test_ja_registrado_enviada_so_conclui(monkeypatch):
    recado = montar_confirmacao_pedido(nome_completo="Maria Silva")
    repo = RepoPedido(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "pedido_de_servico",
            "resposta": "confirmacao_pedido",
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
    abrir = EspiaoAbrir(repo)
    concluidos, _, _, gateway = _processar(monkeypatch, repo, abrir)
    assert abrir.chamadas == []
    assert gateway.envios == []
    assert concluidos == [5]


def test_falha_de_envio_preserva_pedido_e_reagenda(monkeypatch):
    repo = RepoPedido()
    abrir = EspiaoAbrir(repo)
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    concluidos, falhas, reagendados, _ = _processar(
        monkeypatch, repo, abrir, gateway=gateway
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    assert json_cls["id_solicitacao"] == 70
    assert json_cls["resposta"] == "confirmacao_pedido"
    enviada = repo.mensagens[json_cls["id_mensagem_resposta"]]
    assert enviada["status_envio"] == "pendente"
    assert len(abrir.chamadas) == 1
    assert concluidos == []
    assert falhas == []
    assert reagendados


def test_lista_vazia_nao_chama_identificador(monkeypatch):
    from testes.unitarios.modulos.conversa.test_registrar_consumo import (
        Identificador,
        Listar,
        _processar as processar_consumo,
    )

    repo = RepoPedido()
    abrir = EspiaoAbrir(repo)
    identificar = Identificador()
    processar_consumo(
        monkeypatch,
        repo,
        abrir_servico=abrir,
        listar=Listar(itens=()),
        identificar=identificar,
    )
    assert identificar.chamadas == []
    assert abrir.chamadas
    assert repo.mensagens[8]["classificacao_bruta"]["resposta"] == "confirmacao_pedido"
