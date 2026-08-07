"""Foto: caricamento, pulizia dei dati EXIF, limiti, e la regola dell'ingresso."""

from io import BytesIO

import piexif
import pytest
from PIL import Image

from app.core.config import settings
from tests.conftest import auth, carica_foto, immagine_finta, login, registra


def foto_con_gps() -> bytes:
    """Un JPEG con dentro coordinate GPS, come quelli scattati col telefono."""
    exif = piexif.dump(
        {
            "0th": {piexif.ImageIFD.Make: b"Apple", piexif.ImageIFD.Model: b"iPhone 14"},
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((41, 1), (54, 1), (0, 1)),  # Roma
                piexif.GPSIFD.GPSLongitudeRef: b"E",
                piexif.GPSIFD.GPSLongitude: ((12, 1), (29, 1), (0, 1)),
            },
            "Exif": {},
            "1st": {},
            "thumbnail": None,
        }
    )
    buffer = BytesIO()
    Image.new("RGB", (200, 150), (200, 60, 40)).save(buffer, "JPEG", exif=exif)
    return buffer.getvalue()


def leggi_media(percorso_url: str) -> bytes:
    """Legge dal disco il file che sta dietro a un URL /media/…"""
    from pathlib import Path

    return (Path(settings.media_dir) / percorso_url.removeprefix("/media/")).read_bytes()


