"""Cadastro de item vendavel com repositorio falso."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modulos.propriedade import service as propriedade
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL


@dataclass
class Repositorio:
    itens: list = field(default_factory=list)
    proximo: int = 1

    def inserir_item_vendavel(self, conexao, *, id_hotel, nome, preco_atual):
        item = {
            "id_item_vendavel": self.proximo,
            "id_hotel": id_hotel,
            "nome": nome,
            "preco_atual": preco_atual,
            "ativo": True,
            "atualizado_em": datetime(2026, 8, 19, tzinfo=UTC),
        }
        self.proximo += 1
        self.itens.append(item)
        return item

    def atualizar_item_vendavel(
        self,
        conexao,
        *,
        id_hotel,
        id_item_vendavel,
        nome=None,
        preco_atual=None,
        ativo=None,
    ):
        for item in self.itens:
            if item["id_item_vendavel"] == id_item_vendavel and item["id_hotel"] == id_hotel:
                if nome is not None:
                    item["nome"] = nome
                if preco_atual is not None:
                    item["preco_atual"] = preco_atual
                if ativo is not None:
                    item["ativo"] = ativo
                return dict(item)
        return None

    def listar_itens_vendaveis_manutencao(self, conexao, *, id_hotel):
        return [dict(i) for i in self.itens if i["id_hotel"] == id_hotel]

    def listar_itens_vendaveis_ativos(self, conexao, *, id_hotel):
        return [
            {"id_item_vendavel": i["id_item_vendavel"], "nome": i["nome"]}
            for i in self.itens
            if i["id_hotel"] == id_hotel and i["ativo"]
        ]

    def ler_preco_item_ativo(self, conexao, *, id_hotel, id_item_vendavel):
        for item in self.itens:
            if (
                item["id_item_vendavel"] == id_item_vendavel
                and item["id_hotel"] == id_hotel
                and item["ativo"]
            ):
                return item["preco_atual"]
        return None

    def existe_nome_ativo(self, conexao, *, id_hotel, nome, exceto_id=None):
        alvo = nome.casefold()
        for item in self.itens:
            if (
                item["id_hotel"] == id_hotel
                and item["ativo"]
                and item["nome"].casefold() == alvo
                and item["id_item_vendavel"] != exceto_id
            ):
                return True
        return False


def test_criar_e_listar_ativos_devolve_id_e_nome_sem_preco():
    repo = Repositorio()
    criado = propriedade.criar_item_vendavel(
        object(),
        id_hotel=1,
        nome=NOME_ITEM,
        preco_atual=PRECO_ATUAL,
        repositorio=repo,
    )
    ativos = propriedade.listar_itens_vendaveis_ativos(
        object(), id_hotel=1, repositorio=repo
    )
    assert criado.nome == NOME_ITEM
    assert criado.preco_atual == PRECO_ATUAL
    assert ativos == ((criado.id_item_vendavel, NOME_ITEM),)
    assert all(len(par) == 2 for par in ativos)


def test_inativo_nao_entra_em_ativos_e_hotel_b_nao_ve_a():
    repo = Repositorio()
    propriedade.criar_item_vendavel(
        object(),
        id_hotel=1,
        nome=NOME_ITEM,
        preco_atual=PRECO_ATUAL,
        repositorio=repo,
    )
    propriedade.criar_item_vendavel(
        object(),
        id_hotel=2,
        nome="Agua",
        preco_atual=Decimal("5.00"),
        repositorio=repo,
    )
    propriedade.atualizar_item_vendavel(
        object(),
        id_hotel=1,
        id_item_vendavel=1,
        ativo=False,
        repositorio=repo,
    )
    assert propriedade.listar_itens_vendaveis_ativos(
        object(), id_hotel=1, repositorio=repo
    ) == ()
    assert propriedade.listar_itens_vendaveis_ativos(
        object(), id_hotel=2, repositorio=repo
    ) == ((2, "Agua"),)
    manutencao = propriedade.listar_itens_vendaveis_manutencao(
        object(), id_hotel=1, repositorio=repo
    )
    assert len(manutencao) == 1
    assert manutencao[0].ativo is False


def test_preco_negativo_e_nome_vazio_sao_recusados():
    repo = Repositorio()
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.criar_item_vendavel(
            object(),
            id_hotel=1,
            nome=NOME_ITEM,
            preco_atual=Decimal("-0.01"),
            repositorio=repo,
        )
    with pytest.raises(propriedade.DadosInvalidos):
        propriedade.criar_item_vendavel(
            object(),
            id_hotel=1,
            nome="   ",
            preco_atual=PRECO_ATUAL,
            repositorio=repo,
        )
    assert repo.itens == []
