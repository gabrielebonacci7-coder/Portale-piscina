// Il gestionale di Greta ed Elisa: oggi, settimana, clienti, avvisi, numeri.

import * as api from "../api.js";
import { el, icona, avviso, foglio, pallini } from "../ui.js";
import { avatar } from "../avatar.js";
import * as T from "../tempo.js";

let settimanaOffset = 0;
let cerca = "";

export function pagina(sezione, parametro, ctx) {
  switch (sezione) {
    case "settimana": return settimana(ctx);
    case "clienti": return parametro ? schedaCliente(Number(parametro), ctx) : clienti(ctx);
    case "avvisi": return avvisiPagina(ctx);
    case "numeri": return numeri();
    default: return oggi(ctx);
  }
}

function tessera(valore, etichetta) {
  return el("div", { classe: "kpi" }, [el("b", { testo: valore }), el("span", { testo: etichetta })]);
}

async function prova(azione, messaggioOk) {
  try {
    const r = await azione();
    if (messaggioOk) avviso(typeof messaggioOk === "function" ? messaggioOk(r) : messaggioOk, "ok");
    return r;
  } catch (e) {
    avviso(e.message);
    throw e;
  }
}

// --------------------------------------------------------------------- oggi
async function oggi(ctx) {
  // La domenica non ci sono lezioni: si mostra il primo giorno che ne ha.
  const prossime = await api.staffLezioni(T.chiaveGiorno(T.oggi()), 7);
  const giornoK = prossime.length ? T.chiaveGiorno(T.data(prossime[0].inizio)) : T.chiaveGiorno(T.oggi());
  const lez = prossime.filter((l) => T.chiaveGiorno(T.data(l.inizio)) === giornoK);
  const giorno = T.daChiave(giornoK);
  const attive = lez.filter((l) => !l.annullata);
  const iscritte = attive.reduce((n, l) => n + l.occupati, 0);
  const attesa = attive.reduce((n, l) => n + l.attesa.length, 0);
  const numeri = await api.numeri();

  return el("div", { classe: "pagina" }, [
    el("div", { classe: "occhiello", testo: `${T.cap(T.quandoRelativo(giorno))} · ${T.dataLunga(giorno)}` }),
    el("div", { classe: "riepilogo" }, [
      tessera(attive.length, "lezioni"),
      tessera(`${iscritte}/${attive.length * 3}`, "posti presi"),
      tessera(attesa, "in attesa"),
    ]),
    ...lez.map((l) => registro(l, ctx)),
    numeri.da_saldare.length ? el("section", { classe: "sezione" }, [
      el("h2", { classe: "titolo-sezione", testo: "Da saldare in studio" }),
      el("div", { classe: "elenco-clienti" }, numeri.da_saldare.map(rigaCliente)),
    ]) : null,
  ]);
}

/** Il registro di una lezione: chi c'è, le presenze da segnare. */
function registro(l, ctx) {
  const inizio = T.data(l.inizio);
  const cominciata = inizio <= T.ora();
  return el("div", { classe: `registro ${l.annullata ? "annullata" : ""}` }, [
    el("div", { classe: "registro-testa" }, [
      el("div", { classe: "registro-ora" }, [el("b", { testo: T.oraDi(inizio) }), el("span", { testo: T.oraDi(T.data(l.fine)) })]),
      el("div", { classe: "registro-titolo" }, [
        el("b", { testo: l.titolo }),
        el("span", { testo: l.annullata ? "Annullata" : `con ${l.istruttrice.nome} · ${l.occupati}/${l.posti}` }),
      ]),
      el("button", { classe: "tondo", type: "button", "aria-label": "Gestisci la lezione", onclick: () => gestisci(l.id, ctx) }, [icona("matita")]),
    ]),
    l.annullata ? null : el("div", { classe: "registro-elenco" }, [
      ...l.iscritte.map((i) => el("div", { classe: "registro-riga" }, [
        el("a", { classe: "registro-nome", href: `#/studio/clienti/${i.id}` }, [
          i.nome,
          i.lezioni_rimaste < 0 ? el("span", { classe: "ingressi finito piccolo", testo: i.lezioni_rimaste }) : null,
        ]),
        el("div", { classe: "presenza" }, [
          el("button", {
            type: "button", classe: i.presente === true ? "si attivo" : "si", "aria-label": `${i.nome} presente`,
            onclick: () => prova(() => api.segnaPresenza(l.id, i.id, i.presente === true ? null : true)).then(ctx.ridisegna),
          }, [icona("spunta", "icona piccola")]),
          el("button", {
            type: "button", classe: i.presente === false ? "no attivo" : "no", "aria-label": `${i.nome} assente`,
            onclick: () => prova(() => api.segnaPresenza(l.id, i.id, i.presente === false ? null : false)).then(ctx.ridisegna),
          }, [icona("chiudi", "icona piccola")]),
        ]),
      ])),
      ...Array.from({ length: l.liberi }, () => el("div", { classe: "registro-riga libero" }, [el("span", { testo: "Posto libero" })])),
      l.attesa.length ? el("div", { classe: "registro-attesa", testo: `In attesa: ${l.attesa.map((a) => a.nome).join(", ")}` }) : null,
      cominciata || !l.iscritte.length ? null : el("div", { classe: "registro-nota", testo: "Le presenze si segnano durante la lezione" }),
    ]),
  ]);
}

