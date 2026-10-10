// L'app: accesso, cornice (testata e barra in basso) e smistamento delle
// pagine. Le pagine stanno in viste/cliente.js e viste/studio.js.

import { el, icona, avviso, foglio } from "./ui.js";
import * as D from "./dati.js";
import { mostraGuida } from "./avatar.js";
import * as cliente from "./viste/cliente.js";
import * as studio from "./viste/studio.js";

const radice = document.getElementById("radice");
const PARAMETRI = new URLSearchParams(location.search);
// Nel video il selettore "Prototipo" non deve comparire.
const IN_VIDEO = PARAMETRI.has("video");

// Dove siamo. Si tiene qui e non solo nell'indirizzo: dentro una pagina
// pubblicata l'indirizzo non sempre si può cambiare.
let percorsoCorrente = (location.hash || "#/accesso").split("?")[0];

export function vai(href) {
  percorsoCorrente = href;
  try { history.replaceState(null, "", href); } catch { /* pazienza */ }
  disegna();
}

// I link interni (href="#/...") passano da vai().
document.addEventListener("click", (e) => {
  const a = e.target.closest?.('a[href^="#/"]');
  if (!a) return;
  e.preventDefault();
  vai(a.getAttribute("href"));
});

// Chi sta usando l'app in questo momento: una cliente o lo studio.
let ruolo = leggi("pilates-ruolo") || null; // "cliente" | "greta" | "elisa"

function leggi(chiave) {
  try { return sessionStorage.getItem(chiave); } catch { return null; }
}
function scrivi(chiave, valore) {
  try {
    if (valore === null) sessionStorage.removeItem(chiave);
    else sessionStorage.setItem(chiave, valore);
  } catch { /* pazienza */ }
}

export function entra(nuovo) {
  ruolo = nuovo;
  scrivi("pilates-ruolo", nuovo);
}

export function esci() {
  entra(null);
  vai("#/accesso");
}

// ------------------------------------------------------------------ accesso
function paginaAccesso() {
  return el("div", { classe: "accesso" }, [
    el("div", { classe: "accesso-marchio" }, [
      el("img", { src: "immagini/marchio.png", alt: "RE FORMER" }),
    ]),
    el("h1", { classe: "nome-studio", testo: "RE FORMER" }),
    el("p", { classe: "accesso-motto", testo: "Pilates reformer con Greta ed Elisa" }),
    el("form", {
      classe: "modulo",
      onsubmit: (e) => {
        e.preventDefault();
        D.entraComeDemo();
        entra("cliente");
        vai("#/lezioni");
      },
    }, [
      campo("Email", "email", "email", "sofia.marini@example.com"),
      campo("Password", "password", "password", "••••••••"),
      el("button", { classe: "bottone largo", type: "submit", testo: "Accedi" }),
      el("a", { classe: "link-piccolo", href: "#/accesso", testo: "Password dimenticata?" }),
    ]),
    el("div", { classe: "separatore" }, [el("span", { testo: "Prima volta qui?" })]),
    el("a", { classe: "bottone secondario largo", href: "#/registrati", testo: "Crea il tuo account" }),
    IN_VIDEO ? null : el("div", { classe: "accesso-studio" }, [
      el("div", { classe: "occhiello", testo: "Prototipo · accesso studio" }),
      el("div", { classe: "riga-bottoni" }, ["greta", "elisa"].map((chi) =>
        el("button", {
          classe: "bottone fantasma",
          type: "button",
          testo: `Entra come ${chi === "greta" ? "Greta" : "Elisa"}`,
          onclick: () => { entra(chi); vai("#/studio/oggi"); },
        })
      )),
    ]),
  ]);
}

function campo(etichetta, nome, tipo = "text", segnaposto = "", obbligatorio = false) {
  return el("label", { classe: "campo" }, [
    el("span", { testo: etichetta }),
    el("input", { name: nome, type: tipo, placeholder: segnaposto, required: obbligatorio, autocomplete: tipo === "password" ? "new-password" : nome }),
  ]);
}

