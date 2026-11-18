// Come raggiungerci: dove siamo, quando siamo aperti, come si arriva.

import { el } from "../ui.js";
import { IMMAGINE_OMINO } from "../omino.js";

/** La mappa disegnata dei dintorni.

    È un'immagine e non un pezzo di pagina: il disegno si porta dentro il suo
    carattere, quindi si vede uguale anche aperto da solo o mandato a qualcuno. */
function mappaDintorni(info) {
  return el("img", {
    classe: "mappa-dintorni",
    src: "/immagini/dintorni.svg",
    alt: `Mappa dei dintorni: ${info.nome}, ${info.indirizzo}, ${info.riferimento}`,
    // Misure dichiarate: la scatola si prende il suo posto prima che il
    // disegno arrivi, così la pagina non salta. Niente caricamento pigro:
    // è l'illustrazione principale della pagina, e pesa trenta kilobyte.
    width: 820,
    height: 470,
  });
}

export function vistaDove(ctx) {
  const i = ctx.info;
  const ricerca = encodeURIComponent(i.ricerca_mappe);

  return el("div", {}, [
    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [
        el("h2", { testo: i.nome }),
        el("span", { classe: "occhiello", testo: i.stagione }),
      ]),
      el("p", { classe: "tenue piccolo", testo: `${i.gestore} · ${i.comune}` }),
      el("div", { classe: "riga-conto" }, [
        el("span", { testo: "Indirizzo" }),
        el("span", { style: "text-align:right" }, [
          i.indirizzo,
          i.riferimento ? el("div", { classe: "piccolo tenue", testo: i.riferimento }) : null,
        ]),
      ]),
      el("div", { classe: "riga-conto" }, [
        el("span", { testo: "Orari" }),
        el("span", { testo: i.orari }),
      ]),
      el("div", { classe: "riga-conto" }, [
        el("span", { testo: "Telefono" }),
        el("a", { href: `tel:${i.telefono_compatto}`, testo: i.telefono }),
      ]),
      // La mappa dei dintorni: un disegno, non una mappa interattiva. Serve a
      // capire in due secondi da che parte si entra e dove si lascia la
      // macchina; per le indicazioni stradali ci sono i pulsanti qui sotto.
      // Arriva come SVG e si infila nella pagina invece di stare dentro una
      // <img>: così usa gli stessi caratteri del resto dell'app.
      mappaDintorni(i),
      el("div", { style: "display:flex;gap:8px;flex-wrap:wrap;margin-top:16px" }, [
        el("a", {
          classe: "bottone",
          href: `https://www.google.com/maps/search/?api=1&query=${ricerca}`,
          target: "_blank",
          rel: "noopener",
          testo: "Apri in Google Maps",
        }),
        el("a", {
          classe: "bottone secondario",
          href: `https://maps.apple.com/?q=${ricerca}`,
          target: "_blank",
          rel: "noopener",
          testo: "Apri in Mappe",
        }),
        el("a", {
          classe: "bottone secondario",
          href: `tel:${i.telefono_compatto}`,
          testo: "Chiama",
        }),
      ]),
    ]),

    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "Scrivici" })]),
      el("p", { classe: "piccolo tenue", testo:
        "Per una domanda veloce, un gruppo grande o una postazione particolare: " +
        "ti rispondiamo dalla piscina." }),
      el("div", { style: "display:flex;gap:8px;flex-wrap:wrap" }, [
        i.contatti && i.contatti.whatsapp
          ? el("a", {
              classe: "bottone",
              href: `https://wa.me/${i.contatti.whatsapp}?text=${encodeURIComponent(
                i.contatti.messaggio_precompilato || ""
              )}`,
              target: "_blank",
              rel: "noopener",
              testo: "Scrivici su WhatsApp",
            })
          : null,
        el("a", { classe: "bottone secondario", href: `tel:${i.telefono_compatto}`, testo: "Chiama" }),
      ]),
    ]),

    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "Come arrivare" })]),
      ...i.come_arrivare.map((v) =>
        el("div", { style: "margin-bottom:12px" }, [
          el("h3", { testo: v.titolo }),
          el("p", { classe: "piccolo tenue", style: "margin:2px 0 0", testo: v.testo }),
        ])
      ),
    ]),

    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "La struttura" })]),
      el("div", { classe: "numeri" }, [
        el("div", { classe: "numero" }, [
          el("b", { testo: String(i.postazioni.ombrelloni) }),
          el("span", { testo: "ombrelloni" }),
        ]),
        el("div", { classe: "numero" }, [
          el("b", { testo: String(i.postazioni.lettini_solarium) }),
          el("span", { testo: "lettini solarium" }),
        ]),
        el("div", { classe: "numero" }, [
          el("b", { testo: "2" }),
          el("span", { testo: "vasche" }),
        ]),
      ]),
    ]),

    el("div", { classe: "scheda", style: "display:flex;gap:12px;align-items:center" }, [
      el("img", { classe: "omino-mini", src: IMMAGINE_OMINO, alt: "" }),
      el("div", {}, [
        el("h3", { testo: "Rivedi il benvenuto" }),
        el("p", { classe: "piccolo tenue", style: "margin:4px 0 8px", testo:
          "Le due parole di presentazione che vedi la prima volta." }),
        el("button", {
          classe: "bottone secondario piccolo",
          type: "button",
          testo: "Rivedi",
          onclick: () => ctx.mostraBenvenuto(),
        }),
      ]),
    ]),
  ]);
}
