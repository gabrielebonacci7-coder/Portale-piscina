// "Aggiungi alla schermata Home": come si installa Guardlink.
//
// I due sistemi si comportano in modo opposto e la differenza va gestita,
// non nascosta:
//
// - **Android/Chrome** avvisa la pagina con `beforeinstallprompt`, e da lì si
//   può aprire il vero pannello di installazione del sistema. Un pulsante.
// - **iPhone** non ha niente del genere: l'installazione si fa a mano dal menù
//   Condividi, e **solo da Safari**. Da Chrome o Firefox su iPhone la voce non
//   esiste proprio. È il motivo per cui il bagnino "non trova il pulsante":
//   non sta usando Safari.
//
// Quindi su Android si offre il pulsante, su iPhone si spiegano i passi.

import { el, pannello } from "./ui.js";

const RIMANDATO = "installazione-rimandata";

// Evento catturato all'avvio: quando arriva, Android è pronto a installare.
let invitoAndroid = null;

window.addEventListener("beforeinstallprompt", (evento) => {
  // Senza questo il browser mostrerebbe la sua barra, che a volte compare in
  // mezzo alla schermata: meglio scegliere noi dove e quando chiederlo.
  evento.preventDefault();
  invitoAndroid = evento;
});

window.addEventListener("appinstalled", () => {
  invitoAndroid = null;
  document.querySelector(".installa")?.remove();
});

/** True se l'app è già stata aggiunta alla schermata home. */
export function giaInstallata() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    // Safari su iPhone non conosce `display-mode`: usa una sua proprietà.
    window.navigator.standalone === true
  );
}

function suIPhone() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

/** Safari è l'unico browser da cui, su iPhone, si può installare. */
function safariSuIPhone() {
  return suIPhone() && !/crios|fxios|edgios|opt\//i.test(navigator.userAgent);
}

export function puoInstallare() {
  return !giaInstallata() && (invitoAndroid !== null || suIPhone());
}

/** Apre il pannello di sistema (Android) o spiega i passi (iPhone). */
export async function chiediInstallazione() {
  if (invitoAndroid) {
    invitoAndroid.prompt();
    await invitoAndroid.userChoice;
    // Vale una volta sola: dopo averlo usato il browser non lo ridà.
    invitoAndroid = null;
    document.querySelector(".installa")?.remove();
    return;
  }
  istruzioniIPhone();
}

function istruzioniIPhone() {
  const passo = (numero, testo, dettaglio) =>
    el("div", { classe: "voce" }, [
      el("span", { classe: "passo", testo: String(numero) }),
      el("div", { classe: "voce-corpo" }, [
        el("strong", { testo }),
        dettaglio && el("div", { classe: "sommesso", testo: dettaglio }),
      ]),
    ]);

  const contenuto = el("div", {}, [
    !safariSuIPhone() &&
      el("div", { classe: "avviso info" }, [
        el("span", {
          testo:
            "Stai usando un browser diverso da Safari. Su iPhone l'aggiunta " +
            "alla schermata Home funziona solo da Safari: apri lì Guardlink " +
            "e riprova.",
        }),
      ]),
    el("div", { classe: "blocco" }, [
      passo(1, "Premi il tasto Condividi", "Il quadrato con la freccia in su, in basso al centro."),
      passo(2, "Scorri e scegli «Aggiungi a Home»", "È più in basso nell'elenco delle voci."),
      passo(3, "Premi «Aggiungi» in alto a destra"),
    ]),
    el("p", {
      classe: "sommesso",
      testo:
        "Da lì Guardlink si apre come un'app normale, a tutto schermo e senza " +
        "la barra del browser.",
    }),
  ]);

  pannello("Aggiungi alla schermata Home", contenuto);
}

/** Striscia discreta che propone l'installazione. Si può rimandare.

    Non compare subito: chi si è appena iscritto ha altro per la testa. La si
    mostra dalla bacheca, quando l'app ha già dimostrato di servire a qualcosa. */
export function barraInstallazione() {
  if (!puoInstallare()) return null;
  if (localStorage.getItem(RIMANDATO)) return null;

  const barra = el("div", { classe: "installa" }, [
    el("div", {}, [
      el("strong", { testo: "Tienila a portata di mano" }),
      el("div", {
        classe: "sommesso",
        testo: "Aggiungi Guardlink alla schermata Home: si apre come un'app.",
      }),
    ]),
    el("div", { classe: "azioni" }, [
      el("button", {
        classe: "btn piccolo",
        testo: "Aggiungi",
        onclick: () => chiediInstallazione(),
      }),
      el("button", {
        classe: "btn fantasma piccolo",
        testo: "Non ora",
        onclick: () => {
          localStorage.setItem(RIMANDATO, "1");
          barra.remove();
        },
      }),
    ]),
  ]);
  return barra;
}
