"""Bootstrap contra banco real: senha derivada, atomicidade e silencio no log."""

import logging
import os
from io import StringIO

import pytest
from sqlalchemy import bindparam, create_engine, text

from app.comum.seguranca import conferir_senha
from testes.suporte.banco_descartavel import banco_vazio
from testes.suporte.migracao import aplicar_migracoes


@pytest.fixture
def banco_migrado(monkeypatch):
    with banco_vazio() as url:
        aplicar_migracoes(url)
        monkeypatch.setenv("DATABASE_URL", url)
        from app.config import obter_configuracao
        import app.database as modulo_banco

        obter_configuracao.cache_clear()
        modulo_banco.obter_engine.cache_clear()
        yield url
        obter_configuracao.cache_clear()
        modulo_banco.obter_engine.cache_clear()


@pytest.mark.postgres
def test_bootstrap_grava_senha_derivada_e_nao_em_claro(banco_migrado, monkeypatch):
    from app.bootstrap import executar_bootstrap

    senha = "senha-inicial-do-gestor"
    monkeypatch.setenv("BOOTSTRAP_SENHA_INICIAL", senha)

    resultado = executar_bootstrap(
        nome_hotel="Hotel Exemplo",
        telefone_whatsapp="+5511999999999",
        nome_gestor="Thiago Feitosa",
        email_gestor="gestor@hotel.com.br",
    )

    assert resultado.ok
    engine = create_engine(banco_migrado)
    try:
        with engine.connect() as conexao:
            linha = conexao.execute(
                text(
                    "SELECT senha_hash, perfil FROM usuario WHERE email = :email"
                ),
                {"email": "gestor@hotel.com.br"},
            ).one()
    finally:
        engine.dispose()

    assert senha not in linha.senha_hash
    assert linha.perfil == "gestor"
    assert conferir_senha(senha, linha.senha_hash)


@pytest.mark.postgres
def test_bootstrap_falha_no_meio_nao_deixa_propriedade_pela_metade(
    banco_migrado, monkeypatch
):
    from app import bootstrap
    from app.modulos.acesso import service as acesso_service

    monkeypatch.setenv("BOOTSTRAP_SENHA_INICIAL", "senha-inicial-do-gestor")

    def falhar(*_args, **_kwargs):
        raise RuntimeError("falha forçada depois do hotel")

    monkeypatch.setattr(acesso_service, "criar_usuario", falhar)

    with pytest.raises(RuntimeError, match="falha forçada"):
        bootstrap.executar_bootstrap(
            nome_hotel="Hotel Exemplo",
            telefone_whatsapp="+5511999999999",
            nome_gestor="Thiago Feitosa",
            email_gestor="gestor@hotel.com.br",
        )

    engine = create_engine(banco_migrado)
    try:
        with engine.connect() as conexao:
            hoteis = conexao.execute(text("SELECT count(*) FROM hotel")).scalar()
            usuarios = conexao.execute(text("SELECT count(*) FROM usuario")).scalar()
            parametros = conexao.execute(
                text("SELECT count(*) FROM parametro_hotel")
            ).scalar()
    finally:
        engine.dispose()

    assert (hoteis, usuarios, parametros) == (0, 0, 0)


@pytest.mark.postgres
def test_bootstrap_nao_escreve_senha_na_saida_nem_no_log(
    banco_migrado, monkeypatch, capsys, caplog
):
    from app.bootstrap import executar_bootstrap

    senha = "senha-secreta-unica-xyz"
    monkeypatch.setenv("BOOTSTRAP_SENHA_INICIAL", senha)

    with caplog.at_level(logging.DEBUG):
        resultado = executar_bootstrap(
            nome_hotel="Hotel Exemplo",
            telefone_whatsapp="+5511999999999",
            nome_gestor="Thiago Feitosa",
            email_gestor="gestor@hotel.com.br",
        )

    saida = capsys.readouterr().out + capsys.readouterr().err
    assert resultado.ok
    assert senha not in saida
    assert senha not in caplog.text


CHAVES_BOAS_VINDAS = (
    "boas_vindas_cafe",
    "boas_vindas_wifi",
    "boas_vindas_checkout",
    "boas_vindas_convite",
    "horas_validade_boas_vindas",
)


