"""Le regole dello studio, provate attraverso l'API come le usa l'app."""

from reformer.models import Notifica
from reformer.tests.conftest import (
    ELISA,
    GRETA,
    auth,
    carica,
    codice_dal_link,
    lezioni,
    registra,
)


def io(client, token):
    return client.get("/api/io", headers=auth(token)).json()


def domani(client, token, indice=0):
    return lezioni(client, token, "2026-10-13")[indice]


# ------------------------------------------------------------------ orario
def test_orario_della_settimana(client, cliente):
    settimana = lezioni(client, cliente, "2026-10-12", 7)
    per_giorno = {}
    for l in settimana:
        per_giorno.setdefault(l["inizio"][:10], []).append(l)
    assert len(per_giorno["2026-10-12"]) == 3          # lunedì
    assert len(per_giorno["2026-10-17"]) == 2          # sabato
    assert "2026-10-18" not in per_giorno              # domenica chiuso
    assert {l["istruttrice"]["id"] for l in per_giorno["2026-10-13"]} == {"elisa"}  # martedì
    assert {l["istruttrice"]["id"] for l in per_giorno["2026-10-14"]} == {"greta"}  # mercoledì
    assert {l["istruttrice"]["id"] for l in per_giorno["2026-10-17"]} == {"greta"}  # sabato
    assert all(l["posti"] == 3 for l in settimana)


def test_ora_legale(client, cliente):
    """Il 25 ottobre cambia l'ora: le 15:30 restano le 15:30 a Roma."""
    prima = lezioni(client, cliente, "2026-10-23")[0]["inizio"]
    dopo = lezioni(client, cliente, "2026-10-26")[0]["inizio"]
    assert prima.startswith("2026-10-23T13:30")   # 15:30 a Roma, UTC+2
    assert dopo.startswith("2026-10-26T14:30")    # 15:30 a Roma, UTC+1


def test_calendario_entro_limiti_ragionevoli(client, cliente):
    assert client.get("/api/lezioni?da=3000-01-01", headers=auth(cliente)).status_code == 400
    assert client.get("/api/lezioni?da=2020-01-01", headers=auth(cliente)).status_code == 400
    assert client.get("/api/lezioni?da=2026-12-01&giorni=31", headers=auth(cliente)).status_code == 200


def test_la_cliente_non_vede_chi_ce(client, cliente):
    l = lezioni(client, cliente)[0]
    assert "iscritte" not in l and "attesa" not in l


# --------------------------------------------------------------- prenotare
def test_prenota_e_scala_una_lezione(client, staff, cliente):
    carica(client, staff, io(client, cliente)["id"], 5)
    l = domani(client, cliente)
    r = client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    assert r.status_code == 200, r.text
    assert r.json()["lezione"]["mia"] is True
    assert r.json()["lezione"]["liberi"] == 2
    assert r.json()["utente"]["lezioni_rimaste"] == 4


def test_non_due_volte(client, cliente):
    l = domani(client, cliente)
    assert client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente)).status_code == 200
    assert client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente)).status_code == 409


def test_tre_posti_poi_piena(client, cliente):
    l = domani(client, cliente)
    altre = [registra(client, f"c{i}@example.com")["token"] for i in range(3)]
    for t in altre:
        assert client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(t)).status_code == 200
    r = client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    assert r.status_code == 409
    assert "piena" in r.json()["detail"]


def test_non_oltre_un_mese(client, cliente):
    vicina = lezioni(client, cliente, "2026-11-11")[0]   # 30 giorni: si può
    lontana = lezioni(client, cliente, "2026-11-13")[0]  # 32 giorni: no
    assert vicina["prenotabile"] and not lontana["prenotabile"]
    assert client.post(f"/api/lezioni/{vicina['id']}/prenota", headers=auth(cliente)).status_code == 200
    r = client.post(f"/api/lezioni/{lontana['id']}/prenota", headers=auth(cliente))
    assert r.status_code == 409 and "30 giorni" in r.json()["detail"]


def test_non_una_lezione_gia_iniziata(client, cliente, orologio):
    l = lezioni(client, cliente)[0]
    orologio.avanti(hours=8)  # le 17:00, la lezione delle 15:30 è iniziata
    assert client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente)).status_code == 409


