"""Fork de consumo no processador registrar_pedido_servico."""

from decimal import Decimal

import pytest

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.conversa import service as conversa
from app.modulos.conversa.texto_aviso_identificacao import montar_aviso_identificacao
from app.modulos.conversa.texto_confirmacao_consumo import montar_confirmacao_consumo
from app.portas.llm import FalhaDeIdentificacao, ResultadoIdentificacao
from testes.suporte.consumo import (
    NOME_ITEM,
    PRECO_ATUAL,
    TEXTO_PEDIDO_CERVEJA,
    proibicoes_do_recado_consumo,
)
from testes.unitarios.modulos.conversa.test_registrar_pedido import (
    EspiaoAbrir,
    RepoPedido,
    _trabalho,
)


class Identificador:
    def __init__(self, resultado=None, falhar=False):
        self.resultado = resultado or ResultadoIdentificacao(
            desfecho="unico", id_item_vendavel=3, quantidade=1
        )
        self.falhar = falhar
        self.chamadas = []

    def __call__(self, texto, itens):
        self.chamadas.append((texto, itens))
        if self.falhar:
            raise FalhaDeIdentificacao("indisponivel")
        return self.resultado


class Listar:
    def __init__(self, itens=((3, NOME_ITEM),)):
        self.itens = itens
        self.chamadas = []

    def __call__(self, conexao, *, id_hotel):
        self.chamadas.append(id_hotel)
        return self.itens


class LerPreco:
    def __init__(self, preco=PRECO_ATUAL):
        self.preco = preco
        self.chamadas = []

    def __call__(self, conexao, *, id_hotel, id_item_vendavel):
        self.chamadas.append(id_item_vendavel)
        return self.preco


class RepoConsumo(RepoPedido):
    def gravar_confirmacao_consumo(
        self,
        conexao,
        *,
        id_hotel,
        id_mensagem,
        id_mensagem_resposta,
        id_solicitacao,
        id_item_vendavel,
        quantidade,
    ):
        if id_hotel != self.id_hotel:
            return 0
        self.eventos.append("gravar_json")
        atual = dict(self.mensagens[id_mensagem]["classificacao_bruta"] or {})
        atual["resposta"] = "confirmacao_consumo"
        atual["id_mensagem_resposta"] = id_mensagem_resposta
        atual["id_solicitacao"] = id_solicitacao
        atual["id_item_vendavel"] = id_item_vendavel
        atual["quantidade"] = quantidade
        self.mensagens[id_mensagem]["classificacao_bruta"] = atual
        return 1

    def gravar_aviso_identificacao(
        self, conexao, *, id_hotel, id_mensagem, id_mensagem_resposta, desfecho
    ):
        if id_hotel != self.id_hotel:
            return 0
        self.eventos.append("gravar_json")
        atual = dict(self.mensagens[id_mensagem]["classificacao_bruta"] or {})
        atual["resposta"] = "aviso_identificacao"
        atual["desfecho"] = desfecho
        atual["id_mensagem_resposta"] = id_mensagem_resposta
        self.mensagens[id_mensagem]["classificacao_bruta"] = atual
        return 1


def _processar(
    monkeypatch,
    repo,
    *,
    abrir_servico=None,
    abrir_consumo=None,
    listar=None,
    identificar=None,
    ler_preco=None,
    gateway=None,
):
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
        trabalho=_trabalho(id_hotel=repo.id_hotel),
        gateway=porta,
        abrir_servico=abrir_servico or EspiaoAbrir(repo),
        abrir_consumo=abrir_consumo,
        listar_itens_ativos=listar,
        identificar=identificar,
        ler_preco=ler_preco,
        repositorio=repo,
    )
    return concluidos, falhas, reagendados, porta


