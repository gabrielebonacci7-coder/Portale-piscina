# Guardlink

Bacheca turni che mette in contatto **bagnini** e **piscine/strutture** a Roma
e nei Castelli Romani.

Il nome tiene insieme le due cose che fa: i *guard* — chi sorveglia la vasca —
e il *link*, il collegamento fra chi cerca un turno e chi lo offre. Non nomina
la piscina apposta: se un domani la bacheca copre anche il mare, il nome regge.

Stato attuale: **passo 9 — recensioni dall'app**. Il progetto è utilizzabile: backend
completo, interfaccia mobile installabile sul telefono, foto profilo per i
bagnini e galleria per le strutture.

**La bacheca è riservata agli iscritti**: senza login si può solo registrarsi e
leggere l'elenco delle zone (serve al modulo di iscrizione).

## Avvio rapido

```bash
pip install -r requirements.txt      # per i test: requirements-dev.txt

python -m app.db.init_db      # crea le tabelle e inserisce le zone
python -m scripts.seed_demo   # (facoltativo) dati di esempio

uvicorn app.main:app --reload
```

Poi si apre **http://127.0.0.1:8000** — è l'app vera e propria. Un solo
processo serve sia l'API sia l'interfaccia: nessuna porta in più da avviare,
nessun problema di CORS, e il service worker vede tutto sotto la stessa origine.

Account di esempio, tutti con password `demo1234`:

| Email | Chi è |
|---|---|
| `marco.rossi@example.com` | bagnino con brevetto MIP |
| `giulia.conti@example.com` | bagnina con brevetto P |
| `info@aquacenter.example` | struttura che pubblica turni |

Su **/docs** resta la documentazione interattiva dell'API, per provare le
chiamate una per una.

```bash
pytest        # 110 test end-to-end sulle regole di dominio
```

## L'app (PWA)

Interfaccia mobile-first: il bersaglio è un bagnino che guarda il telefono fra
un turno e l'altro. Su iPhone si aggiunge alla schermata home da Safari
(*Condividi → Aggiungi alla schermata Home*) e si apre a tutto schermo, senza
barra del browser.

- **Bacheca** — i turni, urgenti in cima, con ricerca e filtri per zona, tipo,
  compenso minimo. Il segmentato in alto passa all'elenco dei bagnini.
- **Candidature** (bagnino) / **I miei turni** (struttura) — da un lato dove ci
  si è candidati e com'è andata, dall'altro i propri annunci con quante
  risposte hanno ricevuto.
- **Messaggi** — le conversazioni, con il contatore dei non letti sull'icona.
- **Recensioni** — a turno concluso ognuno recensisce la controparte: stelle,
  commento e voti di dettaglio. Il modulo mostra solo i voti del proprio verso,
  così l'errore non è nemmeno possibile.
- **Profilo** — brevetti, esperienze, disponibilità, recensioni ricevute e
  utenti bloccati.

Scelte tecniche:

- **Niente framework e niente passo di compilazione.** JavaScript a moduli ES
  serviti così come sono: per installare basta `pip install`, senza npm né
  bundler. A questa dimensione è un vantaggio, non una rinuncia.
- **Il carattere è quello di sistema** (su iPhone è SF Pro): per un'app che
  vive sulla schermata home, sembrare nativa è una scelta. Il monospazio
  tabellare è riservato a compensi, orari e date, dove le cifre si incolonnano.
- **Il rosso è solo semantico**: urgenza e scadenze, mai decorazione. La
  striscia rossa a lato di una scheda vuol dire "urgente", niente altro.
- **Tema chiaro e scuro**, entrambi disegnati, che seguono il sistema.
- **Il service worker mette in cache il guscio, mai i dati.** Le risposte
  dell'API sono legate al token di chi le ha chieste: salvarle in cache
  significherebbe mostrare a un utente i dati di un altro.
- `web/js/api.js` è **l'unico punto che parla con il backend**: se cambia
  l'indirizzo dell'API o il modo di autenticarsi, si tocca solo quel file.

