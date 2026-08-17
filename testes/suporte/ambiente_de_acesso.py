"""Cenario de teste com duas propriedades e usuarios dos tres perfis.

Quase todo teste de integracao desta fatia precisa disso — inclusive os de
isolamento entre propriedades. A fixture entrega banco descartavel ja migrado,
para que nenhum teste compartilhe estado com outro.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from app.comum.seguranca import derivar_senha, gerar_token, hash_do_token
from testes.suporte.banco_descartavel import banco_vazio
from testes.suporte.migracao import aplicar_migracoes

SENHA_PADRAO = "senha-de-teste-123"
DURACOES = {
    "recepcao": "12",
    "staff": "720",
    "gestor": "12",
}
CHAVES_DE_DURACAO = {
    "recepcao": "duracao_sessao_recepcao_horas",
    "staff": "duracao_sessao_staff_horas",
    "gestor": "duracao_sessao_gestor_horas",
}


@dataclass(frozen=True)
class UsuarioDeTeste:
    id_usuario: int
    id_hotel: int
    nome: str
    email: str
    perfil: str
    senha: str


@dataclass
class PropriedadeDeTeste:
    id_hotel: int
    nome: str
    usuarios: dict[str, UsuarioDeTeste]


@dataclass
class AmbienteDeAcesso:
    url: str
    engine: Engine
    propriedade_a: PropriedadeDeTeste
    propriedade_b: PropriedadeDeTeste

    def conexao(self) -> Connection:
        return self.engine.connect()


def _inserir_hotel(conexao: Connection, nome: str, telefone: str) -> int:
    return conexao.execute(
        text(
            "INSERT INTO hotel (nome, telefone_whatsapp) "
            "VALUES (:nome, :telefone) RETURNING id_hotel"
        ),
        {"nome": nome, "telefone": telefone},
    ).scalar_one()


def _semear_duracoes(conexao: Connection, id_hotel: int) -> None:
    for perfil, valor in DURACOES.items():
        conexao.execute(
            text(
                "INSERT INTO parametro_hotel (id_hotel, chave, valor) "
                "VALUES (:id_hotel, :chave, :valor)"
            ),
            {
                "id_hotel": id_hotel,
                "chave": CHAVES_DE_DURACAO[perfil],
                "valor": valor,
            },
        )


def _semear_parametros_coleta(
    conexao: Connection, id_hotel: int, telefone: str
) -> None:
    for chave, valor in (
        ("contato_responsavel_dados", telefone),
        ("tentativas_max_envio_mensagem", "5"),
        ("horas_ate_reenvio", "24"),
        ("horas_corte_antes_checkin", "12"),
    ):
        conexao.execute(
            text(
                "INSERT INTO parametro_hotel (id_hotel, chave, valor) "
                "VALUES (:id_hotel, :chave, :valor)"
            ),
            {"id_hotel": id_hotel, "chave": chave, "valor": valor},
        )


def _semear_boas_vindas(conexao: Connection, id_hotel: int, sufixo: str) -> None:
    for chave, valor in (
        ("boas_vindas_cafe", f"Cafe da manha das 7h as 10h ({sufixo})"),
        ("boas_vindas_wifi", f"Wi-Fi: rede {sufixo}, senha na recepcao"),
        ("boas_vindas_checkout", f"Checkout ate as 12h ({sufixo})"),
        ("horas_validade_boas_vindas", "12"),
    ):
        conexao.execute(
            text(
                "INSERT INTO parametro_hotel (id_hotel, chave, valor) "
                "VALUES (:id_hotel, :chave, :valor)"
            ),
            {"id_hotel": id_hotel, "chave": chave, "valor": valor},
        )


def _inserir_usuario(
    conexao: Connection,
    id_hotel: int,
    nome: str,
    email: str,
    perfil: str,
    senha: str = SENHA_PADRAO,
    ativo: bool = True,
) -> UsuarioDeTeste:
    id_usuario = conexao.execute(
        text(
            "INSERT INTO usuario (id_hotel, nome, email, senha_hash, perfil, ativo) "
            "VALUES (:id_hotel, :nome, :email, :senha_hash, :perfil, :ativo) "
            "RETURNING id_usuario"
        ),
        {
            "id_hotel": id_hotel,
            "nome": nome,
            "email": email,
            "senha_hash": derivar_senha(senha, iteracoes=1_000),
            "perfil": perfil,
            "ativo": ativo,
        },
    ).scalar_one()
    return UsuarioDeTeste(
        id_usuario=id_usuario,
        id_hotel=id_hotel,
        nome=nome,
        email=email,
        perfil=perfil,
        senha=senha,
    )


def _montar_propriedade(
    conexao: Connection,
    nome_hotel: str,
    telefone: str,
    sufixo_email: str,
) -> PropriedadeDeTeste:
    id_hotel = _inserir_hotel(conexao, nome_hotel, telefone)
    _semear_duracoes(conexao, id_hotel)
    _semear_parametros_coleta(conexao, id_hotel, telefone)
    _semear_boas_vindas(conexao, id_hotel, sufixo_email)
    usuarios = {
        "gestor": _inserir_usuario(
            conexao,
            id_hotel,
            f"Gestor {sufixo_email}",
            f"gestor@{sufixo_email}.com",
            "gestor",
        ),
        "recepcao": _inserir_usuario(
            conexao,
            id_hotel,
            f"Recepcao {sufixo_email}",
            f"recepcao@{sufixo_email}.com",
            "recepcao",
        ),
        "staff": _inserir_usuario(
            conexao,
            id_hotel,
            f"Staff {sufixo_email}",
            f"staff@{sufixo_email}.com",
            "staff",
        ),
    }
    return PropriedadeDeTeste(id_hotel=id_hotel, nome=nome_hotel, usuarios=usuarios)


def criar_sessao(
    conexao: Connection,
    id_usuario: int,
    *,
    horas_de_validade: float = 12,
    dispositivo: str | None = "dispositivo-de-teste",
    revogada: bool = False,
    expirada: bool = False,
) -> tuple[str, int]:
    """Cria sessao e devolve (token em claro, id_sessao).

    `expirada=True` grava criada/expira no passado, respeitando o CHECK de
    que expira_em > criada_em.
    """
    agora = datetime.now(UTC)
    if expirada:
        criada_em = agora - timedelta(hours=2)
        expira_em = agora - timedelta(hours=1)
    else:
        criada_em = agora
        expira_em = agora + timedelta(hours=horas_de_validade)
    token = gerar_token()
    id_sessao = conexao.execute(
        text(
            "INSERT INTO sessao "
            "(id_usuario, token_hash, dispositivo, criada_em, expira_em, revogada_em) "
            "VALUES (:id_usuario, :token_hash, :dispositivo, :criada_em, :expira_em, "
            ":revogada_em) RETURNING id_sessao"
        ),
        {
            "id_usuario": id_usuario,
            "token_hash": hash_do_token(token),
            "dispositivo": dispositivo,
            "criada_em": criada_em,
            "expira_em": expira_em,
            "revogada_em": agora if revogada else None,
        },
    ).scalar_one()
    return token, id_sessao


@contextmanager
def ambiente_de_acesso() -> Iterator[AmbienteDeAcesso]:
    with banco_vazio() as url:
        aplicar_migracoes(url)
        engine = create_engine(url)
        try:
            with engine.begin() as conexao:
                propriedade_a = _montar_propriedade(
                    conexao, "Hotel Alpha", "5511999990001", "alpha"
                )
                propriedade_b = _montar_propriedade(
                    conexao, "Hotel Beta", "5511999990002", "beta"
                )
            yield AmbienteDeAcesso(
                url=url,
                engine=engine,
                propriedade_a=propriedade_a,
                propriedade_b=propriedade_b,
            )
        finally:
            engine.dispose()
