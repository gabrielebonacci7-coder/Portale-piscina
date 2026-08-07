# Portale Piscina

Bacheca annunci che mette in contatto **bagnini** e **piscine/strutture** a Roma.

Stato attuale: **passo 4 — chat interna**. Il backend è completo: modello dati,
API, autenticazione, il giro annuncio → candidatura → assegnazione → recensione,
messaggi diretti con blocco, e i test. Manca l'interfaccia (PWA).

**La bacheca è riservata agli iscritti**: senza login si può solo registrarsi e
leggere l'elenco delle zone (serve al modulo di iscrizione).

## Avvio rapido

```bash
pip install -r requirements.txt

python -m app.db.init_db      # crea le tabelle e inserisce le zone di Roma
python -m scripts.seed_demo   # (facoltativo) dati di esempio

uvicorn app.main:app --reload # http://127.0.0.1:8000/docs
```

Su `/docs` c'è la documentazione interattiva: si fa login con il pulsante
**Authorize** e da lì si provano tutte le chiamate. Gli account di esempio sono
`marco.rossi@example.com`, `giulia.conti@example.com` e
`info@aquacenter.example`, tutti con password `demo1234`.

```bash
pytest        # 91 test end-to-end sulle regole di dominio
```

## Struttura del progetto

```
app/
├── core/
│   ├── config.py        impostazioni (DATABASE_URL, SECRET_KEY...) da env o .env
│   └── security.py      hash bcrypt delle password e token JWT
├── db/
│   ├── base_class.py    Base dichiarativa + mixin creato_il/aggiornato_il
│   ├── types.py         UTCDateTime: datetime sempre aware anche su SQLite
│   ├── session.py       engine, SessionLocal, get_db, PRAGMA foreign_keys
│   └── init_db.py       create_all + seed delle zone
├── models/              tabelle SQLAlchemy (il modello di dominio)
├── schemas/             schemi Pydantic (contratto dell'API)
├── crud/                query e regole di dominio
├── api/
│   ├── deps.py          utente autenticato e controlli di ruolo
│   └── routers/         gli endpoint, raggruppati per area
└── main.py              app FastAPI
scripts/seed_demo.py     dati di esempio
tests/                   test end-to-end
```

I tre livelli hanno compiti distinti: i **router** si occupano di HTTP (status
code, autenticazione, serializzazione), il **crud** del significato (quali
annunci sono visibili, chi può recensire chi), i **models** di come i dati
stanno su disco. Così la stessa regola non finisce scritta in tre posti.

## Endpoint

### Autenticazione
| Metodo | Percorso | Cosa fa |
|---|---|---|
| POST | `/auth/registrazione` | crea l'account (email, password, tipo) |
| POST | `/auth/login` | restituisce il token JWT |
| GET | `/auth/me` | dati dell'account collegato al token |
| POST | `/auth/cambio-password` | richiede la password attuale |

### Bagnini
| Metodo | Percorso | Cosa fa |
|---|---|---|
| POST | `/bagnini` | crea il proprio profilo |
| GET | `/bagnini` | ricerca con filtri (zona, città, abilitati, esperienza) |
| GET | `/bagnini/me` · PATCH | legge/modifica il proprio profilo |
| GET | `/bagnini/{id}` | profilo pubblico |
| POST/DELETE | `/bagnini/me/brevetti[/{id}]` | gestione brevetti |
| POST/DELETE | `/bagnini/me/esperienze[/{id}]` | gestione curriculum |
| POST/DELETE | `/bagnini/me/disponibilita[/{id}]` | fasce orarie settimanali |

### Piscine
| Metodo | Percorso | Cosa fa |
|---|---|---|
| POST | `/piscine` | crea il profilo della struttura |
| GET | `/piscine` | ricerca con filtri (zona, città, tipo struttura) |
| GET | `/piscine/me` · PATCH | legge/modifica il proprio profilo |
| GET | `/piscine/{id}` | scheda pubblica |

