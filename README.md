# Guardlink

> In questo repository ci sono due progetti. Questo è Guardlink; l'altro è la
> [Piscina Comunale di Ciampino](piscina/README.md), l'app per prenotare
> ombrellone e lettini, che vive tutta nella cartella `piscina/`.

Bacheca turni che mette in contatto **bagnini** e **piscine/strutture** a Roma
e nei Castelli Romani.

Il nome tiene insieme le due cose che fa: i *guard* — chi sorveglia la vasca —
e il *link*, il collegamento fra chi cerca un turno e chi lo offre. Non nomina
la piscina apposta: se un domani la bacheca copre anche il mare, il nome regge.

Stato attuale: **passo 13 — pronto per andare online**. Il progetto è completo:
backend, interfaccia mobile installabile sul telefono, foto, chat, recensioni,
pannello di gestione, informativa privacy, e il pacchetto per metterlo su un
server con https e backup. Vedi [Mettere Guardlink online](#mettere-guardlink-online).

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
pytest        # 175 test end-to-end sulle regole di dominio
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
- **Profilo** — brevetti, esperienze, disponibilità, recensioni ricevute,
  utenti bloccati e la sezione "I tuoi dati", da cui si scaricano i propri dati
  o si cancella l'account.
- **Gestione** — c'è solo per chi ha il permesso di staff: le code di verifica,
  la ricerca degli account e il registro delle azioni. Vedi
  [Il pannello di gestione](#il-pannello-di-gestione).

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
- **Gli aggiornamenti si annunciano, non si impongono**: chi ha l'app aperta
  vede una barra e decide quando ricaricare. Vedi
  [Installazione e aggiornamenti](#installazione-e-aggiornamenti).
- `web/js/api.js` è **l'unico punto che parla con il backend**: se cambia
  l'indirizzo dell'API o il modo di autenticarsi, si tocca solo quel file.

## Struttura del progetto

```
web/                     la PWA
├── index.html
├── privacy.html          l'informativa, leggibile anche senza account
├── manifest.webmanifest  nome, icone, avvio a tutto schermo
├── sw.js                 service worker
├── css/stile.css
└── js/
    ├── api.js            il client HTTP: unico punto di contatto col backend
    ├── stato.js          sessione e dati condivisi
    ├── aggiornamenti.js  service worker e barra "nuova versione"
    ├── installa.js       "Aggiungi a Home", con i passi giusti per iPhone
    ├── ui.js             pezzi riusabili: date, chip, stelle, pannelli
    ├── app.js            guscio e navigazione fra le schede
    └── viste/            una per schermata

app/
├── core/
│   ├── config.py        impostazioni (DATABASE_URL, SECRET_KEY...) da env o .env
│   ├── avvio.py         controlli che bloccano l'avvio se la configurazione non regge
│   ├── limiti.py        conta i tentativi di accesso
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
├── crea_staff.py        assegna il permesso di gestione a un account
├── prova_email.py       verifica la configurazione della posta
├── backup.py            copia di sicurezza di database e foto
├── foto_demo.py         immagini disegnate per il seed
├── genera_icone.py      icone PNG della PWA
├── video_demo.py        registra il video dimostrativo
├── demo/palco.html      il "palco" a due telefoni usato dal video
└── aggiorna_schema.py   aggiorna un database creato con una versione precedente
tests/                   test end-to-end

Dockerfile               l'immagine dell'applicazione
docker-compose.yml       app + Caddy, i due contenitori del server
Caddyfile                https automatico e intestazioni di sicurezza
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
| POST | `/auth/recupero-password` | manda il link per reimpostarla |
| POST | `/auth/reimposta-password` | imposta la nuova password e fa entrare |
| POST | `/auth/verifica-email` | conferma l'indirizzo con il codice ricevuto |
| POST | `/auth/invia-verifica` | rimanda il link di conferma |
| GET | `/auth/esporta` | scarica tutti i propri dati (JSON) |
| GET | `/auth/cancellazione/riepilogo` | cosa sparisce e cosa resta |
| DELETE | `/auth/me` | cancella l'account (password + "CANCELLA") |

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

### Gestione (solo staff)
| Metodo | Percorso | Cosa fa |
|---|---|---|
| GET | `/staff/riepilogo` | conteggi: code di verifica, iscritti, sospesi |
| GET | `/staff/brevetti` | coda dei brevetti da controllare, i più vecchi in cima |
| POST | `/staff/brevetti/{id}/verifica` | segna il brevetto come visto sull'originale |
| GET | `/staff/utenti` | elenco account, con ricerca e filtri |
| POST | `/staff/utenti/{id}/verifica` | spunta "verificato" sull'account |
| POST | `/staff/utenti/{id}/stato` | sospende o riattiva un account |
| GET | `/staff/registro` | storico di tutte le azioni dello staff |

A chi non è staff rispondono **404**, non 403: il pannello non deve nemmeno
risultare esistente.

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
| `token_email` | codici usa e getta per verifica indirizzo e recupero password |
| `azioni_staff` | registro di chi ha verificato o sospeso cosa, e perché |

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

**Se hai già un database** creato con una versione precedente, `create_all`
crea le tabelle nuove ma **non aggiunge colonne** a quelle che esistono già.
Si sistema con:

```bash
python -m scripts.aggiorna_schema
```

Aggiunge le colonne mancanti, ricostruisce le aree dall'anagrafica e inserisce
le zone nuove, senza toccare i dati. È un rattoppo mirato: il lavoro vero lo
farà Alembic.

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

## Email: recupero password e conferma indirizzo

Chi dimentava la password restava fuori per sempre: adesso c'è il recupero.

- Si chiede il link da **Password dimenticata?**, e la risposta è **sempre la
  stessa** anche se l'indirizzo non è registrato. Dire "questa email non
  esiste" permetterebbe a chiunque di scoprire chi è iscritto.
- Il link arriva come `/?recupero=CODICE`, e il codice viene **tolto subito
  dalla barra** dell'indirizzo: resterebbe nella cronologia del telefono.
- **Nel database finisce solo l'impronta del codice**, non il codice: chi
  leggesse una copia del database non deve poter entrare negli account, come
  per le password.
- Il codice **vale una volta sola e per 30 minuti**. Chiederne uno nuovo
  annulla il precedente, così non restano più chiavi buone in giro.
- La conferma dell'indirizzo dura 48 ore e non blocca niente: il profilo lo
  segnala, e da lì si rimanda il link.

**Le email in sviluppo non partono**: finiscono nel log con il link in chiaro,
così si prova tutto il giro senza configurare nulla.

### Far partire le email davvero

Le email automatiche sono **due sole**: il link per reimpostare la password e
quello per confermare l'indirizzo. Non serve nessun servizio di newsletter.

Un normale account Gmail basta per cominciare — regge qualche decina di
messaggi al giorno, che a inizio vita sono più di quanti ne servano. Il
mittente sarà il tuo indirizzo Gmail: si vede che è artigianale, ma funziona
e non richiede un dominio.

**1. Attiva la verifica in due passaggi** sull'account Google
(*Account Google → Sicurezza → Verifica in due passaggi*). Senza, il passo 2
non esiste proprio: la voce non compare.

**2. Crea una "password per le app"** su
<https://myaccount.google.com/apppasswords>. Dai un nome qualsiasi
("Guardlink") e Google restituisce **16 lettere**. Quelle sono la password che
va nel file di configurazione — non quella con cui entri in Gmail, che da un
programma esterno non funziona. Si vede una volta sola: se la perdi ne crei
un'altra.

**3. Compila il file di configurazione:**

```bash
cp .env.esempio .env      # poi si apre .env e si mettono i propri valori
```

```bash
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORTA=587
EMAIL_SMTP_UTENTE=tuonome@gmail.com
EMAIL_SMTP_PASSWORD=le16letteredigoogle       # senza spazi
EMAIL_MITTENTE=Guardlink <tuonome@gmail.com>  # stesso indirizzo di sopra
URL_PUBBLICO=http://127.0.0.1:8000            # l'indirizzo pubblico, quando ci sarà
```

`.env` **non finisce su GitHub** (è nel `.gitignore`): contiene una password.

**4. Prova che funzioni:**

```bash
python -m scripts.prova_email tua@email.it
```

Manda un messaggio vero e dice com'è andata. Serve perché l'app, di proposito,
**non segnala mai** un invio fallito: al recupero password risponde sempre
"fatto", altrimenti un errore visibile direbbe a chiunque quali indirizzi sono
registrati. Comodo per la sicurezza, pessimo per capire se hai sbagliato una
lettera: da qui invece l'errore si vede, tradotto in italiano.

Se il messaggio non arriva, **guarda nello spam**: la prima email da un
mittente nuovo ci finisce spesso.

### Quando Gmail non basta più

Quando gli iscritti sono tanti, Gmail comincia a rifiutare: è pensato per
scrivere a persone, non per spedire in automatico. Allora servono un dominio
tuo (`guardlink.it`) e un servizio che spedisce (Brevo, Mailgun, Postmark —
tutti con un piano gratuito che basta a lungo).

Il dominio serve a **dimostrare che il mittente è tuo**: chi riceve va a
controllare nelle impostazioni del dominio due righe che dicono "sì, quel
servizio può spedire a nome mio", e quelle righe puoi metterle solo se il
dominio è tuo. Senza, il messaggio finisce nello spam — cioè il bagnino che ha
perso la password non riceve niente.

Cambiano solo le prime righe del `.env`, il codice no.

## Mettere Guardlink online

Servono un **dominio** (~10-15 €/anno) e un **VPS piccolo** (Hetzner CX22,
Contabo, OVH: ~5 €/mese). Nient'altro: l'app, il database, le foto e il
certificato https stanno tutti lì dentro.

### 1. Il dominio punta al server

Nel pannello di chi ti ha venduto il dominio servono **due record A**, entrambi
verso l'IP del VPS:

| Tipo | Nome | Valore |
|---|---|---|
| A | `@` (oppure vuoto, o il dominio stesso) | l'IP del server |
| A | `www` | lo stesso IP |

Il secondo serve perché chi digita `www.guardlink.it` venga rimandato
all'indirizzo senza `www`: senza quel record Caddy non riesce a ottenere il
certificato per quel nome e lascia un errore nel log — l'app funziona lo
stesso, ma sembra rotta a chi guarda.

Poi si aspetta che si propaghi (di solito minuti, a volte qualche ora):

```bash
ping guardlink.it        # deve rispondere l'IP del tuo server
```

Va fatto **prima** di avviare i contenitori: Caddy chiede il certificato al
primo avvio, e Let's Encrypt lo concede solo se il dominio punta già davvero
lì. Chiedendolo troppe volte a vuoto si finisce in un limite temporaneo di
Let's Encrypt, e allora tocca aspettare qualche ora.

L'app sta su **un solo indirizzo**, quello senza `www`. Non è pignoleria: il
token di accesso e il service worker sono legati all'origine, quindi chi
entrasse da `www` si ritroverebbe una sessione separata e una seconda copia
dell'app installata sul telefono.

### 2. Il server

```bash
ssh root@IP-DEL-SERVER

apt update && apt install -y docker.io docker-compose-v2 git
git clone https://github.com/gabrielebonacci7-coder/Portale-piscina.git guardlink
cd guardlink
```

### 3. La configurazione

```bash
cp .env.esempio .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # la chiave segreta
nano .env
```

Nel file servono:

```bash
DOMINIO=guardlink.it
URL_PUBBLICO=https://guardlink.it
SECRET_KEY=...                      # quella appena generata
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_UTENTE=tuonome@gmail.com
EMAIL_SMTP_PASSWORD=...             # password per le app, 16 lettere
EMAIL_MITTENTE=Guardlink <tuonome@gmail.com>
```

`DEBUG` e `DIETRO_PROXY` non si toccano: li imposta `docker-compose.yml`,
perché non sono scelte ma conseguenze del fatto che l'app gira dietro Caddy.

### 4. Accendere

```bash
docker compose up -d --build
docker compose logs -f app          # Ctrl+C per smettere di guardare
```

Dopo un minuto **https://guardlink.it** risponde, con il certificato già a
posto.

Se l'app **non parte**, guarda il log: se la configurazione non è adatta a
stare online si rifiuta di partire e dice esattamente cosa manca. È voluto —
vedi [Il controllo all'avvio](#il-controllo-allavvio).

### 5. Il primo account staff

```bash
# Iscriviti normalmente dall'app, poi:
docker compose exec app python -m scripts.crea_staff tua@email.it
```

### 6. I backup

```bash
docker compose exec app python -m scripts.backup --dove /dati/backup
```

Automatico ogni notte alle 3, con `crontab -e`:

```
0 3 * * * cd /root/guardlink && docker compose exec -T app python -m scripts.backup --dove /dati/backup
```

Il database **non** si copia con `cp`: se qualcuno sta scrivendo, il file
ottenuto può essere a metà di una transazione — si apre lo stesso, ma i dati
dentro non tornano. `scripts/backup.py` usa l'API di backup di SQLite, che
produce una copia coerente anche con l'app accesa, e tiene le ultime 14.

> **Un backup che sta sullo stesso disco non serve a niente**, perché il caso
> da cui ti difende è proprio il disco che si rompe. Portane una copia fuori —
> `rsync` verso casa, uno spazio di archiviazione, quello che preferisci.

### Aggiornare l'app dopo una modifica

```bash
cd /root/guardlink
git pull
docker compose up -d --build
```

I dati non si toccano: database e foto stanno su volumi, fuori dall'immagine.
Se hai cambiato qualcosa nella cartella `web/`, ricordati di cambiare anche
`VERSIONE` in `web/sw.js`, altrimenti i telefoni continuano a usare la copia
che hanno in cache.

Se hai aggiunto colonne al database:

```bash
docker compose exec app python -m scripts.aggiorna_schema
```

### Il controllo all'avvio

In produzione l'app **si rifiuta di partire** se la configurazione non regge, e
dice quale problema ha. Controlla quattro cose:

| Problema | Perché è grave |
|---|---|
| `SECRET_KEY` ancora quella di sviluppo | Sta scritta nel codice su GitHub: chiunque potrebbe firmarsi un token valido per qualsiasi account |
| `DEBUG` acceso | CORS accetta qualsiasi origine e gli errori mostrano il codice interno |
| Indirizzo senza `https` | Il service worker non parte: niente installazione sul telefono, niente aggiornamenti |
| Posta non configurata | Chi dimentica la password resta fuori per sempre |

Un server acceso male funziona benissimo e sembra a posto: è il motivo per cui
questi controlli bloccano l'avvio invece di scrivere un avvertimento nel log.

"Sono online" si deduce da **due indizi indipendenti**, perché uno solo si
dimentica: `DEBUG=false` è la dichiarazione, un `URL_PUBBLICO` che non punta a
questo computer è il fatto. Basta uno dei due. In locale non scatta niente.

### Limiti ai tentativi

Login, registrazione e recupero password contano i tentativi: senza, si
possono provare password all'infinito.

I limiti **per indirizzo email** sono stretti (5 per quarto d'ora), quelli
**per IP** larghi (30). Non è una svista: in piscina i bagnini stanno tutti
sullo stesso wi-fi e per il server hanno lo stesso indirizzo. Un numero basso
lì non fermerebbe nessun attacco vero — chi ci prova sul serio usa tanti IP —
ma chiuderebbe fuori mezzo spogliatoio.

I contatori stanno in memoria: si azzerano al riavvio, e con due processi
uvicorn il limite effettivo raddoppia. A questa dimensione va bene; se un
giorno servisse un conteggio esatto, il posto dove metterlo è
`app/core/limiti.py`, senza toccare i router.

### SQLite o PostgreSQL

Si parte con **SQLite** e va benissimo: è un file solo, il backup è copiarlo, e
con qualche decina di iscritti regge senza fatica. È attivo il modo WAL, quindi
chi legge non aspetta chi scrive.

Per passare a PostgreSQL più avanti servono due cose: aggiungere il driver
(`psycopg[binary]` in `requirements.txt`) e cambiare `DATABASE_URL`. Il codice
è già indipendente dal motore — le impostazioni specifiche di SQLite si
applicano solo se l'indirizzo comincia per `sqlite` — ma i dati vanno
travasati a mano, quindi meglio farlo quando serve davvero e non "per sicurezza".

## Installazione e aggiornamenti

### Come si installa sul telefono

Non passa da nessun negozio: si apre l'indirizzo nel browser e si aggiunge alla
schermata Home. L'app propone da sola l'operazione dalla bacheca, e la
riproprone sempre dal profilo (*Aggiungi a Home*).

- **iPhone** — *Condividi* (il quadrato con la freccia in su) → *Aggiungi a
  Home* → *Aggiungi*. **Solo da Safari**: da Chrome o Firefox su iPhone quella
  voce non esiste, ed è il motivo per cui qualcuno "non trova il pulsante". Se
  l'app si accorge di non essere in Safari lo dice, invece di far cercare a
  vuoto.
- **Android** — Chrome apre il pannello di installazione del sistema con un
  tocco (`beforeinstallprompt`), quindi lì basta premere *Aggiungi*.

Serve **HTTPS**: senza, il service worker non parte e l'installazione non viene
offerta. In sviluppo `127.0.0.1` fa eccezione, ma in produzione il certificato
è obbligatorio.

### Come arriva un aggiornamento a chi ce l'ha già installata

Il caso da gestire è quello vero: l'app sta sulla schermata Home di un bagnino
che non la chiude da una settimana. Senza qualcosa che se ne accorga, resterebbe
sulla versione vecchia a tempo indeterminato.

1. Il browser ricontrolla `sw.js`. Lo fa da sé alla navigazione; noi glielo
   richiediamo anche quando l'app torna in primo piano, al massimo una volta
   l'ora — un'app installata può restare aperta per giorni senza mai navigare.
2. Se il file è cambiato, la versione nuova si scarica in cache e **aspetta**.
3. Compare la barra **"È disponibile una versione nuova"**.
4. Chi preme *Aggiorna* fa passare avanti la nuova, e la pagina si ricarica.
   La sessione resta: il token sta in `localStorage`, non in cache.

**Il passaggio non è automatico apposta.** Ricaricare da soli sotto le mani di
qualcuno che sta scrivendo un messaggio gli farebbe perdere quello che ha
scritto; e un service worker che subentra subito lascerebbe la pagina vecchia
in esecuzione con i file nuovi già in cache, cioè due versioni mescolate. Per lo
stesso motivo `skipWaiting()` **non** sta nell'`install`: lo chiama la pagina,
quando l'utente decide.

Chi chiude la barra se la ritrova alla riapertura successiva: restare indietro
non è una scelta da rendere definitiva.

**Per rilasciare una versione nuova basta cambiare `VERSIONE` in `web/sw.js`.**
Se non si cambia, il guscio resta quello vecchio in cache e le modifiche non
arrivano a nessuno. È l'unico passaggio manuale del rilascio, e saltarlo è
l'errore facile da fare.

## Privacy e dati personali

L'informativa sta in `web/privacy.html` ed è raggiungibile da `/privacy.html`,
anche senza essere iscritti. È linkata dal modulo di iscrizione e dal profilo.

> **Da compilare prima di andare online.** Nell'informativa ci sono cinque
> segnaposto in rosso — nome del titolare, indirizzo, partita IVA, email di
> contatto e la verifica sui trasferimenti fuori dall'Unione Europea. Sono dati
> che solo tu puoi mettere. Finché restano lì l'informativa non è valida, e si
> vedono a occhio proprio perché non passino inosservati.
>
> Il testo copre quello che l'app fa davvero, ma **non è un parere legale**: se
> la piattaforma cresce, fallo leggere a chi se ne occupa.

**Il consenso si registra, non si presume.** Alla registrazione la casella non
è mai già spuntata e non ha un valore di default: chi non la spunta riceve 422
dal server, non solo un avviso del browser. Sull'account restano *quando* è
stato dato il consenso e *a quale versione* dell'informativa
(`app/core/privacy.py`). La versione conta: senza, la data non dimostrerebbe
niente, perché fra un anno il testo sarà cambiato. **Se modifichi
l'informativa in modo sostanziale, cambia anche `VERSIONE_INFORMATIVA`.**

Gli account creati prima di questa versione restano senza consenso registrato,
e la migrazione **non** lo inventa: un `UPDATE` che riempisse quel campo
darebbe per buono un sì che nessuno ha mai detto.

### I tuoi dati, dal profilo

- **Scarica i miei dati** (`GET /auth/esporta`) — un JSON con account, profilo,
  brevetti, esperienze, annunci, candidature, recensioni e messaggi inviati.
  I messaggi *ricevuti* non ci sono: sono dati di chi li ha scritti, e
  regalarli in un file scaricabile non sarebbe corretto verso di loro.
- **Elimina account** (`DELETE /auth/me`) — chiede la password e la parola
  `CANCELLA` scritta a mano, e prima mostra cosa succede.

### Perché la cancellazione non è un `DELETE`

Cancellare la riga si porterebbe dietro, a cascata, cose che non appartengono
solo a chi se ne va:

- le **recensioni scritte** sono la reputazione di chi le ha ricevute — se
  bastasse cancellarsi per azzerarle, chiunque toglierebbe un giudizio scomodo
  iscrivendosi di nuovo il giorno dopo;
- i **messaggi** sono metà di una conversazione, e l'altra metà è di qualcuno
  che non ha chiesto niente;
- i **turni già svolti** sono la storia lavorativa anche della struttura.

Quindi si cancellano i **dati personali**, non le tracce delle interazioni:
profilo, foto (anche dal disco), brevetti, esperienze, email, telefono e
password spariscono; l'indirizzo diventa `cancellato-N@guardlink.invalid`
(dominio riservato dallo standard, così nessuna email raggiungerà mai una
persona vera) e al posto del nome compare "Utente cancellato". Gli annunci
ancora aperti vengono eliminati — nessuno deve rispondere a un turno di un
account che non esiste più — mentre quelli già assegnati restano.

Non è un cavillo per tenersi i dati: è il modo normale di conciliare il diritto
alla cancellazione con i diritti degli altri, ed è scritto nell'informativa in
modo che chi cancella lo sappia prima.

### Cookie

Non ce ne sono, e non c'è nessun banner perché non c'è niente da autorizzare.
Il token di accesso sta in `localStorage`: è tecnicamente necessario a tenere
l'utente collegato, non traccia nulla e sparisce all'uscita.

## Il pannello di gestione

Serve a chi manda avanti la piattaforma: controllare i brevetti, verificare le
strutture, sospendere chi imbroglia.

```bash
python -m scripts.crea_staff gestione@tuodominio.it   # dà il permesso
python -m scripts.crea_staff --elenco                 # chi ce l'ha
python -m scripts.crea_staff EMAIL --togli            # lo toglie
```

L'account deve **esistere già**: ci si iscrive normalmente dall'app e poi si
lancia il comando. Rientrando, nel menù in basso compare la scheda **Gestione**.

- **Il permesso è separato dal tipo di account** (`utenti.ruolo`, non
  `utenti.tipo`). Chi gestisce la piattaforma può benissimo essere anche il
  titolare di una piscina, e non deve tenere due account per farlo.
- **Non esiste nessuna rotta HTTP che promuova qualcuno a staff.** Si assegna
  solo da riga di comando, cioè solo da chi ha accesso al server: se ci fosse
  un endpoint, basterebbe un account rubato per prendersi il pannello. Il campo
  `ruolo` mandato in registrazione viene ignorato.
- **Lo staff non tocca lo staff**, e nemmeno sé stesso: quelle modifiche si
  fanno da riga di comando. Evita sia l'autoblocco per sbaglio sia il litigio a
  colpi di pulsante. E l'ultimo membro rimasto non può togliersi il ruolo:
  chiuderebbe il pannello a tutti.
- **Sospendere non cancella niente.** Annunci, messaggi e recensioni restano;
  il token smette di funzionare, quindi l'account non entra più. Si annulla
  riattivandolo. Il motivo è **obbligatorio**.
- **Ogni azione finisce in `azioni_staff`**, con chi l'ha fatta, su cosa e
  perché. Sospendere qualcuno è una decisione che prima o poi verrà contestata,
  e allora serve avercelo scritto.

## Il video dimostrativo

```bash
python -m scripts.video_demo            # ~100 secondi, formato 4:5
python -m scripts.video_demo --veloce   # pause dimezzate, per provare i tagli
```

Non è un mockup: guida **l'applicazione vera** dentro due telefoni affiancati —
la struttura a sinistra, il bagnino a destra — e registra quello che succede,
dalla pubblicazione del turno fino alle recensioni. Se l'app cambia, il video
si rifà con un comando.

Due server sulla stessa applicazione, sulla stessa base dati: il token sta in
`localStorage`, che è legato all'origine, quindi due telefoni sulla stessa
porta sarebbero lo stesso utente.

Esce in `demo/`: `guardlink-demo.mp4` e un fotogramma da usare come copertina.

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

1. **Migrazioni con Alembic** al posto di `create_all` e di
   `scripts/aggiorna_schema.py`, che è un rattoppo mirato e non un sistema di
   migrazioni. Serve quando le modifiche allo schema diventano frequenti.

**Poi, quando serve**

2. **Segnalazione degli abusi.** Oggi si può bloccare qualcuno, ma non avvisare
   lo staff: il blocco protegge il singolo, la segnalazione permetterebbe di
   accorgersi di chi molesta dieci persone. Rimandata per scelta: finché gli
   iscritti sono pochi le segnalazioni arrivano a voce.
3. Notifiche push per i turni urgenti nelle proprie zone.
4. Ricerca dei bagnini per disponibilità oraria, non solo per zona.
