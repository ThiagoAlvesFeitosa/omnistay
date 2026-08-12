"""Servico da fila do dia — hotel da sessao."""

from datetime import date

from app.modulos.hospedagem import service as hospedagem


class Repositorio:
    def __init__(self, itens):
        self.itens = itens
        self.chamadas = []

    def listar_fila_do_hotel(self, conexao, *, id_hotel):
        self.chamadas.append(id_hotel)
        return [item for item in self.itens if item["id_hotel"] == id_hotel]


def test_fila_consulta_apenas_hotel_da_sessao_e_preserva_ordem():
    repo = Repositorio(
        [
            {
                "id_hotel": 10,
                "id_reserva": 1,
                "nome_completo": "Antes",
                "telefone_contato": "5511888888888",
                "data_checkin_prevista": date(2026, 8, 20),
                "data_checkout_prevista": date(2026, 8, 21),
                "status": "aguardando_cadastro",
                "ficha_completa": False,
                "chegada_nao_confirmada": False,
            },
            {
                "id_hotel": 10,
                "id_reserva": 2,
                "nome_completo": "Depois",
                "telefone_contato": "5511999999999",
                "data_checkin_prevista": date(2026, 8, 21),
                "data_checkout_prevista": date(2026, 8, 22),
                "status": "aguardando_cadastro",
                "ficha_completa": False,
                "chegada_nao_confirmada": False,
            },
            {
                "id_hotel": 20,
                "id_reserva": 3,
                "nome_completo": "Outro",
                "telefone_contato": "5511777777777",
                "data_checkin_prevista": date(2026, 8, 19),
                "data_checkout_prevista": date(2026, 8, 20),
                "status": "aguardando_cadastro",
                "ficha_completa": False,
                "chegada_nao_confirmada": False,
            },
        ]
    )

    itens = hospedagem.listar_fila_do_dia(
        conexao=object(), id_hotel=10, repositorio=repo
    )

    assert repo.chamadas == [10]
    assert [i.nome for i in itens] == ["Antes", "Depois"]