// ---------------------------------------------------------------- settimana
async function settimana(ctx) {
  const lunedi = T.piuGiorni(T.oggi(), -((T.oggi().getDay() + 6) % 7) + settimanaOffset * 7);
  const sabato = T.piuGiorni(lunedi, 5);
  const lez = await api.staffLezioni(T.chiaveGiorno(lunedi), 6);
  const attive = lez.filter((l) => !l.annullata);
  const presi = attive.reduce((n, l) => n + l.occupati, 0);

  const perGiorno = new Map();
  for (const l of lez) {
    const k = T.chiaveGiorno(T.data(l.inizio));
    if (!perGiorno.has(k)) perGiorno.set(k, []);
    perGiorno.get(k).push(l);
  }

  return el("div", { classe: "pagina" }, [
    el("div", { classe: "naviga-settimana" }, [
      el("button", { classe: "tondo", type: "button", "aria-label": "Settimana prima", onclick: () => { settimanaOffset -= 1; ctx.ridisegna(); } }, [icona("indietro")]),
      el("div", {}, [
        el("b", { testo: `${lunedi.getDate()} – ${sabato.getDate()} ${T.MESI[sabato.getMonth()]}` }),
        el("span", { testo: `${presi} posti presi su ${attive.length * 3}` }),
      ]),
      el("button", { classe: "tondo", type: "button", "aria-label": "Settimana dopo", onclick: () => { settimanaOffset += 1; ctx.ridisegna(); } }, [icona("freccia")]),
    ]),
    ...[...perGiorno.entries()].map(([k, lista]) => {
      const g = T.daChiave(k);
      const ist = lista[0].istruttrice;
      return el("section", { classe: "giorno-studio" }, [
        el("div", { classe: "giorno-studio-testa" }, [
          el("b", { testo: `${T.cap(T.GIORNI[g.getDay()])} ${g.getDate()}` }),
          el("span", {}, [avatar(ist.id, "mini"), ist.nome]),
        ]),
        ...lista.map((l) => el("button", {
          type: "button", classe: `riga-studio ${l.annullata ? "annullata" : ""} ${l.passata ? "passata" : ""}`,
          onclick: () => gestisci(l.id, ctx),
        }, [
          el("b", { testo: T.oraDi(T.data(l.inizio)) }),
          el("span", { classe: "riga-studio-titolo", testo: l.annullata ? "Annullata" : l.titolo }),
          l.annullata ? null : pallini(l.occupati, l.posti),
          l.attesa.length ? el("span", { classe: "etichetta attesa", testo: `+${l.attesa.length}` }) : null,
          icona("freccia", "icona piccola"),
        ])),
        g >= T.oggi() ? el("button", {
          type: "button", classe: "riga-studio aggiungi-lezione",
          onclick: () => aggiungiLezione(k, g, ctx),
        }, [icona("piu", "icona piccola"), el("span", { testo: "Aggiungi una lezione" })]) : null,
      ]);
    }),
  ]);
}

