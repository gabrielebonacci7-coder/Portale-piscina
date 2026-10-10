// Il gestionale di Greta ed Elisa: oggi, settimana, clienti, avvisi, numeri.

import { el, icona, avviso, foglio, pallini } from "../ui.js";
import * as D from "../dati.js";
import { avatar } from "../avatar.js";

let settimanaOffset = 0;
let cerca = "";

export function pagina(sezione, parametro, ctx) {
  switch (sezione) {
    case "settimana": return settimana(ctx);
    case "clienti": return parametro ? schedaCliente(parametro, ctx) : clienti(ctx);
    case "avvisi": return avvisiPagina(ctx);
    case "numeri": return numeri();
    default: return oggi(ctx);
  }
}

const cap = (t) => (t ? t[0].toUpperCase() + t.slice(1) : t);
const nome = (id) => D.nomeCompleto(D.cliente(id));

// --------------------------------------------------------------------- oggi
function oggi(ctx) {
  // La domenica non ci sono lezioni: si mostrano quelle del giorno dopo.
  const giorno = D.prossimiGiorni(1)[0];
  const lez = D.lezioni(giorno, 1);
  const iscritte = lez.reduce((n, l) => n + l.iscritte.length, 0);
  const attesa = lez.reduce((n, l) => n + l.attesa.length, 0);
  const finite = D.clienti().filter((c) => c.ingressi <= 1);
  const nuove = D.clienti().filter((c) => c.nuova);

  return el("div", { classe: "pagina" }, [
    el("div", { classe: "occhiello", testo: cap(D.quandoRelativo(giorno)) + " · " + D.dataLunga(giorno) }),
    el("div", { classe: "riepilogo" }, [
      tessera(lez.length, "lezioni"),
      tessera(`${iscritte}/${lez.length * D.POSTI}`, "posti presi"),
      tessera(attesa, "in attesa"),
    ]),
    nuove.length ? el("a", { classe: "riquadro nuove", href: `#/studio/clienti/${nuove[0].id}` }, [
      icona("persona"),
      el("div", {}, [
        el("b", { testo: nuove.length === 1 ? "Nuova iscritta" : `${nuove.length} nuove iscritte` }),
        el("p", { testo: nuove.map(D.nomeCompleto).join(", ") + " · carica il pacchetto quando paga" }),
      ]),
    ]) : null,
    ...lez.map((l) => registro(l, ctx)),
    finite.length ? el("section", { classe: "sezione" }, [
      el("h2", { classe: "titolo-sezione", testo: "Pacchetto in esaurimento" }),
      ...finite.map((c) => rigaCliente(c)),
    ]) : null,
  ]);
}

function tessera(valore, etichetta) {
  return el("div", { classe: "kpi" }, [el("b", { testo: valore }), el("span", { testo: etichetta })]);
}

/** Il registro di una lezione: chi c'è, e le presenze da segnare. */
function registro(l, ctx) {
  const cominciata = l.inizio <= D.adesso();
  return el("div", { classe: `registro ${l.annullata ? "annullata" : ""}` }, [
    el("div", { classe: "registro-testa" }, [
      el("div", { classe: "registro-ora" }, [el("b", { testo: D.oraDi(l.inizio) }), el("span", { testo: D.oraDi(l.fine) })]),
      el("div", { classe: "registro-titolo" }, [
        el("b", { testo: l.titolo }),
        el("span", { testo: l.annullata ? "Annullata" : `con ${l.istruttrice.nome} · ${l.iscritte.length}/${D.POSTI}` }),
      ]),
      el("button", { classe: "tondo", type: "button", "aria-label": "Gestisci", onclick: () => gestisci(l.id, ctx) }, [icona("matita")]),
    ]),
    l.annullata ? null : el("div", { classe: "registro-elenco" }, [
      ...l.iscritte.map((id) => {
        const p = l.presenze[id];
        return el("div", { classe: "registro-riga" }, [
          el("span", { classe: "registro-nome", testo: nome(id) }),
          el("div", { classe: "presenza" }, [
            el("button", {
              type: "button", classe: p === true ? "si attivo" : "si", "aria-label": "Presente",
              onclick: () => { D.segnaPresenza(l.id, id, true); ctx.ridisegna(); },
            }, [icona("spunta", "icona piccola")]),
            el("button", {
              type: "button", classe: p === false ? "no attivo" : "no", "aria-label": "Assente",
              onclick: () => { D.segnaPresenza(l.id, id, false); ctx.ridisegna(); },
            }, [icona("chiudi", "icona piccola")]),
          ]),
        ]);
      }),
      ...Array.from({ length: D.POSTI - l.iscritte.length }, () =>
        el("div", { classe: "registro-riga libero" }, [el("span", { testo: "Posto libero" })])),
      l.attesa.length ? el("div", { classe: "registro-attesa", testo: `In attesa: ${l.attesa.map(nome).join(", ")}` }) : null,
      cominciata ? null : el("div", { classe: "registro-nota", testo: "Le presenze si segnano durante la lezione" }),
    ]),
  ]);
}

