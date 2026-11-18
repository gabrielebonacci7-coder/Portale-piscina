# Kit skill per Claude Code

Contenuto di `kit-skill-claude.zip`:

- `.claude/skills/`: le 24 skill.
  - Design: `impeccable`, `ui-ux-pro-max`, `web-design-guidelines`.
  - Animazioni, di Emil Kowalski: `animate`, `review-animations`, `improve-animations`, `find-animation-opportunities`, `animation-vocabulary`, `apple-design`, `emil-design-eng`, `prototype`, `pick-ui-library`, `ask-sonner`, `animate-expo`.
  - GSAP: `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-plugins`, `gsap-react`, `gsap-frameworks`, `gsap-utils`, `gsap-performance`.
  - Altro: `react-best-practices`, `write-swift`.
- `CLAUDE.md`: le regole che dicono a Claude di usarle (stili, GSAP, Lenis, React Bits).
- `design-references/`: i file di stile da proporre all'inizio di un sito.
- `skills-lock.json`: l'elenco delle skill con la loro provenienza.

## Come installarle in un altro progetto

1. Estrai lo zip nella cartella principale del repository dell'altro progetto. Le cartelle `.claude/` e `design-references/` devono stare nella stessa cartella dove c'è `.git`.
2. Se il progetto ha già un `CLAUDE.md`, non sovrascriverlo: copia in fondo il contenuto del nuovo.
3. Fai commit e push: `git add .claude CLAUDE.md design-references skills-lock.json`.
4. Apri una **nuova** sessione di Claude Code su quel repository e su quel branch. Le skill si caricano all'avvio della sessione, non a metà.

Per richiamarne una basta scriverla nel messaggio: "usa impeccable", oppure `/impeccable`.

## Cosa NON c'è nello zip (e perché)

- **Le skill già integrate in Claude Code**, come `artifact-design`, `code-review`, `simplify`, `pdf`, `docx`, `pptx` e `xlsx`. Ci sono già in ogni sessione e non vanno copiate.
- **I connettori** (Gmail, GitHub, Claude Docs, Artifacts). Sono collegati al tuo account claude.ai, non al progetto: si attivano dalle impostazioni dell'account e valgono per tutte le sessioni.
- **Le librerie GSAP, Lenis e React Bits.** Non sono skill: si aggiungono al sito quando servono, come spiega il `CLAUDE.md`.
- **"Taste".** Non era installata in questa sessione, quindi qui non c'è.
