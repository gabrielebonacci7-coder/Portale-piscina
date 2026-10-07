// Le pagine della cliente: lezioni, le mie, pacchetto, contatti, notifiche.

import { el, icona, avviso, foglio, pallini } from "../ui.js";
import * as D from "../dati.js";
import { avatar } from "../avatar.js";

// Il giorno scelto e la vista (settimana o mese) restano mentre si naviga.
let giornoScelto = null;
let vista = "settimana";

/** Com'è messo un giorno: ci sono io? c'è ancora posto? */
function statoGiorno(g, io) {
  const lez = D.lezioni(g, 1).filter((l) => !l.passata && !l.annullata);
  if (lez.some((l) => l.iscritte.includes(io.id))) return "mio";
  if (!lez.length) return "vuoto";
  return lez.some((l) => l.liberi > 0) ? "libero" : "pieno";
}

// ------------------------------------------------------------------ lezioni
export function lezioni(ridisegna) {
  const giorni = D.giorniPrenotabili();
  if (!giornoScelto || !giorni.some((g) => D.chiaveGiorno(g) === giornoScelto)) {
    // Si apre sul primo giorno che ha ancora lezioni da fare.
    const conPosto = giorni.find((g) => D.lezioni(g, 1).some((l) => !l.passata));
    giornoScelto = D.chiaveGiorno(conPosto || giorni[0]);
  }
  const giorno = giorni.find((g) => D.chiaveGiorno(g) === giornoScelto);
  const delGiorno = D.lezioni(giorno, 1);
  const chi = D.istruttriceDel(giorno.getDay());
  const io = D.io();
  const scegli = (g) => { giornoScelto = D.chiaveGiorno(g); ridisegna(); };

  const commutatore = el("div", { classe: "vista-testa" }, [
    el("div", { classe: "vista-mese", testo: cap(D.MESI[giorno.getMonth()]) + " " + giorno.getFullYear() }),
    el("div", { classe: "segmentato", role: "group", "aria-label": "Vista" }, [["settimana", "Settimana"], ["mese", "Mese"]].map(([v, t]) =>
      el("button", {
        type: "button", classe: vista === v ? "attivo" : "", "aria-pressed": vista === v ? "true" : "false",
        "data-vista": v, testo: t,
        onclick: () => { vista = v; ridisegna(); },
      }))),
  ]);

  return el("div", { classe: "pagina" }, [
    commutatore,
    vista === "mese" ? calendarioMese(giorni, io, scegli) : striscia(giorni, io, scegli),
    el("div", { classe: "con-chi" }, [
      avatar(chi.id, "piccolo"),
      el("div", {}, [
        el("div", { classe: "con-chi-data", testo: cap(D.quandoRelativo(giorno)) + (D.quandoRelativo(giorno).includes(" ") ? "" : ` · ${D.dataLunga(giorno)}`) }),
        el("div", { classe: "con-chi-nome", html: `Lezioni con <b>${chi.nome}</b>` }),
      ]),
    ]),
    el("div", { classe: "elenco-lezioni" }, delGiorno.map((l) => schedaLezione(l, ridisegna))),
    el("p", { classe: "nota", testo: `Si prenota fino a un mese prima · ${D.POSTI} reformer · disdetta fino a ${D.ORE_DISDETTA} ore prima` }),
  ]);
}

/** La striscia dei giorni, da scorrere col dito fino a un mese avanti. */
function striscia(giorni, io, scegli) {
  const nodo = el("div", { classe: "striscia", role: "tablist" }, giorni.flatMap((g, i) => {
    const stato = statoGiorno(g, io);
    const scelto = D.chiaveGiorno(g) === giornoScelto;
    // Un segno sottile fra una settimana e l'altra.
    const nuovaSettimana = i > 0 && g.getDay() === 1;
    return [
      nuovaSettimana ? el("span", { classe: "striscia-stacco", "aria-hidden": "true" }) : null,
      el("button", {
        type: "button",
        role: "tab",
        "aria-selected": scelto ? "true" : "false",
        classe: `giorno ${scelto ? "scelto" : ""} ${stato === "pieno" ? "pieno" : ""}`,
        "data-giorno": D.chiaveGiorno(g),
        onclick: () => scegli(g),
      }, [
        el("span", { classe: "giorno-nome", testo: D.GIORNI_CORTI[g.getDay()] }),
        el("span", { classe: "giorno-num", testo: g.getDate() }),
        el("i", { classe: stato === "mio" ? "segno mio" : stato === "libero" ? "segno" : "segno vuoto" }),
      ]),
    ];
  }).filter(Boolean));
  // Tiene in vista il giorno scelto.
  requestAnimationFrame(() => nodo.querySelector(".scelto")?.scrollIntoView({ inline: "center", block: "nearest" }));
  return nodo;
}

