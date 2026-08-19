"""Logs de conversa nao carregam conteudo nem telefone."""

import pytest

from app.modulos.conversa import service as conversa
from app.modulos.conversa.schema import EventoEntrada


def test_marcar_sucesso_loga_so_identificadores(monkeypatch):
    class Repo:
        def atualizar_status_envio(self, conexao, *, id_mensagem, status_envio, id_externo=None):
            return None

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    conversa.marcar_envio_sucesso(
        object(), id_mensagem=7, id_externo="fake-7", repositorio=Repo()
    )
    texto = " ".join(registros)
    assert "id_mensagem=7" in texto
    assert "Ola," not in texto
    assert "5511" not in texto


def test_receber_evento_loga_so_identificadores(monkeypatch):
    class Repo:
        def inserir_evento_webhook(self, conexao, *, id_externo, payload):
            return 3

        def resolver_reserva_aguardando_cadastro(self, conexao, *, id_hotel, telefone_contato):
            return {"id_reserva": 10, "id_hotel": 1, "status": "aguardando_cadastro"}

        def inserir_mensagem_recebida(self, conexao, *, id_reserva, conteudo, id_externo=None, enviada_em=None):
            return 8

    def enfileirar(*args, **kwargs):
        return 9

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="evt",
            telefone_origem="11987654321",
            texto="segredo pessoal da ficha",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=Repo(),
        enfileirar=enfileirar,
    )
    texto = " ".join(registros)
    assert "id_mensagem=8" in texto
    assert "segredo pessoal" not in texto
    assert "11987654321" not in texto


def test_agendar_lembrete_loga_so_identificadores(monkeypatch):
    class Repo:
        def inserir_mensagem_enviada_pendente(self, conexao, *, id_reserva, conteudo):
            assert "Maria" in conteudo
            return 4

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    conversa.agendar_lembrete(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=Repo(),
        enfileirar=lambda *a, **k: 1,
    )
    texto = " ".join(registros)
    assert "id_reserva=42" in texto
    assert "id_mensagem=4" in texto
    assert "Maria" not in texto
    assert "Silva" not in texto
    assert "opcional" not in texto


def test_eventos_de_boas_vindas_nao_levam_conteudo(monkeypatch):
    class Repo:
        def inserir_mensagem_enviada_pendente(self, conexao, *, id_reserva, conteudo):
            return 11

        def ler_parametros(self, conexao, id_hotel, chaves):
            return {
                "boas_vindas_cafe": "segredo do cafe",
                "boas_vindas_wifi": "senha-secreta",
                "boas_vindas_checkout": "12h",
            }

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    conversa.agendar_boas_vindas(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=Repo(),
        repositorio_propriedade=Repo(),
        enfileirar=lambda *a, **k: 1,
    )
    texto = " ".join(registros)
    assert "boas_vindas_agendadas" in texto
    assert "id_reserva=42" in texto
    assert "id_mensagem=11" in texto
    assert "segredo do cafe" not in texto
    assert "senha-secreta" not in texto
    assert "Maria" not in texto
    assert "5511" not in texto

    registros.clear()
    class Vazio:
        def ler_parametros(self, conexao, id_hotel, chaves):
            return {}

        def inserir_mensagem_enviada_pendente(self, conexao, *, id_reserva, conteudo):
            raise AssertionError("nao deveria gravar")

    conversa.agendar_boas_vindas(
        object(),
        id_hotel=1,
        id_reserva=7,
        nome_completo="Maria Silva",
        repositorio=Vazio(),
        repositorio_propriedade=Vazio(),
        enfileirar=lambda *a, **k: 1,
    )
    texto = " ".join(registros)
    assert "boas_vindas_bloqueadas" in texto
    assert "chave=boas_vindas_cafe" in texto
    assert "Maria" not in texto
    assert "segredo" not in texto