## Struttura del progetto

```
web/                     la PWA
├── index.html
├── manifest.webmanifest  nome, icone, avvio a tutto schermo
├── sw.js                 service worker
├── css/stile.css
└── js/
    ├── api.js            il client HTTP: unico punto di contatto col backend
    ├── stato.js          sessione e dati condivisi
    ├── ui.js             pezzi riusabili: date, chip, stelle, pannelli
    ├── app.js            guscio e navigazione fra le schede
    └── viste/            una per schermata

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
scripts/
├── seed_demo.py         dati di esempio
├── foto_demo.py         immagini disegnate per il seed
├── genera_icone.py      icone PNG della PWA
└── aggiorna_zone.py     aggiunge le aree a un database preesistente
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

### Foto
| Metodo | Percorso | Cosa fa |
|---|---|---|
| PUT | `/bagnini/me/foto` | carica o sostituisce la foto profilo |
| DELETE | `/bagnini/me/foto` | la rimuove |
| POST | `/piscine/me/foto` | aggiunge una foto (`tipo`: ingresso, vasca, ...) |
| DELETE | `/piscine/me/foto/{id}` | la elimina |

Le foto sono servite da `/media/…`. Ognuna ha anche un'anteprima, con lo
stesso nome più `-p`.

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
| `zone` | quartieri e comuni, raggruppati per area, per i filtri geografici |
| `bagnino_zone` | quali zone copre un bagnino (molti-a-molti) |
| `annunci` | il cuore della bacheca: chi pubblica, quando, dove, quanto, che tipo |
| `candidature` | chi ha risposto a un annuncio, con stato e messaggio |
| `conversazioni` | una chat fra due utenti |
| `partecipanti_conversazione` | chi ne fa parte e fin dove ha letto |
| `messaggi` | i messaggi di una conversazione |
| `blocchi` | chi ha bloccato chi |
| `foto_piscina` | le foto di una struttura, con il tipo (ingresso, vasca...) |
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
- **Le zone hanno tre etichette geografiche**, che rispondono a domande diverse:
  `nome` è come la chiami tu ("EUR", "Frascati"); `citta` è il comune vero, e
  vale "Frascati" per Frascati, non "Roma", perché dire che i Castelli sono
  Roma sarebbe falso; `area` è il gruppo con cui la zona si sceglie nell'app
  ("Roma", "Castelli Romani"); `macro_area` è la sotto-etichetta, che a Roma è
  il municipio e fuori resta vuota.
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

## Il marchio

Un salvagente: anello rosso con quattro settori bianchi, come quelli veri
appesi a bordo vasca. Sta su una piastra scura per due motivi — il bianco ha
bisogno di contrasto, e sulla schermata home di un telefono un'icona scura si
distingue fra tante chiare.

Non è un file da ridisegnare: è **disegnato in codice**, in una decina di righe
di SVG per lo schermo e altrettante di Python per i PNG. Si rigenera con:

```bash
python -m scripts.genera_icone
```

**Il rosso del marchio non è il rosso dell'interfaccia.** Dentro l'app il rosso
vuol dire una cosa sola — urgenza, scadenza — e l'accento resta il verde-acqua.
Nel marchio il rosso è il rosso del soccorso: stesso colore, due ruoli diversi,
tenuti separati apposta.

## Le zone

La bacheca copre due aree, e si estende aggiungendo righe a `ZONE` in
`app/db/init_db.py` — nient'altro.

| Area | Cosa contiene |
|---|---|
| **Roma** | 15 quartieri, uno per municipio |
| **Castelli Romani** | i 16 comuni: Albano, Ariccia, Castel Gandolfo, Ciampino, Colonna, Frascati, Genzano, Grottaferrata, Lanuvio, Marino, Monte Compatri, Monte Porzio Catone, Nemi, Rocca di Papa, Rocca Priora, Velletri |

Ciampino e Velletri non sono Castelli in senso stretto, ma stanno nello stesso
bacino di spostamenti: chi lavora a Marino li considera comunque. Toglierli è
una riga.

Nell'app le zone si scelgono raggruppate per area: con una trentina di voci un
elenco piatto sarebbe scomodo da scorrere sul telefono.

**Se hai già un database** creato prima delle aree, `create_all` non aggiunge la
colonna nuova alle tabelle esistenti. Si sistema con:

```bash
python -m scripts.aggiorna_zone
```

Aggiunge la colonna, assegna a Roma le zone che c'erano e inserisce le nuove,
senza toccare il resto. È un rattoppo mirato: il lavoro vero lo farà Alembic.

Nota: con il nome nuovo il database si chiama `guardlink.db`. Se ne hai uno
vecchio che vuoi tenere, rinominalo — `mv portale_piscina.db guardlink.db` —
oppure indica il percorso con `DATABASE_URL`.

## Le foto

Un bagnino ha una foto profilo, una struttura ne ha fino a sei, ognuna
etichettata con quello che mostra: **ingresso**, vasca, spogliatoi, altro.

**La foto dell'ingresso è obbligatoria per pubblicare un turno.** È quella che
permette a chi arriva di riconoscere il posto, magari di sera e di corsa; senza,
l'annuncio viene rifiutato con un messaggio che spiega cosa fare. Se ne tiene
una sola: caricandone un'altra sostituisce la precedente, perché due ingressi
diversi confonderebbero invece di aiutare.

**Nessun file arriva su disco così com'è.** Ogni immagine viene decodificata,
ruotata secondo l'orientamento originale, ridimensionata e riscritta da capo.
Serve a tre cose insieme:

- **Privacy.** Le foto dal telefono contengono l'EXIF, e dentro l'EXIF ci sono
  le **coordinate GPS del punto dello scatto**. Un bagnino che carica un selfie
  fatto in casa pubblicherebbe l'indirizzo di casa sua. Riscrivendo l'immagine
  l'EXIF sparisce — e c'è un test che lo verifica con un JPEG che contiene
  davvero delle coordinate.
- **Sicurezza.** Un file può dichiararsi `image/jpeg` ed essere altro. Conta
  solo se Pillow riesce a decodificarlo davvero, e la riscrittura scarta
  qualsiasi cosa fosse nascosta fra i byte.
- **Peso.** Una foto da telefono pesa anche 12 MB: ridotta a 1600px sta sotto i
  300 kB, e la bacheca resta veloce anche in 4G.

Il nome del file è casuale: quello scelto dall'utente non tocca mai il disco.
Le foto stanno in `media/`, che non è versionata.

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

**Perché l'app sia usabile da estranei**

1. **Recupero password ed email di verifica.** Oggi chi dimentica la password
   resta fuori per sempre, e chiunque può registrarsi con un'email non sua.
2. **Strumenti per lo staff.** Il campo `verificato` sui brevetti esiste ma
   nessuno può metterlo: manca un pannello per controllare i documenti,
   sospendere un account, leggere le segnalazioni.
3. **Segnalazione degli abusi.** Oggi si può bloccare qualcuno, ma non
   avvisare lo staff: il blocco protegge il singolo, la segnalazione permette
   di accorgersi di chi molesta dieci persone.

**Perché possa stare online**

4. **Messa in produzione**: `SECRET_KEY` da variabile d'ambiente, PostgreSQL al
   posto di SQLite, HTTPS (senza il quale il service worker non parte),
   backup, foto su uno spazio separato dal codice.
5. **Migrazioni con Alembic** al posto di `create_all`.

**Perché sia in regola**

6. **Informativa privacy e trattamento dati.** Si raccolgono dati personali di
   persone reali — nome, telefono, foto — quindi servono informativa, base
   giuridica e un modo per cancellare il proprio account. Non è un dettaglio
   rimandabile: è la legge.

**Poi, quando serve**

7. Notifiche push per i turni urgenti nelle proprie zone.
8. Ricerca dei bagnini per disponibilità oraria, non solo per zona.