/** Il mese intero: lunedì–sabato, da questa settimana a un mese avanti. */
function calendarioMese(giorni, io, scegli) {
  const prenotabili = new Set(giorni.map(D.chiaveGiorno));
  const inizio = new Date(giorni[0]);
  inizio.setDate(inizio.getDate() - ((inizio.getDay() + 6) % 7)); // il lunedì
  const fine = D.ultimoGiornoPrenotabile();

  const celle = [];
  let mesePrima = inizio.getMonth();
  for (const d = new Date(inizio); d <= fine || d.getDay() !== 1; d.setDate(d.getDate() + 1)) {
    if (d.getDay() === 0) continue; // la domenica lo studio è chiuso
    const chiave = D.chiaveGiorno(d);
    const attivo = prenotabili.has(chiave);
    const stato = attivo ? statoGiorno(d, io) : "fuori";
    const g = new Date(d);
    celle.push(el("button", {
      type: "button",
      classe: `cella ${stato} ${chiave === giornoScelto ? "scelta" : ""}`,
      disabled: attivo ? null : true,
      "data-giorno": chiave,
      "aria-label": `${D.dataLunga(g)}${attivo ? "" : ", non prenotabile"}`,
      onclick: () => scegli(g),
    }, [
      // Il primo giorno di un mese nuovo ne porta il nome (il 1° può essere domenica).
      d.getMonth() !== mesePrima ? el("span", { classe: "cella-mese", testo: D.MESI[d.getMonth()].slice(0, 3) }) : null,
      el("span", { classe: "cella-num", testo: d.getDate() }),
      el("i"),
    ]));
    mesePrima = d.getMonth();
  }

  return el("div", { classe: "mese" }, [
    el("div", { classe: "mese-griglia" }, [
      ...[1, 2, 3, 4, 5, 6].map((n) => el("span", { classe: "mese-intestazione", testo: D.GIORNI_CORTI[n] })),
      ...celle,
    ]),
    el("div", { classe: "mese-legenda" }, [
      el("span", {}, [el("i", { classe: "libero" }), "posti liberi"]),
      el("span", {}, [el("i", { classe: "pieno" }), "tutto pieno"]),
      el("span", {}, [el("i", { classe: "mio" }), "prenotata"]),
    ]),
  ]);
}

function statoLezione(l, idCliente) {
  if (l.annullata) return { classe: "annullata", testo: "Annullata" };
  if (l.iscritte.includes(idCliente)) return { classe: "mia", testo: "Prenotata" };
  if (l.passata) return { classe: "passata", testo: "Conclusa" };
  if (l.attesa.includes(idCliente)) return { classe: "attesa", testo: `In attesa · ${l.attesa.indexOf(idCliente) + 1}ª` };
  if (l.liberi === 0) return { classe: "piena", testo: "Piena" };
  if (l.liberi === 1) return { classe: "ultimo", testo: "Ultimo posto" };
  return { classe: "libera", testo: `${l.liberi} posti liberi` };
}

export function schedaLezione(l, ridisegna, { conData = false } = {}) {
  const io = D.io();
  const s = statoLezione(l, io?.id);
  return el("button", {
    type: "button",
    classe: `lezione ${s.classe}`,
    "data-lezione": l.id,
    disabled: l.passata && !l.iscritte.includes(io?.id) ? true : null,
    onclick: () => dettaglio(l.id, ridisegna),
  }, [
    el("div", { classe: "lezione-ora" }, [
      el("b", { testo: D.oraDi(l.inizio) }),
      el("span", { testo: D.oraDi(l.fine) }),
    ]),
    el("div", { classe: "lezione-corpo" }, [
      el("div", { classe: "lezione-titolo", testo: l.titolo }),
      el("div", { classe: "lezione-sotto" }, [
        conData ? el("span", { testo: `${cap(D.quandoRelativo(l.inizio))} · con ${l.istruttrice.nome}` }) : el("span", { testo: `con ${l.istruttrice.nome}` }),
      ]),
    ]),
    el("div", { classe: "lezione-stato" }, [
      l.annullata ? null : pallini(l.iscritte.length, D.POSTI),
      el("span", { classe: `etichetta ${s.classe}`, testo: s.testo }),
    ]),
  ]);
}