def test_desfechos_de_estadia_nao_levam_conteudo_ao_log(monkeypatch):
    class Repo:
        def __init__(self):
            self.eventos = {}
            self.proximo = 1
            self.hospedada = {
                "id_reserva": 20,
                "id_hotel": 1,
                "status": "hospedado",
            }

        def inserir_evento_webhook(self, conexao, *, id_externo, payload):
            if id_externo in self.eventos:
                return None
            eid = self.proximo
            self.proximo += 1
            self.eventos[id_externo] = eid
            return eid

        def resolver_reserva_aguardando_cadastro(
            self, conexao, *, id_hotel, telefone_contato
        ):
            return None

        def resolver_reserva_hospedada(self, conexao, *, id_hotel, telefone_contato):
            return self.hospedada

        def inserir_mensagem_recebida(
            self, conexao, *, id_reserva, conteudo, id_externo=None, enviada_em=None
        ):
            return 8

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    repo = Repo()
    evento = EventoEntrada(
        id_externo="est-log",
        telefone_origem="11987654321",
        texto="segredo da estadia",
        tem_texto_utilizavel=True,
    )
    conversa.receber_evento_entrada(
        object(),
        evento=evento,
        id_hotel=1,
        repositorio=repo,
        enfileirar_estadia=lambda *a, **k: 4,
    )
    conversa.receber_evento_entrada(
        object(),
        evento=evento,
        id_hotel=1,
        repositorio=repo,
        enfileirar_estadia=lambda *a, **k: 4,
    )
    repo.hospedada = None
    conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="orfao-log",
            telefone_origem="11987654321",
            texto="orfao secreto",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
    )
    conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="midia-log",
            telefone_origem="11987654321",
            texto="",
            tem_texto_utilizavel=False,
        ),
        id_hotel=1,
        repositorio=repo,
    )
    texto = " ".join(registros)
    assert "id_evento=" in texto
    assert "webhook_duplicado" in texto
    assert "webhook_sem_reserva" in texto
    assert "webhook_sem_texto" in texto
    assert "segredo da estadia" not in texto
    assert "orfao secreto" not in texto
    assert "11987654321" not in texto


def test_classificar_loga_sem_conteudo_nem_bruto(monkeypatch):
    class Repo:
        def ler_mensagem(self, conexao, *, id_mensagem):
            return {
                "id_mensagem": id_mensagem,
                "id_reserva": 1,
                "conteudo": "segredo da conversa",
                "classificacao_bruta": None,
            }

        def gravar_classificacao_intencao(self, conexao, **kwargs):
            return 1

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    monkeypatch.setattr("app.fila.repository.marcar_concluido", lambda *a, **k: None)

    from app.adaptadores.llm_falso import LLMFalso
    from app.portas.llm import ResultadoClassificacao

    trabalho = {
        "id_trabalho": 5,
        "id_hotel": 1,
        "payload": {"id_reserva": 1, "id_mensagem": 8, "id_evento": 3},
        "tentativas": 0,
    }
    llm = LLMFalso()
    conversa.processar_trabalho_classificar_mensagem(
        object(),
        trabalho=trabalho,
        llm=llm,
        repositorio=Repo(),
        enfileirar_resposta=lambda *a, **k: 1,
    )
    llm.falhar_classificacao = True
    conversa.processar_trabalho_classificar_mensagem(
        object(),
        trabalho=trabalho,
        llm=llm,
        repositorio=Repo(),
        enfileirar_resposta=lambda *a, **k: 1,
    )
    llm.falhar_classificacao = False
    llm.configurar_classificacao(
        ResultadoClassificacao(
            intencao="nao_existe",
            sentimento="neutro",
            urgencia="baixa",
            bruto={"eco": "segredo da conversa"},
        )
    )
    conversa.processar_trabalho_classificar_mensagem(
        object(),
        trabalho=trabalho,
        llm=llm,
        repositorio=Repo(),
        enfileirar_resposta=lambda *a, **k: 1,
    )
    texto = " ".join(registros)
    assert "id_mensagem=8" in texto
    assert "desfecho=" in texto
    assert "segredo da conversa" not in texto
    assert "eco" not in texto


