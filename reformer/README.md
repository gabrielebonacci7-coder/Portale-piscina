# RE FORMER

App dello studio **RE FORMER** per prenotare le lezioni di pilates reformer
con **Greta Lorenzetti** ed **Elisa Bonacci**. Si installa sul telefono come
un'app (PWA), e Greta ed Elisa hanno il loro gestionale dentro la stessa app.

Lo stesso schema della piscina di Ciampino e di Guardlink: FastAPI,
SQLAlchemy, SQLite, interfaccia senza framework, Docker e Caddy per andare
online. L'aspetto viene dal prototipo approvato (`pilates/prototipo/`), con
la palette **Sabbia e nero**.

**Per metterla online: [MESSA-ONLINE.md](MESSA-ONLINE.md)**, passo passo.

## Provarla sul computer

```bash
pip install -r reformer/requirements-dev.txt      # dalla radice del repository

python -m reformer.scripts.dati_esempio           # (facoltativo) clienti finte
uvicorn reformer.main:app --reload --port 8002
```

Poi **http://127.0.0.1:8002**. Con i dati d'esempio si entra come Greta
(`greta.lorenzetti@icloud.com`) o come una cliente
(`sofia.marini@example.com`), password `demo1234`. Le email non partono: il
loro testo, con i link, compare nel terminale.

Su **/docs** c'è la documentazione interattiva dell'API.

```bash
pytest reformer/tests          # 39 prove: le regole, l'avvio, e un giro completo nel browser
```

## Le regole

| | |
|---|---|
| Orario | lun–ven 16:30 · 17:30 · 18:30; sabato 11:30 · 12:30; lezioni da un'ora |
| Chi insegna | Greta lunedì, mercoledì, venerdì, sabato · Elisa martedì e giovedì |
| Posti | 3 per lezione (i 3 reformer) |
| Quanto prima | fino a 30 giorni avanti |
| Disdetta | fino a 12 ore prima; la lezione torna nel pacchetto |
| Lista d'attesa | se una disdice entra la prima in lista, in automatico, e riceve una notifica |
| Lezioni rimaste | le scrivono Greta ed Elisa dal gestionale (numero esatto o +/−, scadenza facoltativa) |
| Lezioni finite | si può prenotare lo stesso, fino a 2 lezioni da saldare (`REFORMER_MAX_LEZIONI_DA_SALDARE`): il saldo va sotto zero e Greta ed Elisa ricevono una notifica |
| Pagamento | solo in studio; nell'app non ci sono prezzi |
| Promemoria | il giorno prima, nell'app e per email |
| Staff | chi si registra con le email di Greta o di Elisa **e la conferma** |

L'orario e le istruttrici stanno in [`dominio/orario.py`](dominio/orario.py);
posti, ore di disdetta e giorni prenotabili nella configurazione
([`core/config.py`](core/config.py), variabili `REFORMER_...`). Tutte le
regole di prenotazione sono in un file solo:
[`servizi/regole.py`](servizi/regole.py).

## Come Greta ed Elisa diventano staff

Gli indirizzi sono nella configurazione (`REFORMER_EMAIL_STAFF`, già
impostata con `greta.lorenzetti@icloud.com` ed `elisabonacci@yahoo.it`).
Quando un account con uno di quegli indirizzi **conferma l'email** dal link
che riceve, diventa staff da solo. Registrarsi con l'indirizzo di Greta non
basta: bisogna anche poter leggere la sua posta.

Riserva, dal server: `python -m reformer.scripts.crea_staff email@...`.

## Com'è fatta

```
reformer/
├── main.py                avvio, controlli di configurazione, promemoria
├── core/                  configurazione, password e token, email, limiti ai tentativi
├── db/                    connessione e creazione delle tabelle
├── models/                le tabelle (un file solo, commentato)
├── dominio/orario.py      orario della settimana e istruttrici
├── servizi/
│   ├── regole.py          prenotare, disdire, attesa, saldo, staff
│   ├── account.py         registrazione, conferma, recupero, privacy
│   ├── promemoria.py      il giro del promemoria del giorno prima
│   └── viste.py           come lezioni e clienti arrivano all'app
├── api/routers/           pubblico, accesso, cliente, staff
├── web/                   la PWA (HTML, CSS, JS, service worker)
├── scripts/               dati d'esempio, backup, ruolo staff, prova email
├── tests/                 le prove
└── deploy/                Dockerfile, docker-compose, Caddyfile, .env.esempio
```

Alcune scelte, e perché:

- **Le lezioni nascono quando servono.** Non c'è un calendario dell'anno
  pre-caricato: quando qualcuno guarda una settimana, le lezioni che mancano
  si creano seguendo l'orario. Se l'orario cambia, i giorni futuri seguono
  quello nuovo da soli.
- **Un processo solo.** Il lucchetto che impedisce a due clienti di prendere
  insieme l'ultimo reformer vive in memoria, e il promemoria deve partire
  una volta sola. In più c'è l'indice unico nel database.
- **La cliente non vede chi c'è.** Le altre clienti vedono solo quanti posti
  sono liberi; i nomi li vede solo lo staff.
- **Ogni variazione del saldo lascia una riga** (Movimenti), con chi l'ha
  fatta: "ma io non avevo ancora tre lezioni?" si risolve in un attimo.
- **Orari sempre di Roma**, sul server (anche al cambio dell'ora legale) e
  sul telefono (anche se è impostato su un altro fuso).
- **Online non si parte con la configurazione di sviluppo**: senza chiave
  segreta vera o con l'indirizzo locale, l'app si ferma e dice perché.

## Da fare più avanti

- **Notifiche push sul telefono.** Oggi le notifiche sono nella campanella
  dell'app, più l'email per il promemoria. Le push vere (anche ad app
  chiusa) si possono aggiungere: su iPhone funzionano solo con l'app
  aggiunta alla schermata Home.
- **Orario modificabile dal gestionale.** Oggi si cambia in
  `dominio/orario.py`; Greta ed Elisa possono già annullare una lezione o
  cambiarle titolo, ma non aggiungerne una fuori orario.
- **Chiusure per ferie in blocco** (oggi si annulla lezione per lezione e
  si manda un avviso).