/** Il foglio di una lezione: prenota, lista d'attesa, disdici. */
function dettaglio(id, ridisegna) {
  const l = D.lezione(id);
  const io = D.io();
  const mia = l.iscritte.includes(io.id);
  const inAttesa = l.attesa.includes(io.id);
  const puoDisdire = D.disdicibile(l);
  const limite = new Date(l.inizio.getTime() - D.ORE_DISDETTA * 3600000);

  const azioni = [];
  const righe = [];

  if (l.annullata) {
    righe.push(riga("orologio", "Questa lezione è stata annullata dallo studio."));
  } else if (mia) {
    if (l.passata) {
      righe.push(riga("spunta", "Lezione fatta. Brava!"));
    } else if (puoDisdire) {
      righe.push(riga("orologio", `Puoi disdire fino a ${D.quandoRelativo(limite)} alle ${D.oraDi(limite)}.`));
      azioni.push(el("button", {
        classe: "bottone secondario largo", type: "button", testo: "Disdici la prenotazione",
        onclick: () => {
          D.disdici(id);
          f.chiudi();
          avviso("Prenotazione disdetta: la lezione torna nel tuo pacchetto", "ok");
          ridisegna();
        },
      }));
    } else {
      righe.push(riga("lucchetto", `Mancano meno di ${D.ORE_DISDETTA} ore: non è più possibile disdire. Per un'emergenza scrivi a ${l.istruttrice.nome}.`));
      azioni.push(bottoneWhatsApp(l.istruttrice, "secondario"));
    }
  } else if (!l.passata) {
    if (l.liberi > 0) {
      righe.push(riga("pacchetto", io.ingressi > 0
        ? `Userai 1 delle tue ${io.ingressi} lezioni.`
        : "Il tuo pacchetto è finito: puoi prenotare e pagare in studio."));
      righe.push(puoDisdire
        ? riga("orologio", `Disdetta gratuita fino a ${D.quandoRelativo(limite)} alle ${D.oraDi(limite)}.`)
        : riga("lucchetto", `Mancano meno di ${D.ORE_DISDETTA} ore: una volta prenotata, questa lezione non si potrà disdire.`));
      azioni.push(el("button", {
        classe: "bottone largo prenota", type: "button", testo: "Prenota",
        onclick: () => {
          try {
            D.prenota(id);
            f.chiudi();
            ridisegna();
            setTimeout(() => conferma(id), 200);
          } catch (e) {
            avviso(e.message);
          }
        },
      }));
    } else if (inAttesa) {
      righe.push(riga("lista", `Sei ${l.attesa.indexOf(io.id) + 1}ª in lista d'attesa. Se si libera un posto entri in automatico e ti avvisiamo.`));
      azioni.push(el("button", {
        classe: "bottone secondario largo", type: "button", testo: "Esci dalla lista d'attesa",
        onclick: () => { D.esciDallAttesa(id); f.chiudi(); ridisegna(); },
      }));
    } else {
      righe.push(riga("lista", l.attesa.length
        ? `La lezione è piena e ${l.attesa.length === 1 ? "c'è già 1 persona" : `ci sono già ${l.attesa.length} persone`} in attesa.`
        : "La lezione è piena. Mettiti in lista d'attesa: se qualcuna disdice, il posto è tuo."));
      azioni.push(el("button", {
        classe: "bottone largo attesa", type: "button", testo: "Mettiti in lista d'attesa",
        onclick: () => {
          const pos = D.mettiInAttesa(id);
          f.chiudi();
          avviso(`Sei ${pos}ª in lista d'attesa: ti avvisiamo se si libera un posto`, "ok");
          ridisegna();
        },
      }));
    }
  }

  const contenuto = el("div", { classe: "dettaglio" }, [
    el("div", { classe: "dettaglio-chi" }, [
      avatar(l.istruttrice.id, "medio"),
      el("div", {}, [
        el("div", { classe: "dettaglio-ora", testo: `${D.oraDi(l.inizio)} – ${D.oraDi(l.fine)}` }),
        el("div", { classe: "sotto", testo: `con ${l.istruttrice.nome} ${l.istruttrice.cognome}` }),
      ]),
    ]),
    l.annullata ? null : el("div", { classe: "reformer" }, [
      ...Array.from({ length: D.POSTI }, (_, i) => {
        const occupato = i < l.iscritte.length;
        const tuo = occupato && l.iscritte[i] === io.id;
        return el("div", { classe: `postazione ${occupato ? "occupata" : ""} ${tuo ? "tua" : ""}` }, [
          el("img", { src: "immagini/marchio.png", alt: "" }),
          el("span", { testo: tuo ? "Tu" : occupato ? "Occupato" : "Libero" }),
        ]);
      }),
    ]),
    ...righe,
    el("div", { classe: "azioni" }, azioni),
  ]);

  const f = foglio(contenuto, { titolo: l.titolo, sottotitolo: cap(D.dataLunga(l.inizio)) });
}

