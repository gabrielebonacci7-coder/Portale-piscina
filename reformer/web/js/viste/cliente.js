// Le pagine della cliente: lezioni, le mie, pacchetto, contatti, notifiche,
// profilo. Ogni pagina chiede al server quello che le serve e restituisce un
// nodo; dopo ogni azione si ridisegna con i dati freschi.

import * as api from "../api.js";
import { el, icona, avviso, foglio, pallini } from "../ui.js";
import { avatar } from "../avatar.js";
import * as T from "../tempo.js";

// Il giorno scelto e la vista restano mentre si naviga.
let giornoScelto = null;
let vista = "settimana";

const POSTI = (ctx) => ctx.info?.regole?.posti ?? 3;
const ORE_DISDETTA = (ctx) => ctx.info?.regole?.ore_disdetta ?? 12;

function statoLezione(l) {
  if (l.annullata) return { classe: "annullata", testo: "Annullata" };
  if (l.mia) return { classe: "mia", testo: "Prenotata" };
  if (l.passata) return { classe: "passata", testo: "Conclusa" };
  if (l.in_attesa) return { classe: "attesa", testo: `In attesa · ${l.in_attesa}ª` };
  if (l.liberi === 0) return { classe: "piena", testo: "Piena" };
  if (l.liberi === 1) return { classe: "ultimo", testo: "Ultimo posto" };
  return { classe: "libera", testo: `${l.liberi} posti liberi` };
}

function statoGiorno(lezioni) {
  const future = lezioni.filter((l) => !l.passata && !l.annullata);
  if (future.some((l) => l.mia)) return "mio";
  if (!future.length) return "vuoto";
  return future.some((l) => l.liberi > 0) ? "libero" : "pieno";
}

// ------------------------------------------------------------------ lezioni
export async function lezioni(ctx) {
  const tutte = (await api.lezioni(T.chiaveGiorno(T.oggi()), 31)).filter((l) => !l.passata && (l.prenotabile || l.mia));
  const perGiorno = new Map();
  for (const l of tutte) {
    const k = T.chiaveGiorno(T.data(l.inizio));
    if (!perGiorno.has(k)) perGiorno.set(k, []);
    perGiorno.get(k).push(l);
  }
  const giorni = [...perGiorno.keys()];
  if (!giorni.length) return el("p", { classe: "vuoto", testo: "Nessuna lezione in calendario." });
  if (!giornoScelto || !perGiorno.has(giornoScelto)) {
    giornoScelto = giorni.find((k) => perGiorno.get(k).some((l) => !l.passata)) || giorni[0];
  }
  const giorno = T.daChiave(giornoScelto);
  const delGiorno = perGiorno.get(giornoScelto);
  const ist = delGiorno[0].istruttrice;
  const scegli = (k) => { giornoScelto = k; ctx.ridisegna(); };

  return el("div", { classe: "pagina" }, [
    ctx.io.email_confermata ? null : avvisoConferma(),
    el("div", { classe: "vista-testa" }, [
      el("div", { classe: "vista-mese", testo: `${T.cap(T.MESI[giorno.getMonth()])} ${giorno.getFullYear()}` }),
      el("div", { classe: "segmentato", role: "group", "aria-label": "Vista" }, [["settimana", "Settimana"], ["mese", "Mese"]].map(([v, t]) =>
        el("button", {
          type: "button", classe: vista === v ? "attivo" : "", "aria-pressed": vista === v ? "true" : "false",
          "data-vista": v, testo: t, onclick: () => { vista = v; ctx.ridisegna(); },
        }))),
    ]),
    vista === "mese" ? calendarioMese(perGiorno, scegli) : striscia(perGiorno, scegli),
    el("div", { classe: "con-chi" }, [
      avatar(ist.id, "piccolo"),
      el("div", {}, [
        el("div", { classe: "con-chi-data", testo: T.cap(T.quandoRelativo(giorno)) + (T.quandoRelativo(giorno).includes(" ") ? "" : ` · ${T.dataLunga(giorno)}`) }),
        el("div", { classe: "con-chi-nome", html: `Lezioni con <b>${ist.nome}</b>` }),
      ]),
    ]),
    el("div", { classe: "elenco-lezioni" }, delGiorno.map((l) => schedaLezione(l, ctx))),
    el("p", { classe: "nota", testo: `Si prenota fino a un mese prima · ${POSTI(ctx)} reformer · disdetta fino a ${ORE_DISDETTA(ctx)} ore prima` }),
  ]);
}

