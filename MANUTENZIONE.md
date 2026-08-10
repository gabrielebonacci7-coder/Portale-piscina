# Guardlink — cosa ricordarsi

Promemoria di gestione per chi tiene in piedi guardlink.it.
Il server è un VPS Hetzner, l'app gira in due contenitori Docker in
`/root/guardlink`.

Per entrare nel server, da un'app SSH:

```bash
ssh root@49.13.154.205
cd /root/guardlink
```

Tutti i comandi qui sotto si danno da lì dentro.

---

## Le due cose che non devi dimenticare mai

Queste due non sono manutenzione, sono sopravvivenza. Se saltano, il sito
sparisce e non è colpa di un bug.

### 1. Il rinnovo del dominio (Aruba, una volta l'anno)

Se `guardlink.it` scade, il sito diventa irraggiungibile **anche se il server
funziona benissimo**. E dopo qualche settimana il nome torna libero e può
comprarselo chiunque.

→ Vai su Aruba e **attiva il rinnovo automatico**. Poi controlla che la carta
salvata sia valida. Costa 10-15 € l'anno.

### 2. Il pagamento del server (Hetzner, ogni mese)

Se la carta scade o il pagamento fallisce, Hetzner prima sospende il server e
poi **lo cancella con tutto quello che c'è dentro**.

→ Controlla che la carta su Hetzner sia valida e non in scadenza. Circa 15 €
al mese.

---

## Da fare regolarmente

### Una volta sola, appena puoi (la cosa più utile della lista)

**Attiva i backup di Hetzner.** Console Hetzner → il tuo server → scheda
*Backups* → abilita. Costa il 20% del server (~2,80 €/mese) e fa istantanee
automatiche dell'intero server, da cui si ripristina con due clic dal browser.

È l'unica cosa che ti protegge davvero se il disco si rompe, e non richiede
nessun comando né di ricordarsi niente.

### Ogni mese — aggiornamenti di sicurezza del server

```bash
apt update && apt upgrade -y
```

Se alla fine dice che serve riavviare:

```bash
reboot
```

L'app riparte da sola (i contenitori hanno `restart: unless-stopped`). Il sito
resta giù una trentina di secondi.

### Ogni mese — controlla che i backup esistano davvero

Un backup che nessuno ha mai guardato non è un backup, è una speranza.

```bash
ls -lh /var/lib/docker/volumes/guardlink_dati/_data/backup/
```

Devi vedere delle cartelle con la data (`2026-08-10_0300`). Se sono vecchie o
non ci sono, il cron non sta girando: verifica con `crontab -l`.

### Ogni mese — spazio sul disco

```bash
df -h /
```

Se `Use%` supera l'80%, libera spazio:

```bash
docker system prune -a          # immagini vecchie delle build precedenti
```

Il database e le foto **non** vengono toccati da questo comando: stanno in un
volume.

### Ogni tanto — porta una copia fuori dal server

Solo se **non** hai attivato i backup Hetzner. Da un computer vero (non da
iPad), scarica le copie sul tuo disco:

```bash
scp -r root@49.13.154.205:/var/lib/docker/volumes/guardlink_dati/_data/backup ./backup-guardlink
```

---

## Come si ripristina un backup

Questa è la parte che rende utili tutte le altre. Vale la pena leggerla
adesso, con calma, invece che il giorno in cui serve.

**Se hai i backup Hetzner:** console Hetzner → server → *Backups* → scegli la
data → *Rollback*. Finito, non serve altro.

**Se devi ripristinare solo il database dal backup del cron:**

```bash
cd /root/guardlink
docker compose down

VOL=/var/lib/docker/volumes/guardlink_dati/_data
ls $VOL/backup/                                  # scegli la data che vuoi

cp $VOL/backup/2026-08-10_0300/guardlink.db $VOL/guardlink.db
rm -f $VOL/guardlink.db-wal $VOL/guardlink.db-shm
chown 1000:1000 $VOL/guardlink.db

docker compose up -d
```

Le due righe in mezzo non sono decorative:

- `rm` dei file `-wal` e `-shm` toglie di mezzo il registro delle scritture del
  database *vecchio*. Se resta lì, SQLite prova ad applicarlo sopra a quello
  nuovo e i dati non tornano.
- `chown 1000:1000` rimette il proprietario giusto: dentro il contenitore l'app
  non gira come root, e su un file copiato da root non potrebbe scrivere.

**Per rimettere anche le foto:**

```bash
docker compose down
tar xzf $VOL/backup/2026-08-10_0300/media.tar.gz -C $VOL
chown -R 1000:1000 $VOL/media
docker compose up -d
```

---

## Comandi di tutti i giorni

```bash
cd /root/guardlink

docker compose logs -f app        # guarda cosa succede (Ctrl+C per uscire)
docker compose restart app        # riavvia solo l'app
docker compose ps                 # i contenitori sono su?

# Backup a mano, subito
docker compose exec app python -m scripts.backup --dove /dati/backup

# Chi ha il pannello Gestione
docker compose exec app python -m scripts.crea_staff --elenco

# Dare il ruolo staff a qualcuno (deve essersi già registrato dall'app)
docker compose exec app python -m scripts.crea_staff email@esempio.it

# Toglierlo
docker compose exec app python -m scripts.crea_staff email@esempio.it --togli

# Le email non arrivano? Questo ti dice perché, in italiano
docker compose exec app python -m scripts.prova_email tua@email.it
```

