"""Logs de conversa nao carregam conteudo nem telefone."""

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