// ---------------------------------------------------------------- settimana
function settimana(ctx) {
  const lunedi = new Date(D.adesso());
  lunedi.setHours(0, 0, 0, 0);
  lunedi.setDate(lunedi.getDate() - ((lunedi.getDay() + 6) % 7) + settimanaOffset * 7);
  const sabato = new Date(lunedi); sabato.setDate(sabato.getDate() + 5);
  const lez = D.lezioni(lunedi, 6);
  const presi = lez.reduce((n, l) => n + (l.annullata ? 0 : l.iscritte.length), 0);
  const totali = lez.filter((l) => !l.annullata).length * D.POSTI;

  const giorni = [];
  for (let i = 0; i < 6; i++) {
    const g = new Date(lunedi); g.setDate(g.getDate() + i);
    giorni.push(g);
  }

  return el("div", { classe: "pagina" }, [
    el("div", { classe: "naviga-settimana" }, [
      el("button", { classe: "tondo", type: "button", "aria-label": "Settimana prima", onclick: () => { settimanaOffset -= 1; ctx.ridisegna(); } }, [icona("indietro")]),
      el("div", {}, [
        el("b", { testo: `${lunedi.getDate()} – ${sabato.getDate()} ${D.MESI[sabato.getMonth()]}` }),
        el("span", { testo: `${presi} posti presi su ${totali}` }),
      ]),
      el("button", { classe: "tondo", type: "button", "aria-label": "Settimana dopo", onclick: () => { settimanaOffset += 1; ctx.ridisegna(); } }, [icona("freccia")]),
    ]),
    ...giorni.map((g) => el("section", { classe: "giorno-studio" }, [
      el("div", { classe: "giorno-studio-testa" }, [
        el("b", { testo: cap(D.GIORNI[g.getDay()]) + " " + g.getDate() }),
        el("span", {}, [avatar(D.istruttriceDel(g.getDay()).id, "mini"), D.istruttriceDel(g.getDay()).nome]),
      ]),
      ...D.lezioni(g, 1).map((l) => el("button", {
        type: "button", classe: `riga-studio ${l.annullata ? "annullata" : ""} ${l.passata ? "passata" : ""}`,
        onclick: () => gestisci(l.id, ctx),
      }, [
        el("b", { testo: D.oraDi(l.inizio) }),
        el("span", { classe: "riga-studio-titolo", testo: l.annullata ? "Annullata" : l.titolo }),
        l.annullata ? null : pallini(l.iscritte.length, D.POSTI),
        l.attesa.length ? el("span", { classe: "etichetta attesa", testo: `+${l.attesa.length}` }) : null,
        icona("freccia", "icona piccola"),
      ])),
    ])),
  ]);
}

