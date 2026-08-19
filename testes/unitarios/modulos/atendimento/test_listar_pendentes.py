"""Lista destacada de consumos pendentes de lancamento."""

from datetime import UTC, datetime
from decimal import Decimal

from app.modulos.atendimento import service as atendimento
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL


class Repo:
    def __init__(self, itens):
        self._itens = itens
        self.leituras = []

    def listar_pendentes(self, conexao, *, id_hotel):
        self.leituras.append(id_hotel)
        return [dict(i) for i in self._itens if True]


def test_listar_pendentes_so_pendente_sem_cadastro():
    agora = datetime(2026, 8, 19, tzinfo=UTC)
    repo = Repo(
        [
            {
                "id_solicitacao": 1,
                "id_reserva": 10,
                "descricao": "uma cerveja",
                "descricao_item": NOME_ITEM,
                "numero_quarto": "402",
                "valor_praticado": PRECO_ATUAL,
                "status_lancamento": "pendente",
                "aberta_em": agora,
                "resolvida_em": None,
            }
        ]
    )
    itens = atendimento.listar_pendentes(object(), id_hotel=1, repositorio=repo)
    assert len(itens) == 1
    assert itens[0]["status_lancamento"] == "pendente"
    assert itens[0]["valor_praticado"] == PRECO_ATUAL
    assert itens[0]["descricao_item"] == NOME_ITEM
    assert "nome" not in itens[0]
    assert "telefone" not in itens[0]
    assert repo.leituras == [1]