/** Aprire una lezione fuori orario (per esempio alle 18:30). */
function aggiungiLezione(chiave, giorno, ctx) {
  const ora = el("input", { type: "time", id: "ora-nuova-lezione", value: ctx.info?.orario_extra?.[(giorno.getDay() + 6) % 7] || "18:30", step: 1800 });
  const titolo = el("input", { id: "titolo-nuova-lezione", placeholder: "Reformer", maxlength: 60 });
  const crea = el("button", {
    classe: "bottone largo", type: "button", testo: "Apri la lezione",
    onclick: () => prova(() => api.nuovaLezione(chiave, ora.value, titolo.value), "Lezione aggiunta: le clienti la vedono già")
      .then(() => { f.chiudi(); ctx.ridisegna(); }),
  });
  const f = foglio(el("div", { classe: "dettaglio" }, [
    el("label", { classe: "campo" }, [el("span", { testo: "Ora d'inizio (dura un'ora)" }), ora]),
    el("label", { classe: "campo" }, [el("span", { testo: "Nome (facoltativo)" }), titolo]),
    el("p", { classe: "nota", testo: "La lezione si prenota come le altre, con 3 posti. Se poi non serve, la annulli dal suo foglio." }),
    crea,
  ]), { titolo: "Lezione in più", sottotitolo: T.cap(T.dataLunga(giorno)) });
}

/** Il foglio per gestire una lezione. */
async function gestisci(id, ctx) {
  let l;
  try { l = await api.staffLezione(id); } catch (e) { avviso(e.message); return; }
  const inizio = T.data(l.inizio);
  const chiudiERidisegna = () => { f.chiudi(); ctx.ridisegna(); };

  const titolo = el("input", { value: l.titolo, id: "titolo-lezione", "aria-label": "Titolo della lezione", maxlength: 60 });
  // Il nome può valere solo per questa lezione o per tutte le settimane.
  const ogniSettimana = el("input", { type: "checkbox", id: "titolo-ogni-settimana", checked: true });
  const salvaTitolo = () => prova(
    () => api.cambiaTitolo(id, titolo.value, ogniSettimana.checked),
    ogniSettimana.checked ? `Nome salvato: ogni ${T.GIORNI[inizio.getDay()]} alle ${T.oraDi(inizio)}` : "Nome salvato per questa lezione",
  ).then(chiudiERidisegna);

  // Aggiungere una cliente (chi ha prenotato per telefono): si cerca per nome.
  const zonaAggiungi = el("div", { classe: "aggiungi" });
  const mostraAggiungi = () => {
    const campoCerca = el("input", { type: "search", id: "cerca-iscritta", placeholder: "Cerca la cliente per nome", classe: "cerca" });
    const risultati = el("div", { classe: "risultati" });
    let timer;
    campoCerca.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        if (campoCerca.value.trim().length < 2) { risultati.replaceChildren(); return; }
        const trovate = (await api.clienti(campoCerca.value)).filter((c) => !l.iscritte.some((i) => i.id === c.id)).slice(0, 6);
        risultati.replaceChildren(...trovate.map((c) => el("button", {
          type: "button", classe: "risultato", testo: `${c.nome} ${c.cognome}`,
          onclick: () => prova(() => api.aggiungiIscritta(id, c.id), `${c.nome} aggiunta`).then(chiudiERidisegna),
        })), trovate.length ? null : el("p", { classe: "sotto", testo: "Nessuna cliente con questo nome." }));
      }, 250);
    });
    zonaAggiungi.replaceChildren(campoCerca, risultati);
    campoCerca.focus();
  };

  const motivo = el("input", { value: "imprevisto dell'istruttrice", id: "motivo-annullamento", "aria-label": "Motivo", maxlength: 200 });
  const zonaAnnulla = el("div", { classe: "annulla" });
  const bottoneAnnulla = () => zonaAnnulla.replaceChildren(el("button", {
    classe: "bottone pericolo largo", type: "button", testo: "Annulla la lezione",
    onclick: () => zonaAnnulla.replaceChildren(
      el("label", { classe: "campo" }, [el("span", { testo: "Motivo da mandare alle iscritte" }), motivo]),
      el("div", { classe: "riga-bottoni" }, [
        el("button", { classe: "bottone secondario", type: "button", testo: "Lascia stare", onclick: bottoneAnnulla }),
        el("button", {
          classe: "bottone conferma-annulla", type: "button", testo: "Annulla e avvisa",
          onclick: () => prova(() => api.annullaLezione(id, motivo.value), (r) => `Lezione annullata: ${r.avvisate} iscritte avvisate`).then(chiudiERidisegna),
        }),
      ])),
  }));
  bottoneAnnulla();

  const contenuto = el("div", { classe: "dettaglio" }, [
    el("label", { classe: "campo" }, [
      el("span", { testo: "Nome della lezione (lo vedono le clienti)" }),
      el("div", { classe: "campo-riga" }, [titolo, el("button", { classe: "bottone piccolo", type: "button", testo: "Salva", onclick: salvaTitolo })]),
    ]),
    el("label", { classe: "spunta" }, [
      ogniSettimana,
      el("span", { testo: `Tutte le settimane: ogni ${T.GIORNI[inizio.getDay()]} alle ${T.oraDi(inizio)}` }),
    ]),
    el("div", { classe: "suggerimenti" }, ["Reformer", "Pilates fitness", "Principianti", "Postura e schiena", "Total body", "Core e addome"].map((t) =>
      el("button", { type: "button", classe: "chip", testo: t, onclick: () => { titolo.value = t; } }))),
    l.annullata
      ? el("div", { classe: "riquadro avviso-riquadro" }, [
          el("p", { testo: `Lezione annullata${l.motivo_annullamento ? ` (${l.motivo_annullamento})` : ""}.` }),
          el("button", {
            classe: "bottone secondario", type: "button", testo: "Rimettila in calendario",
            onclick: () => prova(() => api.ripristinaLezione(id), "Lezione di nuovo in calendario").then(chiudiERidisegna),
          }),
        ])
      : el("div", {}, [
          el("h3", { classe: "titolo-sezione", testo: `Iscritte ${l.occupati}/${l.posti}` }),
          ...l.iscritte.map((i) => el("div", { classe: "riga-iscritta" }, [
            el("span", { testo: i.nome + (i.dalla_lista ? " · dalla lista" : "") }),
            el("button", {
              classe: "link-piccolo", type: "button", testo: "Togli",
              onclick: () => prova(() => api.togliIscritta(id, i.id),
                (r) => (r.entrata ? `Tolta. Entra ${r.entrata} dalla lista d'attesa` : "Tolta: la lezione le è tornata nel pacchetto")).then(chiudiERidisegna),
            }),
          ])),
          l.liberi > 0 && !l.passata ? el("button", { classe: "bottone secondario largo", type: "button", testo: "Aggiungi una cliente", onclick: mostraAggiungi }) : null,
          zonaAggiungi,
          l.attesa.length ? el("h3", { classe: "titolo-sezione", testo: "Lista d'attesa" }) : null,
          ...l.attesa.map((a, n) => el("div", { classe: "riga-iscritta" }, [el("span", { testo: `${n + 1}. ${a.nome}` })])),
          el("p", { classe: "nota", testo: "Chi prenota per telefono la aggiungi da qui. Togliendo una cliente, la lezione le torna nel pacchetto e il posto va alla prima in attesa." }),
          l.passata ? null : zonaAnnulla,
        ]),
  ]);
  const f = foglio(contenuto, { titolo: `${T.cap(T.GIORNI[inizio.getDay()])} ${inizio.getDate()} · ${T.oraDi(inizio)}`, sottotitolo: `con ${l.istruttrice.nome}` });
}

