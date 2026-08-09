// Per il bagnino: le proprie candidature.
// Per la struttura: i propri annunci, con quante risposte hanno ricevuto.

import { api } from "../api.js";
import { ePiscina, stato } from "../stato.js";
import {
  avviso,
  brindisi,
  caricamento,
  chip,
  el,
  etichetta,
  euro,
  quando,
  vuoto,
} from "../ui.js";
import { apriAnnuncio, apriCandidature } from "./bacheca.js";
import { moduloRecensione, siPuoRecensire } from "./recensioni.js";

export function vistaCandidature(navigazione) {
  return ePiscina() ? vistaMieiAnnunci(navigazione) : vistaMieCandidature(navigazione);
}

/** Bagnino: prima i turni che copre, poi dove si è candidato. */
function vistaMieCandidature(navigazione) {
  const contenitore = el("div");
  const zonaTurni = el("div");
  const zonaCandidature = el("div");
  contenitore.append(zonaTurni, zonaCandidature);

  async function carica() {
    zonaTurni.replaceChildren(caricamento());
    zonaCandidature.replaceChildren();

    try {
      // "I miei turni" per un bagnino sono quelli assegnati a lui: è da qui
      // che ritrova un turno concluso per recensire la struttura.
      const [turni, candidature] = await Promise.all([
        api.mieiAnnunci({ limit: 50 }),
        api.mieCandidature(),
      ]);

      const assegnati = turni.elementi.filter((a) => a.assegnato_a_id === stato.utente.id);

      zonaTurni.replaceChildren();
      if (assegnati.length) {
        zonaTurni.append(
          el("span", { classe: "etichetta", style: "display:block;margin-bottom:8px",
                       testo: "Turni che copri" }),
          el("div", { classe: "elenco", style: "margin-bottom:24px" },
             assegnati.map((a) => rigaTurnoAssegnato(a, carica, navigazione))),
        );
      }

      zonaCandidature.append(
        el("span", { classe: "etichetta", style: "display:block;margin-bottom:8px",
                     testo: "Le tue candidature" }),
      );
      if (!candidature.elementi.length) {
        zonaCandidature.append(
          vuoto("Nessuna candidatura", "Quando risponderai a un turno lo troverai qui."),
        );
      } else {
        zonaCandidature.append(
          el("div", { classe: "elenco" },
             candidature.elementi.map((c) => rigaCandidatura(c, carica, navigazione))),
        );
      }
    } catch (e) {
      console.error("Caricamento candidature:", e);
      zonaTurni.replaceChildren(avviso(e.dettaglio));
    }
  }

  carica();
  contenitore.ricarica = carica;
  return contenitore;
}

/** Un turno che il bagnino copre: da concluso, si recensisce la struttura. */
function rigaTurnoAssegnato(a, ricarica, navigazione) {
  const { valore, unita } = euro(a.compenso, a.compenso_tipo);
  const scheda = el("div", { classe: "scheda", style: "cursor:default" }, [
    el("div", { classe: "scheda-testa" }, [
      el("h3", { style: "flex:1", testo: a.titolo }),
      el("span", { classe: "compenso" }, [valore, unita && el("small", { testo: unita })]),
    ]),
    el("div", { classe: "riga-meta" }, [
      el("span", { classe: "dato", testo: quando(a.data_inizio, a.data_fine) }),
      a.zona && el("span", { testo: `· ${a.zona.nome}` }),
    ]),
    el("div", { classe: "chips" }, [
      chip(etichetta("stato", a.stato), a.stato === "chiuso" ? "" : "verde"),
      a.autore && chip(a.autore.nome_visualizzato),
    ]),
  ]);

  const azioni = el("div", { classe: "azioni" });
  if (siPuoRecensire(a)) {
    azioni.append(
      el("button", {
        classe: "btn piccolo",
        testo: "Recensisci la struttura",
        onclick: () => moduloRecensione(a, ricarica),
      }),
    );
  }
  azioni.append(
    el("button", {
      classe: "btn fantasma piccolo",
      testo: "Dettaglio",
      onclick: () => apriAnnuncio(a.id, ricarica, navigazione),
    }),
  );
  scheda.append(azioni);
  return scheda;
}

