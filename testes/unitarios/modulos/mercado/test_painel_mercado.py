"""Painel de mercado: visao atual, situacao e historico. Sem HTTP, sem SQL."""

from datetime import UTC, timedelta
from decimal import Decimal

import pytest

from app.modulos.mercado import service as mercado
from testes.suporte.coleta_mercado import (
    AGORA_PAINEL,
    CHAVE_PERIODICIDADE,
    NOTA_FIXTURE,
    PERIODICIDADE_PADRAO,
    PRECO_FIXTURE,
    SITUACAO_ATUAL,
    SITUACAO_CADENCIA_AUSENTE,
    SITUACAO_DESATUALIZADO,
    SITUACAO_SEM_COLETA,
    SITUACAO_SO_FALHA,
)

ID_HOTEL = 3
ID_A = 10
ID_B = 11


class RepoPainel:
    def __init__(self, fichas=None, sucessos=None, linhas=None, serie=None):
        self.fichas = fichas or []
        self.sucessos = sucessos or {}
        self.linhas = linhas or {}
        self.serie = serie or []
        self.ficha = None

    def listar_manutencao(self, conexao, *, id_hotel):
        return list(self.fichas)

    def ultimos_sucessos(self, conexao, *, id_hotel):
        return dict(self.sucessos)

    def ultimas_linhas(self, conexao, *, id_hotel):
        return dict(self.linhas)

    def listar_serie(self, conexao, *, id_hotel, id_concorrente):
        return list(self.serie)

    def obter(self, conexao, *, id_hotel, id_concorrente):
        return self.ficha


def _parametro(valor=PERIODICIDADE_PADRAO):
    def ler(conexao, id_hotel, chave):
        assert chave == CHAVE_PERIODICIDADE
        return valor

    return ler


def _ficha(id_concorrente=ID_A, nome="Hotel Praia Norte", ativo=True):
    return {
        "id_concorrente": id_concorrente,
        "id_hotel": ID_HOTEL,
        "nome": nome,
        "url_fonte": "https://www.exemplo.com/hotel",
        "ativo": ativo,
    }


def _sucesso(
    id_concorrente=ID_A,
    preco=PRECO_FIXTURE,
    nota_media=NOTA_FIXTURE,
    coletado_em=None,
    id_coleta=1,
):
    return {
        "id_coleta": id_coleta,
        "id_concorrente": id_concorrente,
        "preco": preco,
        "nota_media": nota_media,
        "sucesso": True,
        "coletado_em": coletado_em or AGORA_PAINEL - timedelta(hours=1),
    }


def _falha(id_concorrente=ID_A, coletado_em=None, id_coleta=2):
    return {
        "id_coleta": id_coleta,
        "id_concorrente": id_concorrente,
        "preco": None,
        "nota_media": None,
        "sucesso": False,
        "coletado_em": coletado_em or AGORA_PAINEL,
    }


def test_painel_devolve_ultimo_sucesso_com_data():
    sucesso = _sucesso()
    repo = RepoPainel(
        fichas=[_ficha()],
        sucessos={ID_A: sucesso},
        linhas={ID_A: sucesso},
    )
    painel = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=repo,
        ler_parametro=_parametro(),
    )
    assert painel.periodicidade_horas == 24
    assert len(painel.concorrentes) == 1
    item = painel.concorrentes[0]
    assert item.id_concorrente == ID_A
    assert item.ultimo_sucesso is not None
    assert item.ultimo_sucesso.preco == PRECO_FIXTURE
    assert item.ultimo_sucesso.nota_media == NOTA_FIXTURE
    assert item.ultimo_sucesso.coletado_em == sucesso["coletado_em"]
    assert item.situacao == SITUACAO_ATUAL
    assert item.ultima_falha is None


def test_campo_nao_obtido_fica_vazio_e_zero_permanece_zero():
    so_preco = _sucesso(nota_media=None)
    so_nota = _sucesso(id_concorrente=ID_B, preco=None, id_coleta=3)
    zero = _sucesso(
        id_concorrente=12, preco=Decimal("0.00"), nota_media=None, id_coleta=4
    )
    repo = RepoPainel(
        fichas=[
            _ficha(),
            _ficha(id_concorrente=ID_B, nome="Outro"),
            _ficha(id_concorrente=12, nome="Gratis"),
        ],
        sucessos={ID_A: so_preco, ID_B: so_nota, 12: zero},
        linhas={ID_A: so_preco, ID_B: so_nota, 12: zero},
    )
    painel = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=repo,
        ler_parametro=_parametro(),
    )
    por_id = {item.id_concorrente: item for item in painel.concorrentes}
    assert por_id[ID_A].ultimo_sucesso.preco == PRECO_FIXTURE
    assert por_id[ID_A].ultimo_sucesso.nota_media is None
    assert por_id[ID_B].ultimo_sucesso.preco is None
    assert por_id[ID_B].ultimo_sucesso.nota_media == NOTA_FIXTURE
    assert por_id[12].ultimo_sucesso.preco == Decimal("0.00")
    assert por_id[12].ultimo_sucesso.nota_media is None


