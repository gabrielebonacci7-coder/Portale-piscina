// L'ossatura dell'app: accesso, cornice (testata e barra in basso) e
// smistamento delle pagine. Le pagine stanno in viste/cliente.js e
// viste/studio.js.
//
// Niente framework: le pagine sono funzioni (anche asincrone) che
// restituiscono un nodo, e il "router" è l'hash dell'indirizzo.

import * as api from "./api.js";
import { el, icona, avviso } from "./ui.js";
import { mostraGuida } from "./avatar.js";
import * as cliente from "./viste/cliente.js";
import * as studio from "./viste/studio.js";

const radice = document.getElementById("radice");

const stato = { info: null, io: null, daAccogliere: false };

export function vai(href) {
  if (location.hash === href) disegna();
  else location.hash = href;
}

export function esci() {
  api.esci();
  stato.io = null;
  vai("#/accesso");
}

api.quandoScade(() => {
  stato.io = null;
  avviso("Sessione scaduta, accedi di nuovo");
  vai("#/accesso");
});

// ------------------------------------------------------------------ moduli
function campo(etichetta, nome, tipo = "text", { segnaposto = "", obbligatorio = true, completamento, valore } = {}) {
  return el("label", { classe: "campo" }, [
    el("span", { testo: etichetta }),
    el("input", {
      name: nome, id: `campo-${nome}`, type: tipo, placeholder: segnaposto, required: obbligatorio,
      autocomplete: completamento || nome, value: valore,
    }),
  ]);
}

/** Un modulo che mostra l'errore sotto, e blocca il bottone mentre lavora. */
function modulo(figli, alInvio) {
  const errore = el("p", { classe: "errore", role: "alert" });
  const form = el("form", { classe: "modulo", novalidate: false }, [...figli, errore]);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const bottone = form.querySelector('button[type="submit"]');
    errore.textContent = "";
    bottone.disabled = true;
    try {
      await alInvio(Object.fromEntries(new FormData(form)));
    } catch (err) {
      errore.textContent = err.message || "Qualcosa non ha funzionato";
    } finally {
      bottone.disabled = false;
    }
  });
  return form;
}

function testata(titolo, motto) {
  return [
    el("div", { classe: "accesso-marchio" }, [el("img", { src: "immagini/marchio.png", alt: "RE FORMER" })]),
    el("h1", { classe: "nome-studio", testo: titolo }),
    el("p", { classe: "accesso-motto", testo: motto }),
  ];
}

// ------------------------------------------------------------------ accesso
function paginaAccesso() {
  return el("div", { classe: "accesso" }, [
    ...testata("RE FORMER", "Pilates reformer con Greta ed Elisa"),
    modulo([
      campo("Email", "email", "email", { segnaposto: "nome@email.it", completamento: "username" }),
      campo("Password", "password", "password", { completamento: "current-password" }),
      el("button", { classe: "bottone largo", type: "submit", testo: "Accedi" }),
      el("a", { classe: "link-piccolo", href: "#/recupero", testo: "Password dimenticata?" }),
    ], async (f) => {
      stato.io = await api.accedi(f.email, f.password);
      vai(stato.io.ruolo === "staff" ? "#/studio/oggi" : "#/lezioni");
    }),
    el("div", { classe: "separatore" }, [el("span", { testo: "Prima volta qui?" })]),
    el("a", { classe: "bottone secondario largo", href: "#/registrati", testo: "Crea il tuo account" }),
    el("a", { classe: "link-piccolo", href: "privacy.html", target: "_blank", testo: "Informativa sulla privacy" }),
  ]);
}

