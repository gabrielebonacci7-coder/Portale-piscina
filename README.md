# Portale Piscina

Bacheca annunci che mette in contatto **bagnini** e **piscine/strutture** a Roma.

Stato attuale: **passo 1 — struttura dati**. Ci sono i modelli, il database SQLite
e l'ossatura FastAPI. Non c'è ancora né interfaccia né CRUD.

## Avvio rapido

```bash
pip install -r requirements.txt

python -m app.db.init_db      # crea le tabelle e inserisce le zone di Roma
python -m scripts.seed_demo   # (facoltativo) dati di esempio

uvicorn app.main:app --reload # http://127.0.0.1:8000/docs
```

Endpoint disponibili in questa fase: `/health`, `/schema` (tabelle e colonne),
`/zone`.

## Struttura del progetto

```
app/
├── core/config.py       impostazioni (DATABASE_URL, ecc.) da env o .env
├── db/
│   ├── base_class.py    Base dichiarativa + mixin creato_il/aggiornato_il
│   ├── types.py         UTCDateTime: datetime sempre aware anche su SQLite
│   ├── session.py       engine, SessionLocal, get_db, PRAGMA foreign_keys
│   └── init_db.py       create_all + seed delle zone
├── models/              tabelle SQLAlchemy (il modello di dominio)
├── schemas/             schemi Pydantic (contratto dell'API)
└── main.py              app FastAPI
scripts/seed_demo.py     dati di esempio
```

## Le tabelle

| Tabella | Cosa contiene |
|---|---|
| `utenti` | account e credenziali, con `tipo` = bagnino \| piscina |
| `profili_bagnino` | anagrafica, città, anni di esperienza, disponibilità a chiamata singola |
| `brevetti` | brevetti FIN (P / IP / MIP), numero, rilascio e **scadenza** |
| `esperienze` | curriculum: struttura, mansione, periodo, stagioni |
| `disponibilita` | fasce orarie ricorrenti (giorno 0-6 + ora inizio/fine) |
| `profili_piscina` | struttura, tipo, indirizzo, dati del referente che pubblica |
| `zone` | municipi/quartieri, per i filtri geografici |
| `bagnino_zone` | quali zone copre un bagnino (molti-a-molti) |
| `annunci` | il cuore della bacheca: chi pubblica, quando, dove, quanto, che tipo |
| `recensioni` | recensioni incrociate piscina ↔ bagnino, 1-5 stelle |

### Scelte di modellazione

- **Un utente, due profili.** `utenti` tiene login e contatti; i dati specifici
  stanno in `profili_bagnino` o `profili_piscina` (relazione 1-a-1). Così un
  annuncio o una recensione puntano sempre a `utenti.id`, senza duplicare la
  logica per i due tipi.
- **Età calcolata, non salvata.** Si memorizza `data_nascita`; `eta` è una
  proprietà. Un numero salvato invecchierebbe senza aggiornarsi.
- **Brevetti su tabella separata.** Un bagnino può averne più di uno e ciascuno
  ha una scadenza propria. `Brevetto.valido` confronta `data_scadenza` con oggi,
  e `ProfiloBagnino.abilitato` dice se ne ha almeno uno in corso di validità.
- **Zone normalizzate.** Una tabella di lookup invece di testo libero: "Ostia",
  "ostia" e "Lido di Ostia" sarebbero tre zone diverse e i filtri non
  funzionerebbero.
- **Un'unica tabella `annunci`** per entrambi i versi (piscina cerca bagnino /
  bagnino cerca sostituzione): i campi sono gli stessi, cambia solo `tipo`.
- **Compenso in `Numeric(8,2)`**, mai `float`: sui soldi gli arrotondamenti
  binari fanno danni. Affiancato da `compenso_tipo` (orario, a turno, ...).
- **Recensioni bidirezionali in una tabella sola**, con `autore_id` e
  `destinatario_id`. Il verso si deduce dal tipo dell'autore. I voti di
  dettaglio sono opzionali: una piscina vota puntualità e professionalità, un
  bagnino ambiente e pagamento.
- **Vincoli nel database, non solo in Python:** stelle 1-5, giorno 0-6,
  `ora_fine > ora_inizio`, `data_fine >= data_inizio`, niente autorecensioni,
  una sola recensione per coppia+annuncio. Le foreign key su SQLite vanno
  abilitate a ogni connessione (`PRAGMA foreign_keys=ON`, in `db/session.py`),
  altrimenti vengono ignorate in silenzio.
- **Enum come stringhe** (`native_enum=False`): portabile su SQLite e indolore
  da estendere su PostgreSQL.

### Regole applicative (da far rispettare al livello API, non allo schema)

- `annunci.tipo` deve essere coerente con `utenti.tipo` dell'autore.
- Si recensisce solo chi si è incontrato su un annuncio concluso.
- I voti di dettaglio hanno senso solo nel verso giusto.

## Prossimi passi

1. Endpoint CRUD per utenti, profili e annunci.
2. Autenticazione (hash password + JWT).
3. Ricerca e filtri della bacheca (zona, data, tipo turno, brevetto).
4. Candidature agli annunci e messaggistica interna.
5. Migrazioni con Alembic, poi PWA (frontend + service worker).