### Annunci
| Metodo | Percorso | Cosa fa |
|---|---|---|
| POST | `/annunci` | pubblica |
| GET | `/annunci` | **la bacheca**, con tutti i filtri |
| GET | `/annunci/miei` | i propri, compresi chiusi e scaduti |
| GET | `/annunci/{id}` · PATCH · DELETE | dettaglio e gestione (solo l'autore) |
| POST | `/annunci/{id}/assegna` | assegnazione diretta, senza candidatura |
| POST | `/annunci/{id}/chiudi` | turno concluso, si può recensire |

### Candidature
| Metodo | Percorso | Cosa fa |
|---|---|---|
| POST | `/annunci/{id}/candidature` | candidati a un turno |
| GET | `/annunci/{id}/candidature` | chi ha risposto (solo per chi ha pubblicato) |
| POST | `/annunci/{id}/candidature/{cid}/accetta` | assegna il turno e rifiuta le altre |
| POST | `/annunci/{id}/candidature/{cid}/rifiuta` | scarta una candidatura, l'annuncio resta aperto |
| GET | `/candidature/mie` | le proprie candidature, con titolo e data del turno |
| DELETE | `/candidature/{id}` | ritira la propria candidatura |

Filtri della bacheca: `tipo`, `citta`, `zona_id`, `tipo_turno`,
`brevetto_richiesto`, `solo_urgenti`, `solo_aperti`, `data_da`, `data_a`,
`compenso_min`, `testo`, `skip`, `limit`. L'ordinamento mette gli urgenti in
cima, poi i turni più vicini nel tempo.

### Messaggi
| Metodo | Percorso | Cosa fa |
|---|---|---|
| POST | `/conversazioni` | scrive a un iscritto (riusa la chat se esiste) |
| GET | `/conversazioni` | le proprie chat, con non letti e ultimo messaggio |
| GET | `/conversazioni/non-letti` | contatore complessivo, per il pallino |
| GET | `/conversazioni/{id}/messaggi` | i messaggi; aprirli li segna come letti |
| POST | `/conversazioni/{id}/messaggi` | risponde |
| POST/DELETE | `/blocchi/{utente_id}` | blocca / sblocca un utente |
| GET | `/blocchi` | chi hai bloccato |

### Recensioni
| Metodo | Percorso | Cosa fa |
|---|---|---|
| POST | `/recensioni` | recensisce la controparte di un turno concluso |
| GET | `/utenti/{id}/recensioni` | recensioni ricevute + medie dei voti |

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
| `candidature` | chi ha risposto a un annuncio, con stato e messaggio |
| `conversazioni` | una chat fra due utenti |
| `partecipanti_conversazione` | chi ne fa parte e fin dove ha letto |
| `messaggi` | i messaggi di una conversazione |
| `blocchi` | chi ha bloccato chi |
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

### Regole applicative (nel livello `crud`, non esprimibili nello schema)

Sono i vincoli che una tabella non può descrivere. Ognuno ha il suo test.

- **Il tipo di annuncio deve corrispondere al tipo di account:** una piscina non
  può pubblicare "bagnino cerca sostituzione", e viceversa.
- **Solo l'autore** modifica, cancella, assegna e chiude il proprio annuncio.
- **Il turno si assegna alla controparte:** una piscina non lo assegna a
  un'altra piscina, e nessuno lo assegna a se stesso.
- **Si recensisce solo dopo:** l'annuncio dev'essere assegnato o chiuso, e i due
  devono esserne le due parti. Una sola recensione per coppia e annuncio.
- **I voti di dettaglio seguono il verso:** la struttura vota puntualità e
  professionalità, il bagnino ambiente e pagamento.
- **Un profilo per account**, del tipo giusto; senza profilo non si pubblica.
- **Ci si candida solo dalla controparte**, una volta sola per annuncio, e solo
  finché il turno è aperto e non è ancora iniziato.
- **Il brevetto richiesto è gerarchico:** P ⊂ IP ⊂ MIP, quindi chi ha il MIP
  copre un turno che chiede il P, ma non viceversa. I brevetti scaduti non
  contano. `ALTRO` non è confrontabile e va verificato a mano dallo staff.
- **Accettare una candidatura** assegna il turno e rifiuta le altre in attesa,
  in un'unica transazione: un turno assegnato senza candidatura accettata
  sarebbe uno stato incoerente.
- **Fra due persone la conversazione è una sola**, anche se nasce da annunci
  diversi. Chi non partecipa riceve 404, non 403: non deve nemmeno sapere che
  quella conversazione esiste.
- **Il blocco vale in entrambi i versi.** Chi blocca non vuole essere
  contattato, e chi è bloccato non deve poter aggirare la cosa scrivendo per
  primo da una chat nuova.

## Sicurezza

- Password con hash **bcrypt** (mai in chiaro, mai in risposta).
- Token **JWT** firmati HS256, da passare come `Authorization: Bearer <token>`.
- Il login non rivela se un'email è registrata: stesso messaggio e stesso tempo
  di risposta in entrambi i casi.
- Gli id dell'autore (annunci, recensioni, profili) vengono **dal token**, mai
  dal corpo della richiesta: altrimenti si potrebbe scrivere a nome di altri.
- `SECRET_KEY` in `config.py` è un valore da sviluppo. In produzione va
  impostata la variabile d'ambiente:
  `python -c "import secrets; print(secrets.token_hex(32))"`.

## Prossimi passi

1. **La PWA**: interfaccia mobile-first, service worker, installazione su
   telefono. È l'unico pezzo che manca perché il progetto sia usabile.
2. Segnalazione degli abusi allo staff: oggi si può bloccare, ma non segnalare.
3. Notifiche per i turni urgenti nelle proprie zone.
4. Migrazioni con Alembic al posto di `create_all`.
