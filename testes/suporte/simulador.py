"""Apoio da suíte do simulador de conversa. Uso só em teste."""

from app.config import obter_configuracao

ID_EXTERNO_SIM = "sim:"


def modo_demonstracao(monkeypatch) -> None:
    monkeypatch.setenv("MENSAGERIA_MODO", "demonstracao")
    obter_configuracao.cache_clear()


def modo_real(monkeypatch) -> None:
    monkeypatch.setenv("MENSAGERIA_MODO", "real")
    obter_configuracao.cache_clear()


def id_externo_sim(sufixo: str) -> str:
    return f"{ID_EXTERNO_SIM}{sufixo}"
