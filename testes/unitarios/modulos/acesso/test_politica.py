"""Politica de autorizacao: decisao pura, sem HTTP e sem banco."""

from app.modulos.acesso import politica

OPERACOES_ESPERADAS = {
    "ver_sessao_propria": {"recepcao", "staff", "gestor"},
    "encerrar_sessao_propria": {"recepcao", "staff", "gestor"},
    "listar_sessoes": {"recepcao"},
    "revogar_sessao": {"recepcao"},
    "administrar_usuario": {"gestor"},
    "ler_dado_cadastral_de_hospede": {"recepcao"},
    "ler_ficha_de_hospede": {"recepcao"},
    "alterar_ficha_de_hospede": {"recepcao"},
    "alterar_reserva": {"recepcao"},
    "confirmar_fase_da_reserva": {"recepcao"},
    "ler_fila_do_dia": {"recepcao"},
    "ler_solicitacao_atribuida": {"recepcao", "staff", "gestor"},
    "resolver_solicitacao": {"recepcao", "staff"},
    "lancar_consumo": {"recepcao"},
    "alterar_catalogo": {"recepcao"},
    "ler_catalogo": {"recepcao", "gestor"},
    "ler_indicadores": {"recepcao", "gestor"},
    "alterar_texto_de_boas_vindas": {"recepcao"},
    "ler_texto_de_boas_vindas": {"recepcao", "gestor"},
    "ler_consentimento": {"recepcao", "gestor"},
    "registrar_consentimento": {"recepcao", "gestor"},
    "ler_pedidos_feitos_pelo_chat": {"recepcao", "gestor"},
}


def test_matriz_completa_bate_com_o_contrato():
    assert set(politica.OPERACOES) == set(OPERACOES_ESPERADAS)
    for operacao, perfis in OPERACOES_ESPERADAS.items():
        for perfil in ("recepcao", "staff", "gestor"):
            assert politica.permitido(perfil, operacao) is (perfil in perfis)


def test_staff_nao_le_dado_cadastral_de_hospede():
    assert politica.permitido("staff", "ler_dado_cadastral_de_hospede") is False


def test_gestor_nao_altera_reserva():
    assert politica.permitido("gestor", "alterar_reserva") is False


def test_ler_fila_do_dia_so_recepcao():
    assert politica.permitido("recepcao", "ler_fila_do_dia") is True
    assert politica.permitido("staff", "ler_fila_do_dia") is False
    assert politica.permitido("gestor", "ler_fila_do_dia") is False


def test_ler_indicadores_continua_para_recepcao_e_gestor():
    assert politica.permitido("recepcao", "ler_indicadores") is True
    assert politica.permitido("gestor", "ler_indicadores") is True
    assert politica.permitido("staff", "ler_indicadores") is False


def test_ler_catalogo_recepcao_e_gestor_staff_recusado():
    assert politica.permitido("recepcao", "ler_catalogo") is True
    assert politica.permitido("gestor", "ler_catalogo") is True
    assert politica.permitido("staff", "ler_catalogo") is False


def test_alterar_catalogo_continua_so_recepcao():
    assert politica.permitido("recepcao", "alterar_catalogo") is True
    assert politica.permitido("gestor", "alterar_catalogo") is False
    assert politica.permitido("staff", "alterar_catalogo") is False


def test_operacao_desconhecida_e_recusada():
    assert politica.permitido("gestor", "operacao_inventada") is False


def test_alterar_texto_de_boas_vindas_so_recepcao():
    assert politica.permitido("recepcao", "alterar_texto_de_boas_vindas") is True
    assert politica.permitido("gestor", "alterar_texto_de_boas_vindas") is False
    assert politica.permitido("staff", "alterar_texto_de_boas_vindas") is False


def test_ler_texto_de_boas_vindas_recepcao_e_gestor():
    assert politica.permitido("recepcao", "ler_texto_de_boas_vindas") is True
    assert politica.permitido("gestor", "ler_texto_de_boas_vindas") is True
    assert politica.permitido("staff", "ler_texto_de_boas_vindas") is False


def test_consentimento_recepcao_e_gestor_staff_recusado():
    for operacao in ("ler_consentimento", "registrar_consentimento"):
        assert politica.permitido("recepcao", operacao) is True
        assert politica.permitido("gestor", operacao) is True
        assert politica.permitido("staff", operacao) is False


def test_confirmar_fase_da_reserva_continua_so_recepcao():
    assert politica.permitido("recepcao", "confirmar_fase_da_reserva") is True
    assert politica.permitido("gestor", "confirmar_fase_da_reserva") is False
    assert politica.permitido("staff", "confirmar_fase_da_reserva") is False


def test_ler_pedidos_feitos_pelo_chat_recepcao_e_gestor_staff_recusado():
    assert politica.permitido("recepcao", "ler_pedidos_feitos_pelo_chat") is True
    assert politica.permitido("gestor", "ler_pedidos_feitos_pelo_chat") is True
    assert politica.permitido("staff", "ler_pedidos_feitos_pelo_chat") is False


def test_nenhuma_operacao_da_matriz_contem_parametro_no_nome():
    assert all("parametro" not in nome for nome in politica.OPERACOES)