@pytest.mark.postgres
def test_bootstrap_semeia_chaves_de_boas_vindas(banco_migrado, monkeypatch):
    from app.bootstrap import executar_bootstrap

    monkeypatch.setenv("BOOTSTRAP_SENHA_INICIAL", "senha-inicial-do-gestor")
    resultado = executar_bootstrap(
        nome_hotel="Hotel Exemplo",
        telefone_whatsapp="+5511999999999",
        nome_gestor="Thiago Feitosa",
        email_gestor="gestor@hotel.com.br",
    )
    assert resultado.ok

    from app.modulos.propriedade import service as propriedade_service

    engine = create_engine(banco_migrado)
    try:
        with engine.connect() as conexao:
            linhas = conexao.execute(
                text(
                    "SELECT chave, valor FROM parametro_hotel "
                    "WHERE chave IN :chaves"
                ).bindparams(bindparam("chaves", expanding=True)),
                {"chaves": list(CHAVES_BOAS_VINDAS)},
            ).mappings().all()
    finally:
        engine.dispose()

    valores = {linha["chave"]: linha["valor"] for linha in linhas}
    assert set(valores) == set(CHAVES_BOAS_VINDAS)
    for chave in CHAVES_BOAS_VINDAS:
        assert valores[chave].strip()
    propriedade_service.validar_texto_de_boas_vindas(
        "convite", valores["boas_vindas_convite"]
    )
    convite = valores["boas_vindas_convite"]
    assert "servicos" in convite
    assert "cardapio" in convite
    assert "horarios" in convite


@pytest.mark.postgres
def test_bootstrap_semeia_prazo_minimo_do_pulso(banco_migrado, monkeypatch):
    from app.bootstrap import executar_bootstrap

    monkeypatch.setenv("BOOTSTRAP_SENHA_INICIAL", "senha-inicial-do-gestor")
    resultado = executar_bootstrap(
        nome_hotel="Hotel Exemplo",
        telefone_whatsapp="+5511999999999",
        nome_gestor="Thiago Feitosa",
        email_gestor="gestor@hotel.com.br",
    )
    assert resultado.ok

    engine = create_engine(banco_migrado)
    try:
        with engine.connect() as conexao:
            valor = conexao.execute(
                text(
                    "SELECT valor FROM parametro_hotel "
                    "WHERE chave = 'horas_minimas_para_pulso'"
                )
            ).scalar_one()
    finally:
        engine.dispose()

    assert valor == "24"


@pytest.mark.postgres
def test_bootstrap_semeia_prazo_de_atribuicao_da_pesquisa_saida(
    banco_migrado, monkeypatch
):
    from app.bootstrap import executar_bootstrap

    monkeypatch.setenv("BOOTSTRAP_SENHA_INICIAL", "senha-inicial-do-gestor")
    resultado = executar_bootstrap(
        nome_hotel="Hotel Exemplo",
        telefone_whatsapp="+5511999999999",
        nome_gestor="Thiago Feitosa",
        email_gestor="gestor@hotel.com.br",
    )
    assert resultado.ok

    engine = create_engine(banco_migrado)
    try:
        with engine.connect() as conexao:
            valor = conexao.execute(
                text(
                    "SELECT valor FROM parametro_hotel "
                    "WHERE chave = 'horas_atribuicao_pesquisa_saida'"
                )
            ).scalar_one()
    finally:
        engine.dispose()

    assert valor == "24"


@pytest.mark.postgres
def test_bootstrap_semeia_personalidade_assistente_vazia(banco_migrado, monkeypatch):
    from app.bootstrap import executar_bootstrap

    monkeypatch.setenv("BOOTSTRAP_SENHA_INICIAL", "senha-inicial-do-gestor")
    resultado = executar_bootstrap(
        nome_hotel="Hotel Exemplo",
        telefone_whatsapp="+5511999999999",
        nome_gestor="Thiago Feitosa",
        email_gestor="gestor@hotel.com.br",
    )
    assert resultado.ok

    engine = create_engine(banco_migrado)
    try:
        with engine.connect() as conexao:
            valor = conexao.execute(
                text(
                    "SELECT valor FROM parametro_hotel "
                    "WHERE chave = 'personalidade_assistente'"
                )
            ).scalar_one()
    finally:
        engine.dispose()

    assert valor == ""
