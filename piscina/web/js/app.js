// L'ossatura dell'app: carica i dati comuni, disegna la barra e i tab,
// e sceglie la vista in base all'indirizzo.
//
// Non c'è un framework: le viste sono funzioni che restituiscono un nodo, e
// il "router" è l'hash dell'indirizzo. Per un'app di quattro schermate è
// tutto quello che serve, e si apre in un decimo di secondo anche con la
// linea del telefono che va e viene.

import * as api from "./api.js";
import { avviso, el, ICONE, svuota } from "./ui.js";
import { daMostrare, mostraOmino, nomeRicordato, segnaVisto } from "./omino.js";
import { vistaPrenota } from "./viste/prenota.js";
import { vistaListino } from "./viste/listino.js";
import { vistaDove } from "./viste/dove.js";
import { vistaPrenotazione } from "./viste/prenotazione.js";
import { vistaStaff } from "./viste/staff.js";

const radice = document.getElementById("radice");

const TAB = [
  { rotta: "prenota", etichetta: "Prenota", icona: "ombrellone" },
  { rotta: "prezzi", etichetta: "Prezzi", icona: "listino" },
  { rotta: "dove", etichetta: "Dove siamo", icona: "mappa" },
  { rotta: "prenotazione", etichetta: "La mia", icona: "biglietto" },
];

const VISTE = {
  prenota: vistaPrenota,
  prezzi: vistaListino,
  dove: vistaDove,
  prenotazione: vistaPrenotazione,
  staff: vistaStaff,
};

let ctx = null;

function rottaCorrente() {
  // /staff è un indirizzo vero, così lo staff può salvarlo fra i preferiti.
  if (location.pathname.replace(/\/$/, "") === "/staff") return "staff";
  const hash = location.hash.replace(/^#\/?/, "").split("?")[0];
  return VISTE[hash] ? hash : "prenota";
}

function barra() {
  return el("header", { classe: "barra" }, [
    el("div", { classe: "marchio" }, [
      el("span", {
        style: "width:30px;height:30px;display:grid;place-items:center",
        html: ICONE.ombrellone,
      }),
      el("div", {}, [
        el("div", { classe: "titolo", testo: "Piscina di Ciampino" }),
        el("div", { classe: "sottotitolo", testo: ctx.info.orari }),
      ]),
    ]),
  ]);
}

function tab(rotta) {
  return el("nav", { classe: "tab", "aria-label": "Sezioni" },
    TAB.map((t) =>
      el("a", {
        href: `#/${t.rotta}`,
        "aria-current": rotta === t.rotta ? "page" : null,
      }, [
        el("span", { html: ICONE[t.icona], style: "display:grid;place-items:center" }),
        t.etichetta,
      ])
    )
  );
}

function disegna() {
  const rotta = rottaCorrente();
  const contenuto = el("main", { classe: "contenuto" });

  const pezzi = [rotta === "staff" ? intestazioneStaff() : barra(), contenuto];
  // Il gestionale non ha i tab in basso: non è una delle sezioni dell'app.
  if (rotta !== "staff") pezzi.push(tab(rotta));
  svuota(radice).append(...pezzi);

  try {
    contenuto.append(VISTE[rotta](ctx));
  } catch (guaio) {
    console.error(guaio);
    contenuto.append(avviso("guaio", "Questa pagina non si è aperta. Ricarica l'app."));
  }
  window.scrollTo(0, 0);
}

function intestazioneStaff() {
  return el("header", { classe: "barra" }, [
    el("div", { classe: "marchio" }, [
      el("div", {}, [
        el("div", { classe: "titolo", testo: "Gestionale" }),
        el("div", { classe: "sottotitolo", testo: "Piscina Comunale di Ciampino" }),
      ]),
    ]),
    el("a", {
      classe: "spinta",
      href: "/#/prenota",
      style: "color:inherit;text-decoration:none;font-weight:650;font-size:0.86rem",
      testo: "Vai all'app",
    }),
  ]);
}

async function avvia() {
  try {
    const [info, listino] = await Promise.all([api.info(), api.listino()]);
    ctx = {
      info,
      listino,
      // Il saluto col nome: quello lasciato con l'ultima prenotazione su
      // questo telefono. La prima volta si saluta e basta.
      mostraBenvenuto: () =>
        mostraOmino(info.benvenuto, {
          occhiello: info.stagione,
          titolo: info.nome,
          nome: nomeRicordato(),
          alTermine: segnaVisto,
        }),
      ringrazia: (nome, alTermine) =>
        mostraOmino(info.grazie, {
          occhiello: "Prenotazione confermata",
          nome,
          alTermine,
        }),
    };
  } catch (guaio) {
    svuota(radice).append(
      el("div", { classe: "contenuto" }, [
        avviso("guaio", "Non riesco a contattare la piscina. Controlla la rete e riprova."),
        el("button", {
          classe: "bottone",
          type: "button",
          testo: "Riprova",
          onclick: () => location.reload(),
        }),
      ])
    );
    return;
  }

  window.addEventListener("hashchange", disegna);
  disegna();

  // Il benvenuto solo la prima volta, e mai davanti al gestionale.
  if (rottaCorrente() !== "staff" && daMostrare()) ctx.mostraBenvenuto();

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      /* senza service worker l'app funziona lo stesso, non si installa e basta */
    });
  }
}

avvia();