def test_senza_lezioni_si_prenota_e_lo_staff_lo_sa(client, staff, cliente):
    l = domani(client, cliente)
    r = client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    assert r.status_code == 200
    assert r.json()["utente"]["lezioni_rimaste"] == -1
    avvisi = client.get("/api/notifiche", headers=auth(staff)).json()["elenco"]
    assert any("senza lezioni" in n["testo"] and "Sofia Marini" in n["testo"] for n in avvisi)
    numeri = client.get("/api/staff/numeri", headers=auth(staff)).json()
    assert [c["email"] for c in numeri["da_saldare"]] == ["sofia@example.com"]


def test_al_massimo_due_lezioni_da_saldare(client, cliente):
    settimana = [l for l in lezioni(client, cliente, "2026-10-13", 5)]
    for l in settimana[:2]:
        assert client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente)).status_code == 200
    r = client.post(f"/api/lezioni/{settimana[2]['id']}/prenota", headers=auth(cliente))
    assert r.status_code == 409 and "da saldare" in r.json()["detail"]


# ------------------------------------------------------------------ disdire
def test_disdetta_in_tempo_restituisce_la_lezione(client, staff, cliente):
    carica(client, staff, io(client, cliente)["id"], 3)
    l = domani(client, cliente)
    client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    r = client.delete(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    assert r.status_code == 200, r.text
    assert r.json()["utente"]["lezioni_rimaste"] == 3
    assert r.json()["lezione"]["mia"] is False


def test_meno_di_12_ore_non_si_disdice(client, cliente):
    oggi = lezioni(client, cliente)[0]  # 15:30, fra 6 ore e mezza
    assert oggi["disdicibile"] is False
    client.post(f"/api/lezioni/{oggi['id']}/prenota", headers=auth(cliente))
    r = client.delete(f"/api/lezioni/{oggi['id']}/prenota", headers=auth(cliente))
    assert r.status_code == 409
    assert "12 ore" in r.json()["detail"]


def test_il_limite_e_esatto(client, cliente, orologio):
    l = domani(client, cliente)   # martedì 15:30 = 13:30 UTC
    client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    orologio.avanti(hours=18, minutes=30)  # martedì 03:30 Roma: esattamente 12 ore prima
    assert client.delete(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente)).status_code == 200


# ----------------------------------------------------------- lista d'attesa
def _riempi(client, lezione_id, quante=3):
    tokens = [registra(client, f"piena{i}@example.com", nome=f"Piena{i}")["token"] for i in range(quante)]
    for t in tokens:
        assert client.post(f"/api/lezioni/{lezione_id}/prenota", headers=auth(t)).status_code == 200
    return tokens


def test_lista_d_attesa_ed_entrata_automatica(client, cliente):
    l = domani(client, cliente)
    tokens = _riempi(client, l["id"])
    r = client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(cliente))
    assert r.status_code == 200 and r.json()["posizione"] == 1
    # Una disdice: Sofia entra da sola.
    assert client.delete(f"/api/lezioni/{l['id']}/prenota", headers=auth(tokens[0])).status_code == 200
    mia = domani(client, cliente)
    assert mia["mia"] is True and mia["in_attesa"] is None
    assert io(client, cliente)["lezioni_rimaste"] == -1
    testi = [n["testo"] for n in client.get("/api/notifiche", headers=auth(cliente)).json()["elenco"]]
    assert any("Si è liberato un posto" in t for t in testi)


def test_dalla_lista_salta_chi_ha_troppo_da_saldare(client, staff, cliente):
    l = domani(client, cliente)
    tokens = _riempi(client, l["id"])
    seconda = registra(client, "seconda@example.com", nome="Seconda")["token"]
    client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(cliente))
    client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(seconda))
    carica(client, staff, io(client, cliente)["id"], -2)   # Sofia ha già 2 lezioni da saldare
    carica(client, staff, io(client, seconda)["id"], 5)
    client.delete(f"/api/lezioni/{l['id']}/prenota", headers=auth(tokens[0]))
    assert domani(client, seconda)["mia"] is True
    assert domani(client, cliente)["in_attesa"] == 1


def test_attesa_solo_se_piena(client, cliente):
    l = domani(client, cliente)
    assert client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(cliente)).status_code == 409


def test_ordine_della_lista(client, cliente):
    l = domani(client, cliente)
    tokens = _riempi(client, l["id"])
    seconda = registra(client, "seconda@example.com", nome="Seconda")["token"]
    client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(cliente))
    assert client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(seconda)).json()["posizione"] == 2
    client.delete(f"/api/lezioni/{l['id']}/prenota", headers=auth(tokens[1]))
    assert domani(client, cliente)["mia"] is True
    assert domani(client, seconda)["in_attesa"] == 1


