"""Matriz de perfil por operacao: decisao pura, sem HTTP e sem banco."""

from typing import Final

OPERACOES: Final[dict[str, frozenset[str]]] = {
    "ver_sessao_propria": frozenset({"recepcao", "staff", "gestor"}),
    "encerrar_sessao_propria": frozenset({"recepcao", "staff", "gestor"}),
    "listar_sessoes": frozenset({"recepcao"}),
    "revogar_sessao": frozenset({"recepcao"}),
    "administrar_usuario": frozenset({"gestor"}),
    "ler_dado_cadastral_de_hospede": frozenset({"recepcao"}),
    "ler_ficha_de_hospede": frozenset({"recepcao"}),
    "alterar_ficha_de_hospede": frozenset({"recepcao"}),
    "alterar_reserva": frozenset({"recepcao"}),
    "confirmar_fase_da_reserva": frozenset({"recepcao"}),
    "ler_fila_do_dia": frozenset({"recepcao"}),
    "ler_solicitacao_atribuida": frozenset({"recepcao", "staff", "gestor"}),
    "resolver_solicitacao": frozenset({"recepcao", "staff"}),
    "lancar_consumo": frozenset({"recepcao"}),
    "alterar_catalogo": frozenset({"recepcao"}),
    "ler_catalogo": frozenset({"recepcao", "gestor"}),
    "ler_indicadores": frozenset({"recepcao", "gestor"}),
    "alterar_texto_de_boas_vindas": frozenset({"recepcao"}),
    "ler_texto_de_boas_vindas": frozenset({"recepcao", "gestor"}),
    "ler_consentimento": frozenset({"recepcao", "gestor"}),
    "registrar_consentimento": frozenset({"recepcao", "gestor"}),
    "ler_pedidos_feitos_pelo_chat": frozenset({"recepcao", "gestor"}),
}


def permitido(perfil: str, operacao: str) -> bool:
    """Operacao desconhecida e recusada: erro de digitacao nao pode abrir porta."""
    perfis = OPERACOES.get(operacao)
    if perfis is None:
        return False
    return perfil in perfis