def test_nunca_coletado_e_lista_vazia():
    repo = RepoPainel(fichas=[_ficha()], sucessos={}, linhas={})
    painel = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=repo,
        ler_parametro=_parametro(),
    )
    assert painel.concorrentes[0].situacao == SITUACAO_SEM_COLETA
    assert painel.concorrentes[0].ultimo_sucesso is None
    assert painel.concorrentes[0].ultima_falha is None

    vazio = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=RepoPainel(),
        ler_parametro=_parametro(),
    )
    assert vazio.concorrentes == []


def test_falha_nao_substitui_preco_do_sucesso():
    sucesso = _sucesso()
    falha = _falha()
    repo = RepoPainel(
        fichas=[_ficha()],
        sucessos={ID_A: sucesso},
        linhas={ID_A: falha},
    )
    item = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=repo,
        ler_parametro=_parametro(),
    ).concorrentes[0]
    assert item.ultimo_sucesso.preco == PRECO_FIXTURE
    assert item.ultimo_sucesso.coletado_em == sucesso["coletado_em"]
    assert item.ultima_falha is not None
    assert item.ultima_falha.coletado_em == falha["coletado_em"]


def test_so_falhas_nao_inventa_preco():
    falha = _falha()
    repo = RepoPainel(
        fichas=[_ficha()],
        sucessos={},
        linhas={ID_A: falha},
    )
    item = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=repo,
        ler_parametro=_parametro(),
    ).concorrentes[0]
    assert item.situacao == SITUACAO_SO_FALHA
    assert item.ultimo_sucesso is None
    assert item.ultima_falha.coletado_em == falha["coletado_em"]


def test_sucesso_alem_da_janela_fica_desatualizado():
    sucesso = _sucesso(coletado_em=AGORA_PAINEL - timedelta(hours=24))
    repo = RepoPainel(
        fichas=[_ficha()],
        sucessos={ID_A: sucesso},
        linhas={ID_A: sucesso},
    )
    item = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=repo,
        ler_parametro=_parametro(),
    ).concorrentes[0]
    assert item.situacao == SITUACAO_DESATUALIZADO
    assert item.ultimo_sucesso.coletado_em == sucesso["coletado_em"]


def test_falha_posterior_desatualiza_sem_redatar():
    sucesso = _sucesso()
    falha = _falha()
    item = mercado.ler_painel(
        object(),
        id_hotel=ID_HOTEL,
        agora=AGORA_PAINEL,
        repositorio=RepoPainel(
            fichas=[_ficha()],
            sucessos={ID_A: sucesso},
            linhas={ID_A: falha},
        ),
        ler_parametro=_parametro(),
    ).concorrentes[0]
    assert item.situacao == SITUACAO_DESATUALIZADO
    assert item.ultimo_sucesso.preco == PRECO_FIXTURE
    assert item.ultimo_sucesso.coletado_em == sucesso["coletado_em"]


def test_cadencia_ausente_nao_inventa_vinte_e_quatro():
    sucesso = _sucesso()
    repo = RepoPainel(
        fichas=[_ficha()],
        sucessos={ID_A: sucesso},
        linhas={ID_A: sucesso},
    )
    for valor in (None, "", "0", "-1", "abc"):
        painel = mercado.ler_painel(
            object(),
            id_hotel=ID_HOTEL,
            agora=AGORA_PAINEL,
            repositorio=repo,
            ler_parametro=_parametro(valor),
        )
        assert painel.periodicidade_horas is None
        assert painel.concorrentes[0].situacao == SITUACAO_CADENCIA_AUSENTE
        assert painel.concorrentes[0].ultimo_sucesso.preco == PRECO_FIXTURE


def test_historico_em_ordem_crescente_com_falha_intercalada():
    pontos = [
        _sucesso(id_coleta=1, coletado_em=AGORA_PAINEL - timedelta(days=2), preco=Decimal("140.00")),
        _falha(id_coleta=2, coletado_em=AGORA_PAINEL - timedelta(days=1)),
        _sucesso(id_coleta=3, coletado_em=AGORA_PAINEL - timedelta(hours=1)),
    ]
    repo = RepoPainel(serie=pontos)
    repo.ficha = _ficha()
    historico = mercado.ler_historico(
        object(), id_hotel=ID_HOTEL, id_concorrente=ID_A, repositorio=repo
    )
    assert [p.id_coleta for p in historico.coletas] == [1, 2, 3]
    assert historico.coletas[1].sucesso is False
    assert historico.coletas[1].preco is None
    assert historico.coletas[0].preco == Decimal("140.00")
    assert historico.coletas[2].preco == PRECO_FIXTURE


def test_historico_inexistente_ou_alheio_nao_e_encontrado():
    repo = RepoPainel()
    repo.ficha = None
    with pytest.raises(mercado.ConcorrenteNaoEncontrado):
        mercado.ler_historico(
            object(), id_hotel=ID_HOTEL, id_concorrente=99, repositorio=repo
        )
