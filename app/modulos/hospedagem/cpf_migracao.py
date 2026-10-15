"""Planejamento da forma canonica de CPF. Sem I/O; so ids e grupos."""

from dataclasses import dataclass


def forma_digitos(numero: str) -> str:
    return "".join(c for c in numero if c.isdigit())


@dataclass(frozen=True)
class PlanoMigracaoCpf:
    converter: tuple[int, ...]
    pular: tuple[int, ...]
    pares: int

    def texto_colisao(self) -> str:
        ids = ",".join(str(identidade) for identidade in self.pular)
        return f"cpf_migracao_colisao pares={self.pares} ids={ids}"


def planejar_migracao_cpf(linhas: list[tuple[int, str]]) -> PlanoMigracaoCpf:
    grupos: dict[str, list[int]] = {}
    for id_hospede, numero in linhas:
        forma = forma_digitos(numero)
        if not forma:
            continue
        grupos.setdefault(forma, []).append(id_hospede)

    converter: list[int] = []
    pular: list[int] = []
    pares = 0
    for ids in grupos.values():
        if len(ids) == 1:
            converter.extend(ids)
        else:
            pares += 1
            pular.extend(ids)
    return PlanoMigracaoCpf(tuple(converter), tuple(pular), pares)
