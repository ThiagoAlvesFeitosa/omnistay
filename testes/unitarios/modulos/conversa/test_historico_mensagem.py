"""Historico de mensagens da reserva."""

from dataclasses import dataclass, field

from app.modulos.conversa import service as conversa


@dataclass
class Repo:
    mensagens: list = field(default_factory=list)
    proximo: int = 1

    def inserir_mensagem_enviada_pendente(self, conexao, *, id_reserva, conteudo):
        id_m = self.proximo
        self.proximo += 1
        self.mensagens.append(
            {
                "id_mensagem": id_m,
                "id_reserva": id_reserva,
                "direcao": "enviada",
                "conteudo": conteudo,
                "status_envio": "pendente",
                "id_externo": None,
            }
        )
        return id_m

    def atualizar_status_envio(self, conexao, *, id_mensagem, status_envio, id_externo=None):
        for m in self.mensagens:
            if m["id_mensagem"] == id_mensagem:
                m["status_envio"] = status_envio
                if id_externo is not None:
                    m["id_externo"] = id_externo

    def listar_mensagens_da_reserva(self, conexao, *, id_reserva):
        return [m for m in self.mensagens if m["id_reserva"] == id_reserva]


@dataclass
class Params:
    def ler_parametro(self, conexao, id_hotel, chave):
        return "5511999990001"


def test_apos_agendar_existe_mensagem_de_saida_pendente():
    repo = Repo()

    def enfileirar(*a, **k):
        return 1

    conversa.agendar_coleta_apos_reserva(
        object(),
        id_hotel=1,
        id_reserva=10,
        nome_completo="Maria",
        repositorio=repo,
        repositorio_propriedade=Params(),
        enfileirar=enfileirar,
    )
    lista = repo.listar_mensagens_da_reserva(object(), id_reserva=10)
    assert len(lista) == 1
    assert lista[0]["direcao"] == "enviada"
    assert lista[0]["status_envio"] == "pendente"

    conversa.marcar_envio_sucesso(
        object(), id_mensagem=1, id_externo="x", repositorio=repo
    )
    assert repo.listar_mensagens_da_reserva(object(), id_reserva=10)[0][
        "status_envio"
    ] == "enviada"
