// La bacheca: elenco dei turni con filtri, e la scheda di dettaglio con le
// azioni possibili (candidarsi, gestire le candidature, chiudere).

import { api } from "../api.js";
import { eBagnino, ePiscina, stato, caricaZone } from "../stato.js";
import {
  avviso,
  brindisi,
  caricamento,
  chip,
  el,
  etichetta,
  euro,
  galleria,
  pannello,
  quando,
  quandoEsteso,
  vuoto,
} from "../ui.js";
import { schedaBagnino } from "./bagnini.js";
import { apriChatCon } from "./messaggi.js";

// I filtri restano impostati mentre si naviga: chi cerca turni a Ostia non
// vuole reimpostarli a ogni ritorno in bacheca.
const filtri = {
  zona_id: "",
  tipo_turno: "",
  solo_urgenti: false,
  compenso_min: "",
  testo: "",
};

export function contaFiltriAttivi() {
  return Object.entries(filtri).filter(([, v]) => v !== "" && v !== false).length;
}

export function vistaBacheca(navigazione) {
  const contenitore = el("div");
  const elenco = el("div", { classe: "elenco" });

  const barraRicerca = el("input", {
    type: "search",
    placeholder: "Cerca fra i turni…",
    value: filtri.testo,
    style: "margin-bottom:16px",
    oninput: (e) => {
      filtri.testo = e.target.value;
      clearTimeout(barraRicerca._attesa);
      // Si aspetta che smetta di digitare, altrimenti si interroga il server
      // a ogni tasto premuto.
      barraRicerca._attesa = setTimeout(carica, 350);
    },
  });

  contenitore.append(barraRicerca, elenco);

  async function carica() {
    elenco.replaceChildren(caricamento());
    try {
      const pagina = await api.bacheca({
        zona_id: filtri.zona_id,
        tipo_turno: filtri.tipo_turno,
        solo_urgenti: filtri.solo_urgenti || "",
        compenso_min: filtri.compenso_min,
        testo: filtri.testo,
        limit: 50,
      });
      if (!pagina.elementi.length) {
        elenco.replaceChildren(
          vuoto(
            contaFiltriAttivi() ? "Nessun turno con questi filtri" : "Nessun turno in bacheca",
            contaFiltriAttivi()
              ? "Prova ad allargare la ricerca."
              : "I nuovi annunci compariranno qui.",
          ),
        );
        return;
      }
      elenco.replaceChildren(
        ...pagina.elementi.map((a) => schedaAnnuncio(a, () => apriAnnuncio(a.id, carica, navigazione))),
      );
    } catch (e) {
      elenco.replaceChildren(avviso(e.dettaglio));
    }
  }

  carica();
  contenitore.ricarica = carica;
  return contenitore;
}

/** La scheda compatta mostrata in elenco. */
export function schedaAnnuncio(a, alClic) {
  const { valore, unita } = euro(a.compenso, a.compenso_tipo);
  const cercaBagnino = a.tipo === "piscina_cerca_bagnino";

  const scheda = el(
    "button",
    { classe: `scheda ${a.urgente ? "urgente" : ""}`.trim(), type: "button", onclick: alClic },
    [
      el("div", { classe: "scheda-testa" }, [
        el("h3", { testo: a.titolo }),
        el("span", { classe: "compenso" }, [
          valore,
          unita && el("small", { testo: unita }),
        ]),
      ]),
      el("div", { classe: "riga-meta" }, [
        el("span", { classe: "dato", testo: quando(a.data_inizio, a.data_fine) }),
        a.zona && el("span", { testo: `· ${a.zona.nome}` }),
      ]),
      el("div", { classe: "chips" }, [
        a.urgente && chip("Urgente", "rosso"),
        chip(etichetta("tipo_turno", a.tipo_turno)),
        a.brevetto_richiesto && chip(`Brevetto ${a.brevetto_richiesto}`, "acqua"),
        !cercaBagnino && chip("Cerca sostituzione", "ambra"),
        a.stato !== "aperto" && chip(etichetta("stato", a.stato), "verde"),
      ]),
      el("p", {
        classe: "sommesso",
        style: "margin-top:8px",
        testo: `da ${a.autore?.nome_visualizzato ?? "—"}`,
      }),
    ],
  );
  return scheda;
}

