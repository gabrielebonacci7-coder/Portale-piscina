"""Il gestionale: chi entra, cosa vede, cosa può cambiare."""

from datetime import timedelta

from piscina.dominio.orologio import oggi

DOMANI = (oggi() + timedelta(days=1)).isoformat()


def prenota(client, codici, **extra):
    dati = {
        "giorno": DOMANI,
        "fascia": "giornata",
        "postazioni": [{"codice": c, "lettini": 2} for c in codici],
        "nome": "Mario Rossi",
        "telefono": "333 1234567",
        "email": "mario@example.com",
        "persone": 3,
    }
    dati.update(extra)
    risposta = client.post("/api/prenotazioni", json=dati)
    assert risposta.status_code == 201, risposta.text
    return risposta.json()


def test_senza_token_il_gestionale_e_chiuso(client):
    assert client.get("/api/staff/prenotazioni").status_code == 401
    assert client.get("/api/staff/prenotazioni.csv").status_code == 401
    assert client.get("/api/staff/postazioni").status_code == 401


def test_password_sbagliata_non_entra(client, operatore):
    r = client.post(
        "/api/staff/accesso", json={"email": operatore.email, "password": "sbagliata"}
    )
    assert r.status_code == 401
    # Stesso messaggio anche per un'email che non esiste: chi prova a
    # indovinare non deve capire quale delle due cose ha sbagliato.
    ignota = client.post(
        "/api/staff/accesso", json={"email": "nessuno@example.com", "password": "x"}
    )
    assert ignota.json()["detail"] == r.json()["detail"]


def test_lo_staff_vede_nomi_telefoni_ed_email(staff):
    prenota(staff, ["A1"])
    prenota(staff, ["A2"], nome="Anna Ferri", telefono="349 1112233", email="anna@example.com")

    dati = staff.get("/api/staff/prenotazioni", params={"giorno": DOMANI}).json()
    assert len(dati["prenotazioni"]) == 2
    prima = dati["prenotazioni"][0]
    assert prima["nome"] == "Mario Rossi"
    assert prima["telefono"] == "333 1234567"
    assert prima["email"] == "mario@example.com"
    assert prima["postazioni"] == ["A1"]

    riepilogo = dati["riepilogo"]
    assert riepilogo["prenotazioni"] == 2
    assert riepilogo["persone"] == 6
    assert riepilogo["ombrelloni"] == 2
    assert riepilogo["lettini"] == 4
    assert riepilogo["incasso_previsto"] == "24,00 €"


def test_ricerca_per_nome_telefono_codice_e_postazione(staff):
    uno = prenota(staff, ["B1"])
    prenota(staff, ["B2"], nome="Anna Ferri", telefono="349 1112233", email="anna@example.com")

    def cerca(q):
        return staff.get(
            "/api/staff/prenotazioni", params={"giorno": DOMANI, "cerca": q}
        ).json()["prenotazioni"]

    assert len(cerca("anna")) == 1
    assert len(cerca("3491112233")) == 1
    assert len(cerca(uno["codice"])) == 1
    assert len(cerca("B2")) == 1
    assert cerca("nessuno") == []


def test_segna_arrivato_e_annulla_dal_gestionale(staff):
    codice = prenota(staff, ["C1"])["codice"]

    r = staff.patch(f"/api/staff/prenotazioni/{codice}", json={"stato": "arrivato"})
    assert r.status_code == 200
    assert r.json()["stato"] == "arrivato"

    r = staff.patch(f"/api/staff/prenotazioni/{codice}", json={"stato": "annullata"})
    assert r.json()["stato"] == "annullata"

    # Annullata dallo staff: il posto torna libero come per il cliente.
    mappa = staff.get("/api/mappa", params={"giorno": DOMANI}).json()
    c1 = next(x for x in mappa["postazioni"] if x["codice"] == "C1")
    assert c1["libera_mattina"]

    assert staff.patch(
        f"/api/staff/prenotazioni/{codice}", json={"stato": "inventato"}
    ).status_code == 400


def test_esportazione_csv(staff):
    prenota(staff, ["D1"])
    r = staff.get("/api/staff/prenotazioni.csv", params={"giorno": DOMANI})
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    righe = r.text.strip().splitlines()
    assert righe[0].endswith("Note")
    assert "Mario Rossi" in righe[1]
    assert "333 1234567" in righe[1]


def test_spegnere_una_postazione_la_toglie_dalla_mappa(staff):
    r = staff.patch("/api/staff/postazioni/e1", json={"attiva": False, "nota": "rotto"})
    assert r.status_code == 200
    assert r.json() == {"codice": "E1", "attiva": False, "nota": "rotto"}

    mappa = staff.get("/api/mappa", params={"giorno": DOMANI}).json()
    e1 = next(x for x in mappa["postazioni"] if x["codice"] == "E1")
    assert not e1["attiva"] and not e1["libera_mattina"]
    assert mappa["riepilogo"]["spente"] == 1

    respinta = staff.post(
        "/api/prenotazioni",
        json={
            "giorno": DOMANI,
            "fascia": "giornata",
            "postazioni": [{"codice": "E1", "lettini": 1}],
            "nome": "Mario Rossi",
            "telefono": "333 1234567",
            "email": "mario@example.com",
        },
    )
    assert respinta.status_code == 400

    # E riaccenderla la rimette in gioco.
    staff.patch("/api/staff/postazioni/E1", json={"attiva": True, "nota": ""})
    assert staff.post(
        "/api/prenotazioni",
        json={
            "giorno": DOMANI,
            "fascia": "giornata",
            "postazioni": [{"codice": "E1", "lettini": 1}],
            "nome": "Mario Rossi",
            "telefono": "333 1234567",
            "email": "mario@example.com",
        },
    ).status_code == 201
