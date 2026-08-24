"""Comprovante de retencao: lista do hotel, vazia sem erro, sem texto de hospede."""

from datetime import UTC, datetime

from app.modulos.propriedade import service as propriedade

AGORA = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


class RepoComprovante:
    def __init__(self, por_hotel):
        self.por_hotel = por_hotel

    def listar_execucoes_retencao(self, conexao, *, id_hotel):
        linhas = list(self.por_hotel.get(id_hotel, []))
        return sorted(linhas, key=lambda l: l["executado_em"], reverse=True)


def test_lista_do_hotel_em_ordem_decrescente_sem_texto_de_hospede(monkeypatch):
    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(propriedade.logger, "info", fake_info)
    antiga = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)
    recente = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    repo = RepoComprovante(
        {
            10: [
                {
                    "id_execucao": 1,
                    "executado_em": antiga,
                    "mensagens_anonimizadas": 2,
                    "comentarios_anonimizados": 0,
                    "payloads_anonimizados": 2,
                    "descricoes_anonimizadas": 1,
                    "fichas_apagadas": 0,
                    "prazo_conteudo_ausente": False,
                    "prazo_ficha_ausente": False,
                },
                {
                    "id_execucao": 2,
                    "executado_em": recente,
                    "mensagens_anonimizadas": 0,
                    "comentarios_anonimizados": 0,
                    "payloads_anonimizados": 0,
                    "descricoes_anonimizadas": 0,
                    "fichas_apagadas": 1,
                    "prazo_conteudo_ausente": False,
                    "prazo_ficha_ausente": False,
                },
            ]
        }
    )

    lista = propriedade.listar_execucoes_retencao(
        object(), id_hotel=10, repositorio=repo
    )

    assert [item.id_execucao for item in lista] == [2, 1]
    texto = " ".join(registros)
    assert "id_hotel=10" in texto
    assert "comprovante" in texto
    assert "Ana" not in texto
    assert "5511" not in texto
    assert "documento" not in texto


def test_hotel_sem_execucao_devolve_lista_vazia():
    repo = RepoComprovante({})
    lista = propriedade.listar_execucoes_retencao(
        object(), id_hotel=10, repositorio=repo
    )
    assert lista == []