def test_uscire_dalla_lista(client, cliente):
    l = domani(client, cliente)
    _riempi(client, l["id"])
    client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(cliente))
    assert client.delete(f"/api/lezioni/{l['id']}/attesa", headers=auth(cliente)).status_code == 204
    assert domani(client, cliente)["in_attesa"] is None


# ------------------------------------------------------------------- staff
def test_greta_ed_elisa_diventano_staff_solo_confermando(client, posta_inviata):
    t = registra(client, GRETA.upper(), nome="Greta")["token"]
    # Registrata ma non confermata: per ora è una cliente qualunque.
    assert io(client, t)["ruolo"] == "cliente"
    assert client.get("/api/staff/clienti", headers=auth(t)).status_code == 403
    r = client.post("/api/auth/conferma", json={"codice": codice_dal_link(posta_inviata[-1][2])})
    assert r.json()["utente"]["ruolo"] == "staff"
    assert client.get("/api/staff/clienti", headers=auth(r.json()["token"])).status_code == 200

    registra(client, ELISA, nome="Elisa")
    r = client.post("/api/auth/conferma", json={"codice": codice_dal_link(posta_inviata[-1][2])})
    assert r.json()["utente"]["ruolo"] == "staff"


def test_un_altro_indirizzo_resta_cliente(client, posta_inviata):
    registra(client, "greta.lorenzetti@icloud.it")  # dominio diverso
    r = client.post("/api/auth/conferma", json={"codice": codice_dal_link(posta_inviata[-1][2])})
    assert r.json()["utente"]["ruolo"] == "cliente"


def test_la_cliente_non_entra_nel_gestionale(client, cliente):
    assert client.get("/api/staff/clienti", headers=auth(cliente)).status_code == 403
    assert client.post("/api/staff/clienti/1/lezioni", json={"lezioni": 99}, headers=auth(cliente)).status_code == 403


def test_lo_staff_scrive_le_lezioni_rimaste(client, staff, cliente):
    cid = io(client, cliente)["id"]
    assert carica(client, staff, cid, 10)["lezioni_rimaste"] == 10
    r = client.post(f"/api/staff/clienti/{cid}/lezioni", json={"aggiungi": -2}, headers=auth(staff))
    assert r.json()["lezioni_rimaste"] == 8
    r = client.post(
        f"/api/staff/clienti/{cid}/lezioni",
        json={"cambia_scadenza": True, "scadenza": "2026-12-31"}, headers=auth(staff),
    )
    assert r.json()["scadenza"] == "2026-12-31" and r.json()["lezioni_rimaste"] == 8
    scheda = client.get(f"/api/staff/clienti/{cid}", headers=auth(staff)).json()
    assert [m["variazione"] for m in scheda["movimenti"]] == [-2, 10]
    assert scheda["movimenti"][0]["autore"] == "Greta"
    pacchetto = client.get("/api/pacchetto", headers=auth(cliente)).json()
    assert pacchetto["lezioni_rimaste"] == 8 and pacchetto["scadenza"] == "2026-12-31"


def test_lo_staff_vede_i_nomi_e_segna_le_presenze(client, staff, cliente):
    l = lezioni(client, cliente)[0]
    client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    cid = io(client, cliente)["id"]
    vista = client.get(f"/api/staff/lezioni/{l['id']}", headers=auth(staff)).json()
    assert [i["nome"] for i in vista["iscritte"]] == ["Sofia Marini"]
    r = client.put(f"/api/staff/lezioni/{l['id']}/presenze/{cid}", json={"presente": True}, headers=auth(staff))
    assert r.status_code == 204
    assert client.get(f"/api/staff/lezioni/{l['id']}", headers=auth(staff)).json()["iscritte"][0]["presente"] is True


def test_lo_staff_toglie_anche_all_ultimo(client, staff, cliente):
    l = lezioni(client, cliente)[0]  # oggi, meno di 12 ore
    client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    cid = io(client, cliente)["id"]
    r = client.delete(f"/api/staff/lezioni/{l['id']}/iscritte/{cid}", headers=auth(staff))
    assert r.status_code == 200
    assert io(client, cliente)["lezioni_rimaste"] == 0


