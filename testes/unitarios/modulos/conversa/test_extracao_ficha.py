"""Extracao de ficha via LLM falso + validacao."""

from app.adaptadores.llm_falso import LLMFalso
from app.modulos.conversa import service as conversa
from app.portas.llm import CAMPOS_FICHA_CHAVE, ResultadoExtracao
from testes.suporte.cpf_ficha import CPF_REPROVADO, CPF_VALIDO, CPF_VALIDO_PONTUADO


class RepoFake:
    def __init__(self, conteudo="texto"):
        self.conteudo = conteudo
        self.classificacao = None

    def ler_mensagem(self, conexao, *, id_mensagem):
        return {
            "id_mensagem": id_mensagem,
            "id_reserva": 1,
            "direcao": "recebida",
            "conteudo": self.conteudo,
            "classificacao_bruta": self.classificacao,
        }

    def gravar_classificacao_bruta(self, conexao, *, id_mensagem, classificacao):
        self.classificacao = classificacao


def test_campos_invalidos_reduzem_desfecho():
    repo = RepoFake()
    llm = LLMFalso()
    llm.configurar(
        ResultadoExtracao(
            desfecho="completa",
            campos={
                "nome_completo": "Maria",
                "data_nascimento": "xx",
                "tipo_documento": "cnh",
            },
            campos_reconhecidos=("nome_completo", "data_nascimento", "tipo_documento"),
        )
    )
    resultado = conversa.extrair_campos_via_llm(
        object(), id_mensagem=1, llm=llm, repositorio=repo
    )
    assert resultado.desfecho == "parcial"
    assert resultado.campos == {"nome_completo": "Maria"}
    assert repo.classificacao["desfecho"] == "parcial"


def _nove(*, numero: str, tipo: str = "cpf") -> dict[str, str]:
    return {
        "nome_completo": "Maria Silva",
        "profissao": "Engenheira",
        "data_nascimento": "1990-05-12",
        "tipo_documento": tipo,
        "numero_documento": numero,
        "endereco": "Rua A, 100",
        "cep": "01310100",
        "cidade": "Sao Paulo",
        "telefone": "5511987654321",
    }


def test_cpf_reprovado_na_extracao_fica_parcial_sem_numero():
    repo = RepoFake()
    llm = LLMFalso()
    llm.configurar(
        ResultadoExtracao(
            desfecho="completa",
            campos=_nove(numero=CPF_REPROVADO),
            campos_reconhecidos=tuple(CAMPOS_FICHA_CHAVE),
        )
    )
    resultado = conversa.extrair_campos_via_llm(
        object(), id_mensagem=1, llm=llm, repositorio=repo
    )
    assert resultado.desfecho == "parcial"
    assert "numero_documento" not in resultado.campos
    assert resultado.campos["tipo_documento"] == "cpf"


def test_cpf_pontuado_valido_na_extracao_sai_em_onze_digitos():
    repo = RepoFake()
    llm = LLMFalso()
    llm.configurar(
        ResultadoExtracao(
            desfecho="completa",
            campos=_nove(numero=CPF_VALIDO_PONTUADO),
            campos_reconhecidos=tuple(CAMPOS_FICHA_CHAVE),
        )
    )
    resultado = conversa.extrair_campos_via_llm(
        object(), id_mensagem=1, llm=llm, repositorio=repo
    )
    assert resultado.desfecho == "completa"
    assert resultado.campos["numero_documento"] == CPF_VALIDO


def test_irreconhecivel_grava_desfecho_sem_campos():
    repo = RepoFake()
    llm = LLMFalso()
    llm.configurar(ResultadoExtracao(desfecho="irreconhecivel"))
    resultado = conversa.extrair_campos_via_llm(
        object(), id_mensagem=1, llm=llm, repositorio=repo
    )
    assert resultado.desfecho == "irreconhecivel"
    assert repo.classificacao["desfecho"] == "irreconhecivel"
    assert repo.classificacao["campos_reconhecidos"] == []