/** Scheda completa in pannello, con le azioni permesse a chi guarda. */
export async function apriAnnuncio(id, alCambio, navigazione) {
  const corpo = el("div", {}, caricamento());
  const { chiudi } = pannello("Dettaglio turno", corpo);

  let a;
  try {
    a = await api.annuncio(id);
  } catch (e) {
    corpo.replaceChildren(avviso(e.dettaglio));
    return;
  }

  const mio = a.autore_id === stato.utente.id;
  const { valore, unita } = euro(a.compenso, a.compenso_tipo);

  const dettagli = el("div", { classe: "blocco" }, [
    el("h2", { testo: a.titolo, style: "margin-bottom:12px" }),
    riga("Quando", quandoEsteso(a.data_inizio) + (a.data_fine ? ` — ${quandoEsteso(a.data_fine)}` : "")),
    riga("Dove", [a.zona?.nome, a.indirizzo, a.citta].filter(Boolean).join(" · ") || "—"),
    riga("Compenso", `${valore}${unita} (${etichetta("compenso", a.compenso_tipo)})`),
    riga("Tipo", etichetta("tipo_turno", a.tipo_turno)),
    a.brevetto_richiesto && riga("Brevetto richiesto", etichetta("brevetto", a.brevetto_richiesto)),
    riga("Stato", etichetta("stato", a.stato)),
    riga("Pubblicato da", a.autore?.nome_visualizzato ?? "—"),
  ]);

  if (a.note) {
    dettagli.append(
      el("div", { style: "margin-top:12px" }, [
        el("span", { classe: "etichetta", testo: "Note" }),
        el("p", { testo: a.note, style: "margin-top:4px" }),
      ]),
    );
  }

  corpo.replaceChildren(dettagli);

  // Le foto della struttura, con l'ingresso per primo: è così che chi va a
  // coprire il turno riconosce il posto quando ci arriva.
  if (a.piscina_id) {
    const zonaFoto = el("div", { classe: "blocco" }, [
      el("span", { classe: "etichetta", testo: "La struttura" }),
      caricamento(),
    ]);
    corpo.append(zonaFoto);
    api
      .piscina(a.piscina_id)
      .then((piscina) => {
        zonaFoto.replaceChildren(
          el("span", { classe: "etichetta", testo: "La struttura" }),
          el("h3", { style: "margin:4px 0 10px", testo: piscina.nome_struttura }),
        );
        if (piscina.foto.length) {
          zonaFoto.append(galleria(piscina.foto));
        } else {
          zonaFoto.append(
            el("p", { classe: "sommesso", testo: "Nessuna foto disponibile." }),
          );
        }
      })
      .catch(() => zonaFoto.remove());
  }

  // --- Azioni ---
  const azioni = el("div", { classe: "azioni" });

  if (mio) {
    azioni.append(
      el("button", {
        classe: "btn",
        testo: "Candidature",
        onclick: () => {
          chiudi();
          apriCandidature(a, alCambio);
        },
      }),
    );
    if (a.stato === "assegnato") {
      azioni.append(
        el("button", {
          classe: "btn secondario",
          testo: "Segna come concluso",
          onclick: async () => {
            await api.chiudiAnnuncio(a.id);
            brindisi("Turno concluso: ora potete recensirvi");
            chiudi();
            alCambio?.();
          },
        }),
      );
    }
    azioni.append(
      el("button", {
        classe: "btn pericolo",
        testo: "Elimina",
        onclick: async () => {
          if (!confirm("Eliminare questo annuncio? L'operazione non si annulla.")) return;
          await api.eliminaAnnuncio(a.id);
          brindisi("Annuncio eliminato");
          chiudi();
          alCambio?.();
        },
      }),
    );
  } else {
    const puoCandidarsi =
      a.stato === "aperto" &&
      new Date(a.data_inizio) > new Date() &&
      ((a.tipo === "piscina_cerca_bagnino" && eBagnino()) ||
        (a.tipo === "bagnino_cerca_sostituzione" && ePiscina()));

    if (puoCandidarsi) {
      azioni.append(
        el("button", {
          classe: "btn",
          testo: "Candidati",
          onclick: () => moduloCandidatura(a, chiudi, alCambio),
        }),
      );
    }
    azioni.append(
      el("button", {
        classe: "btn secondario",
        testo: "Scrivi un messaggio",
        onclick: () => {
          chiudi();
          apriChatCon(a.autore_id, a.autore?.nome_visualizzato, navigazione, { annuncio_id: a.id });
        },
      }),
    );
  }

  corpo.append(azioni);
}

function riga(nome, valore) {
  if (!valore) return null;
  return el("div", { classe: "voce" }, [
    el("span", { classe: "etichetta", style: "min-width:120px", testo: nome }),
    el("span", { classe: "voce-corpo", testo: valore }),
  ]);
}

/** Modulo di candidatura, con messaggio facoltativo. */
function moduloCandidatura(a, chiudiDettaglio, alCambio) {
  chiudiDettaglio();
  const errore = el("div");
  const messaggio = el("textarea", {
    placeholder: "Presentati in due righe: perché sei adatto a questo turno.",
    maxlength: 1000,
  });

  const form = el("form", {}, [
    errore,
    el("p", { classe: "sommesso", style: "margin-bottom:12px", testo: a.titolo }),
    el("div", { classe: "campo" }, [
      el("label", { testo: "Messaggio (facoltativo)" }),
      messaggio,
    ]),
    el("button", { type: "submit", classe: "btn largo", testo: "Invia candidatura" }),
  ]);

  const { chiudi } = pannello("Candidati", form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errore.replaceChildren();
    const invio = form.querySelector("button[type=submit]");
    invio.disabled = true;
    try {
      await api.candidati(a.id, { messaggio: messaggio.value.trim() || null });
      brindisi("Candidatura inviata");
      chiudi();
      alCambio?.();
    } catch (err) {
      errore.replaceChildren(avviso(err.dettaglio));
      invio.disabled = false;
    }
  });
}

