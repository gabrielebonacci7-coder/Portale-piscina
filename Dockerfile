# Immagine dell'applicazione. `slim` e non `alpine`: Pillow su alpine va
# compilato a mano e l'immagine ci mette dieci minuti a costruirsi.
FROM python:3.12-slim

# - PYTHONUNBUFFERED: i log escono subito, senza restare nel buffer. Senza,
#   `docker compose logs` sembra vuoto proprio quando serve guardarlo.
# - PYTHONDONTWRITEBYTECODE: niente .pyc dentro al contenitore.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Le dipendenze si copiano da sole e prima del resto: finché il file non
# cambia, Docker riusa questo strato e il rilascio dura secondi invece di
# minuti.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY web/ ./web/
COPY scripts/ ./scripts/

# L'app non gira come root: se un giorno qualcuno riuscisse a farle eseguire
# qualcosa, si troverebbe con i permessi di un utente qualunque.
RUN useradd --create-home --uid 1000 guardlink \
    && mkdir -p /dati/media \
    && chown -R guardlink:guardlink /app /dati
USER guardlink

# Database e foto stanno fuori dall'immagine, su volumi: ricostruire
# l'immagine non deve nemmeno sfiorare i dati degli iscritti.
ENV DATABASE_URL=sqlite:////dati/guardlink.db \
    MEDIA_DIR=/dati/media

EXPOSE 8000

# Due lavoratori: uno serve, l'altro risponde mentre il primo è occupato. Su un
# VPS piccolo di più non conviene — ognuno tiene in memoria la sua copia
# dell'applicazione.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
