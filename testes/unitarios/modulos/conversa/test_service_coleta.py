"""Agendamento de coleta com repositorios falsos."""

from dataclasses import dataclass, field

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
                "direcao": "enviada",
            }
        )
        return id_mensagem

    def listar_mensagens_da_reserva(self, conexao, *, id_reserva):
        return [m for m in self.mensagens if m["id_reserva"] == id_reserva]


@dataclass
class RepoParametro:
    valores: dict

    def ler_parametro(self, conexao, id_hotel, chave):
        return self.valores.get((id_hotel, chave))


@dataclass
class Fila:
    itens: list = field(default_factory=list)

    def __call__(self, conexao, *, id_hotel, id_reserva, id_mensagem):
        self.itens.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "id_mensagem": id_mensagem,
            }
        )
        return len(self.itens)


@dataclass
class GatewayEspiao:
    chamadas: list = field(default_factory=list)

    def enviar_coleta(self, **kwargs):
        self.chamadas.append(kwargs)
        raise AssertionError("agendar nao deve chamar mensageria")


def test_agenda_cria_mensagem_pendente_e_enfileira_sem_chamar_gateway():
    repo = RepoMensagem()
    fila = Fila()
    params = RepoParametro(valores={(1, "contato_responsavel_dados"): "5511999990001"})
    id_mensagem = conversa.agendar_coleta_apos_reserva(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=repo,
        repositorio_propriedade=params,
        enfileirar=fila,
    )
    assert id_mensagem == 1
    assert len(repo.mensagens) == 1
    assert repo.mensagens[0]["status_envio"] == "pendente"
    assert "Ola, Maria!" in repo.mensagens[0]["conteudo"]
    assert fila.itens == [{"id_hotel": 1, "id_reserva": 42, "id_mensagem": 1}]