/** Elenco delle candidature ricevute su un proprio annuncio. */
export async function apriCandidature(a, alCambio) {
  const corpo = el("div", {}, caricamento());
  const { chiudi } = pannello("Candidature ricevute", corpo);

  async function ricarica() {
    try {
      const pagina = await api.candidature(a.id);
      if (!pagina.elementi.length) {
        corpo.replaceChildren(
          vuoto("Ancora nessuna candidatura", "Chi risponderà comparirà qui."),
        );
        return;
      }
      corpo.replaceChildren(
        ...pagina.elementi.map((c) => voceCandidatura(a, c, ricarica, chiudi, alCambio)),
      );
    } catch (e) {
      corpo.replaceChildren(avviso(e.dettaglio));
    }
  }

  ricarica();
}

function voceCandidatura(a, c, ricarica, chiudiPannello, alCambio) {
  const colore = { accettata: "verde", rifiutata: "rosso", ritirata: "" }[c.stato] || "ambra";

  const blocco = el("div", { classe: "blocco" }, [
    el("div", { style: "display:flex;align-items:center;gap:12px" }, [
      el("h3", { style: "flex:1", testo: c.candidato?.nome_visualizzato ?? "—" }),
      chip(etichetta("candidatura", c.stato), colore),
    ]),
    c.messaggio && el("p", { style: "margin-top:8px", testo: c.messaggio }),
  ]);

  const azioni = el("div", { classe: "azioni" });

  azioni.append(
    el("button", {
      classe: "btn fantasma piccolo",
      testo: "Vedi profilo",
      onclick: () => schedaBagnino(c.candidato.id),
    }),
  );

  if (c.stato === "inviata") {
    azioni.append(
      el("button", {
        classe: "btn piccolo",
        testo: "Accetta",
        onclick: async () => {
          try {
            await api.accettaCandidatura(a.id, c.id);
            brindisi(`Turno assegnato a ${c.candidato.nome_visualizzato}`);
            await ricarica();
            alCambio?.();
          } catch (e) {
            alert(e.dettaglio);
          }
        },
      }),
      el("button", {
        classe: "btn secondario piccolo",
        testo: "Scarta",
        onclick: async () => {
          await api.rifiutaCandidatura(a.id, c.id);
          await ricarica();
          alCambio?.();
        },
      }),
    );
  }

  blocco.append(azioni);
  return blocco;
}

/** Pannello dei filtri della bacheca. */
export async function apriFiltri(alApplica) {
  const zone = await caricaZone();

  const selZona = el(
    "select",
    { name: "zona" },
    [el("option", { value: "", testo: "Tutte le zone" })].concat(
      zone.map((z) => el("option", { value: z.id, testo: z.nome, selected: String(z.id) === String(filtri.zona_id) })),
    ),
  );

  const selTurno = el(
    "select",
    { name: "turno" },
    [el("option", { value: "", testo: "Tutti i tipi" })].concat(
      Object.entries({
        turno_fisso: "Turno fisso",
        sostituzione_urgente: "Sostituzione",
        evento_serale: "Evento serale",
        stagionale: "Stagionale",
        weekend: "Weekend",
      }).map(([v, t]) => el("option", { value: v, testo: t, selected: v === filtri.tipo_turno })),
    ),
  );

  const compenso = el("input", {
    type: "number",
    min: 0,
    step: "0.5",
    placeholder: "es. 12",
    value: filtri.compenso_min,
  });

  const urgenti = el("input", { type: "checkbox", checked: filtri.solo_urgenti });

  const form = el("form", {}, [
    el("div", { classe: "campo" }, [el("label", { testo: "Zona" }), selZona]),
    el("div", { classe: "campo" }, [el("label", { testo: "Tipo di turno" }), selTurno]),
    el("div", { classe: "campo" }, [
      el("label", { testo: "Compenso minimo (€)" }),
      compenso,
    ]),
    el("label", { classe: "interruttore" }, [
      el("span", { testo: "Solo turni urgenti" }),
      urgenti,
    ]),
    el("div", { classe: "azioni" }, [
      el("button", {
        type: "button",
        classe: "btn secondario",
        testo: "Azzera",
        onclick: () => {
          Object.assign(filtri, {
            zona_id: "",
            tipo_turno: "",
            solo_urgenti: false,
            compenso_min: "",
          });
          chiudi();
          alApplica();
        },
      }),
      el("button", { type: "submit", classe: "btn", testo: "Applica" }),
    ]),
  ]);

  const { chiudi } = pannello("Filtri", form);

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    filtri.zona_id = selZona.value;
    filtri.tipo_turno = selTurno.value;
    filtri.compenso_min = compenso.value;
    filtri.solo_urgenti = urgenti.checked;
    chiudi();
    alApplica();
  });
}
