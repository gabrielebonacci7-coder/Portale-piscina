# Skill del progetto

Qui dentro stanno le skill che valgono per questo repository: Claude le trova
da solo all'avvio di ogni sessione, senza doverle reinstallare.

**Perché nel repository e non nella cartella personale**: le sessioni di Claude
sul web girano dentro un contenitore che viene buttato via alla fine. Quello
che sta in `~/.claude/` sparisce con lui; quello che sta qui è versionato e
c'è ancora la volta dopo.

## ui-ux-pro-max (v2.13.0)

Banca dati consultabile di regole di interfaccia: stili, palette, abbinamenti
di caratteri, linee guida di accessibilità e usabilità, grafici, icone e
convenzioni per una ventina di tecnologie.

- Origine: <https://github.com/nextlevelbuilder/ui-ux-pro-max-skill> (licenza MIT)
- Copiata da `.claude/skills/ui-ux-pro-max/` di quel repository, senza modifiche
- Funziona **tutta in locale**: gli script leggono i CSV qui accanto e non
  chiamano nessun servizio esterno

Si interroga così:

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "dashboard" --domain style
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "blu" --domain color --json
```

Per aggiornarla si ricopia la cartella dalla versione nuova del repository di
origine. Lì dentro ci sono anche altre sei skill dello stesso pacchetto
(`design`, `ui-styling`, `brand`, `design-system`, `slides`, `banner-design`):
non sono state prese perché pesano insieme una decina di megabyte, ma si
aggiungono allo stesso modo se servono.

## Le dodici skill di Emil Kowalski

Regole di animazione e di rifinitura dell'interfaccia, scritte da chi ha fatto
Sonner e Vaul e ha lavorato in Vercel e Linear. Sono **solo testo**: nessuno
script, nessun dato, nessuna chiamata a niente.

- Origine: <https://github.com/emilkowalski/skills> (licenza MIT)
- Copiate da `skills/` di quel repository, senza modifiche

| Skill | A cosa serve |
|---|---|
| `animate` | costruire un'animazione dall'inizio, decidendo nell'ordine giusto |
| `review-animations` | rivedere un'animazione già scritta con l'asticella alta |
| `improve-animations` | passare al setaccio le animazioni di tutto il progetto |
| `find-animation-opportunities` | trovare i punti che dovrebbero muoversi e non si muovono |
| `animation-vocabulary` | dare il nome giusto a un effetto descritto a parole |
| `apple-design` | il modo di fare di Apple, tradotto per il web |
| `emil-design-eng` | i dettagli invisibili che fanno sembrare curata un'interfaccia |
| `prototype` | fare più versioni di un pezzo di interfaccia e sceglierne una |
| `pick-ui-library` | scegliere la libreria giusta per un problema di interfaccia |
| `animate-expo`, `write-swift`, `ask-sonner` | React Native, Swift e Sonner |

Le ultime tre non riguardano questo progetto — qui non c'è né React Native né
Swift né Sonner — e si possono cancellare senza rompere niente. Restano perché
il pacchetto è quello e pesa in tutto 336 kB.
