"""Validacao pura da ficha."""

from app.modulos.conversa.validacao_ficha import (
    classificar_desfecho,
    refinar_resultado,
    validar_campos_extraidos,
)
from app.portas.llm import CAMPOS_FICHA_CHAVE, ResultadoExtracao
from testes.suporte.cpf_ficha import (
    CPF_ONZE_IGUAIS,
    CPF_ONZE_IGUAIS_PONTUADO,
    CPF_REPROVADO,
    CPF_REPROVADO_PONTUADO,
    CPF_VALIDO,
    CPF_VALIDO_PONTUADO,
)


def test_data_nascimento_valida_e_aceita():
    saida = validar_campos_extraidos({"data_nascimento": "12/05/1990"})
    assert saida["data_nascimento"] == "1990-05-12"


def test_data_impossivel_e_rejeitada():
    assert validar_campos_extraidos({"data_nascimento": "99/99/9999"}) == {}


def test_idade_e_ignorada():
    saida = validar_campos_extraidos(
        {"nome_completo": "Maria", "idade": "34", "data_nascimento": "1990-05-12"}
    )
    assert "idade" not in saida
    assert saida["nome_completo"] == "Maria"


def test_tipo_documento_invalido_nao_conta():
    assert validar_campos_extraidos({"tipo_documento": "cnh"}) == {}


def test_nove_campos_validos_sao_completos():
    campos = {
        "nome_completo": "Maria Silva",
        "profissao": "Engenheira",
        "data_nascimento": "1990-05-12",
        "tipo_documento": "rg",
        "numero_documento": "1234567",
        "endereco": "Rua A, 100",
        "cep": "01310-100",
        "cidade": "Sao Paulo",
        "telefone": "(11) 98765-4321",
    }
    validos = validar_campos_extraidos(campos)
    assert len(validos) == len(CAMPOS_FICHA_CHAVE)
    assert classificar_desfecho(validos) == "completa"


def test_cpf_pontuado_valido_grava_onze_digitos():
    saida = validar_campos_extraidos(
        {"tipo_documento": "cpf", "numero_documento": CPF_VALIDO_PONTUADO}
    )
    assert saida["numero_documento"] == CPF_VALIDO


def test_cpf_sem_pontuacao_valido_grava_onze_digitos():
    saida = validar_campos_extraidos(
        {"tipo_documento": "cpf", "numero_documento": CPF_VALIDO}
    )
    assert saida["numero_documento"] == CPF_VALIDO


def test_cpf_onze_iguais_nao_entra():
    saida = validar_campos_extraidos(
        {"tipo_documento": "cpf", "numero_documento": CPF_ONZE_IGUAIS}
    )
    assert "numero_documento" not in saida
    assert saida.get("tipo_documento") == "cpf"


def test_cpf_onze_iguais_pontuado_nao_entra():
    saida = validar_campos_extraidos(
        {"tipo_documento": "cpf", "numero_documento": CPF_ONZE_IGUAIS_PONTUADO}
    )
    assert "numero_documento" not in saida


def test_cpf_reprovado_nao_entra_e_tipo_permanece():
    saida = validar_campos_extraidos(
        {
            "tipo_documento": "cpf",
            "numero_documento": CPF_REPROVADO_PONTUADO,
        }
    )
    assert saida.get("tipo_documento") == "cpf"
    assert "numero_documento" not in saida
    assert CPF_REPROVADO not in saida.values()


def test_refinar_parcial_quando_faltam_campos():
    bruto = ResultadoExtracao(
        desfecho="completa",
        campos={"nome_completo": "Maria", "idade": "30"},
        campos_reconhecidos=("nome_completo", "idade"),
    )
    refinado = refinar_resultado(bruto)
    assert refinado.desfecho == "parcial"
    assert "idade" not in refinado.campos