function riga(ic, testo) {
  return el("div", { classe: "riga-info" }, [icona(ic, "icona piccola"), el("span", { testo })]);
}

/** Dopo la prenotazione: la conferma, con il promemoria. */
function conferma(id) {
  const l = D.lezione(id);
  const io = D.io();
  const contenuto = el("div", { classe: "conferma" }, [
    el("div", { classe: "conferma-segno" }, [icona("spunta")]),
    el("h2", { testo: "Prenotata!" }),
    el("p", { classe: "conferma-quando", testo: `${cap(D.quandoRelativo(l.inizio))} alle ${D.oraDi(l.inizio)} con ${l.istruttrice.nome}` }),
    el("div", { classe: "conferma-righe" }, [
      riga("campana", "Ti mandiamo un promemoria il giorno prima."),
      riga("pacchetto", io.ingressi >= 0 ? `Ti restano ${io.ingressi} lezioni nel pacchetto.` : "Da saldare in studio alla lezione."),
    ]),
    el("button", { classe: "bottone largo", type: "button", testo: "Perfetto", onclick: () => f.chiudi() }),
  ]);
  const f = foglio(contenuto);
}

// ------------------------------------------------------------------- le mie
export function mie(ridisegna) {
  const { prossime, attesa, fatte } = D.lezioniDi();
  const sezione = (titolo, lista, vuoto) => el("section", { classe: "sezione" }, [
    el("h2", { classe: "titolo-sezione", testo: titolo }),
    lista.length
      ? el("div", { classe: "elenco-lezioni" }, lista.map((l) => schedaLezione(l, ridisegna, { conData: true })))
      : el("p", { classe: "vuoto", testo: vuoto }),
  ]);
  return el("div", { classe: "pagina" }, [
    sezione("In programma", prossime, "Nessuna lezione prenotata. Scegline una da Lezioni!"),
    attesa.length ? sezione("In lista d'attesa", attesa, "") : null,
    el("p", { classe: "nota", testo: `Si può disdire fino a ${D.ORE_DISDETTA} ore prima dell'inizio: la lezione torna nel pacchetto.` }),
    sezione("Già fatte", fatte.slice(0, 6), "Ancora nessuna: la prima è la più bella."),
  ]);
}

// ---------------------------------------------------------------- pacchetto
export function pacchetto() {
  const io = D.io();
  const { prossime } = D.lezioniDi();
  const scadenza = io.scadenza ? new Date(io.scadenza) : null;
  const acquisti = D.movimentiDi(io.id);
  return el("div", { classe: "pagina" }, [
    el("div", { classe: "tessera" }, [
      el("img", { src: "immagini/marchio.png", alt: "", classe: "tessera-marchio" }),
      el("div", { classe: "tessera-etichetta", testo: "Lezioni disponibili" }),
      el("div", { classe: "tessera-numero", testo: Math.max(io.ingressi, 0) }),
      el("div", { classe: "tessera-righe" }, [
        el("span", { testo: `${prossime.length} già prenotate` }),
        scadenza ? el("span", { testo: `Valide fino al ${scadenza.getDate()} ${D.MESI[scadenza.getMonth()]}` }) : el("span", { testo: "Nessun pacchetto attivo" }),
      ]),
      el("div", { classe: "tessera-nome", testo: `${io.nome} ${io.cognome}` }),
    ]),
    io.ingressi < 0 ? el("div", { classe: "riquadro avviso-riquadro", testo: `Hai ${-io.ingressi} lezione da saldare in studio.` }) : null,
    el("div", { classe: "riquadro paga" }, [
      icona("pacchetto"),
      el("div", {}, [
        el("b", { testo: "Si paga in studio" }),
        el("p", { testo: "Contanti o carta, prima della lezione. Greta o Elisa caricano il pacchetto e lo vedi subito qui." }),
      ]),
    ]),
    el("h2", { classe: "titolo-sezione", testo: "Listino" }),
    el("div", { classe: "listino" }, D.PACCHETTI.map((p) =>
      el("div", { classe: "voce-listino" }, [
        el("div", {}, [
          el("b", { testo: p.nome }),
          el("span", { testo: p.validita ? `Valido ${p.validita}` : p.id === "prova" ? "Per chi inizia" : "Una lezione" }),
        ]),
        el("div", { classe: "prezzo", testo: p.prezzo ? `€ ${p.prezzo}` : "€ —" }),
      ])
    )),
    el("p", { classe: "nota", testo: "I prezzi arrivano a breve." }),
    acquisti.length ? el("h2", { classe: "titolo-sezione", testo: "I tuoi acquisti" }) : null,
    ...acquisti.map((m) => {
      const p = D.PACCHETTI.find((x) => x.id === m.pacchetto);
      const d = new Date(m.quando);
      return el("div", { classe: "voce-listino" }, [
        el("div", {}, [el("b", { testo: p.nome }), el("span", { testo: `${d.getDate()} ${D.MESI[d.getMonth()]} · ${m.metodo}` })]),
      ]);
    }),
  ]);
}