function rigaCandidatura(c, ricarica, navigazione) {
  const colore = { accettata: "verde", rifiutata: "rosso", ritirata: "" }[c.stato] || "ambra";

  const scheda = el("div", { classe: "scheda", style: "cursor:default" }, [
    el("div", { classe: "scheda-testa" }, [
      el("h3", { style: "flex:1", testo: c.annuncio_titolo ?? "Annuncio" }),
      chip(etichetta("candidatura", c.stato), colore),
    ]),
    c.annuncio_data_inizio &&
      el("div", { classe: "riga-meta" }, [
        el("span", { classe: "dato", testo: quando(c.annuncio_data_inizio) }),
      ]),
    c.messaggio && el("p", { classe: "sommesso", style: "margin-top:8px", testo: c.messaggio }),
  ]);

  const azioni = el("div", { classe: "azioni" }, [
    el("button", {
      classe: "btn fantasma piccolo",
      testo: "Vedi il turno",
      onclick: () => apriAnnuncio(c.annuncio_id, ricarica, navigazione),
    }),
  ]);

  if (c.stato === "accettata") {
    // Il turno è suo: a cose fatte può recensire la struttura.
    azioni.append(
      el("button", {
        classe: "btn piccolo",
        testo: "Recensisci",
        onclick: async () => {
          const annuncio = await api.annuncio(c.annuncio_id);
          if (siPuoRecensire(annuncio)) moduloRecensione(annuncio, ricarica);
        },
      }),
    );
  }

  if (c.stato === "inviata") {
    azioni.append(
      el("button", {
        classe: "btn secondario piccolo",
        testo: "Ritira",
        onclick: async () => {
          if (!confirm("Ritirare la candidatura?")) return;
          try {
            await api.ritiraCandidatura(c.id);
            brindisi("Candidatura ritirata");
            ricarica();
          } catch (e) {
            alert(e.dettaglio);
          }
        },
      }),
    );
  }

  scheda.append(azioni);
  return scheda;
}

/** Struttura: i miei annunci, con il numero di candidature ricevute. */
function vistaMieiAnnunci(navigazione) {
  const contenitore = el("div");
  const elenco = el("div", { classe: "elenco" });
  contenitore.append(elenco);

  async function carica() {
    elenco.replaceChildren(caricamento());
    try {
      const pagina = await api.mieiAnnunci({ limit: 50 });
      if (!pagina.elementi.length) {
        elenco.replaceChildren(
          vuoto("Nessun annuncio", "Pubblica un turno con il + in alto a destra."),
        );
        return;
      }
      elenco.replaceChildren(
        ...pagina.elementi.map((a) =>
          // Un turno pubblicato da me si gestisce (candidature, dettaglio);
          // uno assegnato a me si copre e basta: le candidature altrui non
          // le posso vedere.
          a.autore_id === stato.utente.id
            ? rigaMioAnnuncio(a, carica, navigazione)
            : rigaTurnoAssegnato(a, carica, navigazione),
        ),
      );
    } catch (e) {
      elenco.replaceChildren(avviso(e.dettaglio));
    }
  }

  carica();
  contenitore.ricarica = carica;
  return contenitore;
}

function rigaMioAnnuncio(a, ricarica, navigazione) {
  const { valore, unita } = euro(a.compenso, a.compenso_tipo);
  const coloreStato = { aperto: "acqua", assegnato: "verde", chiuso: "", scaduto: "ambra" }[a.stato];

  const scheda = el(
    "div",
    { classe: `scheda ${a.urgente && a.stato === "aperto" ? "urgente" : ""}`.trim(), style: "cursor:default" },
    [
      el("div", { classe: "scheda-testa" }, [
        el("h3", { style: "flex:1", testo: a.titolo }),
        el("span", { classe: "compenso" }, [valore, unita && el("small", { testo: unita })]),
      ]),
      el("div", { classe: "riga-meta" }, [
        el("span", { classe: "dato", testo: quando(a.data_inizio, a.data_fine) }),
        a.zona && el("span", { testo: `· ${a.zona.nome}` }),
      ]),
      el("div", { classe: "chips" }, [chip(etichetta("stato", a.stato), coloreStato)]),
    ],
  );

  const azioni = el("div", { classe: "azioni" });
  const contatore = el("button", {
    classe: "btn piccolo",
    testo: "Candidature",
    onclick: () => apriCandidature(a, ricarica),
  });

  // Il numero di risposte è la cosa che interessa di più a chi ha pubblicato.
  api
    .candidature(a.id)
    .then((p) => {
      const inAttesa = p.elementi.filter((c) => c.stato === "inviata").length;
      contatore.textContent = inAttesa
        ? `${inAttesa} in attesa`
        : `Candidature · ${p.totale}`;
    })
    .catch(() => {});

  azioni.append(contatore);

  if (siPuoRecensire(a)) {
    azioni.append(
      el("button", {
        classe: "btn piccolo",
        testo: "Recensisci",
        onclick: () => moduloRecensione(a, ricarica),
      }),
    );
  }

  azioni.append(
    el("button", {
      classe: "btn fantasma piccolo",
      testo: "Dettaglio",
      onclick: () => apriAnnuncio(a.id, ricarica, navigazione),
    }),
  );

  scheda.append(azioni);
  return scheda;
}