def test_responder_duvida_loga_identificadores_sem_conteudo(monkeypatch):
    from app.adaptadores.llm_falso import LLMFalso
    from app.portas.llm import ResultadoResposta
    from testes.suporte.resposta_duvida import resposta_coberta, resposta_nao_coberta
    from testes.unitarios.modulos.conversa.test_responder_duvida import (
        RepoResponder,
        _catalogo_cafe,
        _processar,
    )

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)

    pergunta = "que horas e o cafe"
    fato = "7h as 10h"
    inventado = "piscina olimpica 6h"

    llm_auto = LLMFalso()
    llm_auto.configurar_resposta(resposta_coberta())
    _processar(monkeypatch, RepoResponder(), llm_auto, _catalogo_cafe())

    llm_aviso = LLMFalso()
    llm_aviso.configurar_resposta(resposta_nao_coberta())
    _processar(monkeypatch, RepoResponder(), llm_aviso, _catalogo_cafe())

    llm_infiel = LLMFalso()
    llm_infiel.configurar_resposta(
        ResultadoResposta(
            coberta=True, texto=inventado, trechos_citados=(inventado,)
        )
    )
    _processar(monkeypatch, RepoResponder(), llm_infiel, _catalogo_cafe())

    llm_cair = LLMFalso()
    llm_cair.falhar_conversacao = True
    _processar(monkeypatch, RepoResponder(), llm_cair, _catalogo_cafe())

    texto = " ".join(registros)
    assert "id_mensagem=8" in texto
    assert "id_trabalho=5" in texto
    assert "id_hotel=1" in texto
    assert "resultado=automatica" in texto
    assert "resultado=aviso" in texto
    assert "resultado=nao_fiel" in texto
    assert "resultado=indisponivel" in texto
    assert pergunta not in texto
    assert fato not in texto
    assert inventado not in texto
    assert "Cafe da manha" not in texto
    assert "5511" not in texto


def test_registrar_pedido_loga_identificadores_sem_conteudo(monkeypatch):
    from app.adaptadores.mensageria_falsa import MensageriaFalsa
    from app.modulos.conversa.texto_confirmacao_pedido import (
        montar_confirmacao_pedido,
    )
    from testes.suporte.pedido_servico import TEXTO_COM_QUARTO
    from testes.unitarios.modulos.conversa.test_registrar_pedido import (
        EspiaoAbrir,
        RepoPedido,
        _processar,
    )

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)

    recado = montar_confirmacao_pedido(nome_completo="Maria Silva")
    repo = RepoPedido()
    _processar(monkeypatch, repo, EspiaoAbrir(repo))

    repo_ja = RepoPedido(
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
    _processar(monkeypatch, repo_ja, EspiaoAbrir(repo_ja))

    repo_falha = RepoPedido()
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    _processar(
        monkeypatch, repo_falha, EspiaoAbrir(repo_falha), gateway=gateway
    )

    texto = " ".join(registros)
    assert "id_mensagem=8" in texto
    assert "id_trabalho=5" in texto
    assert "id_hotel=1" in texto
    assert "resultado=registrado" in texto
    assert "resultado=ja_registrado" in texto
    assert "resultado=envio_falhou" in texto
    assert TEXTO_COM_QUARTO not in texto
    assert recado not in texto
    assert "toalha" not in texto
    assert "402" not in texto
    assert "Maria" not in texto
    assert "5511" not in texto


def test_consumo_loga_identificadores_sem_conteudo_nem_valor(monkeypatch):
    from app.adaptadores.mensageria_falsa import MensageriaFalsa
    from app.modulos.conversa.texto_confirmacao_consumo import (
        montar_confirmacao_consumo,
    )
    from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL, TEXTO_PEDIDO_CERVEJA
    from testes.unitarios.modulos.conversa.test_registrar_consumo import (
        Identificador,
        LerPreco,
        Listar,
        RepoConsumo,
        _processar as processar_consumo,
    )
    from testes.unitarios.modulos.conversa.test_registrar_pedido import EspiaoAbrir

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    recado = montar_confirmacao_consumo(
        nome_completo="Maria Silva",
        descricao_item=NOME_ITEM,
        valor_praticado=PRECO_ATUAL,
    )
    repo = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    processar_consumo(
        monkeypatch,
        repo,
        abrir_consumo=EspiaoAbrir(repo, id_solicitacao=80),
        listar=Listar(),
        identificar=Identificador(),
        ler_preco=LerPreco(),
    )
    repo_ja = RepoConsumo(
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
                "status_envio": "enviada",
            }
        },
    )
    processar_consumo(
        monkeypatch,
        repo_ja,
        abrir_consumo=EspiaoAbrir(repo_ja, id_solicitacao=80),
        listar=Listar(),
        identificar=Identificador(),
        ler_preco=LerPreco(),
    )
    repo_falha = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    processar_consumo(
        monkeypatch,
        repo_falha,
        abrir_consumo=EspiaoAbrir(repo_falha, id_solicitacao=80),
        listar=Listar(),
        identificar=Identificador(),
        ler_preco=LerPreco(),
        gateway=gateway,
    )
    repo_humano = RepoConsumo(conteudo=TEXTO_PEDIDO_CERVEJA)
    processar_consumo(
        monkeypatch,
        repo_humano,
        abrir_consumo=EspiaoAbrir(repo_humano, id_solicitacao=80),
        listar=Listar(),
        identificar=Identificador(falhar=True),
        ler_preco=LerPreco(),
    )
    texto = " ".join(registros)
    assert "consumo_registrado" in texto
    assert "consumo_ja_registrado" in texto
    assert "consumo_envio_falhou" in texto
    assert "identificacao_humana" in texto
    assert "resultado=registrado" in texto
    assert TEXTO_PEDIDO_CERVEJA not in texto
    assert recado not in texto
    assert "12,00" not in texto
    assert "12.00" not in texto
    assert "Maria" not in texto