/** Il foglio per gestire una lezione. */
function gestisci(id, ctx) {
  const l = D.lezione(id);
  const ridisegna = () => { f.chiudi(); ctx.ridisegna(); };

  const titolo = el("input", { value: l.titolo, "aria-label": "Titolo della lezione", maxlength: 40 });
  const sceltaCliente = el("select", { "aria-label": "Aggiungi una cliente" }, [
    el("option", { value: "", testo: "Aggiungi una cliente…" }),
    ...D.clienti().filter((c) => !l.iscritte.includes(c.id)).map((c) => el("option", { value: c.id, testo: D.nomeCompleto(c) })),
  ]);
  sceltaCliente.addEventListener("change", () => {
    if (!sceltaCliente.value) return;
    try {
      D.prenota(id, sceltaCliente.value);
      avviso(`${nome(sceltaCliente.value)} aggiunta`, "ok");
      ridisegna();
    } catch (e) { avviso(e.message); }
  });

  // Annullare chiede il motivo nel foglio stesso, senza finestre del browser.
  const motivo = el("input", { value: "imprevisto dell'istruttrice", "aria-label": "Motivo", maxlength: 80 });
  const annulla = el("div", { classe: "annulla" });
  const mostraBottone = () => annulla.replaceChildren(el("button", {
    classe: "bottone pericolo largo", type: "button", testo: "Annulla la lezione",
    onclick: () => annulla.replaceChildren(
      el("label", { classe: "campo" }, [el("span", { testo: "Motivo da mandare alle iscritte" }), motivo]),
      el("div", { classe: "riga-bottoni" }, [
        el("button", { classe: "bottone secondario", type: "button", testo: "Lascia stare", onclick: mostraBottone }),
        el("button", {
          classe: "bottone conferma-annulla", type: "button", testo: "Annulla e avvisa",
          onclick: () => {
            D.annullaLezione(id, motivo.value.trim());
            avviso("Lezione annullata: le iscritte sono state avvisate", "ok");
            ridisegna();
          },
        }),
      ])
    ),
  }));
  mostraBottone();

  const contenuto = el("div", { classe: "dettaglio" }, [
    el("label", { classe: "campo" }, [
      el("span", { testo: "Titolo che vedono le clienti" }),
      el("div", { classe: "campo-riga" }, [
        titolo,
        el("button", {
          classe: "bottone piccolo", type: "button", testo: "Salva",
          onclick: () => { D.cambiaTitolo(id, titolo.value); avviso("Titolo aggiornato", "ok"); ridisegna(); },
        }),
      ]),
    ]),
    el("div", { classe: "suggerimenti" }, ["Reformer", "Principianti", "Postura e schiena", "Total body", "Core e addome"].map((t) =>
      el("button", { type: "button", classe: "chip", testo: t, onclick: () => { titolo.value = t === "Reformer" ? t : `Reformer · ${t}`; } }))),

    l.annullata
      ? el("div", { classe: "riquadro avviso-riquadro" }, [
          el("p", { testo: `Lezione annullata (${l.annullata}).` }),
          el("button", { classe: "bottone secondario", type: "button", testo: "Rimettila in calendario", onclick: () => { D.ripristinaLezione(id); ridisegna(); } }),
        ])
      : el("div", {}, [
          el("h3", { classe: "titolo-sezione", testo: `Iscritte ${l.iscritte.length}/${D.POSTI}` }),
          ...l.iscritte.map((cid) => el("div", { classe: "riga-iscritta" }, [
            el("span", { testo: nome(cid) }),
            el("button", {
              classe: "link-piccolo", type: "button", testo: "Togli",
              onclick: () => {
                const entrata = D.disdici(id, cid, { daStudio: true });
                avviso(entrata ? `Tolta. Entra ${nome(entrata)} dalla lista d'attesa` : "Tolta, l'ingresso le è stato restituito", "ok");
                ridisegna();
              },
            }),
          ])),
          l.liberi > 0 ? sceltaCliente : null,
          l.attesa.length ? el("h3", { classe: "titolo-sezione", testo: "Lista d'attesa" }) : null,
          ...l.attesa.map((cid, i) => el("div", { classe: "riga-iscritta" }, [el("span", { testo: `${i + 1}. ${nome(cid)}` })])),
          el("p", { classe: "nota", testo: "Le clienti prenotate per telefono le aggiungi da qui." }),
          annulla,
        ]),
  ]);
  const f = foglio(contenuto, { titolo: `${cap(D.GIORNI[l.inizio.getDay()])} ${l.inizio.getDate()} · ${D.oraDi(l.inizio)}`, sottotitolo: `con ${l.istruttrice.nome}` });
}

// ------------------------------------------------------------------ clienti
function rigaCliente(c) {
  const stato = c.ingressi <= 0 ? "finito" : c.ingressi === 1 ? "ultimo" : "";
  return el("a", { classe: "riga-cliente", href: `#/studio/clienti/${c.id}` }, [
    el("span", { classe: "iniziali", testo: c.nome[0] + c.cognome[0] }),
    el("div", {}, [
      el("b", { testo: D.nomeCompleto(c) }),
      el("span", { testo: c.nuova ? "Nuova iscritta" : c.telefono }),
    ]),
    el("span", { classe: `ingressi ${stato}`, testo: c.ingressi <= 0 ? (c.ingressi < 0 ? `${c.ingressi}` : "0") : c.ingressi }),
  ]);
}

