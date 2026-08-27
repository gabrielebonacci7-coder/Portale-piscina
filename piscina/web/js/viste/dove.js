// Come raggiungerci: dove siamo, quando siamo aperti, come si arriva.

import { el } from "../ui.js";
import { DISEGNO_OMINO } from "../omino.js";

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
        el("span", { testo: i.indirizzo }),
      ]),
      el("div", { classe: "riga-conto" }, [
        el("span", { testo: "Orari" }),
        el("span", { testo: i.orari }),
      ]),
      el("div", { classe: "riga-conto" }, [
        el("span", { testo: "Telefono" }),
        el("a", { href: `tel:${i.telefono_compatto}`, testo: i.telefono }),
      ]),
      // La mappa vera, dentro la pagina. Si cerca per nome invece che per
      // coordinate: finché l'indirizzo esatto non è confermato, è la
      // ricerca a portare al posto giusto.
      el("iframe", {
        classe: "mappa-incorporata",
        src: `https://www.google.com/maps?q=${ricerca}&output=embed`,
        loading: "lazy",
        referrerpolicy: "no-referrer-when-downgrade",
        title: `Mappa di ${i.nome}`,
      }),
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
      el("div", { style: "flex:0 0 88px", html: DISEGNO_OMINO }),
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