// ------------------------------------------------------------------ clienti
function rigaCliente(c) {
  const stato = c.lezioni_rimaste < 0 ? "finito" : c.lezioni_rimaste <= 1 ? "ultimo" : "";
  return el("a", { classe: "riga-cliente", href: `#/studio/clienti/${c.id}` }, [
    el("span", { classe: "iniziali", testo: (c.nome[0] || "") + (c.cognome[0] || "") }),
    el("div", {}, [
      el("b", { testo: `${c.nome} ${c.cognome}` }),
      el("span", { testo: c.telefono || c.email }),
    ]),
    el("span", { classe: `ingressi ${stato}`, testo: c.lezioni_rimaste }),
  ]);
}

async function clienti(ctx) {
  const elenco = await api.clienti(cerca);
  const campo = el("input", { type: "search", id: "cerca-cliente", placeholder: "Cerca per nome, email o telefono", value: cerca, classe: "cerca" });
  let timer;
  campo.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      cerca = campo.value;
      const trovate = await api.clienti(cerca);
      lista.replaceChildren(...trovate.map(rigaCliente));
      conteggio.textContent = `${trovate.length} clienti`;
    }, 250);
  });
  const lista = el("div", { classe: "elenco-clienti" }, elenco.map(rigaCliente));
  const conteggio = el("span", { testo: `${elenco.length} clienti` });
  return el("div", { classe: "pagina" }, [
    campo,
    el("div", { classe: "legenda" }, [conteggio, el("span", { testo: "Lezioni rimaste →" })]),
    elenco.length ? lista : el("p", { classe: "vuoto", testo: "Ancora nessuna cliente registrata." }),
  ]);
}

