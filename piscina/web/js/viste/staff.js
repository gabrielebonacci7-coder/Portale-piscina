// Il gestionale dello staff: chi arriva oggi, con che numero di telefono.
//
// È l'unica pagina che mostra dati personali. Non è raggiungibile dai tab in
// basso: ci si arriva scrivendo /staff, e senza password non si vede niente.

import * as api from "../api.js";
import { aIso, avviso, brindisi, el, foglio, giornoEsteso, plurale, svuota } from "../ui.js";

export function vistaStaff(ctx) {
  const radice = el("div");

  if (!api.haToken()) {
    disegnaAccesso();
  } else {
    disegnaGestionale();
  }

  function disegnaAccesso(messaggio) {
    const email = el("input", { type: "email", name: "email", autocomplete: "username", required: true });
    const password = el("input", {
      type: "password", name: "password", autocomplete: "current-password", required: true,
    });
    const esito = el("div");
    if (messaggio) esito.append(avviso("info", messaggio));

    svuota(radice).append(
      el("div", { classe: "scheda" }, [
        el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "Accesso staff" })]),
        el("p", { classe: "piccolo tenue", testo:
          "Riservato a chi lavora in piscina. Gli account li crea la direzione." }),
        esito,
        el("form", {
          onsubmit: async (e) => {
            e.preventDefault();
            svuota(esito);
            try {
              await api.accessoStaff(email.value.trim(), password.value);
              disegnaGestionale();
            } catch (guaio) {
              esito.append(avviso("guaio", guaio.dettaglio));
            }
          },
        }, [
          el("label", { classe: "campo" }, [el("span", { testo: "Email" }), email]),
          el("label", { classe: "campo" }, [el("span", { testo: "Password" }), password]),
          el("button", { classe: "bottone largo", type: "submit", testo: "Entra" }),
        ]),
      ])
    );
  }

  function disegnaGestionale() {
    const stato = { giorno: ctx.info.primo_giorno, cerca: "" };
    const zonaFiltri = el("div", { classe: "scheda" });
    const zonaDati = el("div");
    svuota(radice).append(zonaFiltri, zonaDati);

    const data = el("input", {
      type: "date",
      value: stato.giorno,
      onchange: (e) => {
        stato.giorno = e.target.value || stato.giorno;
        carica();
      },
    });
    const cerca = el("input", {
      type: "search",
      placeholder: "Nome, telefono, codice o postazione",
      oninput: (e) => {
        stato.cerca = e.target.value;
        clearTimeout(cerca._attesa);
        // Mezzo secondo di pausa: senza, si interroga il server a ogni tasto.
        cerca._attesa = setTimeout(carica, 400);
      },
    });

    const sposta = (giorni) => {
      const d = new Date(stato.giorno);
      d.setDate(d.getDate() + giorni);
      stato.giorno = aIso(d);
      data.value = stato.giorno;
      carica();
    };

    zonaFiltri.append(
      el("div", { style: "display:flex;gap:8px;align-items:end" }, [
        el("button", { classe: "bottone secondario", type: "button", testo: "‹", "aria-label": "Giorno prima", onclick: () => sposta(-1) }),
        el("label", { classe: "campo", style: "flex:1;margin:0" }, [el("span", { testo: "Giorno" }), data]),
        el("button", { classe: "bottone secondario", type: "button", testo: "›", "aria-label": "Giorno dopo", onclick: () => sposta(1) }),
      ]),
      el("label", { classe: "campo", style: "margin-top:12px;margin-bottom:0" }, [
        el("span", { testo: "Cerca" }), cerca,
      ]),
      el("div", { style: "display:flex;justify-content:flex-end;margin-top:12px" }, [
        el("button", {
          classe: "bottone piccolo fantasma",
          type: "button",
          testo: "Esci",
          onclick: () => {
            api.impostaToken(null);
            disegnaAccesso("Sei uscito dal gestionale.");
          },
        }),
      ])
    );

    async function carica() {
      svuota(zonaDati).append(el("div", { classe: "caricamento", testo: "Carico…" }));
      try {
        disegnaElenco(await api.prenotazioniStaff(stato.giorno, stato.cerca));
      } catch (guaio) {
        if (guaio.stato === 401) return disegnaAccesso("La sessione è scaduta.");
        svuota(zonaDati).append(avviso("guaio", guaio.dettaglio));
      }
    }

    function disegnaElenco(dati) {
      const r = dati.riepilogo;
      svuota(zonaDati).append(
        el("div", { classe: "scheda" }, [
          el("div", { classe: "titolo-sezione" }, [
            el("h2", { testo: giornoEsteso(dati.giorno) }),
            el("button", {
              classe: "bottone piccolo secondario",
              type: "button",
              testo: "Scarica CSV",
              onclick: () => api.scaricaCsv(dati.giorno).catch((g) => brindisi(g.dettaglio, "guaio")),
            }),
          ]),
          el("div", { classe: "numeri" }, [
            numero(r.prenotazioni, "prenotazioni"),
            numero(r.persone, "persone"),
            numero(r.ombrelloni, "ombrelloni"),
            numero(r.lettini, "lettini"),
            numero(r.incasso_previsto, "noleggio"),
          ]),
          r.annullate
            ? el("p", { classe: "piccolo tenue", style: "margin:12px 0 0", testo:
                `${r.annullate} annullate (restano in elenco).` })
            : null,
        ]),
        dati.prenotazioni.length
          ? el("div", { classe: "scheda" }, dati.prenotazioni.map(riga))
          : el("div", { classe: "scheda" }, [
              el("p", { classe: "tenue", style: "margin:0", testo: "Nessuna prenotazione per questo giorno." }),
            ]),
        pannelloPostazioni()
      );
    }

    const numero = (valore, etichetta) =>
      el("div", { classe: "numero" }, [
        el("b", { testo: String(valore) }),
        el("span", { testo: etichetta }),
      ]);

    function riga(p) {
      const azioni = el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;margin-top:6px" });

      const bottone = (testo, nuovoStato, classe = "secondario") =>
        el("button", {
          classe: `bottone piccolo ${classe}`,
          type: "button",
          testo,
          onclick: async (e) => {
            e.target.disabled = true;
            try {
              await api.cambiaStato(p.codice, nuovoStato);
              brindisi(`${p.codice}: ${testo.toLowerCase()}`, "buono");
              carica();
            } catch (guaio) {
              brindisi(guaio.dettaglio, "guaio");
              e.target.disabled = false;
            }
          },
        });

      if (p.stato !== "arrivato") azioni.append(bottone("Segna arrivato", "arrivato", ""));
      if (p.stato === "arrivato") azioni.append(bottone("Rimetti in attesa", "in_attesa"));
      if (p.stato !== "annullata") azioni.append(bottone("Annulla", "annullata"));

      return el("div", { classe: "prenotazione-riga" }, [
        el("div", {}, [
          el("div", { style: "display:flex;align-items:center;gap:8px;flex-wrap:wrap" }, [
            el("span", { classe: `bollo ${p.stato}`, testo: p.stato.replace("_", " ") }),
            el("b", { testo: p.nome }),
            el("span", { classe: "tenue piccolo", testo: `${p.persone} pers.` }),
          ]),
          el("div", { classe: "piccolo contatti" }, [
            el("a", { href: `tel:${p.telefono.replace(/\s/g, "")}`, testo: p.telefono }),
            " · ",
            el("a", { href: `mailto:${p.email}`, testo: p.email }),
          ]),
          el("div", { classe: "piccolo tenue dati", testo:
            `${p.codice} · ${p.fascia_etichetta} ${p.orario} · ${p.postazioni.join(" ")}` +
            (p.lettini ? ` · ${plurale(p.lettini, "lettino", "lettini")}` : "") }),
          p.note ? el("div", { classe: "piccolo", testo: `Note: ${p.note}` }) : null,
          azioni,
        ]),
        el("b", { testo: p.totale }),
      ]);
    }

    function pannelloPostazioni() {
      const contenuto = el("div");
      const scheda = el("div", { classe: "scheda" }, [
        el("div", { classe: "titolo-sezione" }, [
          el("h2", { testo: "Postazioni fuori uso" }),
          el("button", {
            classe: "bottone piccolo secondario",
            type: "button",
            testo: "Gestisci",
            onclick: apri,
          }),
        ]),
        contenuto,
      ]);

      async function aggiorna() {
        const postazioni = await api.postazioniStaff();
        const spente = postazioni.filter((p) => !p.attiva);
        svuota(contenuto).append(
          spente.length
            ? el("div", { classe: "scelte" },
                spente.map((p) =>
                  el("span", { classe: "gettone" }, [
                    `${p.codice}${p.nota ? ` · ${p.nota}` : ""}`,
                    el("button", {
                      type: "button",
                      testo: "×",
                      "aria-label": `Riattiva ${p.codice}`,
                      onclick: async () => {
                        await api.modificaPostazione(p.codice, { attiva: true, nota: "" });
                        brindisi(`${p.codice} di nuovo prenotabile`, "buono");
                        aggiorna();
                      },
                    }),
                  ])
                )
              )
            : el("p", { classe: "tenue piccolo", style: "margin:0", testo:
                "Tutte le postazioni sono prenotabili." })
        );
        return postazioni;
      }

      function apri() {
        const codice = el("input", { placeholder: "Es. B7", autocapitalize: "characters" });
        const nota = el("input", { placeholder: "Motivo (ombrellone rotto…)" });
        const esito = el("div");
        const { chiudi } = foglio(
          el("form", {
            onsubmit: async (e) => {
              e.preventDefault();
              svuota(esito);
              try {
                await api.modificaPostazione(codice.value.trim().toUpperCase(), {
                  attiva: false,
                  nota: nota.value.trim(),
                });
                chiudi();
                brindisi("Postazione spenta", "buono");
                aggiorna();
              } catch (guaio) {
                esito.append(avviso("guaio", guaio.dettaglio));
              }
            },
          }, [
            el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "Spegni una postazione" })]),
            el("p", { classe: "piccolo tenue", testo:
              "Sparisce dalla mappa e non si può più prenotare. Le prenotazioni " +
              "già prese restano: quelle vanno spostate a voce." }),
            esito,
            el("label", { classe: "campo" }, [el("span", { testo: "Codice" }), codice]),
            el("label", { classe: "campo" }, [el("span", { testo: "Nota" }), nota]),
            el("button", { classe: "bottone largo", type: "submit", testo: "Spegni" }),
          ])
        );
      }

      aggiorna().catch(() => svuota(contenuto));
      return scheda;
    }

    carica();
  }

  return radice;
}
