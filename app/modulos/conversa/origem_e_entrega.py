"""Origem e entrega da conversa da estadia — sem coluna nova."""

TIPO_RESPOSTA_RECEPCAO = "resposta_recepcao"


def origem(*, direcao: str, classificacao_bruta: dict | None) -> str:
    if direcao == "recebida":
        return "hospede"
    tipo = (classificacao_bruta or {}).get("tipo")
    if tipo == TIPO_RESPOSTA_RECEPCAO:
        return "recepcao"
    return "automatico"


def entrega(
    *,
    status_envio: str | None,
    status_trabalho: str | None,
) -> tuple[str | None, bool | None]:
    if status_envio is None:
        return None, None
    if status_envio in ("enviada", "entregue"):
        return "enviada", False
    if status_envio == "falha":
        return "falhou", status_trabalho != "concluido"
    return "enviando", False
