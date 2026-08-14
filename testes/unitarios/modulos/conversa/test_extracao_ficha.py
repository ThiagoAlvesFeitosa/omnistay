"""Extracao de ficha via LLM falso + validacao."""

from app.adaptadores.llm_falso import LLMFalso
from app.modulos.conversa import service as conversa
from app.portas.llm import ResultadoExtracao


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
