// La vista principale: scegli il giorno, la fascia, il posto sulla mappa.

import * as api from "../api.js";
import {
  aIso, avviso, brindisi, daIso, el, etichettaGiorno, euro, foglio, giornoEsteso, plurale, svuota,
} from "../ui.js";
import { comandiZoom, disegnaMappa, perche, scegliibile, statoDi } from "../mappa.js";
import { ricordaNome } from "../omino.js";
import { nomePacchetto, prezzoCent, totaleCent } from "../prezzi.js";

export function vistaPrenota(ctx) {
  const stato = {
    giorno: ctx.info.primo_giorno,
    fascia: "giornata",
    scelte: new Map(), // codice -> { tipo, lettini, max_lettini }
    mappa: null,
    elenco: false,
  };

  const radice = el("div");
  const zonaFiltri = el("div", { classe: "scheda" });
  const zonaStrumenti = el("div", { classe: "barra-mappa" });
  const zonaMappa = el("div", { classe: "mappa-guscio" });
  const zonaLegenda = el("div", { classe: "legenda" });
  const zonaScelte = el("div", { classe: "scheda" });
  radice.append(
    zonaFiltri,
    el("div", { classe: "scheda stretta" }, [zonaStrumenti, zonaMappa, zonaLegenda]),
    zonaScelte
  );

  // --- Filtri: giorno e fascia --------------------------------------------
  function disegnaFiltri() {
    const data = el("input", {
      type: "date",
      value: stato.giorno,
      min: ctx.info.primo_giorno,
      max: ctx.info.ultimo_giorno,
      onchange: (e) => {
        if (!e.target.value) return;
        stato.giorno = e.target.value;
        stato.scelte.clear();
        caricaMappa();
      },
    });

    const scorciatoie = el("div", { classe: "scelte", style: "margin-top:8px" },
      [0, 1, 2].map((quanti) => {
        const d = daIso(ctx.info.primo_giorno);
        d.setDate(d.getDate() + quanti);
        const iso = aIso(d);
        return el("button", {
          classe: `bottone piccolo ${iso === stato.giorno ? "" : "secondario"}`,
          type: "button",
          testo: etichettaGiorno(iso, ctx.info.primo_giorno),
          onclick: () => {
            stato.giorno = iso;
            stato.scelte.clear();
            caricaMappa();
          },
        });
      })
    );

    const fasce = el(
      "div",
      { classe: "segmentato", role: "group", "aria-label": "Fascia oraria" },
      ctx.info.fasce.map((f) =>
        el("button", {
          type: "button",
          "aria-pressed": String(f.valore === stato.fascia),
          onclick: () => {
            stato.fascia = f.valore;
            // Le scelte che non valgono più per la nuova fascia si tolgono da
            // sole: meglio che scoprirlo alla conferma.
            for (const codice of [...stato.scelte.keys()]) {
              const p = trova(codice);
              if (!p || !scegliibile(p, stato.fascia)) stato.scelte.delete(codice);
            }
            disegnaTutto();
          },
        }, [f.etichetta, el("small", { testo: f.orario })])
      )
    );

    svuota(zonaFiltri).append(
      el("label", { classe: "campo", style: "margin-bottom:6px" }, [
        el("span", { testo: "Giorno" }), data,
      ]),
      // Il selettore di sistema scrive la data nel formato del telefono, che
      // non sempre è quello italiano: qui sotto si legge per esteso e non
      // resta dubbio su quale giorno si sta prenotando.
      el("div", { classe: "piccolo tenue", testo: giornoEsteso(stato.giorno) }),
      scorciatoie,
      el("div", { style: "height:12px" }),
      fasce
    );
  }

  const trova = (codice) => stato.mappa?.postazioni.find((p) => p.codice === codice);

  // --- Mappa ---------------------------------------------------------------
  function disegnaLegenda() {
    const r = stato.mappa?.riepilogo;
    svuota(zonaLegenda).append(
      ...ctx.info.legenda.map((v) =>
        el("span", {}, [el("i", { classe: `pallino ${v.stato}` }), v.testo])
      ),
      r
        ? el("span", {
            classe: "tenue",
            style: "margin-left:auto",
            testo: `${r.libere} libere · ${r.mezze} a metà · ${r.occupate} occupate`,
          })
        : null
    );
  }

  function disegnaMappaSolarium() {
    if (!stato.mappa) return;

    const interruttore = el("button", {
      classe: "bottone piccolo secondario",
      type: "button",
      testo: stato.elenco ? "Vedi la mappa" : "Vedi l'elenco",
      onclick: () => {
        stato.elenco = !stato.elenco;
        disegnaTutto();
      },
    });

    if (stato.elenco) {
      disegnaElenco();
      svuota(zonaStrumenti).append(
        el("span", { classe: "occhiello", testo: "Elenco dei posti" }),
        interruttore
      );
      return;
    }

    const vista = disegnaMappa(zonaMappa, stato.mappa, {
      fascia: stato.fascia,
      scelte: new Set(stato.scelte.keys()),
      alTocco: apriPostazione,
    });
    const zoom = comandiZoom(vista);
    // Lo zoom sta fuori dalla mappa: sopra, copriva le postazioni dell'angolo.
    svuota(zonaStrumenti).append(interruttore, zoom.comandi);
  }

  function disegnaElenco() {
    const perFila = new Map();
    for (const p of stato.mappa.postazioni) {
      if (!perFila.has(p.fila)) perFila.set(p.fila, []);
      perFila.get(p.fila).push(p);
    }
    const nomeFila = (f) => (f === "S" ? "Lettini solarium" : `Fila ${f}`);

    svuota(zonaMappa).append(
      el("div", { classe: "elenco-file", style: "padding:12px" },
        [...perFila.entries()].map(([fila, posti]) =>
          el("div", {}, [
            el("div", { classe: "fila-titolo", testo: nomeFila(fila) }),
            el("div", { classe: "griglia-codici" },
              posti.map((p) =>
                el("button", {
                  type: "button",
                  classe: `codice-posto ${statoDi(p)}${stato.scelte.has(p.codice) ? " scelta" : ""}`,
                  testo: p.codice,
                  title: perche(p, stato.fascia),
                  disabled: !scegliibile(p, stato.fascia) && !stato.scelte.has(p.codice),
                  onclick: () => apriPostazione(p),
                })
              )
            ),
          ])
        )
      )
    );
  }

  // --- Il foglio di una postazione ----------------------------------------
  function apriPostazione(p) {
    const gia = stato.scelte.get(p.codice);

    if (!scegliibile(p, stato.fascia) && !gia) {
      brindisi(`${p.codice}: ${perche(p, stato.fascia)}`, "attenzione");
      return;
    }

    if (p.tipo === "lettino") {
      // Un lettino non ha pacchetti: o lo prendi o no.
      if (gia) stato.scelte.delete(p.codice);
      else stato.scelte.set(p.codice, { tipo: p.tipo, lettini: 0, max_lettini: 0 });
      disegnaTutto();
      return;
    }

    let lettini = gia ? gia.lettini : 2;

    const opzioni = el("div", { classe: "pacchetti" });
    const disegnaOpzioni = () => {
      svuota(opzioni).append(
        ...Array.from({ length: p.max_lettini + 1 }, (_, n) =>
          el("button", {
            classe: "pacchetto",
            type: "button",
            "aria-pressed": String(n === lettini),
            onclick: () => {
              lettini = n;
              disegnaOpzioni();
            },
          }, [
            el("span", { classe: "disegno", html: disegnoPacchetto(n) }),
            el("span", {}, [
              el("div", { classe: "nome", testo: nomePacchetto(p.tipo, n) }),
              el("div", { classe: "piccolo tenue", testo: etichettaListino(n) }),
            ]),
            el("span", { classe: "prezzo", testo: euro(prezzoCent(ctx.listino, p.tipo, n)) }),
          ])
        )
      );
    };
    disegnaOpzioni();

    const f = foglio(
      el("div", {}, [
        el("div", { classe: "titolo-sezione" }, [
          el("h2", { testo: `Postazione ${p.codice}` }),
          el("span", { classe: "occhiello", testo: perche(p, stato.fascia) }),
        ]),
        el("p", { classe: "piccolo tenue", testo:
          `${giornoEsteso(stato.giorno)} · ${etichettaFascia(ctx, stato.fascia)}` }),
        opzioni,
        el("div", { style: "height:12px" }),
        el("button", {
          classe: "bottone largo",
          type: "button",
          testo: gia ? "Aggiorna la scelta" : "Scegli questa postazione",
          onclick: () => {
            stato.scelte.set(p.codice, { tipo: p.tipo, lettini, max_lettini: p.max_lettini });
            f.chiudi();
            disegnaTutto();
          },
        }),
        gia
          ? el("button", {
              classe: "bottone largo fantasma",
              type: "button",
              style: "margin-top:8px",
              testo: "Togli dalla scelta",
              onclick: () => {
                stato.scelte.delete(p.codice);
                f.chiudi();
                disegnaTutto();
              },
            })
          : null,
      ])
    );
  }

  const etichettaListino = (n) =>
    n === 0 ? "Ombrellone senza lettini" : `Postazione Relax ${n}`;

  function disegnoPacchetto(n) {
    const lettini = Array.from({ length: n }, (_, i) =>
      `<rect x="${4 + i * 12}" y="20" width="9" height="22" rx="4" fill="none"
             stroke="currentColor" stroke-width="2"/>`
    ).join("");
    return `<svg viewBox="0 0 46 46" width="46" height="46" aria-hidden="true">
      ${lettini}
      <path d="M8 16a15 15 0 0 1 30 0z" fill="currentColor" opacity="0.9"/>
      <path d="M23 16v22" stroke="currentColor" stroke-width="2"/></svg>`;
  }

  // --- Le scelte fatte -----------------------------------------------------
  function disegnaScelte() {
    const scelte = [...stato.scelte.entries()];
    const totale = totaleCent(ctx.listino, stato.scelte);

    if (!scelte.length) {
      svuota(zonaScelte).append(
        el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "La tua scelta" })]),
        el("p", { classe: "tenue piccolo", style: "margin:0", testo:
          "Tocca una postazione libera sulla mappa. Puoi sceglierne fino a " +
          `${ctx.info.max_postazioni} in una prenotazione sola.` })
      );
      return;
    }

    svuota(zonaScelte).append(
      el("div", { classe: "titolo-sezione" }, [
        el("h2", { testo: "La tua scelta" }),
        el("span", { classe: "occhiello", testo: `${giornoEsteso(stato.giorno)} · ${etichettaFascia(ctx, stato.fascia)}` }),
      ]),
      el("div", { classe: "scelte" },
        scelte.map(([codice, s]) =>
          el("span", { classe: "gettone" }, [
            `${codice} · ${nomePacchetto(s.tipo, s.lettini)} · ${euro(prezzoCent(ctx.listino, s.tipo, s.lettini))}`,
            el("button", {
              type: "button",
              "aria-label": `Togli ${codice}`,
              testo: "×",
              onclick: () => {
                stato.scelte.delete(codice);
                disegnaTutto();
              },
            }),
          ])
        )
      ),
      el("div", { classe: "riga-conto totale", style: "margin-top:12px" }, [
        el("span", { testo: `Noleggio · ${plurale(scelte.length, "postazione", "postazioni")}` }),
        el("span", { testo: euro(totale) }),
      ]),
      el("p", { classe: "piccolo tenue", style: "margin-top:8px", testo:
        "Il biglietto d'ingresso si paga a parte, in cassa. Vedi la pagina Prezzi." }),
      el("button", {
        classe: "bottone largo",
        type: "button",
        testo: "Continua",
        onclick: apriModulo,
      })
    );
  }

  // --- Il modulo con i dati ------------------------------------------------
  function apriModulo() {
    const errore = el("div");
    const campi = {
      nome: campo("Nome e cognome", { name: "nome", autocomplete: "name", required: true }),
      telefono: campo("Telefono", { name: "telefono", type: "tel", autocomplete: "tel", required: true }),
      email: campo("Email", { name: "email", type: "email", autocomplete: "email", required: true }),
      persone: campo("Quante persone", { name: "persone", type: "number", min: 1, max: 20, value: "2" }),
      note: campo("Note per lo staff (facoltativo)", { name: "note", tag: "textarea" }),
    };

    const invia = el("button", { classe: "bottone largo", type: "submit", testo: "Conferma la prenotazione" });

    const modulo = el("form", {
      onsubmit: async (e) => {
        e.preventDefault();
        invia.disabled = true;
        svuota(errore);
        try {
          const prenotazione = await api.prenota({
            giorno: stato.giorno,
            fascia: stato.fascia,
            postazioni: [...stato.scelte.entries()].map(([codice, s]) => ({
              codice,
              lettini: s.lettini,
            })),
            nome: campi.nome.input.value,
            telefono: campi.telefono.input.value,
            email: campi.email.input.value,
            persone: Number(campi.persone.input.value || 1),
            note: campi.note.input.value,
          });
          f.chiudi();
          stato.scelte.clear();
          caricaMappa();
          // Prima il grazie dell'omino, poi il codice: il codice serve, e non
          // deve restare nascosto dietro a un saluto.
          ricordaNome(prenotazione.nome);
          ctx.ringrazia(prenotazione.nome.trim().split(/\s+/)[0], () =>
            mostraConferma(prenotazione)
          );
        } catch (guaio) {
          errore.append(avviso(guaio.stato === 409 ? "attenzione" : "guaio", guaio.dettaglio));
          if (guaio.stato === 409) caricaMappa();
        } finally {
          invia.disabled = false;
        }
      },
    }, [
      el("div", { classe: "titolo-sezione" }, [el("h2", { testo: "I tuoi dati" })]),
      el("p", { classe: "piccolo tenue", testo:
        "Servono per tenerti il posto e per avvisarti se succede qualcosa. " +
        "Li vede solo lo staff della piscina." }),
      errore,
      campi.nome.nodo,
      campi.telefono.nodo,
      campi.email.nodo,
      campi.persone.nodo,
      campi.note.nodo,
      el("div", { classe: "riga-conto totale" }, [
        el("span", { testo: "Totale noleggio" }),
        el("span", { testo: euro(totaleCent(ctx.listino, stato.scelte)) }),
      ]),
      el("p", { classe: "piccolo tenue", testo: "Si paga in cassa all'arrivo." }),
      invia,
    ]);

    const f = foglio(modulo);
  }

  function campo(etichetta, { tag = "input", ...attributi } = {}) {
    const input = el(tag, attributi);
    return { input, nodo: el("label", { classe: "campo" }, [el("span", { testo: etichetta }), input]) };
  }

  function mostraConferma(p) {
    foglio(
      el("div", {}, [
        el("div", { style: "text-align:center;padding:8px 0 4px" }, [
          el("div", { style: "font-size:2.6rem;line-height:1", testo: "🏖️" }),
          el("h2", { style: "margin-top:8px", testo: "Prenotazione confermata" }),
          el("p", { classe: "dati", style: "font-size:1.6rem;font-weight:800;margin:10px 0 0", testo: p.codice }),
          el("p", { classe: "piccolo tenue", testo: "Conserva questo codice: serve in cassa." }),
        ]),
        avviso("buono", `Ti abbiamo scritto a ${p.email}.`),
        el("div", { classe: "riga-conto" }, [
          el("span", { testo: "Giorno" }),
          el("span", { testo: `${giornoEsteso(p.giorno)} · ${p.orario}` }),
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
        el("p", { classe: "piccolo tenue", style: "margin-top:12px", testo:
          "Il noleggio si paga in cassa insieme al biglietto d'ingresso." }),
        el("a", { classe: "bottone largo", href: "#/prenotazione", testo: "Vedi la prenotazione" }),
      ])
    );
  }

  // --- Caricamento ---------------------------------------------------------
  async function caricaMappa() {
    try {
      stato.mappa = await api.mappa(stato.giorno);
    } catch (guaio) {
      svuota(zonaMappa).append(avviso("guaio", guaio.dettaglio));
      return;
    }
    disegnaTutto();
  }

  function disegnaTutto() {
    disegnaFiltri();
    disegnaMappaSolarium();
    disegnaLegenda();
    disegnaScelte();
  }

  disegnaFiltri();
  svuota(zonaMappa).append(el("div", { classe: "caricamento", testo: "Carico la mappa…" }));
  caricaMappa();

  return radice;
}

export const etichettaFascia = (ctx, valore) =>
  ctx.info.fasce.find((f) => f.valore === valore)?.etichetta ?? valore;