### Aggiornare l'app dopo una modifica al codice

```bash
cd /root/guardlink
git pull
docker compose up -d --build
```

I dati non si toccano: database e foto stanno su volumi, fuori dall'immagine.

---

## Trappole — leggile una volta

**`docker compose down -v` cancella tutti i dati.** Il `-v` elimina i volumi,
cioè database e foto. `docker compose down` da solo è sicuro e ferma soltanto i
contenitori. Non aggiungere mai `-v` a meno di volere davvero la distruzione di
tutto.

**Se modifichi qualcosa in `web/`, alza `VERSIONE` in `web/sw.js`.** Altrimenti
i telefoni che hanno l'app installata continuano a usare la copia che hanno in
memoria e non vedono la modifica. Basta cambiare il numero: `guardlink-v8` →
`guardlink-v9`.

**Il file `.env` non è su GitHub** — contiene la chiave segreta e la password
delle email. Esiste solo sul server. Se perdi il server perdi anche quello:
tieni una copia di `SECRET_KEY` e della password Gmail da qualche parte al
sicuro (un gestore di password, non un file sul desktop).

**Il repository su GitHub è pubblico.** Tutto quello che finisce nel codice lo
può leggere chiunque. Le password vanno solo in `.env`, mai nel codice.

**Il ruolo staff si dà solo da riga di comando.** Non esiste nessuna pagina che
promuova qualcuno: se ci fosse, basterebbe un account rubato per prendersi il
pannello.

**L'ultimo account staff non può togliersi il ruolo da solo.** Chiuderebbe il
pannello a tutti, e per riaprirlo servirebbe di nuovo l'accesso al server.

**Se cambi l'informativa privacy in modo sostanziale**, cambia anche
`VERSIONE_INFORMATIVA` in `app/core/privacy.py` e la data in cima a
`web/privacy.html`. La data salvata su ogni account deve corrispondere al testo
che quella persona ha davvero letto, altrimenti non dimostra più niente.

---

## Cose di cui NON devi occuparti

Elencate perché sapere cosa *non* fare vale quanto sapere cosa fare.

- **Il certificato https.** Caddy lo ottiene da solo e lo rinnova da solo, per
  sempre. Non c'è nessuna scadenza da segnare.
- **I log di Caddy.** Si ruotano da soli: 10 MB per file, 5 file, poi
  ricomincia. Non riempiono il disco.
- **Le copie di backup vecchie.** Lo script tiene le ultime 14 e cancella le
  altre da solo.
- **I bot che cercano `/.env`, `/wp-login.php`, `/.git/config` nei log.** Sono
  scansioni automatiche che passano su ogni indirizzo pubblico esistente.
  Rispondono tutte 404. È rumore di fondo, non un attacco.
- **Riavviare l'app ogni tanto "per sicurezza".** Non serve.

---

## Migliorie possibili, dalla più utile

### 1. Backup automatici di Hetzner — ~2,80 €/mese

Già detto sopra, ma sta in cima anche qui: è il miglior rapporto tra quello che
ti protegge e quello che ti costa fare.

### 2. Firewall — gratis, 5 minuti

Console Hetzner → *Firewalls* → creane uno che lascia entrare solo le porte
**22** (SSH), **80** e **443** (il sito), e applicalo al server. Tutto il resto
viene rifiutato prima ancora di arrivare all'app.

### 3. Accesso SSH con chiave invece che con password — gratis

Un IP pubblico riceve tentativi di indovinare la password di root in
continuazione, giorno e notte. Con una chiave SSH il problema smette di
esistere: si genera dall'app SSH dell'iPad (Termius lo fa dalle impostazioni),
si carica sul server, e poi si disattiva l'accesso con password.

### 4. Monitoraggio — gratis

Iscriviti a UptimeRobot (gratuito), digli di controllare `https://guardlink.it`
ogni 5 minuti. Se il sito cade ti manda un'email. Senza, lo scopri quando te lo
dice un bagnino.

### 5. Un indirizzo email tuo — ~1 €/mese

`info@guardlink.it` al posto di una Gmail personale: più serio verso le piscine,
e toglie dall'informativa il trasferimento dati verso gli Stati Uniti (le email
smetterebbero di passare da Google). Si compra da Aruba, dove hai il dominio.

### 6. Partita IVA — se inizia a generare ricavi

Finché è gratis e non ci guadagni, il codice fiscale nell'informativa va bene.
Se un domani fai pagare le piscine, cambia l'inquadramento e l'informativa va
aggiornata di conseguenza.

### 7. PostgreSQL al posto di SQLite — solo quando servirà

SQLite regge tranquillamente centinaia di utenti. Il giorno in cui non
bastasse, si travasa. Non è un problema di oggi e non vale la pena
anticiparlo.

---

## Numeri e indirizzi

| Cosa | Valore |
|---|---|
| Sito | https://guardlink.it |
| Server (IP) | 49.13.154.205 |
| Cartella sul server | `/root/guardlink` |
| Dominio | Aruba — scade ogni anno |
| Server | Hetzner CPX12 — ~15 €/mese |
| Codice | https://github.com/gabrielebonacci7-coder/Portale-piscina |
| Backup sul server | `/var/lib/docker/volumes/guardlink_dati/_data/backup` |
| Backup automatico | ogni notte alle 3 (`crontab -l` per vederlo) |
