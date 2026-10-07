# Pilates G&E

App per prenotare le lezioni di **reformer** con Greta Lorenzetti ed Elisa
Bonacci. Stessa idea della PWA della piscina di Ciampino: si installa sul
telefono, e due avatar (Greta ed Elisa) accolgono la cliente e le spiegano
come si usa.

**Stato: prototipo da approvare.** Tutto gira nel telefono con dati finti
(localStorage): serve a far vedere aspetto e funzionamento prima di costruire
l'app vera con server e database. Le regole però sono già quelle definitive.

Sta in questo repository solo per ora: quando l'aspetto è approvato passa in
un repository suo.

## Provarlo

```bash
cd pilates && python3 -m http.server 8000
```

Poi si apre **http://127.0.0.1:8000/prototipo/**. In cima c'è la barra
*Prototipo* per passare al volo da cliente a Greta o a Elisa, e ↺ rimette
tutto com'era.

Parametri utili nell'indirizzo:

| Parametro | A cosa serve |
|---|---|
| `?ora=2026-10-12T09:00` | ferma l'orologio a quell'ora (lo usa il video) |
| `?video=1` | nasconde la barra *Prototipo* |
| `?benvenuto` | riapre la guida di Greta ed Elisa |

`artifact.html` è la stessa app senza l'intestazione della pagina: è il file
che si pubblica come pagina da aprire sul telefono. Lì le finestre del
browser (conferma, richiesta di testo) non si vedono, perciò l'app chiede
conferma con i suoi fogli e tiene la pagina corrente da sé, senza dipendere
dall'indirizzo.

## Le regole

| | |
|---|---|
| Lun–Ven | 16:30 · 17:30 · 18:30, lezioni da un'ora |
| Sabato | 11:30 · 12:30 |
| Istruttrice | Greta lunedì, mercoledì, venerdì, sabato · Elisa martedì e giovedì |
| Posti | 3 per lezione (i 3 reformer) |
| Quanto prima | si prenota fino a un mese avanti (`GIORNI_PRENOTABILI`) |
| Disdetta | fino a 12 ore prima, l'ingresso torna nel pacchetto |
| Lista d'attesa | se una disdice, entra in automatico la prima in lista e riceve una notifica |
| Pagamento | solo in studio: Greta o Elisa caricano il pacchetto dal gestionale |
| Titolo lezione | lo scelgono Greta ed Elisa (di base "Reformer") |
| Clienti | si registrano da sole |

Tutte stanno in cima a [`prototipo/js/dati.js`](prototipo/js/dati.js).

## Cosa c'è

**Cliente** — calendario fino a un mese avanti, a giorni (*Settimana*) o a
griglia (*Mese*), con i pallini dei posti liberi, prenotazione
con conferma e promemoria, lista d'attesa, le mie lezioni con la disdetta,
il pacchetto (lezioni rimaste, scadenza, listino), contatti con *Scrivi a
Greta / Elisa* su WhatsApp, notifiche e avvisi dello studio.

**Gestionale (Greta ed Elisa)** — *Oggi* con il registro delle presenze e le
nuove iscritte, *Settimana* con titolo modificabile, aggiunta a mano di chi
prenota per telefono, annullamento con avviso alle iscritte, *Clienti* con
la scheda e la registrazione dei pagamenti, *Avvisi* a tutte, *Numeri*
(riempimento, orari più richiesti, pacchetti venduti).

## Da completare

- **Avatar** di Greta ed Elisa: le immagini vanno in `prototipo/immagini/` e
  il percorso in `RITRATTI`, in cima a [`prototipo/js/avatar.js`](prototipo/js/avatar.js).
  Finché mancano c'è una sagoma disegnata.
- **Prezzi**: nel listino `PACCHETTI` di `dati.js`.

## Il video

```bash
pip install playwright                 # una volta sola
python pilates/video/gira.py           # circa 90 secondi
python pilates/video/gira.py --veloce  # pause dimezzate, per provare
```

Guida il prototipo dentro un telefono e lo riprende, come per Ciampino: se
cambia qualcosa nell'app basta rilanciarlo. Esce in `pilates/video/uscita/`
(video.mp4 verticale 1080×1920, copertina.jpg, copione.txt con il minutaggio
delle didascalie). Senza voce: parlano i fumetti di Greta ed Elisa.

## File

```
pilates/
├── risorse/logo-originale.webp   il logo com'è arrivato
├── prototipo/
│   ├── index.html, manifest.webmanifest
│   ├── css/stile.css             colori e caratteri dal logo
│   ├── font/                     Fraunces (titoli) e DM Sans (testo), in locale
│   ├── icone/, immagini/         icone dell'app e marchio scontornato
│   └── js/
│       ├── dati.js               regole e "finto server"
│       ├── avatar.js             Greta ed Elisa e la guida di benvenuto
│       ├── app.js                accesso, cornice, smistamento
│       └── viste/cliente.js, viste/studio.js
└── video/
    ├── palco.html                il telefono con le didascalie
    └── gira.py                   il regista
```