def test_unico_identifica_sem_preco_grava_enviada_antes_e_abre_consumo(monkeypatch):
    repo = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    abrir_consumo = EspiaoAbrir(repo, id_solicitacao=80)
    abrir_servico = EspiaoAbrir(repo, id_solicitacao=70)
    identificar = Identificador()
    listar = Listar()
    preco = LerPreco()
    concluidos, _, _, gateway = _processar(
        monkeypatch,
        repo,
        abrir_servico=abrir_servico,
        abrir_consumo=abrir_consumo,
        listar=listar,
        identificar=identificar,
        ler_preco=preco,
    )
    texto, itens = identificar.chamadas[0]
    assert texto == TEXTO_PEDIDO_CERVEJA
    assert itens == ((3, NOME_ITEM),)
    assert all(len(par) == 2 for par in itens)
    assert preco.chamadas == [3]
    assert abrir_consumo.enviadas_no_instante == [1]
    assert abrir_servico.chamadas == []
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    recado = montar_confirmacao_consumo(
        nome_completo="Maria Silva",
        descricao_item=NOME_ITEM,
        valor_praticado=PRECO_ATUAL,
    )
    assert json_cls["resposta"] == "confirmacao_consumo"
    assert json_cls["id_solicitacao"] == 80
    assert repo.mensagens[json_cls["id_mensagem_resposta"]]["conteudo"] == recado
    assert gateway.envios[0]["corpo"] == recado
    assert concluidos == [5]


def test_enviada_existe_antes_de_abrir_consumo_e_recado_sem_proibicoes(monkeypatch):
    repo = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    abrir_consumo = EspiaoAbrir(repo, id_solicitacao=80)
    _, _, _, gateway = _processar(
        monkeypatch,
        repo,
        abrir_consumo=abrir_consumo,
        listar=Listar(),
        identificar=Identificador(),
        ler_preco=LerPreco(),
    )
    assert abrir_consumo.enviadas_no_instante == [1]
    corpo = gateway.envios[0]["corpo"].casefold()
    for palavra in proibicoes_do_recado_consumo():
        assert palavra not in corpo


def test_abrir_consumo_levantando_nao_envia(monkeypatch):
    repo = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    abrir_consumo = EspiaoAbrir(repo, falhar=True)
    gateway = MensageriaFalsa()
    with pytest.raises(RuntimeError, match="falha_ao_abrir"):
        _processar(
            monkeypatch,
            repo,
            abrir_consumo=abrir_consumo,
            listar=Listar(),
            identificar=Identificador(),
            ler_preco=LerPreco(),
            gateway=gateway,
        )
    assert gateway.envios == []
    assert "gravar_json" not in repo.eventos


def test_lista_vazia_nao_chama_porta_e_abre_servico(monkeypatch):
    repo = RepoConsumo()
    abrir_servico = EspiaoAbrir(repo)
    identificar = Identificador()
    _processar(
        monkeypatch,
        repo,
        abrir_servico=abrir_servico,
        abrir_consumo=EspiaoAbrir(repo, id_solicitacao=80),
        listar=Listar(itens=()),
        identificar=identificar,
        ler_preco=LerPreco(),
    )
    assert identificar.chamadas == []
    assert abrir_servico.chamadas
    assert repo.mensagens[8]["classificacao_bruta"]["resposta"] == "confirmacao_pedido"


def test_nenhum_abre_servico_nao_consumo(monkeypatch):
    repo = RepoConsumo()
    abrir_servico = EspiaoAbrir(repo)
    abrir_consumo = EspiaoAbrir(repo, id_solicitacao=80)
    _processar(
        monkeypatch,
        repo,
        abrir_servico=abrir_servico,
        abrir_consumo=abrir_consumo,
        listar=Listar(),
        identificar=Identificador(ResultadoIdentificacao(desfecho="nenhum")),
        ler_preco=LerPreco(),
    )
    assert abrir_servico.chamadas
    assert abrir_consumo.chamadas == []


