"""Montagem pura do texto da mensagem de coleta."""

CAMPOS_FICHA = (
    "Nome completo",
    "Profissao",
    "Data de nascimento",
    "Tipo de documento",
    "Numero do documento",
    "Endereco",
    "CEP",
    "Cidade",
    "Telefone",
)


def primeiro_nome(nome_completo: str) -> str:
    partes = nome_completo.strip().split()
    if not partes:
        raise ValueError("nome_completo vazio")
    return partes[0]


def montar_texto_coleta(*, nome_completo: str, contato_responsavel_dados: str) -> str:
    prenome = primeiro_nome(nome_completo)
    lista = "\n".join(
        f"{indice}. {campo}" for indice, campo in enumerate(CAMPOS_FICHA, start=1)
    )
    return (
        f"Ola, {prenome}!\n\n"
        "Para agilizar sua chegada, pedimos que nos envie seus dados cadastrais "
        "respondendo com a lista numerada abaixo. O preenchimento antecipado e "
        "opcional e serve para evitar espera na chegada; sem ele, o cadastro sera "
        "feito na recepcao.\n\n"
        "Finalidade: coletar os dados necessarios ao cadastro de hospede para a "
        "hospedagem prevista, evitando espera na chegada.\n\n"
        f"{lista}\n\n"
        f"Responsavel pelos dados: {contato_responsavel_dados}"
    )
