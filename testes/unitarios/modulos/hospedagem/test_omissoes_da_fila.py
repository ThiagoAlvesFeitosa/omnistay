"""Catalogo de omissao da Fila do dia — o que deixou de acontecer."""

from app.modulos.hospedagem.service import montar_omissoes


def test_ficha_em_falha_gera_rotulo_singular():
    omissoes = montar_omissoes([{"tipo": "interpretar_ficha", "n": 1}])
    assert omissoes == [
        {
            "chave": "ficha_nao_processada",
            "texto": "Ficha não processada",
            "contagem": 1,
        }
    ]


def test_duas_mensagens_do_mesmo_tipo_viram_contagem():
    omissoes = montar_omissoes([{"tipo": "classificar_mensagem", "n": 2}])
    assert omissoes == [
        {
            "chave": "mensagem_hospede_sem_resposta",
            "texto": "2 mensagens do hóspede sem resposta",
            "contagem": 2,
        }
    ]


def test_tipos_de_inbound_colapsam_na_mesma_chave():
    omissoes = montar_omissoes(
        [
            {"tipo": "classificar_mensagem", "n": 1},
            {"tipo": "responder_duvida", "n": 1},
        ]
    )
    assert len(omissoes) == 1
    assert omissoes[0]["chave"] == "mensagem_hospede_sem_resposta"
    assert omissoes[0]["contagem"] == 2


def test_tipo_futuro_sem_chave_nao_inventa_frase():
    assert montar_omissoes([{"tipo": "tipo_inexistente", "n": 1}]) == []


def test_coleta_de_mercado_nao_produz_omissao():
    assert montar_omissoes([{"tipo": "coletar_mercado", "n": 1}]) == []
