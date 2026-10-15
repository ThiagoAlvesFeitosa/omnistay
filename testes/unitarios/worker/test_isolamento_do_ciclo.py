"""Ciclo do worker: uma etapa que estoura nao impede as outras."""

from testes.suporte.isolamento_falha import CPF_NA_MENSAGEM, excecao_com_cpf
from worker import __main__ as worker_main


def _registrar(destino, marca):
    def _acao(*args, **kwargs):
        destino.append(marca)
        return 0

    return _acao


def _estoura(destino, marca):
    def _acao(*args, **kwargs):
        destino.append(marca)
        raise excecao_com_cpf()

    return _acao


def test_falha_na_passagem_ainda_roda_verificacoes_e_expurgo(monkeypatch):
    ordem = []
    monkeypatch.setattr(
        worker_main,
        "processar_uma_passagem_na_engine",
        _estoura(ordem, "passagem"),
    )
    monkeypatch.setattr(worker_main, "_rodar_verificacao", _registrar(ordem, "cadastros"))
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_boas_vindas", _registrar(ordem, "boas_vindas")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_pulsos", _registrar(ordem, "pulsos")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_mercado", _registrar(ordem, "mercado")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_retencao", _registrar(ordem, "retencao")
    )
    worker_main.executar_ciclo(object(), gateway=object(), llm=object())
    assert ordem == [
        "passagem",
        "cadastros",
        "boas_vindas",
        "pulsos",
        "mercado",
        "retencao",
    ]


def test_falha_so_no_mercado_nao_pula_as_outras(monkeypatch):
    ordem = []
    monkeypatch.setattr(
        worker_main,
        "processar_uma_passagem_na_engine",
        _registrar(ordem, "passagem"),
    )
    monkeypatch.setattr(worker_main, "_rodar_verificacao", _registrar(ordem, "cadastros"))
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_boas_vindas", _registrar(ordem, "boas_vindas")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_pulsos", _registrar(ordem, "pulsos")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_mercado", _estoura(ordem, "mercado")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_retencao", _registrar(ordem, "retencao")
    )
    worker_main.executar_ciclo(object(), gateway=object(), llm=object())
    assert ordem == [
        "passagem",
        "cadastros",
        "boas_vindas",
        "pulsos",
        "mercado",
        "retencao",
    ]


def test_falha_no_expurgo_nao_impede_passagem_nem_outras_verificacoes(monkeypatch):
    ordem = []
    monkeypatch.setattr(
        worker_main,
        "processar_uma_passagem_na_engine",
        _registrar(ordem, "passagem"),
    )
    monkeypatch.setattr(worker_main, "_rodar_verificacao", _registrar(ordem, "cadastros"))
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_boas_vindas", _registrar(ordem, "boas_vindas")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_pulsos", _registrar(ordem, "pulsos")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_mercado", _registrar(ordem, "mercado")
    )
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_retencao", _estoura(ordem, "retencao")
    )
    worker_main.executar_ciclo(object(), gateway=object(), llm=object())
    assert "passagem" in ordem
    assert "cadastros" in ordem
    assert "retencao" in ordem


def test_log_da_etapa_falha_nao_repete_cpf(monkeypatch):
    registros = []

    def _info(msg, *args, **kwargs):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(worker_main.logger, "warning", _info)
    monkeypatch.setattr(
        worker_main,
        "processar_uma_passagem_na_engine",
        _estoura([], "passagem"),
    )
    monkeypatch.setattr(worker_main, "_rodar_verificacao", lambda engine: 0)
    monkeypatch.setattr(
        worker_main, "_rodar_verificacao_boas_vindas", lambda engine: 0
    )
    monkeypatch.setattr(worker_main, "_rodar_verificacao_pulsos", lambda engine: 0)
    monkeypatch.setattr(worker_main, "_rodar_verificacao_mercado", lambda engine: 0)
    monkeypatch.setattr(worker_main, "_rodar_verificacao_retencao", lambda engine: 0)
    worker_main.executar_ciclo(object(), gateway=object(), llm=object())
    texto = " ".join(registros)
    assert CPF_NA_MENSAGEM not in texto
    assert "IntegrityError" in texto
    assert "passagem" in texto
    assert "ciclo_etapa_falha" in texto
