// "La mia prenotazione": si ritrova con il codice e il numero di telefono.
// Il numero fa da chiave: senza, chi tira a indovinare un codice leggerebbe
// nome ed email di uno sconosciuto.

import * as api from "../api.js";
import { avviso, brindisi, el, giornoEsteso, svuota } from "../ui.js";
import { nomePacchetto } from "../prezzi.js";

export function vistaPrenotazione(ctx) {
  const radice = el("div");
  const esito = el("div");

  const codice = el("input", {
    name: "codice", placeholder: "PC-XXXXX", autocapitalize: "characters", required: true,
  });
  const telefono = el("input", {
    name: "telefono", type: "tel", autocomplete: "tel", required: true,
  });

  const modulo = el("form", {
    onsubmit: async (e) => {
      e.preventDefault();
      svuota(esito).append(el("div", { classe: "caricamento", testo: "Cerco…" }));
      try {
        mostra(await api.ritrova(codice.value.trim(), telefono.value.trim()));
      } catch (guaio) {
        svuota(esito).append(avviso("guaio", guaio.dettaglio));
      }
    },
  }, [
    el("label", { classe: "campo" }, [el("span", { testo: "Codice prenotazione" }), codice]),
    el("label", { classe: "campo" }, [el("span", { testo: "Il tuo numero di telefono" }), telefono]),
    el("button", { classe: "bottone largo", type: "submit", testo: "Cerca" }),
  ]);

  function mostra(p) {
    const annullabile = p.stato !== "annullata";
    svuota(esito).append(
      el("div", { classe: "scheda" }, [
        el("div", { classe: "titolo-sezione" }, [
          el("h2", { testo: p.codice }),
          el("span", { classe: `bollo ${p.stato}`, testo: p.stato.replace("_", " ") }),
        ]),
        el("div", { classe: "riga-conto" }, [
          el("span", { testo: "Giorno" }),
          el("span", { testo: `${giornoEsteso(p.giorno)} · ${p.orario}` }),
        ]),
        el("div", { classe: "riga-conto" }, [
          el("span", { testo: "Intestata a" }),
          el("span", { testo: p.nome }),
        ]),
        el("div", { classe: "riga-conto" }, [
          el("span", { testo: "Persone" }),
          el("span", { testo: String(p.persone) }),
        ]),
        ...p.righe.map((r) =>
          el("div", { classe: "riga-conto" }, [
            el("span", { testo: `${r.codice} · ${nomePacchetto(r.tipo, r.lettini)}` }),
            el("span", { testo: r.prezzo }),
          ])
        ),
        el("div", { classe: "riga-conto totale" }, [
          el("span", { testo: "Totale noleggio" }),
          el("span", { testo: p.totale }),
        ]),
        annullabile
          ? el("button", {
              classe: "bottone secondario largo",
              type: "button",
              style: "margin-top:16px",
              testo: "Annulla la prenotazione",
              onclick: async (e) => {
                if (!confirm(`Annullare la prenotazione ${p.codice}? I posti tornano liberi.`)) return;
                e.target.disabled = true;
                try {
                  mostra(await api.annullaPrenotazione(p.codice, telefono.value.trim()));
                  brindisi("Prenotazione annullata", "buono");
                } catch (guaio) {
                  esito.prepend(avviso("guaio", guaio.dettaglio));
                }
              },
            })
          : avviso("info", "Questa prenotazione è annullata: i posti sono tornati liberi."),
      ])
    );
  }

  radice.append(
    el("div", { classe: "scheda" }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "La mia prenotazione" })]),
      el("p", { classe: "piccolo tenue", testo:
        "Il codice te lo abbiamo scritto via email quando hai prenotato." }),
      modulo,
    ]),
    esito
  );
  return radice;
}