async function schedaCliente(id, ctx) {
  const s = await api.scheda(id);
  const c = s.cliente;
  const tel = (c.telefono || "").replace(/\D/g, "");
  const telInternazionale = tel.startsWith("39") && tel.length > 10 ? tel : `39${tel}`;

  // Le lezioni rimaste: si scrive il numero, oppure +/−, e si salva.
  let valore = c.lezioni_rimaste;
  const numero = el("input", {
    type: "number", id: "lezioni-rimaste", inputmode: "numeric", value: valore, min: -50, max: 500,
    classe: "saldo-numero", "aria-label": "Lezioni rimaste",
  });
  const scadenza = el("input", { type: "date", id: "scadenza", value: c.scadenza || "", "aria-label": "Valide fino al" });
  const nota = el("input", { id: "nota-saldo", placeholder: "Nota (facoltativa), es. pacchetto 10 pagato", maxlength: 150 });
  const cambia = (d) => { numero.value = Number(numero.value || 0) + d; };
  const salva = el("button", {
    classe: "bottone largo", type: "button", testo: "Salva",
    onclick: () => prova(() => api.impostaSaldo(id, {
      lezioni: Number(numero.value),
      cambia_scadenza: (scadenza.value || null) !== (c.scadenza || null),
      scadenza: scadenza.value || null,
      nota: nota.value,
    }), "Salvato: la cliente lo vede subito").then(ctx.ridisegna),
  });

  return el("div", { classe: "pagina" }, [
    el("a", { classe: "indietro", href: "#/studio/clienti" }, [icona("indietro"), "Clienti"]),
    el("div", { classe: "cliente-testa" }, [
      el("span", { classe: "iniziali grandi", testo: (c.nome[0] || "") + (c.cognome[0] || "") }),
      el("div", {}, [
        el("h2", { testo: `${c.nome} ${c.cognome}` }),
        el("div", { classe: "sotto", testo: `${c.telefono} · ${c.email}${c.email_confermata ? "" : " (non confermata)"}` }),
      ]),
    ]),
    el("div", { classe: "riga-bottoni" }, [
      el("a", { classe: "bottone whatsapp", href: `https://wa.me/${telInternazionale}`, target: "_blank", rel: "noopener" }, [icona("chat", "icona piccola"), "WhatsApp"]),
      el("a", { classe: "bottone secondario", href: `tel:+${telInternazionale}`, testo: "Chiama" }),
    ]),
    el("section", { classe: "riquadro carica" }, [
      el("h3", { testo: "Lezioni rimaste" }),
      el("div", { classe: "saldo" }, [
        el("button", { type: "button", classe: "tondo grande", "aria-label": "Una in meno", onclick: () => cambia(-1) }, [el("span", { testo: "−" })]),
        numero,
        el("button", { type: "button", classe: "tondo grande", "aria-label": "Una in più", onclick: () => cambia(+1) }, [icona("piu")]),
      ]),
      el("div", { classe: "suggerimenti centrati" }, [5, 10].map((n) =>
        el("button", { type: "button", classe: "chip", testo: `+${n}`, onclick: () => cambia(n) }))),
      el("label", { classe: "campo" }, [el("span", { testo: "Valide fino al (facoltativo)" }), scadenza]),
      nota,
      salva,
      c.lezioni_rimaste < 0 ? el("p", { classe: "nota rosso", testo: `Ha ${-c.lezioni_rimaste} ${c.lezioni_rimaste === -1 ? "lezione" : "lezioni"} da saldare.` }) : null,
    ]),
    el("div", { classe: "riepilogo" }, [
      tessera(s.prossime.length, "in programma"),
      tessera(s.fatte, "fatte"),
      tessera(s.assenze, "assenze"),
    ]),
    el("h3", { classe: "titolo-sezione", testo: "Prossime lezioni" }),
    s.prossime.length
      ? el("div", { classe: "elenco-semplice" }, s.prossime.map((p) => el("div", { testo: `${T.cap(T.quando(T.data(p.inizio)))} · ${p.titolo} · ${p.istruttrice}` })))
      : el("p", { classe: "vuoto", testo: "Nessuna in programma." }),
    el("h3", { classe: "titolo-sezione", testo: "Movimenti" }),
    s.movimenti.length
      ? el("div", { classe: "listino" }, s.movimenti.map((m) => el("div", { classe: "voce-listino" }, [
          el("div", {}, [el("b", { testo: m.motivo }), el("span", { testo: `${T.dataBreve(T.data(m.quando))} · saldo ${m.saldo}` })]),
          el("div", { classe: `quante ${m.variazione < 0 ? "meno" : ""}`, testo: m.variazione > 0 ? `+${m.variazione}` : `${m.variazione}` }),
        ])))
      : el("p", { classe: "vuoto", testo: "Ancora nessuno." }),
  ]);
}