function paginaRegistrati() {
  const modulo = el("form", {
    classe: "modulo",
    onsubmit: (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(modulo));
      const nuova = D.registra({
        nome: f.nome.trim(), cognome: f.cognome.trim(),
        telefono: f.telefono.trim(), email: f.email.trim(),
      });
      entra("cliente");
      vai("#/lezioni");
      benvenuto(nuova.nome);
    },
  }, [
    el("div", { classe: "riga-campi" }, [
      campo("Nome", "nome", "text", "Sofia", true),
      campo("Cognome", "cognome", "text", "Marini", true),
    ]),
    campo("Telefono", "telefono", "tel", "333 123 4567", true),
    campo("Email", "email", "email", "nome@email.it", true),
    campo("Password", "password", "password", "Almeno 8 caratteri", true),
    el("label", { classe: "spunta" }, [
      el("input", { type: "checkbox", name: "privacy", required: true }),
      el("span", { testo: "Ho letto l'informativa sulla privacy" }),
    ]),
    el("button", { classe: "bottone largo", type: "submit", testo: "Crea account" }),
  ]);
  return el("div", { classe: "accesso registrati" }, [
    el("a", { classe: "indietro", href: "#/accesso" }, [icona("indietro"), "Indietro"]),
    el("h1", { testo: "Crea il tuo account" }),
    el("p", { classe: "accesso-motto", testo: "Un minuto e puoi prenotare la tua prima lezione." }),
    modulo,
  ]);
}

// --------------------------------------------------------------- benvenuto
export const DISCORSO = [
  { testo: "Ciao {nome}! Ecco la nuova app di RE FORMER: da qui prenoti le tue lezioni in due tocchi." },
  { vetrina: "calendario", testo: "Qui trovi tutte le lezioni: dal lunedì al venerdì 16:30, 17:30 e 18:30, il sabato 11:30 e 12:30." },
  { vetrina: "istruttrici", testo: "Lunedì, mercoledì, venerdì e sabato c'è Greta. Martedì e giovedì c'è Elisa." },
  { vetrina: "posti", testo: "Ogni lezione ha 3 reformer. I pallini ti dicono quanti posti sono ancora liberi." },
  { vetrina: "attesa", testo: "Lezione piena? Mettiti in lista d'attesa: se si libera un posto entri tu, e ti avvisiamo." },
  { vetrina: "disdetta", testo: "Se non puoi venire, disdici fino a 12 ore prima: la lezione torna nel tuo pacchetto." },
  { vetrina: "pacchetto", testo: "Si paga sempre in studio. Qui vedi quante lezioni ti restano e fino a quando valgono." },
  { testo: "Per qualsiasi cosa scrivi a Greta o a Elisa su WhatsApp. Ci vediamo sul reformer!" },
];

