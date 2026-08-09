// Come arriva una versione nuova a chi ha già l'app sul telefono.
//
// Il problema, con una PWA installata: non "si scarica di nuovo" da nessun
// negozio, e chi la tiene aperta sulla schermata home può non chiuderla per
// giorni. Senza qualcosa che se ne accorga, quella persona resterebbe sulla
// versione vecchia a tempo indeterminato.
//
// Il giro è questo:
//   1. il browser ricontrolla `sw.js` — da solo alla navigazione, e noi glielo
//      richiediamo ogni volta che l'app torna in primo piano;
//   2. se il file è cambiato, la versione nuova si installa e **aspetta**;
//   3. compare la barra "Nuova versione disponibile";
//   4. chi preme fa passare avanti la nuova, e la pagina si ricarica.
//
// Il passaggio non è automatico apposta: ricaricare sotto le mani a qualcuno
// che sta scrivendo un messaggio gli farebbe perdere quello che ha scritto.

import { el } from "./ui.js";

// Ogni quanto richiedere il controllo, quando l'app torna davanti.
const ATTESA_FRA_CONTROLLI = 60 * 60 * 1000; // un'ora

let ultimoControllo = 0;
let ricaricoInCorso = false;

export function avviaServiceWorker() {
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", async () => {
    let registrazione;
    try {
      registrazione = await navigator.serviceWorker.register("/sw.js");
    } catch {
      // Senza service worker l'app funziona lo stesso, solo non è
      // installabile e non si apre offline.
      return;
    }

    // Già pronta da una visita precedente: la barra va mostrata subito.
    if (registrazione.waiting && navigator.serviceWorker.controller) {
      mostraBarra(registrazione.waiting);
    }

    registrazione.addEventListener("updatefound", () => {
      const nuova = registrazione.installing;
      if (!nuova) return;
      nuova.addEventListener("statechange", () => {
        // `controller` assente = è la primissima installazione, non un
        // aggiornamento: lì non c'è niente da annunciare.
        if (nuova.state === "installed" && navigator.serviceWorker.controller) {
          mostraBarra(nuova);
        }
      });
    });

    // Quando la nuova prende il controllo, si riparte con il codice nuovo.
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (ricaricoInCorso) return;
      ricaricoInCorso = true;
      location.reload();
    });

    // Un'app installata può restare aperta per giorni senza mai navigare, e
    // senza navigazione il browser non ricontrolla niente da solo.
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState !== "visible") return;
      if (Date.now() - ultimoControllo < ATTESA_FRA_CONTROLLI) return;
      ultimoControllo = Date.now();
      registrazione.update().catch(() => {});
    });
  });
}

function mostraBarra(lavoratriceInAttesa) {
  if (document.querySelector(".aggiornamento")) return;

  const barra = el("div", { classe: "aggiornamento", role: "status" }, [
    el("span", { testo: "È disponibile una versione nuova." }),
    el("button", {
      classe: "btn piccolo",
      testo: "Aggiorna",
      onclick: (e) => {
        e.target.disabled = true;
        e.target.textContent = "Aggiorno…";
        lavoratriceInAttesa.postMessage({ tipo: "passa-alla-nuova" });
      },
    }),
    el("button", {
      classe: "btn-icona",
      "aria-label": "Più tardi",
      html: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
      // Solo per questa sessione: alla prossima apertura si ripropone, perché
      // restare indietro non è una scelta da rendere definitiva.
      onclick: () => barra.remove(),
    }),
  ]);

  document.body.append(barra);
}
