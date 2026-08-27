"""Il giro completo visto dall'app: mappa, prenotazione, conferma, annullamento."""

from datetime import timedelta

from piscina.core import email as posta
from piscina.dominio.orologio import oggi


def corpo(codici, fascia="giornata", lettini=2, giorno=None, **extra):
    dati = {
        "giorno": (giorno or oggi() + timedelta(days=1)).isoformat(),
        "fascia": fascia,
        "postazioni": [{"codice": c, "lettini": lettini} for c in codici],
        "nome": "Mario Rossi",
        "telefono": "333 1234567",
        "email": "mario@example.com",
        "persone": 3,
    }
    dati.update(extra)
    return dati


def test_la_mappa_arriva_con_scenografia_e_riepilogo(client):
    r = client.get("/api/mappa")
    assert r.status_code == 200
    dati = r.json()
    assert dati["viewbox"]
    assert len(dati["postazioni"]) == 62
    assert dati["riepilogo"]["libere"] == 62
    # Le vasche e la cassa servono a capire da che parte si sta guardando.
    tipi = {e["tipo"] for e in dati["scenografia"]}
    assert {"vasca", "cassa", "bagnino"} <= tipi


def test_prenotazione_completa(client):
    r = client.post("/api/prenotazioni", json=corpo(["A1", "A2"]))
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["codice"].startswith("PC-")
    assert p["totale_cent"] == 2400
    assert p["totale"] == "24,00 €"
    assert [riga["codice"] for riga in p["righe"]] == ["A1", "A2"]
    assert p["orario"] == "09:00–19:00"

    # E la mappa lo mostra subito.
    mappa = client.get("/api/mappa", params={"giorno": corpo([])["giorno"]}).json()
    a1 = next(x for x in mappa["postazioni"] if x["codice"] == "A1")
    assert not a1["libera_mattina"] and not a1["libera_pomeriggio"]
    assert mappa["riepilogo"]["occupate"] == 2


def test_posto_gia_preso_risponde_409(client):
    client.post("/api/prenotazioni", json=corpo(["B1"]))
    r = client.post("/api/prenotazioni", json=corpo(["B1"]))
    assert r.status_code == 409
    assert "B1" in r.json()["detail"]


def test_mezze_giornate_diverse_convivono(client):
    assert client.post("/api/prenotazioni", json=corpo(["B2"], "mattina")).status_code == 201
    assert client.post("/api/prenotazioni", json=corpo(["B2"], "pomeriggio")).status_code == 201

    mappa = client.get("/api/mappa", params={"giorno": corpo([])["giorno"]}).json()
    b2 = next(x for x in mappa["postazioni"] if x["codice"] == "B2")
    assert not b2["libera_mattina"] and not b2["libera_pomeriggio"]


def test_mezza_giornata_si_vede_come_mezza(client):
    client.post("/api/prenotazioni", json=corpo(["B3"], "mattina"))
    mappa = client.get("/api/mappa", params={"giorno": corpo([])["giorno"]}).json()
    b3 = next(x for x in mappa["postazioni"] if x["codice"] == "B3")
    assert not b3["libera_mattina"]
    assert b3["libera_pomeriggio"]
    assert mappa["riepilogo"]["mezze"] == 1


def test_dati_del_cliente_controllati(client):
    assert client.post("/api/prenotazioni", json=corpo(["C1"], nome="X")).status_code == 422
    assert client.post("/api/prenotazioni", json=corpo(["C1"], telefono="123")).status_code == 422
    assert client.post(
        "/api/prenotazioni", json=corpo(["C1"], email="non-una-email")
    ).status_code == 422
    assert client.post("/api/prenotazioni", json=corpo([])).status_code == 422


def test_giorno_passato_rifiutato(client):
    r = client.post("/api/prenotazioni", json=corpo(["C2"], giorno=oggi() - timedelta(days=2)))
    assert r.status_code == 400


def test_si_ritrova_e_si_annulla_con_codice_e_telefono(client):
    codice = client.post("/api/prenotazioni", json=corpo(["D1"])).json()["codice"]

    assert client.get(f"/api/prenotazioni/{codice}", params={"telefono": "999"}).status_code == 404
    trovata = client.get(f"/api/prenotazioni/{codice}", params={"telefono": "3331234567"})
    assert trovata.status_code == 200
    assert trovata.json()["nome"] == "Mario Rossi"

    r = client.post(f"/api/prenotazioni/{codice}/annulla", json={"telefono": "333 1234567"})
    assert r.status_code == 200
    assert r.json()["stato"] == "annullata"

    # Il posto è di nuovo libero.
    mappa = client.get("/api/mappa", params={"giorno": corpo([])["giorno"]}).json()
    d1 = next(x for x in mappa["postazioni"] if x["codice"] == "D1")
    assert d1["libera_mattina"] and d1["libera_pomeriggio"]


def test_le_email_partono_a_staff_e_cliente(client, monkeypatch):
    spedite = []
    monkeypatch.setattr(
        posta, "invia_email", lambda a, oggetto, testo: spedite.append((a, oggetto, testo))
    )

    r = client.post("/api/prenotazioni", json=corpo(["E1"]))
    codice = r.json()["codice"]

    destinatari = [a for a, _, _ in spedite]
    assert "cassa@example.com" in destinatari  # il gestionale
    assert "mario@example.com" in destinatari  # la conferma al cliente

    allo_staff = next(t for a, _, t in spedite if a == "cassa@example.com")
    # È questo il punto di tutta la faccenda: allo staff arrivano i contatti.
    assert "Mario Rossi" in allo_staff
    assert "333 1234567" in allo_staff
    assert "mario@example.com" in allo_staff
    assert codice in allo_staff
    assert "E1" in allo_staff


def test_listino_e_info(client):
    listino = client.get("/api/listino").json()
    assert listino["ingressi"][0]["residenti"] == 800
    assert any(v["lettini"] == 3 and v["intera"] == 1700 for v in listino["noleggio"])

    info = client.get("/api/info").json()
    assert info["telefono"]
    assert info["postazioni"]["ombrelloni"] == 50
    assert [f["valore"] for f in info["fasce"]] == ["giornata", "mattina", "pomeriggio"]
    # La guida: paragrafi e sezioni da mostrare mentre si racconta.
    passi = info["benvenuto"]["passi"]
    assert len(passi) >= 3
    assert {"mappa", "prezzi", "contatti"} <= {p.get("vetrina") for p in passi}
    assert info["contatti"]["whatsapp"]
