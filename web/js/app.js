// Guscio dell'app: decide cosa mostrare (accesso, creazione profilo o
// applicazione) e gestisce la navigazione fra le schede.

import { quandoScade } from "./api.js";
import { caricaSessione, ePiscina, eStaff, haProfilo, stato } from "./stato.js";
import { ICONE, avviso, brindisi, el, svuota } from "./ui.js";
import { api } from "./api.js";
import { vistaAccesso, vistaCreaProfilo, vistaReimposta } from "./viste/accesso.js";
import { apriFiltri, contaFiltriAttivi, vistaBacheca } from "./viste/bacheca.js";
import { vistaBagnini } from "./viste/bagnini.js";
import { vistaCandidature } from "./viste/candidature.js";
import { vistaMessaggi } from "./viste/messaggi.js";
import { apriPubblica } from "./viste/pubblica.js";
import { vistaProfilo } from "./viste/profilo.js";
import { vistaStaff } from "./viste/staff.js";

const radice = document.getElementById("radice");

// `sotto` distingue le due sezioni della bacheca (turni / bagnini).
let schedaCorrente = "bacheca";
let sotto = "turni";
let vistaViva = null; // per poterla ricaricare senza ricostruire tutto

const navigazione = {
  vai(scheda) {
    schedaCorrente = scheda;
    disegnaApp();
  },
  allAccesso() {
    avvia();
  },
  aggiornaPallini() {
    const pallino = document.querySelector('[data-scheda="messaggi"] .pallino');
    if (pallino) {
      pallino.textContent = stato.nonLetti > 99 ? "99+" : String(stato.nonLetti);
      pallino.hidden = stato.nonLetti === 0;
    }
  },
};

// Se il token scade mentre si naviga, si torna all'accesso senza schermate rotte.
quandoScade(() => {
  if (stato.utente) {
    stato.utente = null;
    avvia();
  }
});

// ---------- Definizione delle schede ----------
function schede() {
  return [
    { id: "bacheca", nome: "Bacheca", icona: ICONE.bacheca },
    {
      id: "candidature",
      nome: ePiscina() ? "I miei turni" : "Candidature",
      icona: ICONE.candidature,
    },
    { id: "messaggi", nome: "Messaggi", icona: ICONE.messaggi, pallino: true },
    // La scheda in più di chi gestisce la piattaforma. Nasconderla non è una
    // misura di sicurezza — quella sta nel backend — ma toglie di mezzo una
    // sezione che al 99% degli iscritti non serve.
    eStaff() && { id: "staff", nome: "Gestione", icona: ICONE.gestione },
    { id: "profilo", nome: "Profilo", icona: ICONE.profilo },
  ].filter(Boolean);
}

function titoloScheda() {
  return {
    bacheca: sotto === "turni" ? "Bacheca" : "Bagnini",
    candidature: ePiscina() ? "I miei turni" : "Le mie candidature",
    messaggi: "Messaggi",
    staff: "Gestione",
    profilo: "Profilo",
  }[schedaCorrente];
}

// ---------- Disegno ----------
function disegnaApp() {
  svuota(radice);

  const barra = el("header", { classe: "barra" }, [el("h1", { testo: titoloScheda() })]);
  const contenuto = el("main", { classe: "contenuto" });

  // Azioni contestuali nella barra in alto.
  if (schedaCorrente === "bacheca" && sotto === "turni") {
    const attivi = contaFiltriAttivi();
    barra.append(
      el("button", {
        classe: "btn-icona",
        "aria-label": attivi ? `Filtri (${attivi} attivi)` : "Filtri",
        html: ICONE.filtro,
        style: attivi ? "color:var(--accent)" : "",
        onclick: () => apriFiltri(() => ricaricaVista()),
      }),
    );
  }

  const puoPubblicare =
    (schedaCorrente === "bacheca" && sotto === "turni") || schedaCorrente === "candidature";
  if (puoPubblicare) {
    barra.append(
      el("button", {
        classe: "btn-icona",
        "aria-label": "Pubblica un annuncio",
        html: ICONE.piu,
        style: "color:var(--accent)",
        onclick: () => apriPubblica(() => ricaricaVista()),
      }),
    );
  }

  // Nella bacheca si passa fra turni e bagnini con un segmentato.
  if (schedaCorrente === "bacheca") {
    const segmenti = el("div", { classe: "segmenti" });
    for (const [valore, testo] of [
      ["turni", "Turni"],
      ["bagnini", "Bagnini"],
    ]) {
      segmenti.append(
        el("button", {
          type: "button",
          testo,
          "aria-pressed": sotto === valore,
          onclick: () => {
            sotto = valore;
            disegnaApp();
          },
        }),
      );
    }
    contenuto.append(segmenti);
  }

  vistaViva = costruisciVista();
  contenuto.append(vistaViva);

  radice.append(barra, contenuto, barraSchede());
  navigazione.aggiornaPallini();
}