function avvisoConferma() {
  const r = el("div", { classe: "riquadro nuove" }, [
    icona("campana"),
    el("div", {}, [
      el("b", { testo: "Conferma la tua email" }),
      el("p", { testo: "Ti abbiamo mandato un link: serve a ritrovare l'account se dimentichi la password." }),
      el("button", {
        classe: "link-piccolo", type: "button", testo: "Mandamelo di nuovo",
        onclick: async () => {
          try { await api.reinviaConferma(); avviso("Link mandato: controlla anche nello spam", "ok"); }
          catch (e) { avviso(e.message); }
        },
      }),
    ]),
  ]);
  return r;
}

function striscia(perGiorno, scegli) {
  const giorni = [...perGiorno.keys()];
  const nodo = el("div", { classe: "striscia", role: "tablist" }, giorni.flatMap((k, i) => {
    const g = T.daChiave(k);
    const s = statoGiorno(perGiorno.get(k));
    const scelto = k === giornoScelto;
    return [
      i > 0 && g.getDay() === 1 ? el("span", { classe: "striscia-stacco", "aria-hidden": "true" }) : null,
      el("button", {
        type: "button", role: "tab", "aria-selected": scelto ? "true" : "false",
        classe: `giorno ${scelto ? "scelto" : ""} ${s === "pieno" ? "pieno" : ""}`,
        "data-giorno": k, onclick: () => scegli(k),
      }, [
        el("span", { classe: "giorno-nome", testo: T.GIORNI_CORTI[g.getDay()] }),
        el("span", { classe: "giorno-num", testo: g.getDate() }),
        el("i", { classe: s === "mio" ? "segno mio" : s === "libero" ? "segno" : "segno nessuno" }),
      ]),
    ];
  }).filter(Boolean));
  requestAnimationFrame(() => nodo.querySelector(".scelto")?.scrollIntoView({ inline: "center", block: "nearest" }));
  return nodo;
}

function calendarioMese(perGiorno, scegli) {
  const giorni = [...perGiorno.keys()];
  const primo = T.daChiave(giorni[0]);
  const ultimo = T.daChiave(giorni[giorni.length - 1]);
  const d = T.piuGiorni(primo, -((primo.getDay() + 6) % 7)); // il lunedì
  const celle = [];
  let mesePrima = d.getMonth();
  for (; d <= ultimo || d.getDay() !== 1; d.setDate(d.getDate() + 1)) {
    if (d.getDay() === 0) continue; // la domenica lo studio è chiuso
    const k = T.chiaveGiorno(d);
    const attivo = perGiorno.has(k);
    const s = attivo ? statoGiorno(perGiorno.get(k)) : "fuori";
    celle.push(el("button", {
      type: "button", classe: `cella ${s} ${k === giornoScelto ? "scelta" : ""}`,
      disabled: attivo ? null : true, "data-giorno": k,
      "aria-label": `${T.dataLunga(d)}${attivo ? "" : ", non prenotabile"}`,
      onclick: () => scegli(k),
    }, [
      d.getMonth() !== mesePrima ? el("span", { classe: "cella-mese", testo: T.MESI[d.getMonth()].slice(0, 3) }) : null,
      el("span", { classe: "cella-num", testo: d.getDate() }),
      el("i"),
    ]));
    mesePrima = d.getMonth();
  }
  return el("div", { classe: "mese" }, [
    el("div", { classe: "mese-griglia" }, [
      ...[1, 2, 3, 4, 5, 6].map((n) => el("span", { classe: "mese-intestazione", testo: T.GIORNI_CORTI[n] })),
      ...celle,
    ]),
    el("div", { classe: "mese-legenda" }, [
      el("span", {}, [el("i", { classe: "libero" }), "posti liberi"]),
      el("span", {}, [el("i", { classe: "pieno" }), "tutto pieno"]),
      el("span", {}, [el("i", { classe: "mio" }), "prenotata"]),
    ]),
  ]);
}

