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
