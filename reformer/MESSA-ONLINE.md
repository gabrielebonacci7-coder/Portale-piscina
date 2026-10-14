# Mettere RE FORMER online — la guida passo passo

Questa guida parte da zero: niente server, niente dominio, niente casella
email. Alla fine l'app è su `https://iltuodominio.it`, Greta ed Elisa hanno
il gestionale e le clienti possono iscriversi.

**Tempo:** circa un'ora la prima volta, più l'attesa del dominio (da pochi
minuti a qualche ora).

**Costi:**

| Cosa | Dove | Quanto |
|---|---|---|
| Dominio (es. `reformerpilates.it`) | Aruba | ~10-15 € l'anno |
| Server (VPS) | Hetzner, modello CX22 | ~5 € al mese |
| Casella email per spedire | Gmail | gratis |

> **Il server Hetzner di Guardlink.** Se Hetzner te l'ha chiuso perché non
> era pagato, non si recupera: se ne crea uno nuovo (punto 2). Se invece è
> ancora acceso, vedi in fondo "Guardlink e RE FORMER sullo stesso server".

---

## 1. La casella Gmail dello studio (15 minuti)

Le email (conferma dell'iscrizione, password dimenticata, promemoria)
partono da qui. Meglio una casella dello studio che la tua personale: le
clienti vedono quell'indirizzo, e Greta ed Elisa possono averne l'accesso.

1. Crea un account Gmail nuovo, per esempio `reformerstudio@gmail.com`.
   Come numero di telefono metti quello di Greta (o di Elisa): servirà per i
   codici di sicurezza.
2. Vai su **myaccount.google.com → Sicurezza** e attiva la **Verifica in due
   passaggi**. Senza, il punto 3 non compare.
3. Vai su **myaccount.google.com/apppasswords**. Come nome scrivi `RE FORMER`
   e premi **Crea**. Google mostra **16 lettere**: copiale subito (senza
   spazi), non le rivedrai più. Questa è la "password per le app": va nel
   file `.env` al punto 4, **non** la password normale di Gmail.
4. Per dare l'accesso a Greta ed Elisa: basta che accedano a Gmail con
   email e password della casella. Il codice di sicurezza arriva sul
   telefono che hai messo al passo 1.

Limite di Gmail: circa 500 email al giorno. Per uno studio è dieci volte
quello che serve.

## 2. Il server su Hetzner (10 minuti)

1. Entra su **console.hetzner.cloud** (o crea un account) e controlla in
   *Billing* che il metodo di pagamento sia attivo.
2. **Crea un progetto** `reformer`, poi **Add Server**:
   - Location: **Falkenstein** o **Norimberga** (Germania: i dati restano
     nell'Unione Europea, come dice l'informativa privacy);
   - Image: **Ubuntu 24.04**;
   - Type: **CX22** (2 CPU, 4 GB) — basta e avanza;
   - Networking: lascia IPv4 attivo;
   - SSH key: se non sai cos'è, salta: Hetzner ti manda la password di
     `root` per email.
3. Crea il server e **segnati l'indirizzo IPv4** (tipo `95.217.12.34`).

## 3. Il dominio su Aruba (10 minuti + attesa)

1. Su **aruba.it** compra il dominio (solo il dominio, **senza** hosting).
2. Nel pannello Aruba: **Gestione DNS** del dominio. Servono due record
   **A**, entrambi con l'IP del server:

   | Tipo | Nome | Valore |
   |---|---|---|
   | A | `@` (o vuoto) | l'IP del server |
   | A | `www` | l'IP del server |

   Se ci sono già altri record A per `@` o `www` (Aruba a volte mette i
   suoi), cancellali.
3. Aspetta che il dominio "punti" al server. Si controlla da qualsiasi
   computer con `ping iltuodominio.it`: quando risponde l'IP del server, è
   pronto. Può volerci da qualche minuto a qualche ora.

**Non accendere l'app (punto 4.5) prima che il dominio punti al server**:
Caddy chiede il certificato https al primo avvio, e Let's Encrypt lo dà solo
se il dominio porta davvero lì.

## 4. Installare l'app sul server (20 minuti)

### 4.1 Entrare nel server

Dal computer apri il Terminale (su Windows: **PowerShell**) e scrivi:

```bash
ssh root@95.217.12.34        # il tuo IP
```

La prima volta chiede di confermare (`yes`) e la password di root che ti ha
mandato Hetzner (al primo accesso ti fa sceglierne una nuova).

### 4.2 Installare Docker

```bash
curl -fsSL https://get.docker.com | sh
```

### 4.3 Scaricare il codice

```bash
git clone -b claude/zealous-shannon-c8xff8 https://github.com/gabrielebonacci7-coder/Portale-piscina.git reformer-app
cd reformer-app/reformer/deploy
```

(Se un giorno il codice viene unito al ramo principale, si toglie
`-b claude/zealous-shannon-c8xff8`.)

### 4.4 La configurazione

```bash
cp .env.esempio .env
python3 -c "import secrets; print(secrets.token_hex(32))"     # copia il risultato
nano .env
```

Nel file compila:

- `DOMINIO` e `REFORMER_URL_PUBBLICO` con il tuo dominio;
- `REFORMER_SECRET_KEY` con la stringa appena generata;
- `REFORMER_EMAIL_SMTP_UTENTE` e `REFORMER_EMAIL_MITTENTE` con la casella
  Gmail del punto 1;
- `REFORMER_EMAIL_SMTP_PASSWORD` con le 16 lettere della password per le app.

Le email di Greta ed Elisa sono già scritte. Salva con **Ctrl+O**, **Invio**,
poi esci con **Ctrl+X**.

**Copia `REFORMER_SECRET_KEY` e la password Gmail in un posto sicuro**
(un gestore di password): il file `.env` esiste solo sul server.

### 4.5 Accendere

```bash
docker compose up -d --build
docker compose logs -f app        # Ctrl+C per uscire dai log
```

Se nei log c'è `Configurazione non pronta per andare online`, la riga sotto
dice cosa manca nel `.env`. Correggi e rilancia `docker compose up -d`.

### 4.6 Le email partono?

```bash
docker compose exec app python -m reformer.scripts.prova_email tua@email.it
```

Risponde in italiano: "Partita!" oppure cosa c'è che non va.

### 4.7 Prova

Apri `https://iltuodominio.it` dal telefono: deve comparire la schermata di
accesso di RE FORMER, con il lucchetto dell'https.

## 5. Greta ed Elisa nel gestionale (5 minuti)

1. Greta apre l'app e **si registra con `greta.lorenzetti@icloud.com`**.
2. Le arriva una mail "Conferma il tuo indirizzo": apre il link.
3. L'app la porta direttamente nel **Gestionale**. Fatto.
4. Elisa fa lo stesso con `elisabonacci@yahoo.it`.

Se la mail non arriva (spam? Gmail non ancora configurato?), dal server:

```bash
docker compose exec app python -m reformer.scripts.crea_staff greta.lorenzetti@icloud.com
docker compose exec app python -m reformer.scripts.crea_staff elisabonacci@yahoo.it
docker compose exec app python -m reformer.scripts.crea_staff --elenco     # controllo
```

## 6. Il backup di ogni notte (5 minuti)

Sul server, una volta sola:

```bash
crontab -e
```

(se chiede l'editor, scegli `nano`) e in fondo aggiungi questa riga:

```
30 3 * * * cd /root/reformer-app/reformer/deploy && docker compose exec -T app python -m reformer.scripts.backup --dove /dati/backup >> /root/backup-reformer.log 2>&1
```

Ogni notte alle 3:30 si salva una copia del database; ne restano le ultime
30. Per tenerne una anche **fuori** dal server (se il server si rompe, i
backup dentro al server si rompono con lui), una volta al mese dal tuo
computer:

```bash
scp root@95.217.12.34:/var/lib/docker/volumes/reformer_dati/_data/backup/*.db ./
```

Su Hetzner si può anche attivare **Backups** nelle impostazioni del server
(+20% del prezzo, ~1 €/mese): fa una copia di tutto il server ogni giorno.
Consigliato.

## 7. Aggiornare l'app dopo una modifica

```bash
cd /root/reformer-app && git pull
cd reformer/deploy && docker compose up -d --build
```

I dati non si toccano: stanno nel volume, fuori dall'immagine.

**Se si cambia qualcosa in `reformer/web/`, va alzata `VERSIONE` in
`reformer/web/sw.js`** (`reformer-v1` → `reformer-v2`): altrimenti i telefoni
che hanno l'app installata continuano a usare la copia vecchia. Con la
versione nuova, alle clienti compare "C'è una versione nuova — Aggiorna".

---

## Trappole — leggile una volta

- **`docker compose down -v` cancella tutto il database.** Il `-v` elimina i
  volumi. `docker compose down` da solo è sicuro.
- **Il file `.env` non è su GitHub e non deve andarci.** Contiene la chiave
  segreta e la password delle email.
- **Il repository GitHub è pubblico**: password e chiavi solo nel `.env`.
- **Cambiare `REFORMER_SECRET_KEY` fa uscire tutte** le clienti dall'app
  (dovranno rientrare con email e password). Non è grave, ma non farlo per
  sbaglio.
- **Rinnovo del dominio**: Aruba lo chiede ogni anno. Se scade, l'app
  sparisce. Attiva il rinnovo automatico.
- **Hetzner si paga ogni mese**: se il pagamento non passa, dopo qualche
  avviso il server viene spento e poi cancellato, **con i dati**. Tieni la
  carta aggiornata e i backup fuori dal server.

## Comandi utili

```bash
cd /root/reformer-app/reformer/deploy

docker compose ps                         # è tutto acceso?
docker compose logs --tail 100 app        # gli ultimi messaggi dell'app
docker compose restart app                # riavvia l'app
docker compose exec app python -m reformer.scripts.backup --dove /dati/backup   # backup subito
docker compose exec app python -m reformer.scripts.crea_staff --elenco          # chi è staff
docker compose exec app python -m reformer.scripts.prova_email tua@email.it     # le email vanno?
```

## Guardlink e RE FORMER sullo stesso server

Si può, e si risparmiano 5 € al mese, ma con un'attenzione: tutti e due i
progetti portano un loro **Caddy**, e due Caddy non possono stare sulla
stessa porta 80/443. Su un server condiviso ne serve uno solo, che risponda
a entrambi i domini. Non è difficile ma va fatto con calma: è un lavoro da
fare insieme a Claude, in una sessione apposta, partendo da questa frase.

Finché i server sono separati, ognuno con il suo dominio, non c'è niente da
fare.

---

## Il messaggio per le clienti

Quando l'app è online, un messaggio WhatsApp (o una storia) come questo:

> Ciao! Da oggi le lezioni di reformer si prenotano dall'app RE FORMER 🤍
>
> 👉 https://iltuodominio.it
>
> Ti registri una volta con nome, telefono ed email, e poi prenoti in due
> tocchi. Vedi i posti liberi, puoi metterti in lista d'attesa se una lezione
> è piena, e disdire fino a 12 ore prima.
>
> Per averla come un'app: su iPhone apri il link con Safari → Condividi →
> "Aggiungi alla schermata Home". Su Android: Chrome → tre puntini → "Installa
> app".
>
> Greta ed Elisa

Prima di mandarlo: Greta ed Elisa caricano dal gestionale le lezioni che
restano a ogni cliente man mano che si iscrivono (Clienti → nome → Lezioni
rimaste).
