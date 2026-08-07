"""Salvataggio e cancellazione delle foto, con la pulizia dei file su disco."""

from sqlalchemy.orm import Session

from app.core.immagini import elimina_immagine, salva_immagine
from app.models import FotoPiscina, ProfiloBagnino, ProfiloPiscina, TipoFoto


def imposta_foto_bagnino(db: Session, profilo: ProfiloBagnino, dati: bytes) -> ProfiloBagnino:
    """Sostituisce la foto profilo. La precedente viene cancellata dal disco."""
    precedente = profilo.foto
    profilo.foto = salva_immagine(dati, "bagnini")
    db.commit()
    db.refresh(profilo)
    # Si cancella solo dopo il commit: se il salvataggio fallisse, la vecchia
    # foto resterebbe comunque valida.
    elimina_immagine(precedente)
    return profilo


def rimuovi_foto_bagnino(db: Session, profilo: ProfiloBagnino) -> ProfiloBagnino:
    precedente = profilo.foto
    profilo.foto = None
    db.commit()
    db.refresh(profilo)
    elimina_immagine(precedente)
    return profilo


def aggiungi_foto_piscina(
    db: Session,
    piscina: ProfiloPiscina,
    dati: bytes,
    tipo: TipoFoto,
    didascalia: str | None = None,
) -> FotoPiscina:
    percorso = salva_immagine(dati, "piscine")
    foto = FotoPiscina(
        piscina_id=piscina.id,
        percorso=percorso,
        tipo=tipo,
        didascalia=didascalia,
        # L'ingresso va sempre per primo: è la foto che serve a trovare il posto.
        ordine=0 if tipo == TipoFoto.INGRESSO else len(piscina.foto) + 1,
    )
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return foto


def elimina_foto_piscina(db: Session, piscina: ProfiloPiscina, foto_id: int) -> bool:
    foto = db.get(FotoPiscina, foto_id)
    if foto is None or foto.piscina_id != piscina.id:
        return False
    percorso = foto.percorso
    db.delete(foto)
    db.commit()
    elimina_immagine(percorso)
    return True
