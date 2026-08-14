"""Recebimento de evento de entrada — sem LLM."""

from app.modulos.conversa import service as conversa
from app.modulos.conversa.schema import EventoEntrada


class RepoFake:
    def __init__(self):
        self.eventos = {}
        self.mensagens = []
        self.proximo_evento = 1
        self.proximo_msg = 1
        self.reserva = {"id_reserva": 10, "id_hotel": 1, "status": "aguardando_cadastro"}

    def inserir_evento_webhook(self, conexao, *, id_externo, payload):
        if id_externo in self.eventos:
            return None
        eid = self.proximo_evento
        self.proximo_evento += 1
        self.eventos[id_externo] = eid
        return eid

    def resolver_reserva_aguardando_cadastro(self, conexao, *, id_hotel, telefone_contato):
        if self.reserva and telefone_contato == "5511987654321":
            return self.reserva
        return None

    def inserir_mensagem_recebida(self, conexao, *, id_reserva, conteudo, id_externo=None):
        mid = self.proximo_msg
        self.proximo_msg += 1
        self.mensagens.append(
            {
                "id_mensagem": mid,
                "id_reserva": id_reserva,
                "conteudo": conteudo,
                "id_externo": id_externo,
            }
        )
        return mid


def test_evento_novo_grava_mensagem_e_enfileira():
    repo = RepoFake()
    enfileirados = []

    def enfileirar(conexao, *, id_hotel, id_reserva, id_mensagem, id_evento):
        enfileirados.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "id_mensagem": id_mensagem,
                "id_evento": id_evento,
            }
        )
        return 99

    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="w1",
            telefone_origem="11987654321",
            texto="1. Maria",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar=enfileirar,
    )
    assert resultado["status"] == "enfileirado"
    assert len(repo.mensagens) == 1
    assert len(enfileirados) == 1


def test_id_externo_repetido_nao_duplica():
    repo = RepoFake()
    enfileirados = []

    def enfileirar(*args, **kwargs):
        enfileirados.append(1)
        return 1

    evento = EventoEntrada(
        id_externo="w1",
        telefone_origem="11987654321",
        texto="oi",
        tem_texto_utilizavel=True,
    )
    conversa.receber_evento_entrada(
        object(), evento=evento, id_hotel=1, repositorio=repo, enfileirar=enfileirar
    )
    segundo = conversa.receber_evento_entrada(
        object(), evento=evento, id_hotel=1, repositorio=repo, enfileirar=enfileirar
    )
    assert segundo["status"] == "duplicado"
    assert len(repo.mensagens) == 1
    assert len(enfileirados) == 1


def test_receber_nao_chama_llm():
    """Garante que a funcao de recebimento nao recebe porta LLM."""
    import inspect

    sig = inspect.signature(conversa.receber_evento_entrada)
    assert "llm" not in sig.parameters