function clienti(ctx) {
  const elenco = D.clienti().filter((c) => D.nomeCompleto(c).toLowerCase().includes(cerca.toLowerCase()));
  const campo = el("input", { type: "search", placeholder: "Cerca una cliente", value: cerca, classe: "cerca" });
  campo.addEventListener("input", () => {
    cerca = campo.value;
    const nuovo = clienti(ctx);
    campo.closest(".pagina").replaceWith(nuovo);
    const c = nuovo.querySelector(".cerca");
    c.focus();
    c.setSelectionRange(cerca.length, cerca.length);
  });
  return el("div", { classe: "pagina" }, [
    campo,
    el("div", { classe: "legenda" }, [el("span", { testo: `${D.clienti().length} clienti` }), el("span", { testo: "Lezioni rimaste →" })]),
    el("div", { classe: "elenco-clienti" }, elenco.map(rigaCliente)),
  ]);
}

function schedaCliente(id, ctx) {
  const c = D.cliente(id);
  if (!c) return el("p", { classe: "vuoto", testo: "Cliente non trovata." });
  const { prossime, fatte } = D.lezioniDi(id);
  const assenze = fatte.filter((l) => l.presenze[id] === false).length;
  const scelta = { pacchetto: "p10", metodo: "contanti" };

  const opzioni = (lista, chiave) => el("div", { classe: "opzioni" }, lista.map(([valore, testo]) =>
    el("button", {
      type: "button", classe: `chip ${scelta[chiave] === valore ? "attivo" : ""}`, testo,
      onclick: (e) => {
        scelta[chiave] = valore;
        e.target.parentNode.querySelectorAll(".chip").forEach((b) => b.classList.toggle("attivo", b === e.target));
      },
    })));

  return el("div", { classe: "pagina" }, [
    el("a", { classe: "indietro", href: "#/studio/clienti" }, [icona("indietro"), "Clienti"]),
    el("div", { classe: "cliente-testa" }, [
      el("span", { classe: "iniziali grandi", testo: c.nome[0] + c.cognome[0] }),
      el("div", {}, [
        el("h2", { testo: D.nomeCompleto(c) }),
        el("div", { classe: "sotto", testo: `${c.telefono} · ${c.email}` }),
      ]),
    ]),
    el("div", { classe: "riga-bottoni" }, [
      el("a", { classe: "bottone whatsapp", href: `https://wa.me/39${c.telefono.replace(/\D/g, "")}`, target: "_blank", rel: "noopener" }, [icona("chat", "icona piccola"), "WhatsApp"]),
      el("a", { classe: "bottone secondario", href: `tel:+39${c.telefono.replace(/\D/g, "")}`, testo: "Chiama" }),
    ]),
    el("div", { classe: "riepilogo" }, [
      tessera(c.ingressi, "lezioni rimaste"),
      tessera(fatte.length, "fatte"),
      tessera(assenze, "assenze"),
    ]),
    c.scadenza ? el("p", { classe: "nota", testo: `Pacchetto valido fino al ${new Date(c.scadenza).getDate()} ${D.MESI[new Date(c.scadenza).getMonth()]}` }) : null,

    el("section", { classe: "riquadro carica" }, [
      el("h3", { testo: "Registra un pagamento" }),
      opzioni(D.PACCHETTI.map((p) => [p.id, p.nome.replace("Pacchetto ", "")]), "pacchetto"),
      opzioni([["contanti", "Contanti"], ["POS", "Carta / POS"]], "metodo"),
      el("button", {
        classe: "bottone largo", type: "button", testo: "Carica sul suo account",
        onclick: () => {
          D.caricaPacchetto(id, scelta.pacchetto, scelta.metodo);
          avviso("Pacchetto caricato: la cliente lo vede subito", "ok");
          ctx.ridisegna();
        },
      }),
    ]),

    el("h3", { classe: "titolo-sezione", testo: "Prossime lezioni" }),
    prossime.length
      ? el("div", { classe: "elenco-semplice" }, prossime.map((l) => el("div", { testo: `${cap(D.quandoRelativo(l.inizio))} · ${D.oraDi(l.inizio)} · ${l.titolo}` })))
      : el("p", { classe: "vuoto", testo: "Nessuna in programma." }),
    el("h3", { classe: "titolo-sezione", testo: "Pagamenti" }),
    ...D.movimentiDi(id).map((m) => {
      const d = new Date(m.quando);
      return el("div", { classe: "elenco-semplice" }, [el("div", { testo: `${d.getDate()} ${D.MESI[d.getMonth()]} · ${D.PACCHETTI.find((p) => p.id === m.pacchetto).nome} · ${m.metodo}` })]);
    }),
    D.movimentiDi(id).length ? null : el("p", { classe: "vuoto", testo: "Ancora nessuno." }),
  ]);
}

