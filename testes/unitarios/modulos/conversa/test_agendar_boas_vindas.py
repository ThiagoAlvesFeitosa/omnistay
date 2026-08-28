"""Agendamento do recado de boas-vindas com dependencias falsas."""

from dataclasses import dataclass, field

from sqlalchemy.exc import IntegrityError

from app.modulos.conversa import service as conversa


@dataclass
class RepoMensagem:
    mensagens: list = field(default_factory=list)
    proximo: int = 1

    def inserir_mensagem_enviada_pendente(self, conexao, *, id_reserva, conteudo):
        id_mensagem = self.proximo
        self.proximo += 1
        self.mensagens.append(
            {
                "id_mensagem": id_mensagem,
                "id_reserva": id_reserva,
                "conteudo": conteudo,
                "status_envio": "pendente",
            }
        )
        return id_mensagem


class RepoPropriedade:
    def __init__(self, valores):
        self.valores = dict(valores)

    def ler_parametros(self, conexao, id_hotel, chaves):
        return {
            chave: self.valores[chave]
            for chave in chaves
            if chave in self.valores
        }


class Fila:
    def __init__(self, falhar=False):
        self.itens = []
        self.falhar = falhar

    def __call__(self, conexao, *, id_hotel, id_reserva, id_mensagem):
        if self.falhar:
            raise IntegrityError("dup", {}, Exception())
        self.itens.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "id_mensagem": id_mensagem,
            }
        )
        return len(self.itens)


SLOTS_OK = {
    "boas_vindas_cafe": "Cafe das 7h as 10h",
    "boas_vindas_wifi": "rede Hotel",
    "boas_vindas_checkout": "ate as 12h",
    "boas_vindas_convite": "Pode perguntar sobre o spa.",
}


def test_slots_validos_inserem_mensagem_e_enfileiram():
    repo = RepoMensagem()
    fila = Fila()
    desfecho = conversa.agendar_boas_vindas(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=repo,
        repositorio_propriedade=RepoPropriedade(SLOTS_OK),
        enfileirar=fila,
    )
    assert desfecho == "agendada"
    assert len(repo.mensagens) == 1
    assert "Cafe das 7h as 10h" in repo.mensagens[0]["conteudo"]
    assert fila.itens == [{"id_hotel": 1, "id_reserva": 42, "id_mensagem": 1}]


def test_slot_ausente_nao_grava_nada():
    repo = RepoMensagem()
    fila = Fila()
    incompleto = dict(SLOTS_OK)
    del incompleto["boas_vindas_wifi"]
    desfecho = conversa.agendar_boas_vindas(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=repo,
        repositorio_propriedade=RepoPropriedade(incompleto),
        enfileirar=fila,
    )
    assert desfecho == "nao_enviada_slot_ausente"
    assert repo.mensagens == []
    assert fila.itens == []


def test_convite_ausente_nao_grava_e_loga_so_a_chave(monkeypatch):
    repo = RepoMensagem()
    fila = Fila()
    incompleto = dict(SLOTS_OK)
    del incompleto["boas_vindas_convite"]
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    desfecho = conversa.agendar_boas_vindas(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=repo,
        repositorio_propriedade=RepoPropriedade(incompleto),
        enfileirar=fila,
    )
    assert desfecho == "nao_enviada_slot_ausente"
    assert repo.mensagens == []
    assert fila.itens == []
    texto = " ".join(registros)
    assert "chave=boas_vindas_convite" in texto
    assert SLOTS_OK["boas_vindas_convite"] not in texto
    assert "Pode perguntar sobre o spa." not in texto


def test_integridade_do_indice_devolve_ja_agendada():
    repo = RepoMensagem()
    fila = Fila(falhar=True)
    desfecho = conversa.agendar_boas_vindas(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=repo,
        repositorio_propriedade=RepoPropriedade(SLOTS_OK),
        enfileirar=fila,
    )
    assert desfecho == "ja_agendada"
    assert fila.itens == []
