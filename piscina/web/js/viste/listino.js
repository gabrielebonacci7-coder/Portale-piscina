// La pagina Prezzi: il cartello affisso in piscina, leggibile sul telefono.

import { el, euro } from "../ui.js";

function tabella(intestazioni, righe) {
  return el("div", { classe: "scorri-x" }, [
    el("table", { classe: "tabella" }, [
      el("thead", {}, [
        el("tr", {}, intestazioni.map((t, i) =>
          el("th", { classe: i === 0 ? "" : "cifra", testo: t })
        )),
      ]),
      el("tbody", {}, righe.map((celle) =>
        el("tr", {}, celle.map((c, i) =>
          el("td", { classe: i === 0 ? "" : "cifra", testo: c })
        ))
      )),
    ]),
  ]);
}

export function vistaListino(ctx) {
  const l = ctx.listino;

  return el("div", {}, [
    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [
        el("h2", { testo: "Ingressi" }),
        el("span", { classe: "occhiello", testo: l.stagione }),
      ]),
      tabella(
        ["Tipologia", "Residenti / soci", "Non residenti"],
        l.ingressi.map((r) => [r.tipo, euro(r.residenti), euro(r.non_residenti)])
      ),
      el("p", { classe: "piccolo tenue", style: "margin-top:12px", testo:
        "Giornata ridotta: 9:00–14:00 oppure 14:00–19:00." }),
    ]),

    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "Noleggio attrezzature" })]),
      tabella(
        ["Attrezzatura", "Intera", "Abb. settimanale", "Abb. mensile"],
        l.noleggio.map((r) => [
          r.tipo,
          `${euro(r.intera)}/g`,
          euro(r.abbonato_settimanale),
          euro(r.abbonato_mensile),
        ])
      ),
      el("p", { classe: "piccolo tenue", style: "margin-top:12px", testo:
        "Le tariffe scontate valgono per chi ha un abbonamento in corso." }),
    ]),

    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "Abbonamenti" })]),
      tabella(
        ["Tipologia", "Residenti / soci", "Non residenti"],
        l.abbonamenti.map((r) => [
          `${r.tipo} — ${r.validita}`,
          euro(r.residenti),
          euro(r.non_residenti),
        ])
      ),
      el("ul", { classe: "piccolo tenue", style: "margin:12px 0 0;padding-left:20px" },
        l.abbonamenti.map((r) => el("li", { testo: `${r.tipo}: ${r.vantaggio}` }))
      ),
    ]),

    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "Da sapere" })]),
      el("ul", { classe: "piccolo", style: "margin:0;padding-left:20px" },
        l.note.map((n) => el("li", { testo: n }))
      ),
    ]),
  ]);
}