def test_lo_staff_aggiunge_chi_ha_telefonato(client, staff, cliente):
    l = domani(client, cliente)
    cid = io(client, cliente)["id"]
    r = client.post(f"/api/staff/lezioni/{l['id']}/iscritte", json={"cliente_id": cid}, headers=auth(staff))
    assert r.status_code == 200
    assert domani(client, cliente)["mia"] is True


def test_annullare_una_lezione(client, staff, cliente):
    l = domani(client, cliente)
    carica(client, staff, io(client, cliente)["id"], 4)
    tokens = _riempi(client, l["id"], 2)
    client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    attesa = registra(client, "attesa@example.com")["token"]
    client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(attesa))
    r = client.post(f"/api/staff/lezioni/{l['id']}/annulla", json={"motivo": "Elisa ha la febbre"}, headers=auth(staff))
    assert r.json()["avvisate"] == 3
    assert io(client, cliente)["lezioni_rimaste"] == 4
    for t in (cliente, attesa, tokens[0]):
        testi = [n["testo"] for n in client.get("/api/notifiche", headers=auth(t)).json()["elenco"]]
        assert any("annullata: Elisa ha la febbre" in x for x in testi)
    assert client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(attesa)).status_code == 409
    assert domani(client, cliente)["annullata"] is True


def test_pilates_fitness_lunedi_e_mercoledi_alle_16_30(client, cliente):
    settimana = lezioni(client, cliente, "2026-10-12", 6)
    titoli = {(l["inizio"][:10], l["inizio"][11:16]): l["titolo"] for l in settimana}
    assert titoli[("2026-10-12", "14:30")] == "Pilates fitness"   # lunedì 16:30 a Roma
    assert titoli[("2026-10-14", "14:30")] == "Pilates fitness"   # mercoledì 16:30
    assert titoli[("2026-10-12", "15:30")] == "Reformer"          # lunedì 17:30
    assert titoli[("2026-10-13", "14:30")] == "Reformer"          # martedì 16:30


def test_nome_per_tutte_le_settimane(client, staff, cliente):
    l = domani(client, cliente)   # martedì 15:30
    r = client.patch(f"/api/staff/lezioni/{l['id']}", json={"titolo": "Postura", "ogni_settimana": True}, headers=auth(staff))
    assert r.status_code == 200
    # Martedì dopo, già nel calendario, e fra un mese, non ancora creato.
    assert lezioni(client, cliente, "2026-10-20")[0]["titolo"] == "Postura"
    assert lezioni(client, cliente, "2026-11-10")[0]["titolo"] == "Postura"
    assert lezioni(client, cliente, "2026-10-20")[1]["titolo"] == "Reformer"   # le 16:30 no
    # Solo per una lezione: le altre settimane restano.
    client.patch(f"/api/staff/lezioni/{l['id']}", json={"titolo": "Speciale"}, headers=auth(staff))
    assert domani(client, cliente)["titolo"] == "Speciale"
    assert lezioni(client, cliente, "2026-10-20")[0]["titolo"] == "Postura"


def test_lo_staff_apre_una_lezione_alle_18_30(client, staff, cliente):
    r = client.post("/api/staff/lezioni", json={"giorno": "2026-10-13", "ora": "18:30"}, headers=auth(staff))
    assert r.status_code == 201, r.text
    giorno = lezioni(client, cliente, "2026-10-13")
    assert [l["inizio"][11:16] for l in giorno] == ["13:30", "14:30", "15:30", "16:30"]
    extra = giorno[-1]
    assert extra["istruttrice"]["id"] == "elisa" and extra["posti"] == 3
    assert client.post(f"/api/lezioni/{extra['id']}/prenota", headers=auth(cliente)).status_code == 200
    # Doppione, domenica, ora passata, cliente: no.
    assert client.post("/api/staff/lezioni", json={"giorno": "2026-10-13", "ora": "18:30"}, headers=auth(staff)).status_code == 409
    assert client.post("/api/staff/lezioni", json={"giorno": "2026-10-18", "ora": "18:30"}, headers=auth(staff)).status_code == 400
    assert client.post("/api/staff/lezioni", json={"giorno": "2026-10-12", "ora": "08:00"}, headers=auth(staff)).status_code == 400
    assert client.post("/api/staff/lezioni", json={"giorno": "2026-10-14", "ora": "18:30"}, headers=auth(cliente)).status_code == 403