function costruisciVista() {
  switch (schedaCorrente) {
    case "bacheca":
      return sotto === "turni" ? vistaBacheca(navigazione) : vistaBagnini(navigazione);
    case "candidature":
      return vistaCandidature(navigazione);
    case "messaggi":
      return vistaMessaggi(navigazione);
    case "staff":
      return vistaStaff(navigazione);
    case "profilo":
      return vistaProfilo(navigazione);
    default:
      return el("div");
  }
}

function ricaricaVista() {
  vistaViva?.ricarica?.();
}

function barraSchede() {
  const nav = el("nav", { classe: "tabs", "aria-label": "Sezioni" });
  for (const s of schede()) {
    const bottone = el(
      "button",
      {
        classe: "tab",
        "data-scheda": s.id,
        "aria-current": schedaCorrente === s.id ? "page" : null,
        onclick: () => navigazione.vai(s.id),
      },
      [el("span", { html: s.icona }).firstChild, el("span", { testo: s.nome })],
    );
    if (s.pallino) {
      bottone.append(
        el("span", { classe: "pallino", hidden: stato.nonLetti === 0, testo: String(stato.nonLetti) }),
      );
    }
    nav.append(bottone);
  }
  return nav;
}

// ---------- Link arrivati per email ----------
/** Legge il codice dall'indirizzo e lo toglie dalla barra.

    I link nelle email puntano a `/?recupero=CODICE` o `/?verifica=CODICE`.
    Il codice va tolto subito dall'indirizzo: resterebbe nella cronologia del
    telefono e in quello che si condivide per sbaglio. */
function codiceDaIndirizzo() {
  const parametri = new URLSearchParams(location.search);
  for (const azione of ["recupero", "verifica"]) {
    const codice = parametri.get(azione);
    if (codice) {
      history.replaceState(null, "", location.pathname);
      return { azione, codice };
    }
  }
  return null;
}

async function confermaEmail(codice) {
  svuota(radice);
  const contenitore = el("div", { classe: "accesso" });
  radice.append(contenitore);
  try {
    await api.verificaEmail(codice);
    brindisi("Indirizzo confermato");
  } catch (e) {
    contenitore.append(avviso(e.dettaglio));
    // Si lascia leggere l'errore prima di passare oltre.
    await new Promise((r) => setTimeout(r, 2600));
  }
}

// ---------- Avvio ----------
async function avvia() {
  svuota(radice);
  radice.append(el("div", { classe: "caricamento", testo: "Caricamento…" }));

  const arrivo = codiceDaIndirizzo();
  if (arrivo?.azione === "recupero") {
    svuota(radice).append(vistaReimposta(arrivo.codice, avvia, avvia));
    return;
  }
  if (arrivo?.azione === "verifica") {
    await confermaEmail(arrivo.codice);
  }

  const dentro = await caricaSessione();

  if (!dentro) {
    svuota(radice).append(vistaAccesso(avvia));
    return;
  }
  if (!haProfilo()) {
    svuota(radice).append(vistaCreaProfilo(avvia));
    return;
  }
  schedaCorrente = "bacheca";
  disegnaApp();
}

avvia();

// ---------- Service worker ----------
// Permette l'installazione sulla schermata home e l'apertura anche offline.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Senza service worker l'app funziona lo stesso, solo non è installabile.
    });
  });
}