// ------------------------------------------------------------------- avvisi
async function avvisiPagina(ctx) {
  const elenco = await api.avvisi();
  const testo = el("textarea", { rows: 4, id: "testo-avviso", placeholder: "Es. Sabato 1 novembre lo studio è chiuso. Buon ponte!" });
  return el("div", { classe: "pagina" }, [
    el("div", { classe: "riquadro" }, [
      el("h3", { testo: "Scrivi a tutte le clienti" }),
      testo,
      el("button", {
        classe: "bottone largo", type: "button", testo: "Invia l'avviso",
        onclick: () => {
          if (testo.value.trim().length < 3) return avviso("Scrivi prima il messaggio");
          prova(() => api.pubblicaAvviso(testo.value.trim()), "Avviso inviato a tutte").then(ctx.ridisegna);
        },
      }),
      el("p", { classe: "nota", testo: "Compare nella campanella dell'app di ogni cliente." }),
    ]),
    el("h2", { classe: "titolo-sezione", testo: "Inviati" }),
    elenco.length ? null : el("p", { classe: "vuoto", testo: "Ancora nessun avviso." }),
    ...elenco.map((a) => el("div", { classe: "notifica" }, [
      el("div", { classe: "notifica-icona" }, [icona("megafono", "icona piccola")]),
      el("div", { stile: "flex:1" }, [
        el("div", { classe: "notifica-da", testo: `Da ${a.da || "lo studio"} · ${T.cap(T.quando(T.data(a.quando)))}` }),
        el("p", { testo: a.testo }),
        el("button", {
          classe: "link-piccolo", type: "button", testo: "Togli",
          onclick: () => prova(() => api.togliAvviso(a.id), "Avviso tolto").then(ctx.ridisegna),
        }),
      ]),
    ])),
  ]);
}

// ------------------------------------------------------------------- numeri
async function numeri() {
  const n = await api.numeri();
  return el("div", { classe: "pagina" }, [
    el("div", { classe: "occhiello", testo: "Ultime 4 settimane" }),
    el("div", { classe: "riepilogo" }, [
      tessera(`${n.riempimento}%`, "posti occupati"),
      tessera(n.presenze, "prenotazioni"),
      tessera(n.assenze, "assenze"),
    ]),
    n.fasce.length ? el("h2", { classe: "titolo-sezione", testo: "Gli orari più richiesti" }) : null,
    n.fasce.length ? el("div", { classe: "barre", role: "table", "aria-label": "Riempimento medio per orario" }, n.fasce.map((f) =>
      el("div", { classe: "barra", role: "row", title: `${f.fascia}: in media ${f.riempimento}% dei posti presi` }, [
        el("span", { classe: "barra-nome", role: "cell", testo: f.fascia }),
        el("span", { classe: "barra-traccia", role: "presentation" }, [el("i", { stile: `width:${f.riempimento}%` })]),
        el("span", { classe: "barra-valore", role: "cell", testo: `${f.riempimento}%` }),
      ]))) : el("p", { classe: "vuoto", testo: "I numeri compaiono dopo le prime lezioni." }),
    el("div", { classe: "riepilogo due" }, [
      tessera(n.clienti, "clienti iscritte"),
      tessera(n.da_saldare.length, "da saldare"),
    ]),
    n.da_saldare.length ? el("div", { classe: "elenco-clienti" }, n.da_saldare.map(rigaCliente)) : null,
  ]);
}
