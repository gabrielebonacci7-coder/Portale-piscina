"""Ricezione, pulizia e salvataggio delle foto caricate dagli utenti.

Nessun file arriva su disco così com'è: viene decodificato, ridimensionato e
riscritto da capo. Questo risolve tre problemi in un colpo solo.

1. **Privacy.** Le foto scattate col telefono portano dentro l'EXIF, che
   contiene le coordinate GPS del punto dello scatto. Un bagnino che carica
   un selfie fatto a casa pubblicherebbe l'indirizzo di casa sua. Riscrivendo
   l'immagine l'EXIF sparisce.
2. **Sicurezza.** Un file può dichiararsi `image/jpeg` ed essere altro. Qui
   conta solo se Pillow riesce davvero a decodificarlo; e la riscrittura
   scarta qualsiasi cosa fosse nascosta fra i byte.
3. **Peso.** Una foto da telefono pesa anche 12 MB: ridotta a 1600px sta
   sotto i 300 kB, e la bacheca resta veloce anche in 4G.
"""

import secrets
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

# Difesa dalle "decompression bomb": immagini piccole da scaricare che si
# espandono a miliardi di pixel e saturano la memoria del server.
Image.MAX_IMAGE_PIXELS = 64_000_000

FORMATI_AMMESSI = {"JPEG", "PNG", "WEBP", "HEIF", "HEIC", "MPO"}


class ErroreImmagine(ValueError):
    """Immagine non accettabile: il messaggio è pensato per l'utente finale."""


def _cartella(sezione: str) -> Path:
    percorso = Path(settings.media_dir) / sezione
    percorso.mkdir(parents=True, exist_ok=True)
    return percorso


def _riduci(immagine: Image.Image, lato_max: int) -> Image.Image:
    copia = immagine.copy()
    copia.thumbnail((lato_max, lato_max), Image.LANCZOS)
    return copia


def salva_immagine(dati: bytes, sezione: str) -> str:
    """Salva la foto e la sua anteprima. Restituisce il percorso relativo.

    `sezione` è la sottocartella ("bagnini", "piscine"). Il nome del file è
    casuale: quello scelto dall'utente non tocca mai il disco.
    """
    if not dati:
        raise ErroreImmagine("Il file è vuoto")
    if len(dati) > settings.max_upload_bytes:
        limite = settings.max_upload_bytes // (1024 * 1024)
        raise ErroreImmagine(f"La foto supera {limite} MB. Provane una più leggera.")

    try:
        with Image.open(_flusso(dati)) as originale:
            if originale.format not in FORMATI_AMMESSI:
                raise ErroreImmagine(
                    "Formato non riconosciuto. Usa una foto JPEG, PNG o WEBP."
                )
            # `exif_transpose` applica la rotazione registrata nell'EXIF prima
            # che l'EXIF venga buttato via: senza, le foto verticali fatte col
            # telefono verrebbero mostrate coricate.
            immagine = ImageOps.exif_transpose(originale)
            # Il JPEG non gestisce la trasparenza: si appiattisce su bianco.
            if immagine.mode in ("RGBA", "LA", "P"):
                sfondo = Image.new("RGB", immagine.size, (255, 255, 255))
                convertita = immagine.convert("RGBA")
                sfondo.paste(convertita, mask=convertita.split()[-1])
                immagine = sfondo
            else:
                immagine = immagine.convert("RGB")

            grande = _riduci(immagine, settings.foto_lato_max)
            anteprima = _riduci(immagine, settings.foto_lato_anteprima)
    except ErroreImmagine:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise ErroreImmagine("Il file non sembra un'immagine valida")

    nome = secrets.token_urlsafe(12)
    cartella = _cartella(sezione)
    # `exif=b""` e niente altro: si salva solo la matrice di pixel.
    grande.save(cartella / f"{nome}.jpg", "JPEG", quality=85, optimize=True, exif=b"")
    anteprima.save(cartella / f"{nome}-p.jpg", "JPEG", quality=80, optimize=True, exif=b"")

    return f"{sezione}/{nome}.jpg"


def elimina_immagine(percorso_relativo: str | None) -> None:
    """Cancella foto e anteprima. Non solleva se il file non c'è già più."""
    if not percorso_relativo:
        return
    base = Path(settings.media_dir)
    file = (base / percorso_relativo).resolve()
    # Non si cancella nulla fuori dalla cartella media, qualunque cosa dica
    # il percorso salvato.
    if not file.is_relative_to(base.resolve()):
        return
    file.unlink(missing_ok=True)
    file.with_name(file.stem + "-p.jpg").unlink(missing_ok=True)


def url_foto(percorso_relativo: str | None) -> str | None:
    return f"/media/{percorso_relativo}" if percorso_relativo else None


def url_anteprima(percorso_relativo: str | None) -> str | None:
    if not percorso_relativo:
        return None
    radice, _, _ = percorso_relativo.rpartition(".")
    return f"/media/{radice}-p.jpg"


def _flusso(dati: bytes):
    from io import BytesIO

    return BytesIO(dati)