export function schedaLezione(l, ctx, { conData = false } = {}) {
  const s = statoLezione(l);
  const inizio = T.data(l.inizio);
  const fine = T.data(l.fine);
  return el("button", {
    type: "button", classe: `lezione ${s.classe}`, "data-lezione": l.id,
    disabled: l.passata && !l.mia ? true : null,
    onclick: ctx ? () => dettaglio(l, ctx) : null,
  }, [
    el("div", { classe: "lezione-ora" }, [el("b", { testo: T.oraDi(inizio) }), el("span", { testo: T.oraDi(fine) })]),
    el("div", { classe: "lezione-corpo" }, [
      el("div", { classe: "lezione-titolo", testo: l.titolo }),
      el("div", { classe: "lezione-sotto" }, [
        avatar(l.istruttrice.id, "mini"),
        el("span", { testo: conData ? `${T.cap(T.quandoRelativo(inizio))} · con ${l.istruttrice.nome}` : `con ${l.istruttrice.nome}` }),
      ]),
    ]),
    el("div", { classe: "lezione-stato" }, [
      l.annullata ? null : pallini(l.occupati, l.posti),
      el("span", { classe: `etichetta ${s.classe}`, testo: s.testo }),
    ]),
  ]);
}

function riga(ic, testo) {
  return el("div", { classe: "riga-info" }, [icona(ic, "icona piccola"), el("span", { testo })]);
}

/** Esegue un'azione dal foglio: blocca il bottone, mostra l'errore. */
async function agisci(bottone, azione) {
  bottone.disabled = true;
  try {
    await azione();
  } catch (e) {
    avviso(e.message);
    bottone.disabled = false;
  }
}

