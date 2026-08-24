"""Anonimizacao de mensagem e payload: marca no vencido, linha permanece."""

from datetime import UTC, datetime

from app.comum.retencao import MARCA_PAYLOAD, MARCA_TEXTO, vencido_em_meses
from app.modulos.conversa import service as conversa

AGORA = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
CHECKOUT_VENCIDO = datetime(2025, 7, 24, 12, 0, tzinfo=UTC)
CHECKOUT_DENTRO = datetime(2025, 9, 24, 12, 0, tzinfo=UTC)


class RepoConversa:
    def __init__(self, reservas, mensagens, payloads):
        self.reservas = reservas
        self.mensagens = mensagens
        self.payloads = payloads
        self.deletes = []

    def delete(self, *args, **kwargs):
        self.deletes.append((args, kwargs))

    def anonimizar_mensagens_vencidas(
        self, conexao, *, id_hotel, agora, meses, marca
    ):
        afetadas = 0
        for mensagem in self.mensagens:
            reserva = self.reservas[mensagem["id_reserva"]]
            if reserva["id_hotel"] != id_hotel:
                continue
            if not vencido_em_meses(reserva.get("checkout_em"), agora, meses):
                continue
            if mensagem["conteudo"] == marca:
                continue
            mensagem["conteudo"] = marca
            mensagem["classificacao_bruta"] = None
            afetadas += 1
        return afetadas

    def anonimizar_payloads_vencidos(
        self, conexao, *, id_hotel, agora, meses, marca_json
    ):
        import json

        marca = json.loads(marca_json)
        externos = set()
        for mensagem in self.mensagens:
            reserva = self.reservas[mensagem["id_reserva"]]
            if reserva["id_hotel"] != id_hotel:
                continue
            if not vencido_em_meses(reserva.get("checkout_em"), agora, meses):
                continue
            if mensagem.get("id_externo"):
                externos.add(mensagem["id_externo"])
        afetados = 0
        for evento in self.payloads:
            if evento["id_externo"] not in externos:
                continue
            if evento["payload"] == marca:
                continue
            evento["payload"] = marca
            afetados += 1
        return afetados


def _repo_vencido():
    return RepoConversa(
        reservas={
            1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO},
            2: {"id_hotel": 10, "checkout_em": CHECKOUT_DENTRO},
            3: {"id_hotel": 99, "checkout_em": CHECKOUT_VENCIDO},
        },
        mensagens=[
            {
                "id_reserva": 1,
                "conteudo": "ar condicionado barulhento",
                "classificacao_bruta": {"eco": "ar condicionado barulhento"},
                "intencao": "reclamacao_tecnica",
                "sentimento": "negativo",
                "urgencia": "alta",
                "id_externo": "evt-1",
            },
            {
                "id_reserva": 2,
                "conteudo": "ainda dentro do prazo",
                "classificacao_bruta": {"eco": "ainda"},
                "intencao": "duvida_geral",
                "sentimento": "neutro",
                "urgencia": "baixa",
                "id_externo": "evt-2",
            },
            {
                "id_reserva": 3,
                "conteudo": "outro hotel",
                "classificacao_bruta": {"eco": "outro"},
                "intencao": "duvida_geral",
                "sentimento": "neutro",
                "urgencia": "baixa",
                "id_externo": "evt-3",
            },
        ],
        payloads=[
            {"id_externo": "evt-1", "payload": {"texto": "ar condicionado barulhento"}},
            {"id_externo": "evt-2", "payload": {"texto": "ainda dentro do prazo"}},
            {"id_externo": "evt-orfao", "payload": {"texto": "sem mensagem"}},
        ],
    )


def test_reserva_vencida_anonimiza_conteudo_e_zera_classificacao_bruta():
    repo = _repo_vencido()

    afetadas = conversa.anonimizar_mensagens_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetadas == 1
    vencida = repo.mensagens[0]
    assert vencida["conteudo"] == MARCA_TEXTO
    assert vencida["classificacao_bruta"] is None
    assert vencida["intencao"] == "reclamacao_tecnica"
    assert vencida["sentimento"] == "negativo"
    assert vencida["urgencia"] == "alta"


def test_mensagem_enviada_da_reserva_vencida_tambem_e_anonimizada():
    repo = RepoConversa(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        mensagens=[
            {
                "id_reserva": 1,
                "direcao": "enviada",
                "conteudo": "recebemos seu pedido de toalha",
                "classificacao_bruta": None,
                "intencao": None,
                "sentimento": None,
                "urgencia": None,
                "id_externo": None,
            }
        ],
        payloads=[],
    )

    afetadas = conversa.anonimizar_mensagens_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetadas == 1
    assert repo.mensagens[0]["conteudo"] == MARCA_TEXTO
    assert repo.mensagens[0]["direcao"] == "enviada"


def test_mensagem_ja_marcada_nao_conta_de_novo():
    repo = _repo_vencido()
    conversa.anonimizar_mensagens_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    segunda = conversa.anonimizar_mensagens_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert segunda == 0


def test_payload_casa_por_id_externo_e_orfao_nao_e_tocado():
    repo = _repo_vencido()

    afetados = conversa.anonimizar_payloads_vencidos(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetados == 1
    assert repo.payloads[0]["payload"] == MARCA_PAYLOAD
    assert repo.payloads[1]["payload"] == {"texto": "ainda dentro do prazo"}
    assert repo.payloads[2]["payload"] == {"texto": "sem mensagem"}


def test_anonimizar_mensagem_nao_apaga_linha():
    repo = _repo_vencido()

    conversa.anonimizar_mensagens_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert len(repo.mensagens) == 3
    assert repo.deletes == []