export function benvenuto(nome) {
  mostraGuida(DISCORSO, {
    nome,
    vetrina: cliente.vetrina,
    invito: "Prenota la prima lezione",
    alTermine: () => disegna(),
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

function cornice(contenuto, { tab, titolo, sottotitolo, campanella }) {
  const percorso = percorsoCorrente;
  const nonLette = campanella ? D.nonLette() : 0;
  return el("div", { classe: `cornice ${ruolo === "cliente" ? "" : "studio"}` }, [
    el("header", { classe: "testata" }, [
      el("img", { src: "immagini/marchio.png", alt: "", classe: "testata-marchio" }),
      el("div", { classe: "testata-testo" }, [
        el("div", { classe: "testata-titolo", testo: titolo }),
        sottotitolo ? el("div", { classe: "testata-sotto", testo: sottotitolo }) : null,
      ]),
      campanella
        ? el("a", { classe: "tondo campanella", href: "#/avvisi", "aria-label": "Notifiche" }, [
            icona("campana"),
            nonLette ? el("b", { testo: nonLette }) : null,
          ])
        : el("button", { classe: "tondo", type: "button", "aria-label": "Esci", onclick: esci }, [icona("esci")]),
    ]),
    el("main", { classe: "contenuto" }, [contenuto]),
    el("nav", { classe: "tab" }, tab.map(([href, ic, nome]) =>
      el("a", { href, classe: percorso.startsWith(href) ? "attivo" : "" }, [icona(ic), el("span", { testo: nome })])
    )),
  ]);
}

/** Chiede conferma dentro la pagina: confirm() non sempre si vede. */
function ricominciaChiedendo() {
  const f = foglio(el("div", { classe: "dettaglio" }, [
    el("p", { testo: "Tutte le prenotazioni di prova tornano come all'inizio." }),
    el("div", { classe: "azioni" }, [
      el("button", {
        classe: "bottone largo", type: "button", testo: "Ricomincia",
        onclick: () => { f.chiudi(); D.ricomincia(); entra(null); vai("#/accesso"); },
      }),
      el("button", { classe: "bottone secondario largo", type: "button", testo: "Lascia com'è", onclick: () => f.chiudi() }),
    ]),
  ]), { titolo: "Rimettere il prototipo com'era?" });
}

/** Il selettore del prototipo: passa al volo da cliente a studio. */
function selettore() {
  if (IN_VIDEO || !ruolo) return null;
  const voci = [["cliente", "Cliente"], ["greta", "Greta"], ["elisa", "Elisa"]];
  return el("div", { classe: "prototipo" }, [
    el("span", { testo: "Prototipo" }),
    ...voci.map(([chi, nome]) =>
      el("button", {
        type: "button",
        classe: ruolo === chi ? "attivo" : "",
        testo: nome,
        onclick: () => {
          if (chi === "cliente") D.entraComeDemo();
          entra(chi);
          vai(chi === "cliente" ? "#/lezioni" : "#/studio/oggi");
        },
      })
    ),
    el("button", {
      type: "button", testo: "↺", title: "Ricomincia da capo",
      onclick: ricominciaChiedendo,    }),
  ]);
}

// ------------------------------------------------------------------- smista
export function disegna() {
  const percorso = percorsoCorrente.replace(/^#/, "") || "/accesso";
  const pezzi = percorso.split("/").filter(Boolean);
  let pagina;

  if (!ruolo || pezzi[0] === "accesso" || pezzi[0] === "registrati") {
    pagina = pezzi[0] === "registrati" ? paginaRegistrati() : paginaAccesso();
  } else if (ruolo === "cliente") {
    const io = D.io();
    if (!io) { esci(); return; }
    const pagine = {
      lezioni: () => cliente.lezioni(disegna),
      mie: () => cliente.mie(disegna),
      pacchetto: () => cliente.pacchetto(),
      contatti: () => cliente.contatti(),
      avvisi: () => cliente.notifiche(),
    };
    const titoli = {
      lezioni: ["Ciao " + io.nome, "Prenota il tuo reformer"],
      mie: ["Le mie lezioni", null],
      pacchetto: ["Il mio pacchetto", null],
      contatti: ["Greta ed Elisa", "Scrivici quando vuoi"],
      avvisi: ["Notifiche", null],
    };
    const chiave = pagine[pezzi[0]] ? pezzi[0] : "lezioni";
    const [titolo, sottotitolo] = titoli[chiave];
    pagina = cornice(pagine[chiave](), { tab: TAB_CLIENTE, titolo, sottotitolo, campanella: true });
  } else {
    const chi = D.ISTRUTTRICI[ruolo];
    const sezione = pezzi[1] || "oggi";
    const contenuto = studio.pagina(sezione, pezzi[2], { chi, ridisegna: disegna });
    pagina = cornice(contenuto, { tab: TAB_STUDIO, titolo: "Gestionale", sottotitolo: `Ciao ${chi.nome}` });
  }

  const scorrimento = window.scrollY;
  const stessaPagina = radice.dataset.percorso === percorso;
  radice.replaceChildren(...[selettore(), pagina].filter(Boolean));
  radice.dataset.percorso = percorso;
  window.scrollTo(0, stessaPagina ? scorrimento : 0);
}

window.addEventListener("hashchange", () => { percorsoCorrente = location.hash.split("?")[0]; disegna(); });
disegna();

// Si può aprire direttamente il benvenuto: utile per farlo vedere.
if (PARAMETRI.has("benvenuto") && ruolo === "cliente") benvenuto(D.io()?.nome);

// Per il video: lo script chiama queste da fuori.
window.prototipo = {
  benvenuto,
  avviso,
  // Nel video: Greta carica il pacchetto mentre la cliente guarda la pagina.
  simulaPagamento() {
    D.caricaPacchetto(D.io().id, "p10", "contanti");
    disegna();
  },
};
