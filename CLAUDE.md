# Note per Claude

## Quando si fa un sito o un'interfaccia

Per ogni sito, app o schermata nuova tieni in considerazione le skill in
`.claude/skills/` (se una non serve, dillo in una riga e vai avanti):

- `impeccable`: progettare, rifinire e controllare un'interfaccia.
- `ui-ux-pro-max`: stili, palette, abbinamenti di caratteri, accessibilità.
- Le skill di Emil Kowalski (`animate`, `review-animations`, `improve-animations`,
  `find-animation-opportunities`, `animation-vocabulary`, `apple-design`,
  `emil-design-eng`, `prototype`, `pick-ui-library`): animazioni e dettagli.
- `web-design-guidelines`: controllo di accessibilità e linee guida web.
- `react-best-practices`: solo se il sito usa React o Next.js.
- Le skill ufficiali di GSAP (`gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`,
  `gsap-plugins`, `gsap-react`, `gsap-frameworks`, `gsap-utils`,
  `gsap-performance`): quando un sito usa GSAP.

## Librerie da considerare (non sono skill: si aggiungono al sito quando servono)

- **GSAP** (github.com/greensock/GSAP): animazioni e animazioni legate allo
  scorrimento. Per siti vetrina e landing; non per gestionali o app come RE FORMER,
  dove bastano le transizioni CSS.
- **Lenis** (github.com/darkroomengineering/lenis): scorrimento morbido. Solo
  su siti vetrina; va spento con "riduci animazioni" e non va usato dove ci
  sono moduli, liste lunghe o scorrimenti interni.
- **React Bits** (github.com/DavidHDev/react-bits): componenti animati per
  React da copiare nel progetto. Solo se il sito è in React; prendere un
  componente alla volta, non l'intera raccolta.

Rispetta sempre `prefers-reduced-motion` e non appesantire la pagina: se
un'animazione non aiuta a capire o a usare il sito, si toglie.

`design-references/` raccoglie file di stile per marchio (editoriale, caldo,
vetro, cinematografico, ...). All'inizio di un sito proponi due o tre stili da
lì e chiedi quale preferisce, prima di disegnare.

Dopo aver costruito un sito, passalo con `web-design-guidelines`.
