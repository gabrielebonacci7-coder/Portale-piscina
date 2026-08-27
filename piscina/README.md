# Piscina Comunale di Ciampino

App per prenotare **ombrellone e lettini** scegliendo il posto su una vista
dall'alto del solarium. Si installa sul telefono come un'applicazione, e ogni
prenotazione arriva per email allo staff, con nome, telefono ed email di chi
l'ha fatta.

Sta nella stessa cartella di Guardlink ma è un progetto a sé: database suo,
configurazione sua, nessun pezzo di codice in comune. Condividono solo le
librerie e il modo di scrivere le cose.

## Avvio rapido

```bash
pip install -r requirements.txt        # dalla radice del repository

python -m piscina.db.init_db           # crea le tabelle e le 62 postazioni
python -m piscina.scripts.dati_esempio # (facoltativo) qualche prenotazione finta
python -m piscina.scripts.crea_operatore "Nome Cognome" tua@email.it

uvicorn piscina.main:app --reload --port 8001
```

Poi si apre **http://127.0.0.1:8001** — l'app vera e propria. Il gestionale
dello staff sta su **/staff**, e su **/docs** c'è la documentazione
interattiva dell'API.

```bash
pytest piscina/tests      # 33 prove sulle regole di prenotazione
```

## Com'è fatta

### La mappa

Le 50 postazioni con ombrellone e i 12 lettini del solarium stanno in un file
solo: [`dominio/piantina.py`](dominio/piantina.py). Ci sono dentro le
coordinate, i codici e la scenografia (le due vasche, la cassa, le docce, la
sedia del bagnino, il campo da beach volley).

Sono numerate per fila, come si dicono a voce in cassa:

| Fila | Quante | Dove |
|---|---|---|
| A | 12 | sopra la vasca grande |
| B | 12 | lato destro, verso le docce |
| C | 8 | sotto la vasca grande, accanto al bagnino |
| D | 8 | fra la vasca piccola e il prato |
| E | 10 | in fondo, davanti all'ingresso |
| S | 12 | lettini singoli delle due zone solarium |

**Se la disposizione cambia si tocca solo quel file**: il disegno, il database
e l'app si adeguano da soli (`python -m piscina.db.init_db` riallinea le
postazioni senza perdere le prenotazioni né le postazioni spente a mano).

Lo stile è quello di una piscina vista dal drone: prato, pavimento in pietra
chiara, acqua con i riflessi del sole. Le tre grane (erba, acqua, pietra) sono
piastrelle da 256 pixel che si ripetono senza giunture, disegnate una volta
sola da `python -m piscina.scripts.genera_texture` e pesanti in tutto una
decina di kilobyte. Tutto il resto — vasche, ombrelloni, lettini, palme — è
vettoriale: si ingrandisce senza sgranare e cambia colore da solo.

Sulla mappa il colore dice una cosa sola:

- 🟢 **verde** — libera tutto il giorno
- 🟡 **giallo** — libera solo la mattina o solo il pomeriggio
- 🔴 **rosso** — occupata
- ⚪ **grigio** — fuori uso (la spegne lo staff dal gestionale)

Il colore sta sui lettini e in un alone sotto l'ombrellone; gli ombrelloni
restano color panna, come sono davvero. Tingerli tutti trasformerebbe la mappa
in un semaforo: da lontano si legge l'alone, da vicino la postazione.

Si tocca "lì attorno" e prende la postazione più vicina: su un telefono un
ombrellone è largo pochi pixel, e chiedere di centrarlo sarebbe come chiedere
di infilare un ago. Chi preferisce, dal bottone *Vedi l'elenco* ha la stessa
scelta in forma di lista — che è anche il modo in cui la usa un lettore di
schermo.

### Le fasce

Giornata intera 9–19, mattina 9–14, pomeriggio 14–19: sono le stesse del
listino comunale.

Mattina e pomeriggio convivono sotto lo stesso ombrellone, la giornata intera
no. Questa regola non è scritta in un `if`: ogni prenotazione occupa una o due
**mezze giornate** nella tabella `occupazioni`, che ha un vincolo di unicità su
(postazione, giorno, metà). Se due persone toccano lo stesso ombrellone nello
stesso istante, è il database a respingere la seconda — un controllo scritto in
Python le lascerebbe passare entrambe, e la lite scoppierebbe sotto
l'ombrellone invece che qui.

### I prezzi

Copiati dal cartello della stagione 2026, in
[`dominio/listino.py`](dominio/listino.py). Tutti gli importi sono in
centesimi: sui soldi non si usano i decimali in virgola mobile.

| Noleggio (al giorno) | Intera | Abb. settimanale | Abb. mensile |
|---|---|---|---|
| Ombrellone | 5 € | 4 € | 3 € |
| Lettino | 5 € | 4 € | 3 € |
| Relax 1 (ombrellone + 1 lettino) | 7 € | 5 € | 4 € |
| Relax 2 (ombrellone + 2 lettini) | 12 € | 9 € | 8 € |
| Relax 3 (ombrellone + 3 lettini) | 17 € | 13 € | 11 € |

