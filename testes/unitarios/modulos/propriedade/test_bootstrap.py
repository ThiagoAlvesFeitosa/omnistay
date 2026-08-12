"""Criacao inicial da propriedade: unidade, com repositorios falsos."""

from dataclasses import dataclass, field

import pytest

from app.modulos.propriedade import service as propriedade_service


@dataclass
class RepositorioDePropriedadeFalso:
    propriedades: list = field(default_factory=list)
    parametros: list = field(default_factory=list)
    falhar_em: str | None = None

    def existe_propriedade(self, conexao) -> bool:
        return bool(self.propriedades)

    def inserir_hotel(self, conexao, nome: str, telefone_whatsapp: str) -> int:
        if self.falhar_em == "hotel":
            raise RuntimeError("falha forçada na criação do hotel")
        id_hotel = len(self.propriedades) + 1
        self.propriedades.append(
            {"id_hotel": id_hotel, "nome": nome, "telefone": telefone_whatsapp}
        )
        return id_hotel

    def inserir_parametro(self, conexao, id_hotel: int, chave: str, valor: str) -> None:
        if self.falhar_em == "parametro":
            raise RuntimeError("falha forçada na criação do parâmetro")
        self.parametros.append(
            {"id_hotel": id_hotel, "chave": chave, "valor": valor}
        )


@dataclass
class ServicoDeUsuarioFalso:
    usuarios: list = field(default_factory=list)
    falhar: bool = False

    def criar_usuario(
        self,
        conexao,
        *,
        id_hotel: int,
        nome: str,
        email: str,
        perfil: str,
        senha: str,
    ) -> int:
        if self.falhar:
            raise RuntimeError("falha forçada na criação do usuário")
        id_usuario = len(self.usuarios) + 1
        self.usuarios.append(
            {
                "id_usuario": id_usuario,
                "id_hotel": id_hotel,
                "nome": nome,
                "email": email,
                "perfil": perfil,
                "senha": senha,
            }
        )
        return id_usuario


def test_criacao_inicial_grava_propriedade_gestor_e_duracoes():
    propriedade = RepositorioDePropriedadeFalso()
    usuarios = ServicoDeUsuarioFalso()

    resultado = propriedade_service.criar_instalacao_inicial(
        conexao=object(),
        nome_hotel="Hotel Exemplo",
        telefone_whatsapp="+5511999999999",
        nome_gestor="Thiago Feitosa",
        email_gestor="gestor@hotel.com.br",
        senha_gestor="senha-inicial-do-gestor",
        repositorio=propriedade,
        servico_de_usuario=usuarios,
    )

    assert resultado.id_hotel == 1
    assert resultado.email_gestor == "gestor@hotel.com.br"
    assert propriedade.propriedades[0]["nome"] == "Hotel Exemplo"
    assert usuarios.usuarios[0]["perfil"] == "gestor"
    assert usuarios.usuarios[0]["senha"] == "senha-inicial-do-gestor"
    chaves = {p["chave"] for p in propriedade.parametros}
    assert chaves == {
        "duracao_sessao_recepcao_horas",
        "duracao_sessao_staff_horas",
        "duracao_sessao_gestor_horas",
    }
    valores = {p["chave"]: p["valor"] for p in propriedade.parametros}
    assert valores["duracao_sessao_recepcao_horas"] == "12"
    assert valores["duracao_sessao_staff_horas"] == "720"
    assert valores["duracao_sessao_gestor_horas"] == "12"


def test_criacao_inicial_recusa_quando_ja_existe_propriedade():
    propriedade = RepositorioDePropriedadeFalso()
    propriedade.propriedades.append({"id_hotel": 1})
    usuarios = ServicoDeUsuarioFalso()

    with pytest.raises(propriedade_service.InstalacaoJaExiste) as erro:
        propriedade_service.criar_instalacao_inicial(
            conexao=object(),
            nome_hotel="Outro Hotel",
            telefone_whatsapp="+5511888888888",
            nome_gestor="Outro",
            email_gestor="outro@hotel.com.br",
            senha_gestor="senha-qualquer-123",
            repositorio=propriedade,
            servico_de_usuario=usuarios,
        )

    assert "propriedade" in str(erro.value).lower()
    assert usuarios.usuarios == []
    assert len(propriedade.propriedades) == 1