function dettaglio(l, ctx) {
  const inizio = T.data(l.inizio);
  const limite = T.data(l.limite_disdetta);
  const rimaste = ctx.io.lezioni_rimaste;
  const azioni = [];
  const righe = [];
  const bottone = (testo, classe, azione) => {
    const b = el("button", { classe: `bottone largo ${classe}`, type: "button", testo });
    b.addEventListener("click", () => agisci(b, azione));
    return b;
  };

  if (l.annullata) {
    righe.push(riga("orologio", `Lezione annullata dallo studio${l.motivo_annullamento ? `: ${l.motivo_annullamento}` : ""}.`));
  } else if (l.mia) {
    if (l.passata) {
      righe.push(riga("spunta", "Lezione fatta. Brava!"));
    } else if (l.disdicibile) {
      righe.push(riga("orologio", `Puoi disdire fino a ${T.quando(limite)}.`));
      azioni.push(bottone("Disdici la prenotazione", "secondario", async () => {
        const r = await api.disdici(l.id);
        ctx.io.lezioni_rimaste = r.utente.lezioni_rimaste;
        f.chiudi();
        avviso("Prenotazione disdetta: la lezione torna nel tuo pacchetto", "ok");
        ctx.ridisegna();
      }));
    } else {
      righe.push(riga("lucchetto", `Mancano meno di ${ORE_DISDETTA(ctx)} ore: non è più possibile disdire. Per un'emergenza avvisa ${l.istruttrice.nome}.`));
    }
  } else if (!l.passata && rimaste <= 0 && !l.in_attesa) {
    // A pacchetto finito non si prenota: si rinnova in studio.
    righe.push(riga("pacchetto", "Hai finito le lezioni del pacchetto: rinnovalo in studio con Greta o Elisa e poi potrai prenotare."));
  } else if (!l.passata) {
    if (l.liberi > 0) {
      righe.push(riga("pacchetto", `Userai 1 delle tue ${rimaste} lezioni.`));
      righe.push(l.disdicibile
        ? riga("orologio", `Disdetta gratuita fino a ${T.quando(limite)}.`)
        : riga("lucchetto", `Mancano meno di ${ORE_DISDETTA(ctx)} ore: una volta prenotata, questa lezione non si potrà disdire.`));
      azioni.push(bottone("Prenota", "prenota", async () => {
        const r = await api.prenota(l.id);
        ctx.io.lezioni_rimaste = r.utente.lezioni_rimaste;
        f.chiudi();
        ctx.ridisegna();
        setTimeout(() => conferma(r.lezione, ctx), 220);
      }));
    } else if (l.in_attesa) {
      righe.push(riga("lista", `Sei ${l.in_attesa}ª in lista d'attesa. Se si libera un posto entri in automatico e ti avvisiamo.`));
      azioni.push(bottone("Esci dalla lista d'attesa", "secondario", async () => {
        await api.esciDallAttesa(l.id);
        f.chiudi();
        ctx.ridisegna();
      }));
    } else {
      righe.push(riga("lista", l.attesa_quante
        ? `La lezione è piena e ${l.attesa_quante === 1 ? "c'è già 1 persona" : `ci sono già ${l.attesa_quante} persone`} in attesa.`
        : "La lezione è piena. Mettiti in lista d'attesa: se qualcuna disdice, il posto è tuo."));
      azioni.push(bottone("Mettiti in lista d'attesa", "attesa", async () => {
        const r = await api.entraInAttesa(l.id);
        f.chiudi();
        avviso(`Sei ${r.posizione}ª in lista d'attesa: ti avvisiamo se si libera un posto`, "ok");
        ctx.ridisegna();
      }));
    }
  }

  const contenuto = el("div", { classe: "dettaglio" }, [
    el("div", { classe: "dettaglio-chi" }, [
      avatar(l.istruttrice.id, "medio"),
      el("div", {}, [
        el("div", { classe: "dettaglio-ora", testo: `${T.oraDi(inizio)} – ${T.oraDi(T.data(l.fine))}` }),
        el("div", { classe: "sotto", testo: `con ${l.istruttrice.nome} ${l.istruttrice.cognome}` }),
      ]),
    ]),
    l.annullata ? null : el("div", { classe: "reformer" }, Array.from({ length: l.posti }, (_, i) => {
      // I posti si contano, non si nominano: la tua è la prima casella.
      const tuo = l.mia && i === 0;
      const occupato = i < l.occupati;
      return el("div", { classe: `postazione ${occupato ? "occupata" : ""} ${tuo ? "tua" : ""}` }, [
        el("img", { src: "immagini/marchio.png", alt: "" }),
        el("span", { testo: tuo ? "Tu" : occupato ? "Occupato" : "Libero" }),
      ]);
    })),
    ...righe,
    el("div", { classe: "azioni" }, azioni),
  ]);
  const f = foglio(contenuto, { titolo: l.titolo, sottotitolo: T.cap(T.dataLunga(inizio)) });
}

function conferma(l, ctx) {
  const inizio = T.data(l.inizio);
  const rimaste = ctx.io.lezioni_rimaste;
  const f = foglio(el("div", { classe: "conferma" }, [
    el("div", { classe: "conferma-segno" }, [icona("spunta")]),
    el("h2", { testo: "Prenotata!" }),
    el("p", { classe: "conferma-quando", testo: `${T.cap(T.quando(inizio))} con ${l.istruttrice.nome}` }),
    el("div", { classe: "conferma-righe" }, [
      riga("campana", "Ti mandiamo un promemoria il giorno prima."),
      riga("pacchetto", rimaste >= 0 ? `Ti restano ${rimaste} lezioni nel pacchetto.` : "Da saldare in studio alla lezione."),
    ]),
    el("button", { classe: "bottone largo", type: "button", testo: "Perfetto", onclick: () => f.chiudi() }),
  ]));
}

// ------------------------------------------------------------------- le mie
export async function mie(ctx) {
  const { prossime, attesa } = await api.mie();
  const sezione = (titolo, lista, vuoto) => el("section", { classe: "sezione" }, [
    el("h2", { classe: "titolo-sezione", testo: titolo }),
    lista.length
      ? el("div", { classe: "elenco-lezioni" }, lista.map((l) => schedaLezione(l, ctx, { conData: true })))
      : el("p", { classe: "vuoto", testo: vuoto }),
  ]);
  return el("div", { classe: "pagina" }, [
    sezione("In programma", prossime, "Nessuna lezione prenotata. Scegline una da Lezioni!"),
    attesa.length ? sezione("In lista d'attesa", attesa, "") : null,
    el("p", { classe: "nota", testo: `Si può disdire fino a ${ORE_DISDETTA(ctx)} ore prima dell'inizio: la lezione torna nel pacchetto.` }),
  ]);
}