function paginaRegistrati() {
  return el("div", { classe: "accesso registrati" }, [
    el("a", { classe: "indietro", href: "#/accesso" }, [icona("indietro"), "Indietro"]),
    el("h1", { testo: "Crea il tuo account" }),
    el("p", { classe: "accesso-motto", testo: "Un minuto e puoi prenotare la tua lezione." }),
    modulo([
      el("div", { classe: "riga-campi" }, [
        campo("Nome", "nome", "text", { completamento: "given-name" }),
        campo("Cognome", "cognome", "text", { completamento: "family-name" }),
      ]),
      campo("Telefono", "telefono", "tel", { segnaposto: "333 123 4567", completamento: "tel" }),
      campo("Email", "email", "email", { segnaposto: "nome@email.it" }),
      campo("Password", "password", "password", { segnaposto: "Almeno 8 caratteri", completamento: "new-password" }),
      el("label", { classe: "spunta" }, [
        el("input", { type: "checkbox", name: "privacy", id: "campo-privacy", required: true }),
        el("span", {}, ["Ho letto l'", el("a", { href: "privacy.html", target: "_blank", testo: "informativa sulla privacy" })]),
      ]),
      el("button", { classe: "bottone largo", type: "submit", testo: "Crea account" }),
    ], async (f) => {
      stato.io = await api.registrati({ ...f, privacy: f.privacy === "on" });
      // La guida si apre quando la pagina delle lezioni è pronta (vedi
      // disegna): aprirla adesso vorrebbe dire chiuderla al cambio di pagina.
      stato.daAccogliere = true;
      vai("#/lezioni");
    }),
  ]);
}

function paginaRecupero() {
  const fatto = el("div");
  return el("div", { classe: "accesso registrati" }, [
    el("a", { classe: "indietro", href: "#/accesso" }, [icona("indietro"), "Indietro"]),
    el("h1", { testo: "Password dimenticata" }),
    el("p", { classe: "accesso-motto", testo: "Scrivi la tua email: ti mandiamo un link per sceglierne una nuova." }),
    modulo([
      campo("Email", "email", "email"),
      el("button", { classe: "bottone largo", type: "submit", testo: "Mandami il link" }),
    ], async (f) => {
      await api.recupero(f.email);
      fatto.replaceChildren(el("div", { classe: "riquadro" }, [
        el("p", { testo: "Se l'indirizzo è registrato, fra poco ti arriva una mail. Controlla anche nello spam." }),
      ]));
    }),
    fatto,
  ]);
}

function paginaNuovaPassword(codice) {
  return el("div", { classe: "accesso registrati" }, [
    el("h1", { testo: "Nuova password" }),
    modulo([
      campo("Nuova password", "password", "password", { segnaposto: "Almeno 8 caratteri", completamento: "new-password" }),
      el("button", { classe: "bottone largo", type: "submit", testo: "Salva e accedi" }),
    ], async (f) => {
      stato.io = await api.nuovaPassword(codice, f.password);
      avviso("Password cambiata", "ok");
      vai(stato.io.ruolo === "staff" ? "#/studio/oggi" : "#/lezioni");
    }),
  ]);
}

async function paginaConferma(codice) {
  try {
    stato.io = await api.conferma(codice);
    avviso(stato.io.ruolo === "staff" ? "Email confermata: benvenuta nel gestionale" : "Email confermata, grazie!", "ok");
    vai(stato.io.ruolo === "staff" ? "#/studio/oggi" : "#/lezioni");
    return el("div");
  } catch (e) {
    return el("div", { classe: "accesso registrati" }, [
      el("h1", { testo: "Link scaduto" }),
      el("p", { classe: "accesso-motto", testo: e.message }),
      el("a", { classe: "bottone largo", href: api.haToken() ? "#/profilo" : "#/accesso", testo: "Chiedine uno nuovo" }),
    ]);
  }
}

// --------------------------------------------------------------- benvenuto
const DISCORSO = [
  { testo: "Ciao {nome}! Ecco la nuova app di RE FORMER: da qui prenoti le tue lezioni in due tocchi." },
  { vetrina: "calendario", testo: "Qui trovi tutte le lezioni: dal lunedì al venerdì 15:30, 16:30 e 17:30, il sabato 11:30 e 12:30." },
  { vetrina: "istruttrici", testo: "Lunedì, mercoledì, venerdì e sabato c'è Greta. Martedì e giovedì c'è Elisa." },
  { vetrina: "posti", testo: "Ogni lezione ha 3 reformer. I pallini ti dicono quanti posti sono ancora liberi." },
  { vetrina: "attesa", testo: "Lezione piena? Mettiti in lista d'attesa: se si libera un posto entri tu, e ti avvisiamo." },
  { vetrina: "disdetta", testo: "Se non puoi venire, disdici fino a 12 ore prima: la lezione torna nel tuo pacchetto." },
  { vetrina: "pacchetto", testo: "Le lezioni si pagano in studio. Qui vedi quante te ne restano." },
  { testo: "Per qualsiasi dubbio chiedi a Greta o a Elisa in studio. Ci vediamo sul reformer!" },
];

