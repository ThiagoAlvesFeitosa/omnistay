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
        self.reserva_hospedada = None
        self.reserva_pesquisa = None
        self.reserva_encerrada = None

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

    def resolver_reserva_hospedada(self, conexao, *, id_hotel, telefone_contato):
        if self.reserva_hospedada and telefone_contato == "5511987654321":
            return self.reserva_hospedada
        return None

    def resolver_reserva_encerrada_pesquisa(
        self, conexao, *, id_hotel, telefone_contato
    ):
        if self.reserva_pesquisa and telefone_contato == "5511987654321":
            return self.reserva_pesquisa
        return None

    def resolver_reserva_encerrada(self, conexao, *, id_hotel, telefone_contato):
        if self.reserva_encerrada and telefone_contato == "5511987654321":
            return self.reserva_encerrada
        return None

    def gravar_classificacao_bruta(self, conexao, *, id_mensagem, classificacao):
        for mensagem in self.mensagens:
            if mensagem["id_mensagem"] == id_mensagem:
                mensagem["classificacao"] = classificacao

    def inserir_mensagem_recebida(
        self, conexao, *, id_reserva, conteudo, id_externo=None, enviada_em=None
    ):
        mid = self.proximo_msg
        self.proximo_msg += 1
        self.mensagens.append(
            {
                "id_mensagem": mid,
                "id_reserva": id_reserva,
                "conteudo": conteudo,
                "id_externo": id_externo,
                "enviada_em": enviada_em,
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
    assert "gateway" not in sig.parameters


def test_hospedado_grava_mensagem_e_enfileira_estadia():
    repo = RepoFake()
    repo.reserva = None
    repo.reserva_hospedada = {
        "id_reserva": 20,
        "id_hotel": 1,
        "status": "hospedado",
    }
    fichas = []
    estadias = []

    def enfileirar_ficha(*args, **kwargs):
        fichas.append(1)
        return 1

    def enfileirar_estadia(conexao, *, id_hotel, id_reserva, id_mensagem, id_evento):
        estadias.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "id_mensagem": id_mensagem,
                "id_evento": id_evento,
            }
        )
        return 50

    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="est-1",
            telefone_origem="11987654321",
            texto="o ar nao gela",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar=enfileirar_ficha,
        enfileirar_estadia=enfileirar_estadia,
    )
    assert resultado["status"] == "enfileirado"
    assert resultado["id_reserva"] == 20
    assert len(repo.mensagens) == 1
    assert repo.mensagens[0]["conteudo"] == "o ar nao gela"
    assert len(estadias) == 1
    assert fichas == []


def test_aguardando_cadastro_prevalece_sobre_hospedado():
    repo = RepoFake()
    repo.reserva_hospedada = {
        "id_reserva": 20,
        "id_hotel": 1,
        "status": "hospedado",
    }
    fichas = []
    estadias = []

    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="ambos",
            telefone_origem="11987654321",
            texto="1. Maria",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar=lambda *a, **k: fichas.append(1) or 1,
        enfileirar_estadia=lambda *a, **k: estadias.append(1) or 1,
    )
    assert resultado["status"] == "enfileirado"
    assert resultado["id_reserva"] == 10
    assert len(fichas) == 1
    assert estadias == []


def test_telefone_sem_reserva_elegivel_nao_grava_mensagem():
    repo = RepoFake()
    repo.reserva = None
    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="orfao",
            telefone_origem="11987654321",
            texto="oi",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar=lambda *a, **k: 1,
        enfileirar_estadia=lambda *a, **k: 1,
    )
    assert resultado["status"] == "sem_reserva"
    assert repo.mensagens == []


def test_midia_sem_texto_nao_enfileira_estadia():
    repo = RepoFake()
    repo.reserva = None
    repo.reserva_hospedada = {
        "id_reserva": 20,
        "id_hotel": 1,
        "status": "hospedado",
    }
    estadias = []
    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="midia",
            telefone_origem="11987654321",
            texto="",
            tem_texto_utilizavel=False,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar_estadia=lambda *a, **k: estadias.append(1) or 1,
    )
    assert resultado["status"] == "sem_texto"
    assert repo.mensagens == []
    assert estadias == []


def test_hospedado_id_externo_repetido_nao_duplica():
    repo = RepoFake()
    repo.reserva = None
    repo.reserva_hospedada = {
        "id_reserva": 20,
        "id_hotel": 1,
        "status": "hospedado",
    }
    estadias = []
    evento = EventoEntrada(
        id_externo="dup-est",
        telefone_origem="11987654321",
        texto="toalha",
        tem_texto_utilizavel=True,
    )
    conversa.receber_evento_entrada(
        object(),
        evento=evento,
        id_hotel=1,
        repositorio=repo,
        enfileirar_estadia=lambda *a, **k: estadias.append(1) or 1,
    )
    segundo = conversa.receber_evento_entrada(
        object(),
        evento=evento,
        id_hotel=1,
        repositorio=repo,
        enfileirar_estadia=lambda *a, **k: estadias.append(1) or 1,
    )
    assert segundo["status"] == "duplicado"
    assert len(repo.mensagens) == 1
    assert len(estadias) == 1


def test_encerrada_com_pesquisa_incompleta_enfileira_interpretacao():
    repo = RepoFake()
    repo.reserva = None
    repo.reserva_pesquisa = {
        "id_reserva": 30,
        "id_hotel": 1,
        "status": "encerrado",
    }
    pesquisas = []
    estadias = []

    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="ps-1",
            telefone_origem="11987654321",
            texto="5 e sim",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar=lambda *a, **k: 1,
        enfileirar_estadia=lambda *a, **k: estadias.append(1) or 1,
        enfileirar_pesquisa=lambda *a, **k: pesquisas.append(k) or 9,
    )
    assert resultado["status"] == "enfileirado"
    assert resultado["id_reserva"] == 30
    assert len(pesquisas) == 1
    assert pesquisas[0]["id_reserva"] == 30
    assert "id_evento" not in pesquisas[0]
    assert estadias == []


def test_encerrada_sem_pesquisa_grava_mensagem_sem_trabalho():
    repo = RepoFake()
    repo.reserva = None
    repo.reserva_encerrada = {
        "id_reserva": 40,
        "id_hotel": 1,
        "status": "encerrado",
    }
    pesquisas = []

    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="ps-2",
            telefone_origem="11987654321",
            texto="oi",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar_pesquisa=lambda *a, **k: pesquisas.append(1) or 1,
    )
    assert resultado["status"] == "registrada"
    assert len(repo.mensagens) == 1
    assert pesquisas == []


def test_ficha_prevalece_sobre_pesquisa_pendente():
    repo = RepoFake()
    repo.reserva_pesquisa = {
        "id_reserva": 30,
        "id_hotel": 1,
        "status": "encerrado",
    }
    fichas = []
    pesquisas = []

    resultado = conversa.receber_evento_entrada(
        object(),
        evento=EventoEntrada(
            id_externo="ambos-ps",
            telefone_origem="11987654321",
            texto="1. Maria",
            tem_texto_utilizavel=True,
        ),
        id_hotel=1,
        repositorio=repo,
        enfileirar=lambda *a, **k: fichas.append(1) or 1,
        enfileirar_pesquisa=lambda *a, **k: pesquisas.append(1) or 1,
    )
    assert resultado["id_reserva"] == 10
    assert len(fichas) == 1
    assert pesquisas == []
