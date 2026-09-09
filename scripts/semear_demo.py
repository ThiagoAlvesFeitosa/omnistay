"""Povoa a propriedade com um cenario de demonstracao.

Nao substitui o bootstrap: rode `python -m app.bootstrap` primeiro. Este script
usa a API HTTP, entao passa pelas mesmas regras e permissoes do sistema real —
nada entra no banco por caminho que a aplicacao nao permitiria.

Uso:
    uv run python scripts/semear_demo.py --email thiago@hotel.com.br --senha SENHA

O que ele cria:
    - usuario de recepcao e usuario de equipe operacional
    - catalogo com itens em quatro categorias
    - tres itens vendaveis com preco
    - os quatro textos do recado de boas-vindas
    - cinco reservas em estados diferentes, para a fila do dia nao nascer vazia

O que ele NAO cria: chamados, pedidos e consumos. Esses nascem da conversa do
hospede no simulador, e e assim que devem ser demonstrados.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

import httpx

BASE = "http://127.0.0.1:8000"

SENHA_RECEPCAO = "recepcao2026demo"
SENHA_EQUIPE = "equipe2026demo"

CATALOGO = [
    ("horario", "Cafe da manha",
     "Servido das 7h as 10h no salao terreo. Aos domingos ate as 11h."),
    ("horario", "Piscina",
     "Aberta das 8h as 22h. Criancas devem estar acompanhadas de um adulto."),
    ("horario", "Academia",
     "Aberta 24 horas. O acesso e feito com a chave do quarto."),
    ("servico", "Lavanderia",
     "Entrega em ate 24 horas. Pedidos feitos ate as 18h saem no dia seguinte."),
    ("servico", "Estacionamento",
     "Vagas cobertas no subsolo, sem custo adicional para hospedes."),
    ("cardapio", "Bar da piscina",
     "Caipirinha, cerveja long neck, agua com gas e porcoes. Das 10h as 22h."),
    ("programacao", "Musica ao vivo",
     "Sextas e sabados, das 19h as 22h, no bar da piscina."),
    ("regra", "Animais",
     "Nao aceitamos animais de estimacao."),
    ("regra", "Horario de silencio",
     "Das 22h as 7h, por respeito aos demais hospedes."),
]

VENDAVEIS = [
    ("Caipirinha", "28.00"),
    ("Agua com gas 500ml", "9.00"),
    ("Lavanderia - camisa", "32.00"),
]

CONCORRENTES = [
    ("Pousada Alvorada", "https://exemplo-pousada-alvorada.com.br/tarifas"),
    ("Hotel Central", "https://exemplo-hotel-central.com.br/reservas"),
    ("Ibis Centro", "https://exemplo-ibis-centro.com.br/quartos"),
]

BOAS_VINDAS = {
    "cafe": "das 7h as 10h no salao terreo",
    "wifi": "rede HotelExemplo, senha na recepcao",
    "checkout": "12h",
    "convite": "Quer saber dos nossos servicos, do cardapio ou dos horarios? "
               "E so perguntar por aqui.",
}


def _erro(resposta: httpx.Response, o_que: str) -> None:
    print(f"  ! falhou ao {o_que}: {resposta.status_code} {resposta.text[:160]}")


def entrar(cliente: httpx.Client, email: str, senha: str) -> bool:
    r = cliente.post("/sessoes", json={"email": email, "senha": senha})
    if r.status_code >= 400:
        _erro(r, f"entrar como {email}")
        return False
    print(f"  entrou como {email} ({r.json().get('perfil')})")
    return True


def criar_usuarios(cliente: httpx.Client, *, criar_recepcao: bool = True) -> None:
    print("Usuarios")
    desejados = [("Ivan Souza", "ivan@hotel.com.br", "staff", SENHA_EQUIPE)]
    if criar_recepcao:
        desejados.insert(
            0, ("Cleber Rocha", "cleber@hotel.com.br", "recepcao", SENHA_RECEPCAO)
        )
    else:
        print("  recepcao: usando o usuario que voce ja tem")
    for nome, email, perfil, senha in desejados:
        r = cliente.post("/usuarios", json={
            "nome": nome, "email": email, "perfil": perfil, "senha": senha,
        })
        if r.status_code >= 400:
            print(f"  {email}: ja existe ou recusado ({r.status_code})")
        else:
            print(f"  criado {email} ({perfil})")


def criar_concorrentes(cliente: httpx.Client) -> None:
    """So a gestao cadastra concorrente. A coleta e disparada pelo worker."""
    print("Concorrentes")
    for nome, url in CONCORRENTES:
        r = cliente.post("/concorrentes", json={"nome": nome, "url_fonte": url})
        if r.status_code >= 400:
            print(f"  {nome}: ja existe ou recusado ({r.status_code})")
        else:
            print(f"  {nome}")
    print("  (para coletar: uv run python -m worker --verificar-mercado)")


def criar_catalogo(cliente: httpx.Client) -> None:
    print("Catalogo")
    for categoria, titulo, conteudo in CATALOGO:
        r = cliente.post("/catalogo", json={
            "categoria": categoria, "titulo": titulo, "conteudo": conteudo,
        })
        if r.status_code >= 400:
            _erro(r, f"criar item {titulo}")
        else:
            print(f"  {categoria}: {titulo}")


def criar_vendaveis(cliente: httpx.Client) -> None:
    print("Itens vendaveis")
    for nome, preco in VENDAVEIS:
        r = cliente.post("/itens-vendaveis", json={
            "nome": nome, "preco_atual": preco,
        })
        if r.status_code >= 400:
            _erro(r, f"criar item vendavel {nome}")
        else:
            print(f"  {nome} - R$ {preco}")


def gravar_boas_vindas(cliente: httpx.Client) -> None:
    print("Recado de boas-vindas")
    r = cliente.put("/propriedade/boas-vindas", json=BOAS_VINDAS)
    if r.status_code >= 400:
        _erro(r, "gravar o recado")
    else:
        print("  quatro campos gravados")


def criar_reservas(cliente: httpx.Client) -> None:
    """Cinco reservas em estados diferentes, para a fila do dia ter o que mostrar."""
    print("Reservas")
    hoje = date.today()
    cenarios = [
        # (nome, telefone, entrada, saida, confirmar_chegada)
        ("Marina Duarte", "11987654321", hoje, hoje + timedelta(days=2), False),
        ("Rafael Nunes", "21978889999", hoje, hoje + timedelta(days=1), False),
        ("Ana Prado", "11994445555", hoje, hoje + timedelta(days=4), False),
        # chegada vencida: entrou ontem e ninguem confirmou — vira o alerta da fila
        ("Carlos Beltrao", "31982221111", hoje - timedelta(days=1),
         hoje + timedelta(days=1), False),
        # ja hospedada: confirma a chegada logo em seguida
        ("Julia Manso", "11967778888", hoje - timedelta(days=2),
         hoje + timedelta(days=3), True),
    ]
    for nome, telefone, entrada, saida, confirmar in cenarios:
        r = cliente.post("/reservas", json={
            "nome": nome,
            "telefone": telefone,
            "data_checkin_prevista": entrada.isoformat(),
            "data_checkout_prevista": saida.isoformat(),
        })
        if r.status_code >= 400:
            _erro(r, f"criar reserva de {nome}")
            continue
        id_reserva = r.json()["id_reserva"]
        marca = ""
        if confirmar:
            c = cliente.post(f"/reservas/{id_reserva}/chegada", json={})
            marca = " [hospedada]" if c.status_code < 400 else " [chegada recusada]"
        elif entrada < hoje:
            marca = " [chegada vencida]"
        print(f"  #{id_reserva} {nome}{marca}")


def main() -> int:
    p = argparse.ArgumentParser(description="Povoa a propriedade para demonstracao.")
    p.add_argument("--email", required=True, help="e-mail do gestor criado no bootstrap")
    p.add_argument("--senha", required=True, help="senha do gestor")
    p.add_argument(
        "--email-recepcao",
        help="usar um usuario de recepcao que ja existe, em vez de criar um novo",
    )
    p.add_argument("--senha-recepcao", help="senha do usuario de recepcao existente")
    p.add_argument("--base", default=BASE, help=f"endereco da API (padrao {BASE})")
    a = p.parse_args()

    usar_existente = bool(a.email_recepcao and a.senha_recepcao)
    email_recepcao = a.email_recepcao or "cleber@hotel.com.br"
    senha_recepcao = a.senha_recepcao or SENHA_RECEPCAO

    with httpx.Client(base_url=a.base, timeout=30.0, follow_redirects=True) as cliente:
        print("== Gestao ==")
        if not entrar(cliente, a.email, a.senha):
            print("\nNao consegui entrar. A API esta rodando? A senha esta certa?")
            return 1
        criar_usuarios(cliente, criar_recepcao=not usar_existente)
        criar_concorrentes(cliente)

        print("\n== Recepcao ==")
        if not entrar(cliente, email_recepcao, senha_recepcao):
            print("\nNao consegui entrar como recepcao.")
            return 1
        criar_catalogo(cliente)
        criar_vendaveis(cliente)
        gravar_boas_vindas(cliente)
        criar_reservas(cliente)

    print("\nPronto. Abra http://localhost:8000/app e entre como:")
    print(f"  recepcao  {email_recepcao}")
    print(f"  equipe    ivan@hotel.com.br / {SENHA_EQUIPE}")
    print(f"  gestao    {a.email} / (a sua senha)")
    print("\nO worker precisa estar rodando para as mensagens sairem da fila.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
