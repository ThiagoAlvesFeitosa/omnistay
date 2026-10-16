"""Walker estrutural do Artigo XIV — inventario falso, sem banco."""

from testes.suporte.artigo_xiv import EXCECOES, tabelas_sem_dono


def _tabela(*, colunas=(), fks=()):
    return {"colunas": set(colunas), "fks": list(fks)}


def test_tabela_so_referenciada_sem_id_hotel_entra_na_lista():
    inventario = {
        "hotel": _tabela(colunas=("id_hotel",)),
        "hospede": _tabela(colunas=("id_hospede",)),
        "reserva": _tabela(
            colunas=("id_hotel",),
            fks=({"tabela": "hotel", "nula": False},),
        ),
        "reserva_hospede": _tabela(
            fks=(
                {"tabela": "reserva", "nula": False},
                {"tabela": "hospede", "nula": False},
            ),
        ),
    }

    assert "hospede" in tabelas_sem_dono(inventario)


def test_tabela_com_id_hotel_nao_entra_na_lista():
    inventario = {
        "hotel": _tabela(colunas=("id_hotel",)),
        "hospede": _tabela(colunas=("id_hospede", "id_hotel")),
    }

    assert "hospede" not in tabelas_sem_dono(inventario)


def test_filha_por_fk_obrigatoria_nao_entra_na_lista():
    inventario = {
        "hotel": _tabela(colunas=("id_hotel",)),
        "hospede": _tabela(colunas=("id_hospede", "id_hotel")),
        "consentimento": _tabela(
            fks=({"tabela": "hospede", "nula": False},),
        ),
    }

    assert "consentimento" not in tabelas_sem_dono(inventario)


def test_excecoes_nomeadas_nao_entram_na_lista():
    inventario = {
        "hotel": _tabela(colunas=("id_hotel",)),
        "alembic_version": _tabela(colunas=("version_num",)),
        "evento_webhook": _tabela(colunas=("id_externo",)),
    }

    reprovadas = tabelas_sem_dono(inventario)
    assert "alembic_version" not in reprovadas
    assert "evento_webhook" not in reprovadas
    assert "alembic_version" in EXCECOES
    assert "evento_webhook" in EXCECOES
