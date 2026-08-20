"""CLI do worker: --uma-passagem nao verifica cadastros."""

from worker import __main__ as worker_main


def test_uma_passagem_nao_chama_agendador(monkeypatch):
    verificacoes = []
    pulsos = []
    monkeypatch.setattr(
        worker_main,
        "processar_uma_passagem_na_engine",
        lambda *args, **kwargs: 0,
    )
    monkeypatch.setattr(
        worker_main,
        "_rodar_verificacao",
        lambda engine: verificacoes.append("v") or 0,
    )
    monkeypatch.setattr(
        worker_main,
        "_rodar_verificacao_pulsos",
        lambda engine: pulsos.append("p") or 0,
    )
    monkeypatch.setattr(
        worker_main,
        "create_engine",
        lambda url: object(),
    )
    monkeypatch.setattr(
        worker_main,
        "obter_configuracao",
        lambda: type("C", (), {"database_url": "postgresql://x"})(),
    )
    worker_main.main(["--uma-passagem"])
    assert verificacoes == []
    assert pulsos == []


def test_verificar_cadastros_chama_agendador(monkeypatch):
    verificacoes = []
    monkeypatch.setattr(
        worker_main,
        "_rodar_verificacao",
        lambda engine: verificacoes.append("v") or 0,
    )
    monkeypatch.setattr(worker_main, "create_engine", lambda url: object())
    monkeypatch.setattr(
        worker_main,
        "obter_configuracao",
        lambda: type("C", (), {"database_url": "postgresql://x"})(),
    )
    worker_main.main(["--verificar-cadastros"])
    assert verificacoes == ["v"]


def test_verificar_boas_vindas_chama_varredura_e_encerra(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        worker_main,
        "_rodar_verificacao_boas_vindas",
        lambda engine: chamadas.append("b") or 0,
    )
    monkeypatch.setattr(worker_main, "create_engine", lambda url: object())
    monkeypatch.setattr(
        worker_main,
        "obter_configuracao",
        lambda: type("C", (), {"database_url": "postgresql://x"})(),
    )
    worker_main.main(["--verificar-boas-vindas"])
    assert chamadas == ["b"]


def test_verificar_pulsos_chama_varredura_e_encerra(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        worker_main,
        "_rodar_verificacao_pulsos",
        lambda engine: chamadas.append("p") or 0,
    )
    monkeypatch.setattr(worker_main, "create_engine", lambda url: object())
    monkeypatch.setattr(
        worker_main,
        "obter_configuracao",
        lambda: type("C", (), {"database_url": "postgresql://x"})(),
    )
    worker_main.main(["--verificar-pulsos"])
    assert chamadas == ["p"]
