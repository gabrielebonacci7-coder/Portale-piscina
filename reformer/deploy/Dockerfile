# Immagine dell'applicazione. Si costruisce dalla radice del repository:
#     docker compose build      (da reformer/deploy/, vedi docker-compose.yml)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Le dipendenze prima del resto: finché il file non cambia, Docker riusa
# questo strato e l'aggiornamento dura secondi invece di minuti.
COPY reformer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reformer/ ./reformer/

# L'app non gira come root.
RUN useradd --create-home --uid 1000 reformer \
    && mkdir -p /dati \
    && chown -R reformer:reformer /app /dati
USER reformer

ENV REFORMER_DATABASE_URL=sqlite:////dati/reformer.db

EXPOSE 8000

# Un solo processo, apposta: il lucchetto che impedisce a due clienti di
# prendere insieme l'ultimo reformer vive in memoria (servizi/regole.py), e
# il promemoria del giorno prima deve partire una volta sola. Per uno studio
# con tre reformer un processo è anche fin troppo.
CMD ["uvicorn", "reformer.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