export function benvenuto() {
  mostraGuida(DISCORSO, {
    nome: stato.io?.nome,
    vetrina: (nome) => cliente.vetrina(nome, stato.info),
    invito: "Prenota la tua lezione",
  });
}

// ------------------------------------------------------------------ cornice
const TAB_CLIENTE = [
  ["#/lezioni", "calendario", "Lezioni"],
  ["#/mie", "lista", "Le mie"],
  ["#/pacchetto", "pacchetto", "Pacchetto"],
  ["#/contatti", "chat", "Contatti"],
];
const TAB_STUDIO = [
  ["#/studio/oggi", "oggi", "Oggi"],
  ["#/studio/settimana", "calendario", "Settimana"],
  ["#/studio/clienti", "persone", "Clienti"],
  ["#/studio/avvisi", "megafono", "Avvisi"],
  ["#/studio/numeri", "grafico", "Numeri"],
];

let nonLette = 0;

async function aggiornaCampanella() {
  try {
    nonLette = (await api.notifiche()).non_lette;
  } catch { /* la campanella può aspettare */ }
  const b = document.querySelector(".campanella b");
  const c = document.querySelector(".campanella");
  if (!c) return;
  if (b) b.remove();
  if (nonLette) c.append(el("b", { testo: nonLette > 9 ? "9+" : nonLette }));
}

function cornice(contenuto, { titolo, sottotitolo, tab }) {
  const percorso = location.hash.split("?")[0];
  return el("div", { classe: `cornice ${stato.io.ruolo === "staff" ? "studio" : ""}` }, [
    el("header", { classe: "testata" }, [
      el("img", { src: "immagini/marchio.png", alt: "", classe: "testata-marchio" }),
      el("div", { classe: "testata-testo" }, [
        el("div", { classe: "testata-titolo", testo: titolo }),
        sottotitolo ? el("div", { classe: "testata-sotto", testo: sottotitolo }) : null,
      ]),
      el("a", { classe: "tondo campanella", href: "#/notifiche", "aria-label": "Notifiche" }, [
        icona("campana"),
        nonLette ? el("b", { testo: nonLette > 9 ? "9+" : nonLette }) : null,
      ]),
      el("a", { classe: "tondo", href: "#/profilo", "aria-label": "Il tuo profilo" }, [icona("persona")]),
    ]),
    el("main", { classe: "contenuto" }, [contenuto]),
    el("nav", { classe: "tab", "aria-label": "Sezioni" }, tab.map(([href, ic, nome]) =>
      el("a", { href, classe: percorso.startsWith(href) ? "attivo" : "", "aria-current": percorso.startsWith(href) ? "page" : null }, [
        icona(ic), el("span", { testo: nome }),
      ])
    )),
  ]);
}

function caricamento() {
  return el("div", { classe: "caricamento", role: "status" }, [el("i"), el("span", { testo: "Un attimo…" })]);
}

function erroreCaricamento(e) {
  return el("div", { classe: "vuoto" }, [
    el("p", { testo: e.message || "Non riesco a caricare i dati." }),
    el("button", { classe: "bottone secondario", type: "button", testo: "Riprova", onclick: () => disegna() }),
  ]);
}

// ------------------------------------------------------------------- smista
let giro = 0;