def test_titolo_e_avvisi(client, staff, cliente):
    l = domani(client, cliente)
    client.patch(f"/api/staff/lezioni/{l['id']}", json={"titolo": "Reformer · Principianti"}, headers=auth(staff))
    assert domani(client, cliente)["titolo"] == "Reformer · Principianti"
    client.post("/api/staff/avvisi", json={"testo": "Sabato chiusi per il ponte"}, headers=auth(staff))
    n = client.get("/api/notifiche", headers=auth(cliente)).json()
    assert any(x["tipo"] == "avviso" and "ponte" in x["testo"] for x in n["elenco"])
    assert n["non_lette"] >= 2
    client.post("/api/notifiche/lette", headers=auth(cliente))
    assert client.get("/api/notifiche", headers=auth(cliente)).json()["non_lette"] == 0


# ----------------------------------------------------------------- account
def test_accesso(client, cliente):
    r = client.post("/api/auth/accedi", json={"email": "SOFIA@example.com", "password": "pilates2026"})
    assert r.status_code == 200
    assert client.post("/api/auth/accedi", json={"email": "sofia@example.com", "password": "sbagliata"}).status_code == 401
    assert client.post("/api/auth/accedi", json={"email": "nessuno@example.com", "password": "x"}).status_code == 401


def test_email_gia_usata_e_privacy(client, cliente):
    r = client.post("/api/auth/registrati", json={
        "nome": "A", "cognome": "B", "telefono": "3331234567", "email": "sofia@example.com",
        "password": "pilates2026", "privacy": True,
    })
    assert r.status_code == 409
    r = client.post("/api/auth/registrati", json={
        "nome": "A", "cognome": "B", "telefono": "3331234567", "email": "nuova@example.com",
        "password": "pilates2026", "privacy": False,
    })
    assert r.status_code == 422


def test_cambio_password_chiude_gli_altri_telefoni(client, cliente):
    r = client.post("/api/io/password", json={"attuale": "pilates2026", "nuova": "nuovapassword"}, headers=auth(cliente))
    assert r.status_code == 200
    assert client.get("/api/io", headers=auth(cliente)).status_code == 401
    assert client.get("/api/io", headers=auth(r.json()["token"])).status_code == 200


def test_password_dimenticata(client, cliente, posta_inviata):
    assert client.post("/api/auth/recupero", json={"email": "sofia@example.com"}).status_code == 204
    assert client.post("/api/auth/recupero", json={"email": "nessuno@example.com"}).status_code == 204
    codice = codice_dal_link(posta_inviata[-1][2])
    r = client.post("/api/auth/nuova-password", json={"codice": codice, "password": "nuovapassword"})
    assert r.status_code == 200
    assert client.post("/api/auth/nuova-password", json={"codice": codice, "password": "altra12345"}).status_code == 400
    assert client.post("/api/auth/accedi", json={"email": "sofia@example.com", "password": "nuovapassword"}).status_code == 200


def test_cancellare_l_account_libera_il_posto(client, cliente):
    l = domani(client, cliente)
    tokens = _riempi(client, l["id"])
    client.post(f"/api/lezioni/{l['id']}/attesa", headers=auth(cliente))
    r = client.post("/api/io/cancella", json={"password": "pilates2026"}, headers=auth(tokens[0]))
    assert r.status_code == 204
    assert client.get("/api/io", headers=auth(tokens[0])).status_code == 401
    assert domani(client, cliente)["mia"] is True


# --------------------------------------------------------------- promemoria
def test_promemoria_una_volta(client, cliente, posta_inviata, orologio):
    from reformer.db.session import SessionLocal
    from reformer.servizi.promemoria import manda_promemoria

    l = domani(client, cliente)  # martedì 16:30
    client.post(f"/api/lezioni/{l['id']}/prenota", headers=auth(cliente))
    with SessionLocal() as db:
        assert manda_promemoria(db) == 0          # lunedì 9:00: più di 24 ore
    orologio.avanti(hours=8)                       # lunedì 17:00: mancano 23 ore e mezza
    with SessionLocal() as db:
        assert manda_promemoria(db) == 1
        assert manda_promemoria(db) == 0
        assert db.query(Notifica).filter(Notifica.testo.like("Promemoria%")).count() == 1
    assert any("Promemoria" in o for _, o, _ in posta_inviata)
