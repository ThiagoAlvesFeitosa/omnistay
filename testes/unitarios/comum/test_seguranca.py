"""Primitivas de seguranca: derivacao de senha e token de sessao.

Testes de unidade puros: nao tocam banco, nao sobem aplicacao.
"""

from app.comum import seguranca

ITERACOES_DE_TESTE = 1_000


def test_a_mesma_senha_derivada_duas_vezes_produz_valores_diferentes():
    senha = "senha-do-cleber-123"

    primeiro = seguranca.derivar_senha(senha, iteracoes=ITERACOES_DE_TESTE)
    segundo = seguranca.derivar_senha(senha, iteracoes=ITERACOES_DE_TESTE)

    assert primeiro != segundo


def test_conferencia_aceita_a_senha_correta():
    gravado = seguranca.derivar_senha("senha-correta-123", iteracoes=ITERACOES_DE_TESTE)

    assert seguranca.conferir_senha("senha-correta-123", gravado) is True


def test_conferencia_recusa_a_senha_errada():
    gravado = seguranca.derivar_senha("senha-correta-123", iteracoes=ITERACOES_DE_TESTE)

    assert seguranca.conferir_senha("senha-errada-123", gravado) is False


def test_valor_gravado_nao_contem_a_senha_em_claro():
    gravado = seguranca.derivar_senha("senha-do-cleber-123", iteracoes=ITERACOES_DE_TESTE)

    assert "senha-do-cleber-123" not in gravado


def test_valor_gravado_declara_algoritmo_iteracoes_e_sal():
    gravado = seguranca.derivar_senha("senha-qualquer-123", iteracoes=ITERACOES_DE_TESTE)

    algoritmo, iteracoes, sal, derivado = gravado.split("$")

    assert (algoritmo, int(iteracoes)) == ("pbkdf2_sha256", ITERACOES_DE_TESTE)
    assert sal and derivado


def test_valor_gravado_com_menos_iteracoes_continua_conferindo():
    """A verificacao usa o numero de iteracoes da propria linha.

    E o que permite elevar o custo da derivacao depois sem invalidar as senhas
    ja cadastradas.
    """
    gravado_antigo = seguranca.derivar_senha("senha-antiga-123", iteracoes=100)

    assert seguranca.conferir_senha("senha-antiga-123", gravado_antigo) is True


def test_conferencia_recusa_valor_gravado_malformado():
    assert seguranca.conferir_senha("senha-qualquer-123", "nao-e-um-hash") is False


def test_dois_tokens_gerados_nunca_coincidem():
    tokens = {seguranca.gerar_token() for _ in range(100)}

    assert len(tokens) == 100


def test_hash_do_token_e_estavel_para_o_mesmo_token():
    token = seguranca.gerar_token()

    assert seguranca.hash_do_token(token) == seguranca.hash_do_token(token)


def test_hash_do_token_nao_revela_o_token():
    """A FR-007: vazamento da tabela de sessoes nao equivale a vazamento de acesso."""
    token = seguranca.gerar_token()

    hash_gravado = seguranca.hash_do_token(token)

    assert token not in hash_gravado
    assert len(hash_gravado) == 64


def test_hash_de_referencia_tem_o_formato_de_um_valor_gravado():
    """Usado para igualar o tempo de resposta quando o e-mail nao existe."""
    referencia = seguranca.hash_de_referencia(iteracoes=ITERACOES_DE_TESTE)

    assert referencia.startswith("pbkdf2_sha256$")
    assert seguranca.conferir_senha("qualquer-tentativa-123", referencia) is False
