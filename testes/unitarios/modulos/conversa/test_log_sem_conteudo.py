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

        def inserir_mensagem_recebida(self, conexao, *, id_reserva, conteudo, id_externo=None):
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