// ---------------------------------------------------------------- pacchetto
export async function pacchetto(ctx) {
  const p = await api.pacchetto();
  ctx.io.lezioni_rimaste = p.lezioni_rimaste;
  const { prossime } = await api.mie();
  const scadenza = p.scadenza ? T.daChiave(p.scadenza) : null;
  return el("div", { classe: "pagina" }, [
    el("div", { classe: "tessera" }, [
      el("img", { src: "immagini/marchio.png", alt: "", classe: "tessera-marchio" }),
      el("div", { classe: "tessera-etichetta", testo: "Lezioni disponibili" }),
      el("div", { classe: "tessera-numero", testo: Math.max(p.lezioni_rimaste, 0) }),
      el("div", { classe: "tessera-righe" }, [
        el("span", { testo: `${prossime.length} già prenotate` }),
        scadenza ? el("span", { testo: `Valide fino al ${T.dataBreve(scadenza)}` }) : null,
      ]),
      el("div", { classe: "tessera-nome", testo: `${ctx.io.nome} ${ctx.io.cognome}` }),
    ]),
    p.lezioni_rimaste === 0
      ? el("div", { classe: "riquadro avviso-riquadro", testo: "Pacchetto finito: rinnovalo in studio con Greta o Elisa per prenotare di nuovo." })
      : null,
    p.lezioni_rimaste < 0
      ? el("div", { classe: "riquadro avviso-riquadro", testo: `Hai ${-p.lezioni_rimaste} ${p.lezioni_rimaste === -1 ? "lezione" : "lezioni"} da saldare in studio.` })
      : null,
    el("div", { classe: "riquadro paga" }, [
      icona("pacchetto"),
      el("div", {}, [
        el("b", { testo: "Si paga in studio" }),
        el("p", { testo: "Greta o Elisa caricano le tue lezioni sul tuo account e le vedi subito qui." }),
      ]),
    ]),
    p.movimenti.length ? el("h2", { classe: "titolo-sezione", testo: "Movimenti" }) : null,
    p.movimenti.length ? el("div", { classe: "listino" }, p.movimenti.map((m) => {
      const d = T.data(m.quando);
      return el("div", { classe: "voce-listino" }, [
        el("div", {}, [el("b", { testo: m.motivo }), el("span", { testo: `${T.dataBreve(d)} · saldo ${m.saldo}` })]),
        el("div", { classe: `quante ${m.variazione < 0 ? "meno" : ""}`, testo: m.variazione > 0 ? `+${m.variazione}` : `${m.variazione}` }),
      ]);
    })) : null,
  ]);
}

// ----------------------------------------------------------------- contatti
export function contatti(ctx) {
  const giorni = { greta: "Lunedì · mercoledì · sabato", elisa: "Martedì · giovedì · venerdì" };
  const orario = ctx.info?.orario || [];
  return el("div", { classe: "pagina" }, [
    ...(ctx.info?.istruttrici || []).map((ist) =>
      el("div", { classe: "istruttrice" }, [
        avatar(ist.id, "grande"),
        el("div", { classe: "istruttrice-corpo" }, [
          el("h2", { testo: `${ist.nome} ${ist.cognome}` }),
          el("div", { classe: "sotto", testo: giorni[ist.id] }),
        ]),
      ])),
    el("h2", { classe: "titolo-sezione", testo: "Orario delle lezioni" }),
    el("div", { classe: "orario" }, orario.map((g) =>
      el("div", { classe: "orario-riga" }, [
        el("b", { testo: T.cap(g.nome) }),
        el("span", { testo: g.ore.join(" · ") }),
        avatar(g.istruttrice, "mini"),
      ]))),
    el("h2", { classe: "titolo-sezione", testo: "Mettila sul telefono" }),
    el("div", { classe: "riquadro installa" }, [
      el("p", { html: "<b>iPhone</b>: apri in Safari, tocca <b>Condividi</b> e poi <b>Aggiungi alla schermata Home</b>." }),
      el("p", { html: "<b>Android</b>: apri in Chrome, tocca i <b>tre puntini</b> e poi <b>Installa app</b>." }),
    ]),
  ]);
}

