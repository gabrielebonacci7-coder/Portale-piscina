"""Le regole che decidono chi può stare dove: mattina, pomeriggio, giornata."""

from datetime import timedelta

import pytest

from piscina.crud import prenotazioni as crud
from piscina.dominio.disponibilita import GIORNATA, MATTINA, POMERIGGIO
from piscina.dominio.orologio import oggi
from piscina.models import Postazione


def prenota(db, codici, fascia=GIORNATA, lettini=2, giorno=None, nome="Mario Rossi"):
    return crud.crea(
        db,
        giorno=giorno or oggi() + timedelta(days=1),
        fascia=fascia,
        scelte=[crud.Scelta(codice=c, lettini=lettini) for c in codici],
        nome=nome,
        telefono="333 1234567",
        email="mario@example.com",
        persone=2,
    )


def stato(db, giorno, codice):
    return next(p for p in crud.mappa_del_giorno(db, giorno) if p["codice"] == codice)


def test_piantina_ha_cinquanta_ombrelloni(db):
    postazioni = crud.mappa_del_giorno(db, oggi())
    ombrelloni = [p for p in postazioni if p["tipo"] == "ombrellone"]
    lettini = [p for p in postazioni if p["tipo"] == "lettino"]
    assert len(ombrelloni) == 50
    assert len(lettini) == 12
    # Tutte libere: nessuno ha ancora prenotato niente.
    assert all(p["libera_mattina"] and p["libera_pomeriggio"] for p in postazioni)


def test_giornata_intera_occupa_tutto_il_giorno(db):
    domani = oggi() + timedelta(days=1)
    prenota(db, ["A1"], GIORNATA)
    a1 = stato(db, domani, "A1")
    assert not a1["libera_mattina"] and not a1["libera_pomeriggio"]
    # Il giorno dopo non c'entra niente.
    assert stato(db, domani + timedelta(days=1), "A1")["libera_mattina"]


def test_mattina_e_pomeriggio_convivono_sulla_stessa_postazione(db):
    domani = oggi() + timedelta(days=1)
    prenota(db, ["A2"], MATTINA)
    dopo = stato(db, domani, "A2")
    assert not dopo["libera_mattina"]
    assert dopo["libera_pomeriggio"]

    # Un'altra persona prende lo stesso ombrellone per il pomeriggio: si può.
    prenota(db, ["A2"], POMERIGGIO, nome="Anna Ferri")
    pieno = stato(db, domani, "A2")
    assert not pieno["libera_mattina"] and not pieno["libera_pomeriggio"]


def test_due_volte_la_stessa_mezza_giornata_non_si_puo(db):
    prenota(db, ["A3"], MATTINA)
    with pytest.raises(crud.PostoOccupato) as e:
        prenota(db, ["A3"], MATTINA, nome="Anna Ferri")
    assert "A3" in str(e.value)


def test_la_giornata_intera_non_entra_dove_c_e_gia_una_mezza(db):
    prenota(db, ["A4"], POMERIGGIO)
    with pytest.raises(crud.PostoOccupato):
        prenota(db, ["A4"], GIORNATA, nome="Anna Ferri")


def test_annullare_libera_subito_il_posto(db):
    domani = oggi() + timedelta(days=1)
    prenotazione = prenota(db, ["A5"], GIORNATA)
    crud.annulla(db, prenotazione)

    libera = stato(db, domani, "A5")
    assert libera["libera_mattina"] and libera["libera_pomeriggio"]
    # E adesso la può prendere qualcun altro.
    prenota(db, ["A5"], GIORNATA, nome="Anna Ferri")


def test_postazione_spenta_non_si_prenota(db):
    a6 = db.query(Postazione).filter_by(codice="A6").one()
    a6.attiva = False
    a6.nota = "ombrellone rotto"
    db.commit()

    assert not stato(db, oggi(), "A6")["libera_mattina"]
    with pytest.raises(crud.RichiestaNonValida):
        prenota(db, ["A6"])


def test_troppi_lettini_sotto_un_ombrellone(db):
    with pytest.raises(crud.RichiestaNonValida):
        prenota(db, ["A7"], lettini=4)


def test_il_lettino_del_solarium_non_porta_altri_lettini(db):
    prenotazione = prenota(db, ["S1"], lettini=3)
    riga = prenotazione.righe[0]
    assert riga.lettini == 0
    assert riga.prezzo_cent == 500  # tariffa lettino singolo


def test_il_conto_segue_il_listino(db):
    # Relax 2 = ombrellone + 2 lettini = 12 €, per due postazioni 24 €.
    prenotazione = prenota(db, ["C1", "C2"], lettini=2)
    assert prenotazione.totale_cent == 2400
    # Solo ombrellone: 5 €.
    assert prenota(db, ["C3"], lettini=0).totale_cent == 500
    # Relax 1 e Relax 3.
    assert prenota(db, ["C4"], lettini=1).totale_cent == 700
    assert prenota(db, ["C5"], lettini=3).totale_cent == 1700


def test_non_si_prenota_nel_passato(db):
    with pytest.raises(crud.RichiestaNonValida):
        prenota(db, ["D1"], giorno=oggi() - timedelta(days=1))


def test_non_si_prenota_troppo_avanti(db):
    with pytest.raises(crud.RichiestaNonValida):
        prenota(db, ["D2"], giorno=oggi() + timedelta(days=365))


def test_stessa_postazione_due_volte_nella_stessa_prenotazione(db):
    with pytest.raises(crud.RichiestaNonValida):
        prenota(db, ["D3", "D3"])


def test_tetto_alle_postazioni_per_prenotazione(db):
    with pytest.raises(crud.RichiestaNonValida):
        prenota(db, ["E1", "E2", "E3", "E4", "E5"])


def test_postazione_inesistente(db):
    with pytest.raises(crud.RichiestaNonValida):
        prenota(db, ["Z9"])


def test_si_ritrova_con_codice_e_telefono_scritto_in_altro_modo(db):
    prenotazione = prenota(db, ["E6"])
    trovata = crud.per_codice_e_telefono(db, prenotazione.codice.lower(), "+39 333 12 34 567")
    assert trovata is not None and trovata.id == prenotazione.id
    assert crud.per_codice_e_telefono(db, prenotazione.codice, "333 0000000") is None