def test_abrir_chamado_loga_identificadores_sem_conteudo(monkeypatch):
    from app.adaptadores.mensageria_falsa import MensageriaFalsa
    from app.modulos.conversa.texto_confirmacao_reclamacao import (
        montar_confirmacao_reclamacao,
    )
    from testes.suporte.reclamacao import TEXTO_COM_QUARTO_SEM_HORARIO
    from testes.unitarios.modulos.conversa.test_abrir_chamado import (
        EspiaoAbrirReclamacao,
        RepoChamado,
        _processar_chamado,
    )

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)

    recado = montar_confirmacao_reclamacao(
        nome_completo="Maria Silva", perguntar_horario=True
    )
    repo = RepoChamado()
    _processar_chamado(monkeypatch, repo, EspiaoAbrirReclamacao(repo))

    repo_ja = RepoChamado(
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
    _processar_chamado(monkeypatch, repo_ja, EspiaoAbrirReclamacao(repo_ja))

    repo_falha = RepoChamado()
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    _processar_chamado(
        monkeypatch,
        repo_falha,
        EspiaoAbrirReclamacao(repo_falha),
        gateway=gateway,
    )

    texto = " ".join(registros)
    assert "id_mensagem=8" in texto
    assert "id_trabalho=5" in texto
    assert "id_hotel=1" in texto
    assert "resultado=aberto" in texto
    assert "resultado=ja_aberto" in texto
    assert "resultado=envio_falhou" in texto
    assert TEXTO_COM_QUARTO_SEM_HORARIO not in texto
    assert recado not in texto
    assert "gelando" not in texto
    assert "402" not in texto
    assert "Maria" not in texto
    assert "5511" not in texto


def test_janela_registrada_loga_identificadores_sem_texto(monkeypatch):
    class Repo:
        def ler_mensagem(self, conexao, *, id_mensagem):
            return {
                "id_mensagem": id_mensagem,
                "id_reserva": 1,
                "conteudo": "depois das 14h",
                "classificacao_bruta": None,
            }

        def gravar_classificacao_intencao(self, conexao, **kwargs):
            return 1

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    monkeypatch.setattr("app.fila.repository.marcar_concluido", lambda *a, **k: None)

    from app.adaptadores.llm_falso import LLMFalso

    conversa.processar_trabalho_classificar_mensagem(
        object(),
        trabalho={
            "id_trabalho": 5,
            "id_hotel": 1,
            "payload": {"id_reserva": 1, "id_mensagem": 8},
            "tentativas": 0,
        },
        llm=LLMFalso(),
        repositorio=Repo(),
        enfileirar_resposta=lambda *a, **k: 1,
        enfileirar_pedido=lambda *a, **k: 1,
        enfileirar_chamado=lambda *a, **k: 1,
        completar_janela=lambda *a, **k: 70,
    )
    texto = " ".join(registros)
    assert "id_mensagem=8" in texto
    assert "id_trabalho=5" in texto
    assert "id_hotel=1" in texto
    assert "resultado=janela_registrada" in texto
    assert "depois das 14h" not in texto


def test_resolucao_loga_identificadores_sem_conteudo(monkeypatch):
    from datetime import UTC, datetime

    from app.adaptadores.mensageria_falsa import MensageriaFalsa
    from app.modulos.atendimento import service as atendimento
    from app.modulos.conversa.texto_confirmacao_resolucao import (
        montar_confirmacao_resolucao,
    )
    from testes.unitarios.modulos.atendimento.test_resolver import (
        Agendador,
        Relogio,
        Repo,
    )
    from testes.unitarios.modulos.conversa.test_confirmacao_resolucao import (
        Fila,
        RepoMensagem,
        _processar,
    )

    recado = montar_confirmacao_resolucao(
        nome_completo="Maria Silva", tipo="reclamacao"
    )
    descricao = "o ar do quarto 402 nao esta gelando"
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(atendimento.logger, "info", fake_info)
    monkeypatch.setattr(conversa.logger, "info", fake_info)

    instante = datetime(2026, 8, 18, 14, 32, tzinfo=UTC)
    atendimento.resolver(
        object(),
        id_hotel=1,
        id_solicitacao=7,
        id_usuario=3,
        repositorio=Repo(
            resultado={
                "id_solicitacao": 7,
                "id_reserva": 42,
                "tipo": "reclamacao",
                "status": "resolvida",
                "resolvida_em": instante,
                "id_usuario_responsavel": 3,
            }
        ),
        agendar_confirmacao=Agendador(),
        relogio=Relogio(instante),
    )
    with pytest.raises(atendimento.ResolucaoNaoPermitida):
        atendimento.resolver(
            object(),
            id_hotel=1,
            id_solicitacao=7,
            id_usuario=3,
            repositorio=Repo(
                resultado=None,
                existente={"status": "resolvida", "tipo": "reclamacao"},
            ),
            agendar_confirmacao=Agendador(),
        )

    conversa.agendar_confirmacao_resolucao(
        object(),
        id_hotel=1,
        id_reserva=42,
        id_solicitacao=7,
        tipo="reclamacao",
        repositorio=RepoMensagem(),
        enfileirar=Fila(falhar=True),
    )

    repo_falha = RepoMensagem()
    repo_falha.mensagens[1] = {
        "id_mensagem": 1,
        "id_reserva": 42,
        "conteudo": recado,
        "status_envio": "pendente",
        "classificacao_bruta": {
            "tipo": "confirmacao_resolucao",
            "id_solicitacao": 7,
        },
    }
    gateway = MensageriaFalsa()
    gateway.falhar_sempre = True
    _processar(monkeypatch, repo_falha, gateway=gateway)

    texto = " ".join(registros)
    assert "chamado_resolvido" in texto
    assert "resolucao_recusada" in texto
    assert "resolucao_ja_agendada" in texto
    assert "resolucao_envio_falhou" in texto
    assert "id_solicitacao=7" in texto
    assert "id_hotel=1" in texto
    assert "resultado=resolvido" in texto
    assert recado not in texto
    assert descricao not in texto
    assert "402" not in texto
    assert "Maria" not in texto
    assert "5511" not in texto


def test_prazo_ausente_loga_hotel_sem_descricao(monkeypatch):
    from app.modulos.atendimento import service as atendimento

    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(atendimento.logger, "info", fake_info)

    class Repo:
        def listar_abertas(self, conexao, *, id_hotel):
            return []

    atendimento.listar_abertas(
        object(),
        id_hotel=9,
        repositorio=Repo(),
        ler_parametro=lambda *a, **k: None,
    )
    texto = " ".join(registros)
    assert "prazo_ausente" in texto
    assert "id_hotel=9" in texto
    assert "ar nao gela" not in texto
    assert "depois das" not in texto