# --- Bagnino --------------------------------------------------------------
def test_bagnino_carica_la_foto_profilo(client, bagnino):
    r = client.put(
        "/bagnini/me/foto",
        files={"file": ("io.png", immagine_finta(), "image/png")},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["foto_url"].startswith("/media/bagnini/")
    assert corpo["foto_anteprima_url"].endswith("-p.jpg")


def test_la_foto_compare_nell_elenco_e_sul_profilo_pubblico(client, bagnino, piscina):
    client.put(
        "/bagnini/me/foto",
        files={"file": ("io.png", immagine_finta(), "image/png")},
        headers=auth(bagnino["token"]),
    )
    elenco = client.get("/bagnini", headers=auth(piscina["token"])).json()
    assert elenco["elementi"][0]["foto_anteprima_url"] is not None

    pubblico = client.get(
        f"/bagnini/{bagnino['profilo_id']}", headers=auth(piscina["token"])
    ).json()
    assert pubblico["foto_url"] is not None


def test_sostituire_la_foto_cancella_la_precedente(client, bagnino):
    from pathlib import Path

    prima = client.put(
        "/bagnini/me/foto",
        files={"file": ("a.png", immagine_finta(), "image/png")},
        headers=auth(bagnino["token"]),
    ).json()["foto_url"]

    client.put(
        "/bagnini/me/foto",
        files={"file": ("b.png", immagine_finta(colore=(1, 2, 3)), "image/png")},
        headers=auth(bagnino["token"]),
    )
    vecchia = Path(settings.media_dir) / prima.removeprefix("/media/")
    assert not vecchia.exists(), "la foto vecchia è rimasta sul disco"


def test_rimozione_foto(client, bagnino):
    client.put(
        "/bagnini/me/foto",
        files={"file": ("io.png", immagine_finta(), "image/png")},
        headers=auth(bagnino["token"]),
    )
    r = client.delete("/bagnini/me/foto", headers=auth(bagnino["token"]))
    assert r.status_code == 200
    assert r.json()["foto_url"] is None


# --- Privacy --------------------------------------------------------------
def test_i_dati_gps_vengono_rimossi(client, bagnino):
    """Il punto più importante: una foto fatta a casa non deve pubblicare
    l'indirizzo di casa."""
    originale = foto_con_gps()
    assert piexif.load(originale)["GPS"], "l'immagine di prova deve avere il GPS"

    r = client.put(
        "/bagnini/me/foto",
        files={"file": ("selfie.jpg", originale, "image/jpeg")},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 200

    salvata = leggi_media(r.json()["foto_url"])
    exif = piexif.load(salvata)
    assert not exif["GPS"], "le coordinate GPS sono finite sul server"
    assert not exif["0th"], "marca e modello del telefono sono rimasti"


# --- File non validi ------------------------------------------------------
def test_un_file_che_finge_di_essere_immagine_viene_rifiutato(client, bagnino):
    r = client.put(
        "/bagnini/me/foto",
        files={"file": ("finto.jpg", b"#!/bin/sh\nrm -rf /", "image/jpeg")},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 422
    assert "immagine" in r.json()["detail"].lower()


def test_file_vuoto_rifiutato(client, bagnino):
    r = client.put(
        "/bagnini/me/foto",
        files={"file": ("vuoto.jpg", b"", "image/jpeg")},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 422


def test_foto_troppo_grande_rifiutata(client, bagnino):
    troppo = b"x" * (settings.max_upload_bytes + 1024)
    r = client.put(
        "/bagnini/me/foto",
        files={"file": ("enorme.jpg", troppo, "image/jpeg")},
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 413


def test_la_foto_viene_rimpicciolita(client, bagnino):
    grande = immagine_finta(dimensione=(3000, 2000), formato="JPEG")
    r = client.put(
        "/bagnini/me/foto",
        files={"file": ("grande.jpg", grande, "image/jpeg")},
        headers=auth(bagnino["token"]),
    )
    with Image.open(BytesIO(leggi_media(r.json()["foto_url"]))) as img:
        assert max(img.size) <= settings.foto_lato_max
    with Image.open(BytesIO(leggi_media(r.json()["foto_anteprima_url"]))) as ant:
        assert max(ant.size) <= settings.foto_lato_anteprima


# --- Struttura ------------------------------------------------------------
def test_piscina_carica_piu_foto(client, piscina):
    # Il fixture ha già caricato l'ingresso.
    r = carica_foto(client, piscina["token"], "/piscine/me/foto", tipo="vasca")
    assert r.status_code == 201
    assert r.json()["tipo"] == "vasca"

    profilo = client.get("/piscine/me", headers=auth(piscina["token"])).json()
    assert len(profilo["foto"]) == 2
    assert profilo["ha_foto_ingresso"] is True
    # L'ingresso resta in cima: è il riferimento per trovare il posto.
    assert profilo["foto"][0]["tipo"] == "ingresso"


def test_una_sola_foto_di_ingresso(client, piscina):
    carica_foto(client, piscina["token"], "/piscine/me/foto", tipo="ingresso")
    profilo = client.get("/piscine/me", headers=auth(piscina["token"])).json()
    ingressi = [f for f in profilo["foto"] if f["tipo"] == "ingresso"]
    assert len(ingressi) == 1


def test_limite_al_numero_di_foto(client, piscina):
    for _ in range(settings.max_foto_piscina - 1):  # l'ingresso c'è già
        assert (
            carica_foto(client, piscina["token"], "/piscine/me/foto", tipo="vasca").status_code
            == 201
        )
    r = carica_foto(client, piscina["token"], "/piscine/me/foto", tipo="altro")
    assert r.status_code == 409


def test_eliminazione_foto(client, piscina):
    foto = carica_foto(client, piscina["token"], "/piscine/me/foto", tipo="vasca").json()
    assert (
        client.delete(f"/piscine/me/foto/{foto['id']}", headers=auth(piscina["token"])).status_code
        == 204
    )
    assert (
        client.delete(f"/piscine/me/foto/{foto['id']}", headers=auth(piscina["token"])).status_code
        == 404
    )


def test_non_si_cancella_la_foto_di_un_altra_struttura(client, piscina):
    foto = carica_foto(client, piscina["token"], "/piscine/me/foto", tipo="vasca").json()

    registra(client, "altra@test.it", "piscina")
    token = login(client, "altra@test.it")
    client.post("/piscine", json={"nome_struttura": "Altra"}, headers=auth(token))

    r = client.delete(f"/piscine/me/foto/{foto['id']}", headers=auth(token))
    assert r.status_code == 404


# --- La regola dell'ingresso ----------------------------------------------
def test_senza_foto_ingresso_non_si_pubblica(client):
    registra(client, "senzafoto@test.it", "piscina")
    token = login(client, "senzafoto@test.it")
    client.post("/piscine", json={"nome_struttura": "Senza Foto"}, headers=auth(token))

    r = client.post(
        "/annunci",
        json={
            "titolo": "Turno",
            "tipo": "piscina_cerca_bagnino",
            "data_inizio": "2030-06-01T08:00:00Z",
        },
        headers=auth(token),
    )
    assert r.status_code == 409
    assert "ingresso" in r.json()["detail"]

    # Caricata la foto, la pubblicazione passa.
    carica_foto(client, token, "/piscine/me/foto", tipo="ingresso")
    r = client.post(
        "/annunci",
        json={
            "titolo": "Turno",
            "tipo": "piscina_cerca_bagnino",
            "data_inizio": "2030-06-01T08:00:00Z",
        },
        headers=auth(token),
    )
    assert r.status_code == 201


def test_il_bagnino_pubblica_senza_bisogno_di_foto(client, bagnino):
    """La regola vale per le strutture: un bagnino che cerca un sostituto no."""
    r = client.post(
        "/annunci",
        json={
            "titolo": "Cerco sostituto",
            "tipo": "bagnino_cerca_sostituzione",
            "data_inizio": "2030-06-01T08:00:00Z",
        },
        headers=auth(bagnino["token"]),
    )
    assert r.status_code == 201


def test_serve_il_login_per_caricare(client):
    r = client.put("/bagnini/me/foto", files={"file": ("x.png", immagine_finta(), "image/png")})
    assert r.status_code == 401
