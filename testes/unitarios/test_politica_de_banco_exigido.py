from testes.suporte.politica_de_banco import Acao, decidir_execucao


def test_com_banco_alcancavel_o_teste_executa():
    decisao = decidir_execucao(banco_alcancavel=True, banco_exigido=False)

    assert decisao.acao is Acao.EXECUTAR


def test_sem_banco_e_sem_exigencia_o_teste_e_pulado():
    decisao = decidir_execucao(banco_alcancavel=False, banco_exigido=False)

    assert decisao.acao is Acao.PULAR


def test_teste_pulado_declara_o_motivo():
    decisao = decidir_execucao(banco_alcancavel=False, banco_exigido=False)

    assert "EXIGIR_POSTGRES" in decisao.motivo


def test_sem_banco_e_com_exigencia_o_teste_falha():
    decisao = decidir_execucao(banco_alcancavel=False, banco_exigido=True)

    assert decisao.acao is Acao.FALHAR


def test_falha_por_banco_exigido_declara_o_motivo():
    decisao = decidir_execucao(banco_alcancavel=False, banco_exigido=True)

    assert "EXIGIR_POSTGRES" in decisao.motivo


def test_com_banco_alcancavel_a_exigencia_nao_muda_a_decisao():
    decisao = decidir_execucao(banco_alcancavel=True, banco_exigido=True)

    assert decisao.acao is Acao.EXECUTAR