// ---------------------------------------------------------------- notifiche
export async function notifiche() {
  const { elenco } = await api.notifiche();
  if (elenco.some((n) => !n.letta)) setTimeout(() => api.segnaLette().catch(() => {}), 1200);
  return el("div", { classe: "pagina" }, [
    elenco.length ? null : el("p", { classe: "vuoto", testo: "Nessuna notifica." }),
    ...elenco.map((n) => {
      const d = T.data(n.quando);
      return el("div", { classe: `notifica ${n.letta ? "" : "nuova"}` }, [
        el("div", { classe: "notifica-icona" }, [icona(n.tipo === "avviso" ? "megafono" : "campana", "icona piccola")]),
        el("div", {}, [
          el("div", { classe: "notifica-da", testo: n.tipo === "avviso" ? `Avviso da ${n.da}` : "Per te" }),
          el("p", { testo: n.testo }),
          el("div", { classe: "sotto", testo: T.cap(T.quando(d)) }),
        ]),
      ]);
    }),
  ]);
}

// ------------------------------------------------------------------ profilo
export function profilo(ctx) {
  const io = ctx.io;
  const dati = el("form", { classe: "modulo riquadro" }, [
    el("h3", { testo: "I tuoi dati" }),
    el("div", { classe: "riga-campi" }, [
      campo("Nome", "nome", io.nome), campo("Cognome", "cognome", io.cognome),
    ]),
    campo("Telefono", "telefono", io.telefono, "tel"),
    el("p", { classe: "sotto", testo: `Email: ${io.email}${io.email_confermata ? "" : " (da confermare)"}` }),
    el("button", { classe: "bottone", type: "submit", testo: "Salva" }),
  ]);
  dati.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      Object.assign(ctx.io, await api.modificaIo(Object.fromEntries(new FormData(dati))));
      avviso("Dati salvati", "ok");
    } catch (err) { avviso(err.message); }
  });

  const pwd = el("form", { classe: "modulo riquadro" }, [
    el("h3", { testo: "Cambia password" }),
    campo("Password attuale", "attuale", "", "password"),
    campo("Nuova password", "nuova", "", "password"),
    el("button", { classe: "bottone secondario", type: "submit", testo: "Cambia password" }),
  ]);
  pwd.addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(pwd));
    try {
      await api.cambiaPassword(f.attuale, f.nuova);
      pwd.reset();
      avviso("Password cambiata: gli altri telefoni dovranno rientrare", "ok");
    } catch (err) { avviso(err.message); }
  });

  const zonaCancella = el("div", { classe: "annulla" });
  const mostraCancella = () => zonaCancella.replaceChildren(el("button", {
    classe: "link-piccolo", type: "button", testo: "Cancella il mio account",
    onclick: () => {
      const conferma = el("input", { type: "password", id: "campo-conferma-cancella", placeholder: "La tua password" });
      zonaCancella.replaceChildren(
        el("p", { classe: "sotto", testo: "Le prenotazioni future vengono liberate e i tuoi dati personali cancellati. Le lezioni rimaste nel pacchetto si perdono: parlane prima con lo studio." }),
        el("label", { classe: "campo" }, [el("span", { testo: "Scrivi la password per confermare" }), conferma]),
        el("div", { classe: "riga-bottoni" }, [
          el("button", { classe: "bottone secondario", type: "button", testo: "Lascia stare", onclick: mostraCancella }),
          el("button", {
            classe: "bottone conferma-annulla", type: "button", testo: "Cancella",
            onclick: async () => {
              try { await api.cancellaAccount(conferma.value); avviso("Account cancellato"); ctx.esci(); }
              catch (err) { avviso(err.message); }
            },
          }),
        ]),
      );
    },
  }));
  mostraCancella();

  return el("div", { classe: "pagina" }, [
    io.email_confermata ? null : avvisoConferma(),
    dati,
    pwd,
    el("div", { classe: "riquadro" }, [
      el("h3", { testo: "Privacy" }),
      el("a", { href: "privacy.html", target: "_blank", testo: "Leggi l'informativa" }),
      el("button", {
        classe: "link-piccolo", type: "button", testo: "Scarica i miei dati",
        onclick: async () => {
          try {
            const dati = await api.esporta();
            const blob = new Blob([JSON.stringify(dati, null, 2)], { type: "application/json" });
            const a = el("a", { href: URL.createObjectURL(blob), download: "i-miei-dati-reformer.json" });
            document.body.append(a); a.click(); a.remove();
          } catch (err) { avviso(err.message); }
        },
      }),
      // Gli account dello staff non si cancellano da qui (il server lo rifiuta).
      io.ruolo === "staff" ? null : zonaCancella,
    ]),
    el("button", { classe: "bottone secondario largo", type: "button", testo: "Esci", onclick: () => ctx.esci() }),
  ]);
}