def test_ambiguo_avisa_sem_abrir(monkeypatch):
    repo = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    abrir_servico = EspiaoAbrir(repo)
    abrir_consumo = EspiaoAbrir(repo, id_solicitacao=80)
    _, _, _, gateway = _processar(
        monkeypatch,
        repo,
        abrir_servico=abrir_servico,
        abrir_consumo=abrir_consumo,
        listar=Listar(),
        identificar=Identificador(ResultadoIdentificacao(desfecho="ambiguo")),
        ler_preco=LerPreco(),
    )
    assert abrir_servico.chamadas == []
    assert abrir_consumo.chamadas == []
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    assert json_cls["resposta"] == "aviso_identificacao"
    assert json_cls["desfecho"] == "item_ambiguo"
    recado = montar_aviso_identificacao(nome_completo="Maria Silva")
    assert gateway.envios[0]["corpo"] == recado
    assert "r$" not in recado.casefold()


def test_falha_e_id_invalido_viram_humano(monkeypatch):
    repo = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    abrir_consumo = EspiaoAbrir(repo, id_solicitacao=80)
    _processar(
        monkeypatch,
        repo,
        abrir_consumo=abrir_consumo,
        listar=Listar(),
        identificar=Identificador(falhar=True),
        ler_preco=LerPreco(),
    )
    assert repo.mensagens[8]["classificacao_bruta"]["desfecho"] == (
        "identificacao_indisponivel"
    )
    assert abrir_consumo.chamadas == []

    repo2 = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    abrir2 = EspiaoAbrir(repo2, id_solicitacao=80)
    _processar(
        monkeypatch,
        repo2,
        abrir_consumo=abrir2,
        listar=Listar(),
        identificar=Identificador(
            ResultadoIdentificacao(desfecho="unico", id_item_vendavel=99, quantidade=1)
        ),
        ler_preco=LerPreco(),
    )
    assert repo2.mensagens[8]["classificacao_bruta"]["desfecho"] == (
        "identificacao_indisponivel"
    )
    assert abrir2.chamadas == []


def test_ja_registrado_consumo_nao_identifica_de_novo(monkeypatch):
    recado = montar_confirmacao_consumo(
        nome_completo="Maria Silva",
        descricao_item=NOME_ITEM,
        valor_praticado=PRECO_ATUAL,
    )
    repo = RepoConsumo(
        classificacao={
            "tipo": "classificacao_intencao",
            "desfecho": "classificado",
            "intencao": "pedido_de_servico",
            "resposta": "confirmacao_consumo",
            "id_mensagem_resposta": 20,
            "id_solicitacao": 80,
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
    identificar = Identificador()
    abrir_consumo = EspiaoAbrir(repo, id_solicitacao=80)
    concluidos, _, _, gateway = _processar(
        monkeypatch,
        repo,
        abrir_consumo=abrir_consumo,
        listar=Listar(),
        identificar=identificar,
        ler_preco=LerPreco(),
    )
    assert identificar.chamadas == []
    assert abrir_consumo.chamadas == []
    assert gateway.envios[0]["corpo"] == recado
    assert concluidos == [5]


def test_falha_de_envio_preserva_consumo(monkeypatch):
    repo = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    abrir_consumo = EspiaoAbrir(repo, id_solicitacao=80)
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    concluidos, falhas, reagendados, _ = _processar(
        monkeypatch,
        repo,
        abrir_consumo=abrir_consumo,
        listar=Listar(),
        identificar=Identificador(),
        ler_preco=LerPreco(),
        gateway=gateway,
    )
    json_cls = repo.mensagens[8]["classificacao_bruta"]
    assert json_cls["id_solicitacao"] == 80
    assert json_cls["resposta"] == "confirmacao_consumo"
    assert repo.mensagens[json_cls["id_mensagem_resposta"]]["status_envio"] == "pendente"
    assert len(abrir_consumo.chamadas) == 1
    assert concluidos == []
    assert falhas == []
    assert reagendados