Gli sconti per gli abbonati non si calcolano: sono quelli **esposti sul
cartello**, già arrotondati. Il 20% di 7 € farebbe 5,60 e il cartello dice 5.

**Si paga tutto in cassa all'arrivo**: l'app non incassa niente e non chiede
carte di credito. Il totale che mostra è il solo noleggio; gli ingressi si
contano in cassa, perché dipendono da quante persone sono e da chi è residente.

### Le immagini

Gli originali stanno in `risorse/`, e da lì tre script ricavano quello che
serve all'app. Si rilanciano solo quando cambia un disegno:

| Comando | Cosa fa |
|---|---|
| `python -m piscina.scripts.genera_icone` | le icone del telefono, dall'icona disegnata |
| `python -m piscina.scripts.ritaglia_omino` | scontorna l'omino (via lo sfondo a raggiera) |
| `python -m piscina.scripts.genera_texture` | erba, acqua e pietra della mappa |

### Chi prenota

Niente iscrizione: nome, telefono, email e via. Il codice della prenotazione
(`PC-4KH7Q`, senza lettere che si confondono al telefono) più il numero
servono a ritrovarla e ad annullarla dalla sezione *La mia*.

### Il gestionale

Su `/staff`, con email e password. Gli account li crea la direzione da riga di
comando: non c'è nessuna registrazione da nessuna parte.

Mostra il giorno scelto con nomi, telefoni cliccabili, email, postazioni e
incasso previsto; si cerca per nome, telefono, codice o postazione; si segna
chi è arrivato; si scarica il CSV per Excel; si spengono le postazioni fuori
uso.

## Prima di andare online

Le email non partono finché non si compila il `.env` (vedi
[`.env.esempio`](../.env.esempio), sezione `PISCINA_`). Senza SMTP le
prenotazioni si vedono lo stesso nel gestionale, e il testo dell'email finisce
nel log.

La riga che conta è **`PISCINA_EMAIL_STAFF`**: è quella che collega il modulo
sul telefono del cliente al banco della cassa.

### Cose da confermare

Sono segnate `DA CONFERMARE` in [`dominio/struttura.py`](dominio/struttura.py):

- **parcheggio e fermata più vicina**, per la pagina *Dove siamo* (l'indirizzo
  — Via Superga, accanto al campo sportivo — c'è);
- **le date di apertura e chiusura** della stagione (`PISCINA_STAGIONE_*`):
  finché sono vuote si prenota tutto l'anno;
- **se mezza giornata costa meno** della giornata intera
  (`PISCINA_SCONTO_MEZZA_GIORNATA`): sul cartello 2026 c'è una tariffa sola,
  quindi per ora costano uguale.

### La guida di apertura

Alla prima apertura l'omino non recita un monologo: accompagna. Ogni paragrafo
del discorso può portarsi dietro una **vetrina** — la sezione di cui sta
parlando, mostrata davvero — e le vetrine non sono figurine ma dati veri: la
mappa è quella del giorno, i prezzi vengono dal listino in corso. Una figurina
invecchierebbe al primo cambio di listino e nessuno se ne accorgerebbe, fino a
quando un cliente non arriva in cassa con la cifra sbagliata in testa.

Discorso e vetrine stanno in `BENVENUTO` dentro
[`dominio/struttura.py`](dominio/struttura.py): si aggiunge un paragrafo
scrivendo una riga, e `"vetrina": "mappa" | "prezzi" | "contatti"` decide cosa
far vedere mentre lo si legge.

### Scrivere alla piscina

Il bottone *Scrivici* apre **WhatsApp** sul numero della piscina, con il
messaggio già impostato. Non è una chat dentro l'app, ed è una scelta: una
chat propria vuole qualcuno che la guardi, e una chat che nessuno guarda è
peggio che non averla. WhatsApp lo staff ce l'ha già aperto sul telefono.

### Come saluta l'omino

`Buongiorno {nome}!` — il nome è quello lasciato con l'ultima prenotazione su
quel telefono, e resta lì (non passa mai dal server). Chi apre l'app per la
prima volta viene salutato senza nome: `{nome}` sparisce insieme allo spazio
che ha davanti. Se un domani servisse un vero account per i clienti, è l'unico
punto da cambiare.

## Struttura dei file

```
piscina/
  main.py              avvio, monta API e PWA
  core/                configurazione, password, email, limiti ai tentativi
  db/                  sessione, tabelle, allineamento delle postazioni
  models/              postazioni, prenotazioni, occupazioni, operatori
  dominio/             piantina, listino, fasce, dati della struttura
  crud/                le regole delle prenotazioni (niente HTTP qui dentro)
  api/routers/         pubblico, prenotazioni, staff
  risorse/             gli originali dei disegni (icona, omino)
  scripts/             operatori, dati di esempio, icone, omino, texture
  tests/               33 prove
  web/                 la PWA (HTML, CSS e JavaScript, senza framework)
```
