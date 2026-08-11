from app.modulos.sistema.service import obter_saude


def test_service_banco_ok_retorna_sucesso():
    def verificar_conectividade_falsa() -> bool:
        return True

    saude = obter_saude(verificar_conectividade=verificar_conectividade_falsa)

    assert saude.banco == "ok"


def test_service_banco_indisponivel_retorna_falha():
    def verificar_conectividade_falsa() -> bool:
        return False

    saude = obter_saude(verificar_conectividade=verificar_conectividade_falsa)

    assert saude.banco == "indisponivel"
