"""Marcacao sem_cadastro_previo com repositorio falso."""

from dataclasses import dataclass, field

from app.modulos.hospedagem import service as hospedagem


@dataclass
class Repo:
    updates: list = field(default_factory=list)

    def marcar_sem_cadastro_previo(self, conexao, *, id_hotel, id_reserva):
        self.updates.append({"id_hotel": id_hotel, "id_reserva": id_reserva})


def test_marcar_passa_id_hotel_e_id_reserva():
    repo = Repo()
    hospedagem.marcar_sem_cadastro_previo(
        object(), id_hotel=10, id_reserva=7, repositorio=repo
    )
    assert repo.updates == [{"id_hotel": 10, "id_reserva": 7}]
