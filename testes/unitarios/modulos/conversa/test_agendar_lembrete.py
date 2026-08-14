"""Agendamento do lembrete com repositorios falsos."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modulos.conversa import service as conversa


@dataclass
class RepoMensagem:
    mensagens: list = field(default_factory=list)
    proximo: int = 1
    enviada_em: datetime | None = None

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

    def atualizar_status_envio(
        self, conexao, *, id_mensagem, status_envio, id_externo=None, agora=None
    ):
        for mensagem in self.mensagens:
            if mensagem["id_mensagem"] == id_mensagem:
                mensagem["status_envio"] = status_envio
                if status_envio == "enviada":
                    mensagem["enviada_em"] = agora or datetime.now(UTC)


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


def test_agenda_lembrete_cria_mensagem_pendente_e_enfileira():
    repo = RepoMensagem()
    fila = Fila()
    id_mensagem = conversa.agendar_lembrete(
        object(),
        id_hotel=1,
        id_reserva=42,
        nome_completo="Maria Silva",
        repositorio=repo,
        enfileirar=fila,
    )
    assert id_mensagem == 1
    assert "opcional" in repo.mensagens[0]["conteudo"]
    assert "Ola, Maria!" in repo.mensagens[0]["conteudo"]
    assert fila.itens == [{"id_hotel": 1, "id_reserva": 42, "id_mensagem": 1}]


def test_marcar_sucesso_grava_enviada_em():
    repo = RepoMensagem()
    repo.inserir_mensagem_enviada_pendente(object(), id_reserva=1, conteudo="x")
    instante = datetime(2026, 8, 1, 15, 0, tzinfo=UTC)
    repo.atualizar_status_envio(
        object(), id_mensagem=1, status_envio="enviada", agora=instante
    )
    assert repo.mensagens[0]["enviada_em"] == instante
    assert repo.mensagens[0]["status_envio"] == "enviada"