// ------------------------------------------------------------------- avvisi
function avvisiPagina(ctx) {
  const testo = el("textarea", { rows: 4, placeholder: "Es. Sabato 1 novembre lo studio è chiuso. Buon ponte!" });
  return el("div", { classe: "pagina" }, [
    el("div", { classe: "riquadro" }, [
      el("h3", { testo: "Scrivi a tutte le clienti" }),
      testo,
      el("button", {
        classe: "bottone largo", type: "button", testo: "Invia l'avviso",
        onclick: () => {
          if (!testo.value.trim()) return avviso("Scrivi prima il messaggio");
          D.pubblicaAvviso(testo.value.trim(), ctx.chi.nome);
          avviso("Avviso inviato a tutte", "ok");
          ctx.ridisegna();
        },
      }),
      el("p", { classe: "nota", testo: "Arriva come notifica sul telefono e resta nella campanella dell'app." }),
    ]),
    el("h2", { classe: "titolo-sezione", testo: "Inviati" }),
    ...D.avvisi().map((a) => {
      const d = new Date(a.quando);
      return el("div", { classe: "notifica" }, [
        el("div", {}, [
          el("div", { classe: "notifica-da", testo: `Da ${a.da} · ${cap(D.quandoRelativo(d))}` }),
          el("p", { testo: a.testo }),
        ]),
      ]);
    }),
  ]);
}

// ------------------------------------------------------------------- numeri
function numeri() {
  const ora = D.adesso();
  const da = new Date(ora); da.setDate(da.getDate() - 28);
  const passate = D.lezioni(da, 28).filter((l) => l.passata && !l.annullata);
  const presi = passate.reduce((n, l) => n + l.iscritte.length, 0);
  const riempimento = passate.length ? Math.round((presi / (passate.length * D.POSTI)) * 100) : 0;
  const presenze = passate.flatMap((l) => Object.values(l.presenze));
  const assenze = presenze.filter((p) => p === false).length;

  // Riempimento medio per fascia oraria: dice quali orari tirano di più.
  const fasce = {};
  for (const l of passate) {
    const chiave = `${l.inizio.getDay() === 6 ? "Sab" : "Lun–Ven"} ${D.oraDi(l.inizio)}`;
    (fasce[chiave] ||= []).push(l.iscritte.length / D.POSTI);
  }
  const righe = Object.entries(fasce)
    .map(([k, v]) => [k, Math.round((v.reduce((a, b) => a + b, 0) / v.length) * 100)])
    .sort((a, b) => b[1] - a[1]);

  const mese = D.movimenti().filter((m) => new Date(m.quando).getMonth() === ora.getMonth());

  return el("div", { classe: "pagina" }, [
    el("div", { classe: "occhiello", testo: "Ultime 4 settimane" }),
    el("div", { classe: "riepilogo" }, [
      tessera(`${riempimento}%`, "posti occupati"),
      tessera(presi, "lezioni fatte"),
      tessera(assenze, "assenze"),
    ]),
    el("h2", { classe: "titolo-sezione", testo: "Gli orari più richiesti" }),
    el("div", { classe: "barre", role: "table", "aria-label": "Riempimento medio per orario" }, righe.map(([k, v]) =>
      el("div", { classe: "barra", role: "row", title: `${k}: in media ${v}% dei posti presi` }, [
        el("span", { classe: "barra-nome", role: "cell", testo: k }),
        el("span", { classe: "barra-traccia", role: "presentation" }, [el("i", { stile: `width:${v}%` })]),
        el("span", { classe: "barra-valore", role: "cell", testo: `${v}%` }),
      ]))),
    el("h2", { classe: "titolo-sezione", testo: "Questo mese" }),
    el("div", { classe: "riepilogo" }, [
      tessera(mese.length, "pacchetti venduti"),
      tessera(mese.reduce((n, m) => n + D.PACCHETTI.find((p) => p.id === m.pacchetto).ingressi, 0), "lezioni vendute"),
      tessera(D.clienti().length, "clienti"),
    ]),
  ]);
}