export async function disegna() {
  const mio = ++giro;
  const [, primo = "", secondo, terzo] = location.hash.replace(/^#/, "").split("?")[0].split("/");

  if (!stato.info) {
    try { stato.info = await api.info(); } catch { /* si riprova al prossimo giro */ }
  }

  // Pagine che non chiedono l'accesso.
  const libere = {
    accesso: paginaAccesso, registrati: paginaRegistrati, recupero: paginaRecupero,
    "nuova-password": () => paginaNuovaPassword(secondo), conferma: () => paginaConferma(secondo),
  };
  if (libere[primo] && !(primo === "accesso" && api.haToken() && stato.io)) {
    const nodo = await libere[primo]();
    if (mio === giro && nodo) mostra(nodo);
    return;
  }

  if (!api.haToken()) {
    vai("#/accesso");
    return;
  }
  if (!stato.io) {
    try {
      stato.io = await api.io();
    } catch (e) {
      if (e.stato !== 401) mostra(erroreCaricamento(e));
      return;
    }
  }
  const staff = stato.io.ruolo === "staff";
  const ctx = { info: stato.info, io: stato.io, ridisegna: disegna, vai, esci, aggiornaIo };

  let titolo, sottotitolo, pagina;
  if (primo === "studio" && staff) {
    titolo = "Gestionale";
    sottotitolo = `Ciao ${stato.io.nome}`;
    pagina = () => studio.pagina(secondo || "oggi", terzo, ctx);
  } else {
    const pagine = {
      lezioni: ["Ciao " + stato.io.nome, "Prenota il tuo reformer", () => cliente.lezioni(ctx)],
      mie: ["Le mie lezioni", null, () => cliente.mie(ctx)],
      pacchetto: ["Il mio pacchetto", null, () => cliente.pacchetto(ctx)],
      contatti: ["Greta ed Elisa", "Chi insegna e quando", () => cliente.contatti(ctx)],
      notifiche: ["Notifiche", null, () => cliente.notifiche(ctx)],
      profilo: ["Il tuo profilo", null, () => cliente.profilo(ctx)],
    };
    const chiave = pagine[primo] ? primo : staff ? null : "lezioni";
    if (!chiave) {
      vai("#/studio/oggi");
      return;
    }
    [titolo, sottotitolo, pagina] = pagine[chiave];
  }

  const tab = staff ? TAB_STUDIO : TAB_CLIENTE;
  const cornicePronta = cornice(caricamento(), { titolo, sottotitolo, tab });
  // La cornice compare subito; il contenuto arriva appena il server risponde.
  const stessa = radice.dataset.percorso === location.hash;
  const scorrimento = window.scrollY;
  if (!stessa) mostra(cornicePronta);
  let nodo;
  try {
    nodo = await pagina();
  } catch (e) {
    nodo = erroreCaricamento(e);
  }
  if (mio !== giro) return;
  const finale = cornice(nodo, { titolo, sottotitolo, tab });
  mostra(finale);
  if (stessa) window.scrollTo(0, scorrimento);
  aggiornaCampanella();
  if (stato.daAccogliere && !staff) {
    stato.daAccogliere = false;
    benvenuto();
  }
}

function mostra(nodo) {
  radice.replaceChildren(nodo);
  radice.dataset.percorso = location.hash;
}

async function aggiornaIo() {
  stato.io = await api.io();
  return stato.io;
}

window.addEventListener("hashchange", () => {
  window.scrollTo(0, 0);
  disegna();
});

// Tornando sull'app (dopo averla lasciata in background) i dati si
// rinfrescano: i posti liberi possono essere cambiati nel frattempo.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && api.haToken() && stato.io) disegna();
});

disegna();

// Il service worker rende l'app installabile e veloce da riaprire. Quando ne
// arriva una versione nuova lo si dice, invece di cambiare l'app sotto le dita.
if ("serviceWorker" in navigator) {
  // Alla prima visita il service worker prende il comando senza bisogno di
  // ricaricare: si ricarica solo quando sostituisce una versione precedente.
  const avevaVersione = Boolean(navigator.serviceWorker.controller);
  navigator.serviceWorker.register("sw.js").then((reg) => {
    reg.addEventListener("updatefound", () => {
      const nuovo = reg.installing;
      nuovo?.addEventListener("statechange", () => {
        if (nuovo.state === "installed" && navigator.serviceWorker.controller) {
          const barra = el("div", { classe: "aggiornamento", role: "status" }, [
            el("span", { testo: "C'è una versione nuova dell'app" }),
            el("button", {
              type: "button", testo: "Aggiorna",
              onclick: () => { nuovo.postMessage("aggiorna"); },
            }),
          ]);
          document.body.append(barra);
        }
      });
    });
  }).catch(() => { /* senza service worker l'app funziona lo stesso */ });
  // Quando la versione nuova prende il comando, si ricarica una volta sola.
  let ricaricata = false;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (ricaricata || !avevaVersione) return;
    ricaricata = true;
    location.reload();
  });
}
