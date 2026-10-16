"""Planejamento da migracao de hospede por hotel. Sem I/O; so ids."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class CopiaHospede:
    id_hospede_origem: int
    id_hotel: int
    ids_reserva: tuple[int, ...]


@dataclass(frozen=True)
class PlanoHospedePorHotel:
    atribuir: tuple[tuple[int, int], ...]
    copias: tuple[CopiaHospede, ...]
    orfaos: tuple[int, ...]
    consentimentos_copiar: tuple = ()

    def texto_orfaos(self) -> str:
        ids = ",".join(str(identidade) for identidade in self.orfaos)
        return f"hospede_migracao_orfao n={len(self.orfaos)} ids={ids}"


def planejar_hospede_por_hotel(
    *,
    ids_hospede: Sequence[int],
    vinculos: Sequence[tuple[int, int, int]],
    ids_hotel: Sequence[int],
) -> PlanoHospedePorHotel:
    reservas_por_hospede: dict[int, dict[int, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for id_hospede, id_hotel, id_reserva in vinculos:
        reservas_por_hospede[id_hospede][id_hotel].append(id_reserva)

    hoteis = tuple(ids_hotel)
    atribuir: list[tuple[int, int]] = []
    copias: list[CopiaHospede] = []
    orfaos: list[int] = []

    for id_hospede in ids_hospede:
        por_hotel = reservas_por_hospede.get(id_hospede, {})
        if not por_hotel:
            if len(hoteis) == 1:
                atribuir.append((id_hospede, hoteis[0]))
            elif len(hoteis) >= 2:
                orfaos.append(id_hospede)
            continue
        hoteis_do_hospede = tuple(sorted(por_hotel))
        original = hoteis_do_hospede[0]
        atribuir.append((id_hospede, original))
        for id_hotel in hoteis_do_hospede[1:]:
            ids_reserva = tuple(por_hotel[id_hotel])
            copias.append(
                CopiaHospede(
                    id_hospede_origem=id_hospede,
                    id_hotel=id_hotel,
                    ids_reserva=ids_reserva,
                )
            )

    return PlanoHospedePorHotel(
        atribuir=tuple(atribuir),
        copias=tuple(copias),
        orfaos=tuple(orfaos),
    )
