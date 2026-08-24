"""Varredura de retencao: prazos, comprovante, skip do dia e log sem texto."""

from datetime import UTC, datetime

from app.comum.retencao import CHAVE_ANOS, CHAVE_MESES
from worker import agendador

AGORA = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


class RepoPropriedade:
    def __init__(self, ids, parametros, ja_executou=False):
        self.ids = ids
        self.parametros = parametros
        self.ja_executou = ja_executou
        self.registros = []

    def listar_ids_hotel(self, conexao):
        return list(self.ids)

    def ja_executou_retencao_no_dia(self, conexao, *, id_hotel, agora):
        if isinstance(self.ja_executou, dict):
            return bool(self.ja_executou.get(id_hotel))
        return bool(self.ja_executou)

    def ler_parametro(self, conexao, id_hotel, chave):
        return self.parametros.get((id_hotel, chave))

    def registrar_execucao_retencao(self, conexao, **kwargs):
        self.registros.append(kwargs)
        return len(self.registros)


class Espiao:
    def __init__(self, retorno=1):
        self.chamadas = []
        self.retorno = retorno

    def __call__(self, conexao, *, id_hotel, agora, meses=None, anos=None):
        self.chamadas.append(
            {
                "id_hotel": id_hotel,
                "agora": agora,
                "meses": meses,
                "anos": anos,
            }
        )
        return self.retorno


def _prazos_validos(id_hotel=10):
    return {
        (id_hotel, CHAVE_MESES): "12",
        (id_hotel, CHAVE_ANOS): "5",
    }


def test_passagem_com_prazos_validos_grava_comprovante_e_nao_loga_texto(monkeypatch):
    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(agendador.logger, "info", fake_info)
    repo = RepoPropriedade([10], _prazos_validos())
    mensagens = Espiao(3)
    payloads = Espiao(2)
    descricoes = Espiao(1)
    comentarios = Espiao(1)
    fichas = Espiao(0)

    n = agendador.verificar_retencao(
        object(),
        agora=AGORA,
        repositorio_propriedade=repo,
        anonimizar_mensagens=mensagens,
        anonimizar_payloads=payloads,
        anonimizar_descricoes=descricoes,
        anonimizar_comentarios=comentarios,
        apagar_fichas=fichas,
    )

    assert n == 1
    assert mensagens.chamadas[0]["id_hotel"] == 10
    assert mensagens.chamadas[0]["meses"] == 12
    assert fichas.chamadas[0]["anos"] == 5
    gravado = repo.registros[0]
    assert gravado["mensagens_anonimizadas"] == 3
    assert gravado["payloads_anonimizados"] == 2
    assert gravado["descricoes_anonimizadas"] == 1
    assert gravado["comentarios_anonimizados"] == 1
    assert gravado["prazo_conteudo_ausente"] is False
    texto = " ".join(registros)
    assert "retencao_aplicada" in texto
    assert "id_hotel=10" in texto
    assert "ar condicionado" not in texto
    assert "5511" not in texto


def test_chave_ausente_nao_trata_conteudo_nem_inventa_doze_meses(monkeypatch):
    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(agendador.logger, "info", fake_info)
    repo = RepoPropriedade(
        [10],
        {(10, CHAVE_ANOS): "5"},
    )
    mensagens = Espiao()
    n = agendador.verificar_retencao(
        object(),
        agora=AGORA,
        repositorio_propriedade=repo,
        anonimizar_mensagens=mensagens,
        anonimizar_payloads=Espiao(),
        anonimizar_descricoes=Espiao(),
        anonimizar_comentarios=Espiao(),
        apagar_fichas=Espiao(0),
    )

    assert n == 1
    assert mensagens.chamadas == []
    assert repo.registros[0]["prazo_conteudo_ausente"] is True
    assert repo.registros[0]["mensagens_anonimizadas"] == 0
    texto = " ".join(registros)
    assert "prazo_conteudo_ausente" in texto


def test_chave_zero_ou_nao_numerica_nao_usa_default(monkeypatch):
    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(agendador.logger, "info", fake_info)
    repo = RepoPropriedade(
        [10],
        {(10, CHAVE_MESES): "0", (10, CHAVE_ANOS): "abc"},
    )
    mensagens = Espiao()
    fichas = Espiao()
    agendador.verificar_retencao(
        object(),
        agora=AGORA,
        repositorio_propriedade=repo,
        anonimizar_mensagens=mensagens,
        anonimizar_payloads=Espiao(),
        anonimizar_descricoes=Espiao(),
        anonimizar_comentarios=Espiao(),
        apagar_fichas=fichas,
    )

    assert mensagens.chamadas == []
    assert fichas.chamadas == []
    assert repo.registros[0]["prazo_conteudo_ausente"] is True
    assert repo.registros[0]["prazo_ficha_ausente"] is True
    texto = " ".join(registros)
    assert "prazo_conteudo_ausente" in texto
    assert "prazo_ficha_ausente" in texto


def test_ja_executou_hoje_nao_trata_e_loga_codigo(monkeypatch):
    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(agendador.logger, "info", fake_info)
    repo = RepoPropriedade([10], _prazos_validos(), ja_executou=True)
    mensagens = Espiao()
    n = agendador.verificar_retencao(
        object(),
        agora=AGORA,
        repositorio_propriedade=repo,
        anonimizar_mensagens=mensagens,
        anonimizar_payloads=Espiao(),
        anonimizar_descricoes=Espiao(),
        anonimizar_comentarios=Espiao(),
        apagar_fichas=Espiao(),
    )

    assert n == 0
    assert mensagens.chamadas == []
    assert repo.registros == []
    assert "retencao_ja_executada_hoje" in " ".join(registros)
