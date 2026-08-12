"""Autenticacao e ciclo de vida da sessao — unidade, com dependencias falsas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from app.comum import seguranca
from app.modulos.acesso import service as acesso_service

INSTANTE = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)
ITERACOES = 1_000


@dataclass
class UsuarioFalso:
    id_usuario: int
    id_hotel: int
    nome: str
    email: str
    senha_hash: str
    perfil: str
    ativo: bool = True


@dataclass
class RepositorioFalso:
    usuarios: dict[str, UsuarioFalso] = field(default_factory=dict)
    sessoes: list = field(default_factory=list)
    conferencias: list = field(default_factory=list)
    proximo_id: int = 1

    def buscar_por_email(self, conexao, email: str):
        return self.usuarios.get(email)

    def inserir_sessao(self, conexao, *, id_usuario, token_hash, dispositivo, criada_em, expira_em):
        id_sessao = self.proximo_id
        self.proximo_id += 1
        self.sessoes.append(
            {
                "id_sessao": id_sessao,
                "id_usuario": id_usuario,
                "token_hash": token_hash,
                "dispositivo": dispositivo,
                "criada_em": criada_em,
                "expira_em": expira_em,
                "revogada_em": None,
            }
        )
        return id_sessao

    def buscar_sessao_por_hash(self, conexao, token_hash: str):
        for sessao in self.sessoes:
            if sessao["token_hash"] == token_hash:
                usuario = next(
                    u for u in self.usuarios.values() if u.id_usuario == sessao["id_usuario"]
                )
                return type(
                    "Row",
                    (),
                    {
                        **sessao,
                        "id_hotel": usuario.id_hotel,
                        "nome": usuario.nome,
                        "email": usuario.email,
                        "perfil": usuario.perfil,
                        "ativo": usuario.ativo,
                    },
                )()
        return None

    def revogar_sessao(self, conexao, id_sessao, revogada_em):
        for sessao in self.sessoes:
            if sessao["id_sessao"] == id_sessao and sessao["revogada_em"] is None:
                sessao["revogada_em"] = revogada_em


@dataclass
class PropriedadeFalsa:
    duracoes: dict[str, int]

    def duracao(self, conexao, *, id_hotel, perfil):
        return self.duracoes[perfil]


def _montar(ativo=True, perfil="staff"):
    senha = "senha-do-cleber-123"
    repo = RepositorioFalso(
        usuarios={
            "cleber@hotel.com.br": UsuarioFalso(
                id_usuario=3,
                id_hotel=1,
                nome="Cleber Rocha",
                email="cleber@hotel.com.br",
                senha_hash=seguranca.derivar_senha(senha, iteracoes=ITERACOES),
                perfil=perfil,
                ativo=ativo,
            )
        }
    )
    propriedade = PropriedadeFalsa({"staff": 720, "recepcao": 12, "gestor": 12})
    return repo, propriedade, senha


def test_credencial_correta_cria_sessao_com_hash_e_expiracao_do_perfil():
    repo, propriedade, senha = _montar()

    resultado = acesso_service.autenticar(
        conexao=object(),
        email="cleber@hotel.com.br",
        senha=senha,
        dispositivo="Celular da manutencao",
        repositorio=repo,
        ler_duracao=propriedade.duracao,
        agora=lambda: INSTANTE,
    )

    assert resultado.id_usuario == 3
    assert resultado.perfil == "staff"
    assert resultado.expira_em == INSTANTE + timedelta(hours=720)
    assert len(repo.sessoes) == 1
    assert repo.sessoes[0]["token_hash"] == seguranca.hash_do_token(resultado.token)
    assert resultado.token not in repo.sessoes[0]["token_hash"]


def test_senha_errada_recusa_sem_criar_sessao():
    repo, propriedade, _ = _montar()

    with pytest.raises(acesso_service.CredenciaisInvalidas):
        acesso_service.autenticar(
            conexao=object(),
            email="cleber@hotel.com.br",
            senha="senha-errada-123",
            dispositivo=None,
            repositorio=repo,
            ler_duracao=propriedade.duracao,
            agora=lambda: INSTANTE,
        )

    assert repo.sessoes == []


def test_usuario_inativo_recusa_mesmo_com_senha_correta():
    repo, propriedade, senha = _montar(ativo=False)

    with pytest.raises(acesso_service.CredenciaisInvalidas):
        acesso_service.autenticar(
            conexao=object(),
            email="cleber@hotel.com.br",
            senha=senha,
            dispositivo=None,
            repositorio=repo,
            ler_duracao=propriedade.duracao,
            agora=lambda: INSTANTE,
        )


def test_email_inexistente_ainda_executa_derivacao(monkeypatch):
    repo, propriedade, _ = _montar()
    chamadas = {"n": 0}
    original = seguranca.conferir_senha

    def contador(senha, valor):
        chamadas["n"] += 1
        return original(senha, valor)

    monkeypatch.setattr(seguranca, "conferir_senha", contador)

    with pytest.raises(acesso_service.CredenciaisInvalidas):
        acesso_service.autenticar(
            conexao=object(),
            email="ninguem@hotel.com.br",
            senha="qualquer-senha-123",
            dispositivo=None,
            repositorio=repo,
            ler_duracao=propriedade.duracao,
            agora=lambda: INSTANTE,
            conferir=contador,
        )

    assert chamadas["n"] >= 1
    assert repo.sessoes == []


def test_sessoes_dos_tres_perfis_nascem_com_expiracoes_diferentes():
    senha = "senha-de-teste-123"
    repo = RepositorioFalso(
        usuarios={
            f"{perfil}@hotel.com.br": UsuarioFalso(
                id_usuario=i,
                id_hotel=1,
                nome=perfil,
                email=f"{perfil}@hotel.com.br",
                senha_hash=seguranca.derivar_senha(senha, iteracoes=ITERACOES),
                perfil=perfil,
            )
            for i, perfil in enumerate(("recepcao", "staff", "gestor"), start=1)
        }
    )
    propriedade = PropriedadeFalsa({"recepcao": 12, "staff": 720, "gestor": 12})

    expiracoes = {}
    for perfil in ("recepcao", "staff", "gestor"):
        resultado = acesso_service.autenticar(
            conexao=object(),
            email=f"{perfil}@hotel.com.br",
            senha=senha,
            dispositivo=perfil,
            repositorio=repo,
            ler_duracao=propriedade.duracao,
            agora=lambda: INSTANTE,
        )
        expiracoes[perfil] = resultado.expira_em

    assert expiracoes["staff"] == INSTANTE + timedelta(hours=720)
    assert expiracoes["recepcao"] == INSTANTE + timedelta(hours=12)
    assert expiracoes["gestor"] == INSTANTE + timedelta(hours=12)


def test_alterar_duracao_nao_muda_sessao_ja_criada():
    repo, propriedade, senha = _montar()
    resultado = acesso_service.autenticar(
        conexao=object(),
        email="cleber@hotel.com.br",
        senha=senha,
        dispositivo=None,
        repositorio=repo,
        ler_duracao=propriedade.duracao,
        agora=lambda: INSTANTE,
    )
    expiracao_original = resultado.expira_em
    propriedade.duracoes["staff"] = 1

    assert repo.sessoes[0]["expira_em"] == expiracao_original


def test_falta_da_chave_de_duracao_falha_explicitamente():
    repo, _, senha = _montar()

    def sem_chave(*_a, **_k):
        from app.modulos.propriedade.service import DuracaoNaoConfigurada

        raise DuracaoNaoConfigurada("ausente")

    with pytest.raises(Exception, match="ausente"):
        acesso_service.autenticar(
            conexao=object(),
            email="cleber@hotel.com.br",
            senha=senha,
            dispositivo=None,
            repositorio=repo,
            ler_duracao=sem_chave,
            agora=lambda: INSTANTE,
        )