// ----------------------------------------------------------------- contatti
export function bottoneWhatsApp(ist, tipo = "") {
  const testo = encodeURIComponent(`Ciao ${ist.nome}! `);
  return el("a", {
    classe: `bottone whatsapp ${tipo}`,
    href: `https://wa.me/${ist.telefono}?text=${testo}`,
    target: "_blank",
    rel: "noopener",
  }, [icona("chat", "icona piccola"), `Scrivi a ${ist.nome}`]);
}

export function contatti() {
  const giorni = { greta: "Lunedì · mercoledì · venerdì · sabato", elisa: "Martedì · giovedì" };
  return el("div", { classe: "pagina" }, [
    ...Object.values(D.ISTRUTTRICI).map((ist) =>
      el("div", { classe: "istruttrice" }, [
        avatar(ist.id, "grande"),
        el("div", { classe: "istruttrice-corpo" }, [
          el("h2", { testo: `${ist.nome} ${ist.cognome}` }),
          el("div", { classe: "sotto", testo: giorni[ist.id] }),
          el("div", { classe: "riga-bottoni" }, [
            bottoneWhatsApp(ist),
            el("a", { classe: "bottone secondario", href: `tel:+${ist.telefono}`, testo: ist.leggibile }),
          ]),
        ]),
      ])
    ),
    el("h2", { classe: "titolo-sezione", testo: "Orario delle lezioni" }),
    el("div", { classe: "orario" }, [1, 2, 3, 4, 5, 6].map((g) =>
      el("div", { classe: "orario-riga" }, [
        el("b", { testo: cap(D.GIORNI[g]) }),
        el("span", { testo: D.ORARIO[g].join(" · ") }),
        avatar(D.istruttriceDel(g).id, "mini"),
      ])
    )),
    el("h2", { classe: "titolo-sezione", testo: "Mettila sul telefono" }),
    el("div", { classe: "riquadro installa" }, [
      el("p", { html: "<b>iPhone</b>: apri in Safari, tocca <b>Condividi</b> e poi <b>Aggiungi alla schermata Home</b>." }),
      el("p", { html: "<b>Android</b>: apri in Chrome, tocca i <b>tre puntini</b> e poi <b>Installa app</b>." }),
    ]),
  ]);
}

// ---------------------------------------------------------------- notifiche
export function notifiche() {
  const elenco = D.notificheDi();
  setTimeout(() => D.segnaLette(), 1500);
  return el("div", { classe: "pagina" }, [
    elenco.length ? null : el("p", { classe: "vuoto", testo: "Nessuna notifica." }),
    ...elenco.map((n) => {
      const d = new Date(n.quando);
      return el("div", { classe: `notifica ${n.letta ? "" : "nuova"} ${n.tipo}` }, [
        n.tipo === "avviso"
          ? el("div", { classe: "notifica-avatar" }, [avatar("greta", "mini"), avatar("elisa", "mini")])
          : el("div", { classe: "notifica-icona" }, [icona("campana", "icona piccola")]),
        el("div", {}, [
          el("div", { classe: "notifica-da", testo: n.tipo === "avviso" ? `Avviso da ${n.da}` : "Per te" }),
          el("p", { testo: n.testo }),
          el("div", { classe: "sotto", testo: `${cap(D.quandoRelativo(d))} alle ${D.oraDi(d)}` }),
        ]),
      ]);
    }),
  ]);
}

