// L'omino che accoglie chi apre l'app.
//
// È un disegno vettoriale, non una fotografia: pesa due chilobyte, resta
// nitido su qualsiasi schermo, funziona senza rete e si adatta al tema scuro.
// La somiglianza sta nelle poche cose che si riconoscono al primo sguardo —
// la barba, la giacca azzurra della squadra, i pantaloni scuri, le scarpe
// bianche.
//
// Le battute non stanno qui: arrivano da /api/info, cioè dal file
// piscina/dominio/struttura.py. Per cambiare il discorso non si tocca il
// disegno.

import { el } from "./ui.js";

export const DISEGNO_OMINO = `
<svg viewBox="0 0 200 430" xmlns="http://www.w3.org/2000/svg" class="omino"
     role="img" aria-label="Il gestore della piscina che ti dà il benvenuto">
  <ellipse cx="100" cy="416" rx="62" ry="11" fill="rgba(0,0,0,0.22)"/>

  <!-- gambe -->
  <path d="M62 240 h76 l6 92 -6 62 h-32 l-6 -62 -6 62 H62 l-6 -62 z" fill="#1e2028"/>
  <path d="M100 244 v150" stroke="#2b2e38" stroke-width="2"/>

  <!-- scarpe -->
  <path d="M56 386 h34 v14 q0 8 -9 8 H50 q-8 0 -8 -7 0 -8 14 -15z" fill="#f4f3ee" stroke="#d9d7cd" stroke-width="2"/>
  <path d="M110 386 h34 q14 7 14 15 0 7 -8 7 h-31 q-9 0 -9 -8z" fill="#f4f3ee" stroke="#d9d7cd" stroke-width="2"/>

  <!-- braccia (sotto alla giacca, così le spalle restano pulite) -->
  <path d="M60 146 q-16 10 -19 34 l-8 74 q-1 12 11 13 12 1 14 -11 l12 -70z" fill="#1668c9"/>
  <path d="M140 146 q16 10 19 34 l8 74 q1 12 -11 13 -12 1 -14 -11 l-12 -70z" fill="#1668c9"/>
  <circle cx="37" cy="268" r="11" fill="#eec49b"/>
  <circle cx="163" cy="268" r="11" fill="#eec49b"/>

  <!-- giacca -->
  <path d="M100 124 q-24 2 -40 16 -6 6 -5 16 l4 88 q41 12 82 0 l4 -88 q1 -10 -5 -16 -16 -14 -40 -16z" fill="#1a76dd"/>
  <path d="M100 124 q-24 2 -40 16 -6 6 -5 16 l2 40 q43 -6 86 0 l2 -40 q1 -10 -5 -16 -16 -14 -40 -16z"
        fill="#2a8cf0" opacity="0.55"/>
  <!-- zip e colletto -->
  <path d="M100 128 v116" stroke="#0b4d95" stroke-width="3"/>
  <path d="M78 132 q22 14 44 0 l-3 -10 q-19 10 -38 0z" fill="#f6f7f8"/>
  <!-- stemma della squadra -->
  <ellipse cx="128" cy="172" rx="14" ry="10" fill="#ffffff" opacity="0.92"/>
  <path d="M120 174 q8 -7 16 -2" stroke="#1a76dd" stroke-width="2.6" fill="none" stroke-linecap="round"/>

  <!-- collo e testa -->
  <path d="M88 100 h24 v22 q-12 8 -24 0z" fill="#dcae86"/>
  <ellipse cx="100" cy="72" rx="31" ry="35" fill="#eec49b"/>
  <circle cx="69" cy="76" r="6.5" fill="#eec49b"/>
  <circle cx="131" cy="76" r="6.5" fill="#eec49b"/>

  <!-- barba -->
  <path d="M70 68 q2 40 30 44 28 -4 30 -44 -6 22 -30 24 -24 -2 -30 -24z" fill="#4a3626"/>
  <path d="M86 96 q14 8 28 0 -4 12 -14 12 -10 0 -14 -12z" fill="#c96a5c"/>
  <path d="M88 97 q12 5 24 0 -12 4 -24 0z" fill="#ffffff"/>

  <!-- capelli -->
  <path d="M68 66 q0 -40 32 -40 32 0 32 40 -6 -18 -32 -20 -26 2 -32 20z" fill="#3d2b1d"/>

  <!-- occhi e sopracciglia -->
  <ellipse cx="87" cy="68" rx="3.6" ry="4.2" fill="#26313a"/>
  <ellipse cx="113" cy="68" rx="3.6" ry="4.2" fill="#26313a"/>
  <path d="M80 58 q7 -5 14 -1" stroke="#3d2b1d" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M106 57 q7 -4 14 1" stroke="#3d2b1d" stroke-width="3" fill="none" stroke-linecap="round"/>
</svg>`;

/**
 * Il benvenuto a schermo intero: l'omino e le sue battute, una alla volta.
 * Si vede una volta sola per telefono; si rivede dal menu "Chi siamo".
 */
export function mostraBenvenuto(info, { alTermine } = {}) {
  const benvenuto = info.benvenuto || {};
  const battute = benvenuto.battute || [];
  let indice = 0;

  const fumetto = el("div", { classe: "fumetto" });
  const punti = el("div", { classe: "punti" });
  const avanti = el("button", { classe: "bottone avanti", type: "button" });

  const scena = el("div", { classe: "benvenuto", role: "dialog", "aria-modal": "true" }, [
    el("div", { classe: "insegna" }, [
      el("div", { classe: "occhiello", testo: info.stagione || "" }),
      el("h1", { testo: info.nome || "" }),
    ]),
    el("div", { classe: "scena" }, [
      el("div", { classe: "omino", html: DISEGNO_OMINO }),
      el("div", { classe: "parlato" }, [
        benvenuto.nome
          ? el("div", { classe: "chi", testo: benvenuto.nome })
          : null,
        fumetto,
      ]),
    ]),
    punti,
    el("div", { classe: "comandi" }, [
      el("button", { classe: "salta", type: "button", testo: "Salta", onclick: chiudi }),
      avanti,
    ]),
  ]);

  function disegna() {
    fumetto.textContent = battute[indice] || "";
    avanti.textContent = indice === battute.length - 1 ? benvenuto.invito || "Iniziamo" : "Avanti";
    punti.replaceChildren(
      ...battute.map((_, i) => el("i", { classe: i === indice ? "attivo" : "" }))
    );
  }

  function chiudi() {
    scena.remove();
    document.body.style.overflow = "";
    alTermine?.();
  }

  avanti.addEventListener("click", () => {
    if (indice < battute.length - 1) {
      indice += 1;
      disegna();
    } else {
      chiudi();
    }
  });

  disegna();
  document.body.style.overflow = "hidden";
  document.body.append(scena);
  avanti.focus();
  return { chiudi };
}

const CHIAVE_VISTO = "piscina-benvenuto-visto";

/** Vero se questo telefono non ha mai visto il benvenuto. */
export function daMostrare() {
  try {
    return localStorage.getItem(CHIAVE_VISTO) !== "1";
  } catch {
    // Navigazione privata o cookie bloccati: si mostra e basta.
    return true;
  }
}

export function segnaVisto() {
  try {
    localStorage.setItem(CHIAVE_VISTO, "1");
  } catch {
    /* pazienza: la prossima volta lo rivede */
  }
}
