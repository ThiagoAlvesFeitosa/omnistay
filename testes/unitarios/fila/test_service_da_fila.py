"""Fila: reagendar, falha definitiva e reclaim."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.fila import service as fila_service


@dataclass
class RepoFila:
    falhas: list = field(default_factory=list)
    reagendamentos: list = field(default_factory=list)

    def marcar_falha(self, conexao, *, id_trabalho, tentativas, erro):
        self.falhas.append(
            {"id_trabalho": id_trabalho, "tentativas": tentativas, "erro": erro}
        )

    def reagendar(self, conexao, *, id_trabalho, tentativas, erro, proxima_tentativa_em):
        self.reagendamentos.append(
            {
                "id_trabalho": id_trabalho,
                "tentativas": tentativas,
                "erro": erro,
                "proxima": proxima_tentativa_em,
            }
        )


@dataclass
class RepoParam:
    valor: str | None = "3"

    def ler_parametro(self, conexao, id_hotel, chave):
        return self.valor


@dataclass
class RepoParamPorHotel:
    valores: dict

    def ler_parametro(self, conexao, id_hotel, chave):
        return self.valores.get(id_hotel)


def test_falha_abaixo_do_teto_reagenda():
    repo = RepoFila()
    destino = fila_service.registrar_falha_de_envio(
        object(),
        id_trabalho=1,
        id_hotel=10,
        tentativas_atuais=0,
        codigo_erro="mensageria_indisponivel",
        repositorio=repo,
        repositorio_propriedade=RepoParam("3"),
    )
    assert destino == "reagendado"
    assert len(repo.reagendamentos) == 1
    assert repo.reagendamentos[0]["tentativas"] == 1
    assert repo.falhas == []


def test_falha_no_teto_marca_falha_definitiva():
    repo = RepoFila()
    destino = fila_service.registrar_falha_de_envio(
        object(),
        id_trabalho=1,
        id_hotel=10,
        tentativas_atuais=2,
        codigo_erro="mensageria_indisponivel",
        repositorio=repo,
        repositorio_propriedade=RepoParam("3"),
    )
    assert destino == "falha"
    assert repo.falhas[0]["tentativas"] == 3
    assert "mensageria" in repo.falhas[0]["erro"]
    assert repo.reagendamentos == []


def test_backoff_cresce_com_tentativas():
    a = fila_service.backoff_apos(1)
    b = fila_service.backoff_apos(3)
    assert b > a
    assert a > datetime.now(UTC)
    assert isinstance(b - a, timedelta)


def test_teto_ausente_usa_padrao_cinco():
    teto = fila_service.tentativas_maximas(
        object(),
        id_hotel=10,
        repositorio_propriedade=RepoParam(None),
    )
    assert teto == 5


def test_teto_ilegivel_usa_padrao_cinco():
    teto = fila_service.tentativas_maximas(
        object(),
        id_hotel=10,
        repositorio_propriedade=RepoParam("abc"),
    )
    assert teto == 5


def test_teto_numerico_da_propriedade_e_respeitado():
    teto = fila_service.tentativas_maximas(
        object(),
        id_hotel=10,
        repositorio_propriedade=RepoParam("7"),
    )
    assert teto == 7


def test_teto_e_o_da_propriedade_do_trabalho():
    repo = RepoParamPorHotel({10: "3", 20: "9"})
    assert (
        fila_service.tentativas_maximas(
            object(), id_hotel=10, repositorio_propriedade=repo
        )
        == 3
    )
    assert (
        fila_service.tentativas_maximas(
            object(), id_hotel=20, repositorio_propriedade=repo
        )
        == 9
    )