// ----------------------------------------------------------------- vetrine
/** Le anteprime che Greta ed Elisa mostrano nella guida di benvenuto. */
export function vetrina(nome) {
  const finta = (ora, titolo, chi, occupati, extra = {}) => ({
    id: "vetrina", inizio: new Date(`2026-01-01T${ora}:00`), fine: new Date(`2026-01-01T${String(+ora.slice(0, 2) + 1).padStart(2, "0")}:${ora.slice(3)}:00`),
    istruttrice: D.ISTRUTTRICI[chi], titolo, iscritte: Array(occupati).fill("x"), attesa: [],
    liberi: D.POSTI - occupati, annullata: null, passata: false, ...extra,
  });
  const scheda = (l, stato) => {
    const s = stato || statoLezione(l, "nessuna");
    return el("div", { classe: `lezione ${s.classe}` }, [
      el("div", { classe: "lezione-ora" }, [el("b", { testo: D.oraDi(l.inizio) }), el("span", { testo: D.oraDi(l.fine) })]),
      el("div", { classe: "lezione-corpo" }, [
        el("div", { classe: "lezione-titolo", testo: l.titolo }),
        el("div", { classe: "lezione-sotto", testo: `con ${l.istruttrice.nome}` }),
      ]),
      el("div", { classe: "lezione-stato" }, [pallini(l.iscritte.length, D.POSTI), el("span", { classe: `etichetta ${s.classe}`, testo: s.testo })]),
    ]);
  };

  switch (nome) {
    case "calendario":
      return el("div", { classe: "vetrina-colonna" }, [
        el("div", { classe: "striscia finta" }, D.prossimiGiorni(5).map((g, i) =>
          el("div", { classe: `giorno ${i === 0 ? "scelto" : ""}` }, [
            el("span", { classe: "giorno-nome", testo: D.GIORNI_CORTI[g.getDay()] }),
            el("span", { classe: "giorno-num", testo: g.getDate() }),
          ]))),
        scheda(finta("16:30", "Reformer · Principianti", "greta", 1)),
        scheda(finta("17:30", "Reformer", "greta", 2)),
        scheda(finta("18:30", "Reformer · Total body", "greta", 3)),
      ]);
    case "istruttrici":
      return el("div", { classe: "orario vetrina-colonna" }, [1, 2, 3, 4, 5, 6].map((g) =>
        el("div", { classe: "orario-riga" }, [
          el("b", { testo: cap(D.GIORNI[g]) }),
          el("span", { testo: D.istruttriceDel(g).nome }),
          avatar(D.istruttriceDel(g).id, "mini"),
        ])));
    case "posti":
      return el("div", { classe: "vetrina-colonna" }, [
        scheda(finta("16:30", "Reformer", "elisa", 0)),
        scheda(finta("17:30", "Reformer", "elisa", 2)),
        scheda(finta("18:30", "Reformer", "elisa", 3)),
      ]);
    case "attesa":
      return el("div", { classe: "vetrina-colonna" }, [
        scheda(finta("18:30", "Reformer · Core e addome", "greta", 3), { classe: "attesa", testo: "In attesa · 1ª" }),
        el("div", { classe: "toast finto" }, [icona("campana", "icona piccola"), el("span", { testo: "Si è liberato un posto: sei dentro!" })]),
      ]);
    case "disdetta":
      return el("div", { classe: "vetrina-colonna" }, [
        scheda(finta("17:30", "Reformer", "elisa", 2), { classe: "mia", testo: "Prenotata" }),
        riga("orologio", `Puoi disdire fino a ${D.ORE_DISDETTA} ore prima.`),
        el("div", { classe: "bottone secondario largo", testo: "Disdici la prenotazione" }),
      ]);
    case "pacchetto":
      return el("div", { classe: "tessera piccola" }, [
        el("img", { src: "immagini/marchio.png", alt: "", classe: "tessera-marchio" }),
        el("div", { classe: "tessera-etichetta", testo: "Lezioni disponibili" }),
        el("div", { classe: "tessera-numero", testo: "8" }),
        el("div", { classe: "tessera-righe" }, [el("span", { testo: "Si paga in studio" })]),
      ]);
    default:
      return null;
  }
}

function cap(t) {
  return t ? t[0].toUpperCase() + t.slice(1) : t;
}