function campo(etichetta, nome, valore, tipo = "text") {
  return el("label", { classe: "campo" }, [
    el("span", { testo: etichetta }),
    el("input", { name: nome, id: `profilo-${nome}`, value: valore, type: tipo, required: true }),
  ]);
}

// ----------------------------------------------------------------- vetrine
/** Le anteprime della guida di benvenuto: dati finti ma schede vere. */
export function vetrina(nome, info) {
  const ist = (id) => info?.istruttrici?.find((i) => i.id === id) || { id, nome: id === "greta" ? "Greta" : "Elisa" };
  const finta = (ora, titolo, chi, occupati, extra = {}) => {
    const inizio = new Date(`2026-01-05T${ora}:00`);
    return {
      id: 0, inizio: inizio.toISOString(), fine: new Date(inizio.getTime() + 3600000).toISOString(),
      istruttrice: ist(chi), titolo, posti: 3, occupati, liberi: 3 - occupati,
      annullata: false, passata: false, mia: false, in_attesa: null, ...extra,
    };
  };
  switch (nome) {
    case "calendario": {
      const giorni = [];
      for (let d = T.oggi(); giorni.length < 5; d = T.piuGiorni(d, 1)) if (d.getDay() !== 0) giorni.push(d);
      return el("div", { classe: "vetrina-colonna" }, [
        el("div", { classe: "striscia finta" }, giorni.map((g, i) =>
          el("div", { classe: `giorno ${i === 0 ? "scelto" : ""}` }, [
            el("span", { classe: "giorno-nome", testo: T.GIORNI_CORTI[g.getDay()] }),
            el("span", { classe: "giorno-num", testo: g.getDate() }),
          ]))),
        schedaLezione(finta("15:30", "Pilates", "greta", 1)),
        schedaLezione(finta("16:30", "Pilates fitness", "greta", 2)),
        schedaLezione(finta("17:30", "Pilates", "greta", 3)),
      ]);
    }
    case "istruttrici":
      return el("div", { classe: "orario vetrina-colonna" }, (info?.orario || []).map((g) =>
        el("div", { classe: "orario-riga" }, [
          el("b", { testo: T.cap(g.nome) }),
          el("span", { testo: ist(g.istruttrice).nome }),
          avatar(g.istruttrice, "mini"),
        ])));
    case "posti":
      return el("div", { classe: "vetrina-colonna" }, [
        schedaLezione(finta("16:30", "Pilates", "elisa", 0)),
        schedaLezione(finta("17:30", "Pilates", "elisa", 2)),
        schedaLezione(finta("18:30", "Pilates", "elisa", 3)),
      ]);
    case "attesa":
      return el("div", { classe: "vetrina-colonna" }, [
        schedaLezione(finta("18:30", "Pilates", "greta", 3, { in_attesa: 1 })),
        el("div", { classe: "toast finto" }, [icona("campana", "icona piccola"), el("span", { testo: "Si è liberato un posto: sei dentro!" })]),
      ]);
    case "disdetta":
      return el("div", { classe: "vetrina-colonna" }, [
        schedaLezione(finta("17:30", "Pilates", "elisa", 2, { mia: true })),
        riga("orologio", "Puoi disdire fino a 12 ore prima."),
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
