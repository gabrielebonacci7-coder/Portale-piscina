// Le vetrine della guida: mentre l'omino parla di una sezione, questa la fa
// vedere davvero.
//
// Non sono figurine: la mappa è quella vera del giorno, i prezzi arrivano dal
// listino. Un'immagine finta invecchierebbe al primo cambio di listino, e
// nessuno se ne accorgerebbe fino a quando un cliente non arriva in cassa con
// la cifra sbagliata in testa.

import { el, euro } from "./ui.js";
import { adattaDentro, disegnaMappa } from "./mappa.js";
import * as api from "./api.js";

function guscio(titolo, contenuto, classe = "") {
  return el("div", { classe: `vetrina ${classe}` }, [
    el("div", { classe: "vetrina-titolo", testo: titolo }),
    contenuto,
  ]);
}

/** La mappa del solarium, in piccolo e senza tocchi: qui si guarda e basta. */
function vetrinaMappa(ctx) {
  const dentro = el("div", { classe: "vetrina-mappa-guscio" }, [
    el("div", { classe: "caricamento", testo: "…" }),
  ]);

  api
    .mappa()
    .then((dati) => {
      const vista = disegnaMappa(dentro, dati, {
        fascia: "giornata",
        scelte: new Set(),
        alTocco: () => {},
      });
      // Dopo il primo disegno: prima, la scatola non ha ancora una misura.
      requestAnimationFrame(() => adattaDentro(vista));
    })
    .catch(() => {
      dentro.replaceChildren(
        el("p", { classe: "tenue piccolo", testo: "La mappa si vede dalla sezione Prenota." })
      );
    });

  return guscio("La mappa del solarium", dentro, "vetrina-mappa");
}

/** Quattro righe di listino: quelle che la gente chiede in cassa. */
function vetrinaPrezzi(ctx) {
  const noleggio = ctx.listino.noleggio.filter((r) => r.lettini !== 1);
  const ingresso = ctx.listino.ingressi[0];

  const riga = (nome, prezzo, nota) =>
    el("div", { classe: "riga-conto" }, [
      el("span", {}, [nome, nota ? el("div", { classe: "piccolo tenue", testo: nota }) : null]),
      el("b", { testo: prezzo }),
    ]);

  return guscio(
    "Prezzi e pacchetti",
    el("div", {}, [
      ...noleggio.map((r) => riga(r.tipo.split(" — ")[0], `${euro(r.intera)}/g`, r.tipo.split(" — ")[1])),
      riga(ingresso.tipo, euro(ingresso.residenti), "residenti e soci"),
      el("p", { classe: "piccolo tenue", style: "margin:10px 0 0", testo:
        "Abbonati: sconto sul noleggio. Si paga tutto in cassa." }),
    ])
  );
}

/** Come si scrive alla piscina: il bottone è vero, la conversazione è finta. */
function vetrinaContatti(ctx) {
  const c = ctx.info.contatti || {};
  const link = c.whatsapp
    ? `https://wa.me/${c.whatsapp}?text=${encodeURIComponent(c.messaggio_precompilato || "")}`
    : `tel:${ctx.info.telefono_compatto}`;

  return guscio(
    "Scrivi alla piscina",
    el("div", {}, [
      el("div", { classe: "chat-finta" }, [
        el("div", { classe: "bolla loro", testo: "Buongiorno! Avete ancora posto sabato mattina?" }),
        el("div", { classe: "bolla noi", testo: "Buongiorno! Sì, guardi pure sulla mappa 🙂" }),
        el("div", { classe: "piccolo tenue", style: "text-align:center", testo: "esempio" }),
      ]),
      el("a", {
        classe: "bottone largo",
        href: link,
        target: "_blank",
        rel: "noopener",
        testo: c.whatsapp ? "Scrivici su WhatsApp" : "Chiamaci",
      }),
    ])
  );
}

const VETRINE = {
  mappa: vetrinaMappa,
  prezzi: vetrinaPrezzi,
  contatti: vetrinaContatti,
};

export function vetrina(nome, ctx) {
  const costruisci = VETRINE[nome];
  return costruisci ? costruisci(ctx) : null;
}
