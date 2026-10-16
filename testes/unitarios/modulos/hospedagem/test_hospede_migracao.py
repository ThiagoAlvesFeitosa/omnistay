"""Planejamento da migracao de hospede por hotel. Sem I/O."""

from app.modulos.hospedagem.hospede_migracao import planejar_hospede_por_hotel


def test_reservas_de_um_hotel_atribuem_esse_hotel():
    plano = planejar_hospede_por_hotel(
        ids_hospede=(7,),
        vinculos=((7, 10, 100),),
        ids_hotel=(10, 20),
    )
    assert plano.atribuir == ((7, 10),)
    assert plano.copias == ()
    assert plano.orfaos == ()


def test_dois_hoteis_conservam_o_menor_e_planejam_copia_sem_consentimento():
    plano = planejar_hospede_por_hotel(
        ids_hospede=(7,),
        vinculos=((7, 20, 201), (7, 10, 101), (7, 20, 202)),
        ids_hotel=(10, 20),
    )
    assert plano.atribuir == ((7, 10),)
    assert len(plano.copias) == 1
    copia = plano.copias[0]
    assert copia.id_hospede_origem == 7
    assert copia.id_hotel == 20
    assert copia.ids_reserva == (201, 202)
    assert getattr(plano, "consentimentos_copiar", ()) == ()
    assert plano.orfaos == ()


def test_orfao_com_um_hotel_fica_desse_hotel():
    plano = planejar_hospede_por_hotel(
        ids_hospede=(9,),
        vinculos=(),
        ids_hotel=(10,),
    )
    assert plano.atribuir == ((9, 10),)
    assert plano.copias == ()
    assert plano.orfaos == ()


def test_orfao_com_dois_hoteis_nao_recebe_dono():
    plano = planejar_hospede_por_hotel(
        ids_hospede=(9,),
        vinculos=(),
        ids_hotel=(10, 20),
    )
    assert plano.orfaos == (9,)
    assert plano.atribuir == ()
    assert plano.copias == ()


def test_texto_de_orfao_nao_traz_documento():
    plano = planejar_hospede_por_hotel(
        ids_hospede=(9, 11),
        vinculos=(),
        ids_hotel=(10, 20),
    )
    recado = plano.texto_orfaos()
    assert "hospede_migracao_orfao" in recado
    assert "n=2" in recado
    assert "ids=" in recado
    assert "9" in recado
    assert "11" in recado
    assert "cpf" not in recado.lower()
    assert "52998224725" not in recado
