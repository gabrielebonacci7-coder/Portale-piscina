// Scrivere una recensione dopo un turno concluso.
//
// I voti di dettaglio dipendono dal verso: una struttura giudica puntualità e
// professionalità di chi è venuto, un bagnino l'ambiente e la puntualità del
// pagamento. Il backend rifiuta i voti nel verso sbagliato, quindi qui si
// mostrano solo quelli giusti — l'errore non deve nemmeno essere possibile.

import { api } from "../api.js";
import { eBagnino, stato } from "../stato.js";
import { avviso, brindisi, el, pannello } from "../ui.js";

const VOTI = {
  piscina: [
    ["voto_puntualita", "Puntualità"],
    ["voto_professionalita", "Professionalità"],
  ],
  bagnino: [
    ["voto_ambiente", "Ambiente di lavoro"],
    ["voto_pagamento", "Pagamento puntuale"],
  ],
};

/** Chi devo recensire in questo turno: la controparte, chiunque io sia. */
export function controparte(annuncio) {
  if (annuncio.autore_id === stato.utente.id) return annuncio.assegnato_a ?? null;
  if (annuncio.assegnato_a_id === stato.utente.id) return annuncio.autore ?? null;
  return null;
}

/** Vero se il turno è arrivato al punto in cui ha senso recensire. */
export function siPuoRecensire(annuncio) {
  return (
    ["assegnato", "chiuso"].includes(annuncio.stato) && controparte(annuncio) !== null
  );
}

/** Scelta a stelle: grande abbastanza da centrarla con il pollice. */
function sceltaStelle(nome, valoreIniziale = 0) {
  let valore = valoreIniziale;
  const gruppo = el("div", { classe: "voti-stelle", role: "radiogroup", "aria-label": nome });
  const bottoni = [];

  const ridisegna = () => {
    bottoni.forEach((b, i) => b.setAttribute("aria-pressed", i < valore));
  };

  for (let i = 1; i <= 5; i++) {
    const b = el("button", {
      type: "button",
      testo: "★",
      "aria-label": `${i} su 5`,
      onclick: () => {
        // Ritoccare la stessa stella azzera: serve a togliere un voto messo
        // per sbaglio su un campo che è comunque facoltativo.
        valore = valore === i ? 0 : i;
        ridisegna();
      },
    });
    bottoni.push(b);
    gruppo.append(b);
  }
  ridisegna();

  return { elemento: gruppo, leggi: () => valore || null };
}

export function moduloRecensione(annuncio, alFatto) {
  const altro = controparte(annuncio);
  if (!altro) return;

  const errore = el("div");
  const stelle = sceltaStelle("Valutazione complessiva");
  const commento = el("textarea", {
    maxlength: 2000,
    placeholder: "Com'è andata? Due righe aiutano chi legge più di un voto secco.",
  });

  const dettaglio = VOTI[eBagnino() ? "bagnino" : "piscina"].map(([campo, etichetta]) => {
    const scelta = sceltaStelle(etichetta);
    return {
      campo,
      leggi: scelta.leggi,
      riga: el("div", { classe: "voce" }, [
        el("span", { classe: "voce-corpo", testo: etichetta }),
        scelta.elemento,
      ]),
    };
  });

  const form = el("form", {}, [
    errore,
    el("p", { classe: "sommesso", testo: annuncio.titolo }),
    el("div", { classe: "campo", style: "margin-top:16px" }, [
      el("label", { testo: "Valutazione complessiva" }),
      stelle.elemento,
    ]),
    el("div", { classe: "blocco" }, [
      el("span", { classe: "etichetta", testo: "Nel dettaglio (facoltativo)" }),
      ...dettaglio.map((d) => d.riga),
    ]),
    el("div", { classe: "campo" }, [el("label", { testo: "Commento" }), commento]),
    el("button", { type: "submit", classe: "btn largo", testo: "Invia recensione" }),
  ]);

  const { chiudi } = pannello(`Recensisci ${altro.nome_visualizzato}`, form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();

    if (!stelle.leggi()) {
      errore.replaceChildren(avviso("Assegna almeno una stella"));
      return;
    }

    const invio = form.querySelector("button[type=submit]");
    invio.disabled = true;
    invio.textContent = "Invio…";

    const dati = {
      destinatario_id: altro.id,
      annuncio_id: annuncio.id,
      stelle: stelle.leggi(),
      commento: commento.value.trim() || null,
    };
    for (const d of dettaglio) dati[d.campo] = d.leggi();

    try {
      await api.recensisci(dati);
      brindisi("Recensione pubblicata");
      chiudi();
      alFatto?.();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
      invio.disabled = false;
      invio.textContent = "Invia recensione";
    }
  });
}
