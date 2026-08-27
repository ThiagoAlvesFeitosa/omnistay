"""Texto da mensagem de coleta — privacidade e transparencia."""

from app.modulos.conversa.texto_coleta import montar_texto_coleta, primeiro_nome


CONTATO = "5511999990001"


def test_lista_numerada_tem_nove_campos_e_opcionalidade():
    texto = montar_texto_coleta(
        nome_completo="Maria Silva", contato_responsavel_dados=CONTATO
    )
    for indice in range(1, 10):
        assert f"{indice}. " in texto
    assert "Nome completo" in texto
    assert "Profissao" in texto
    assert "Telefone" in texto
    assert "opcional" in texto
    assert "evitar espera" in texto


def test_finalidade_e_contato_aparecem():
    texto = montar_texto_coleta(
        nome_completo="Maria Silva", contato_responsavel_dados=CONTATO
    )
    assert "Finalidade:" in texto
    assert "cadastro de hospede" in texto
    assert CONTATO in texto
    assert "Responsavel pelos dados" in texto


def test_saudacao_usa_apenas_primeiro_nome():
    assert primeiro_nome("Maria Silva") == "Maria"
    texto = montar_texto_coleta(
        nome_completo="Maria Silva", contato_responsavel_dados=CONTATO
    )
    assert "Ola, Maria!" in texto
    assert "Silva" not in texto.split("!")[0]


def test_coleta_nao_traz_aviso_de_assistente_virtual():
    texto = montar_texto_coleta(
        nome_completo="Maria Silva", contato_responsavel_dados=CONTATO
    )
    assert "assistente virtual" not in texto.lower()
    assert "recepcao assume" not in texto.lower()


def test_corpo_nao_vaza_telefone_documento_endereco_do_titular():
    texto = montar_texto_coleta(
        nome_completo="Maria Silva", contato_responsavel_dados=CONTATO
    )
    assert "5511987654321" not in texto
    assert "11987654321" not in texto
    assert "Rua " not in texto
    assert "Silva" not in texto


def test_contato_de_outro_hotel_nao_aparece():
    texto = montar_texto_coleta(
        nome_completo="Maria", contato_responsavel_dados="5511111111111"
    )
    assert "5511111111111" in texto
    assert "5511999990001" not in texto
