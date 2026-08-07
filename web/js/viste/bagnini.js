// Ricerca dei bagnini e scheda pubblica del singolo profilo.

import { api } from "../api.js";
import { caricaZone, stato } from "../stato.js";
import {
  GIORNI_LUNGHI,
  avatar,
  avviso,
  caricamento,
  chip,
  el,
  etichetta,
  opzioniZone,
  oraBreve,
  pannello,
  stelle,
  vuoto,
} from "../ui.js";
import { apriChatCon } from "./messaggi.js";

const filtri = { zona_id: "", solo_abilitati: false, chiamata_singola: "" };

export function vistaBagnini(navigazione) {
  const contenitore = el("div");
  const elenco = el("div", { classe: "elenco" });

  const selZona = el("select", { style: "margin-bottom:12px" }, [
    el("option", { value: "", testo: "Tutte le zone" }),
  ]);
  caricaZone().then((zone) => selZona.append(...opzioniZone(zone, filtri.zona_id)));
  selZona.addEventListener("change", () => {
    filtri.zona_id = selZona.value;
    carica();
  });

  const abilitati = el("input", { type: "checkbox", checked: filtri.solo_abilitati });
  abilitati.addEventListener("change", () => {
    filtri.solo_abilitati = abilitati.checked;
    carica();
  });

  contenitore.append(
    selZona,
    el("label", { classe: "interruttore", style: "margin-bottom:16px" }, [
      el("span", {}, [
        el("span", { testo: "Solo con brevetto valido" }),
        el("span", {
          classe: "aiuto",
          style: "display:block",
          testo: "Esclude chi ha il brevetto scaduto",
        }),
      ]),
      abilitati,
    ]),
    elenco,
  );

  async function carica() {
    elenco.replaceChildren(caricamento());
    try {
      const pagina = await api.bagnini({
        zona_id: filtri.zona_id,
        solo_abilitati: filtri.solo_abilitati || "",
        limit: 50,
      });
      if (!pagina.elementi.length) {
        elenco.replaceChildren(vuoto("Nessun bagnino trovato", "Prova ad allargare la ricerca."));
        return;
      }
      elenco.replaceChildren(
        ...pagina.elementi.map((b) => rigaBagnino(b, () => schedaBagnino(b.id, navigazione))),
      );
    } catch (e) {
      elenco.replaceChildren(avviso(e.dettaglio));
    }
  }

  carica();
  contenitore.ricarica = carica;
  return contenitore;
}

function rigaBagnino(b, alClic) {
  const nome = `${b.nome} ${b.cognome}`;
  return el("button", { classe: "scheda", type: "button", onclick: alClic }, [
    el("div", { classe: "scheda-testa" }, [
      avatar(b.foto_anteprima_url, nome),
      el("div", { style: "flex:1;min-width:0" }, [
        el("h3", { testo: nome }),
        el("div", { classe: "riga-meta" }, [
          b.eta && el("span", { testo: `${b.eta} anni` }),
          el("span", {
            testo: `${b.eta ? "· " : ""}${b.anni_esperienza} ${
              b.anni_esperienza === 1 ? "anno" : "anni"
            } di esperienza`,
          }),
        ]),
      ]),
    ]),
    el("div", { classe: "chips" }, [
      b.abilitato ? chip("Brevetto valido", "verde") : chip("Brevetto da verificare", "ambra"),
      b.disponibile_chiamata_singola && chip("Anche turni singoli", "acqua"),
      ...b.zone.slice(0, 3).map((z) => chip(z.nome)),
    ]),
  ]);
}

/** Scheda pubblica completa: brevetti, esperienze, disponibilità, recensioni. */
export async function schedaBagnino(bagninoId, navigazione) {
  const corpo = el("div", {}, caricamento());
  const { chiudi } = pannello("Profilo", corpo);

  let b;
  try {
    b = await api.bagnino(bagninoId);
  } catch (e) {
    corpo.replaceChildren(avviso(e.dettaglio));
    return;
  }

  const nomeCompleto = `${b.nome} ${b.cognome}`;
  const testa = el("div", { classe: "blocco" }, [
    el("div", { style: "display:flex;gap:14px;align-items:center" }, [
      avatar(b.foto_url, nomeCompleto, true),
      el("h2", { style: "flex:1;min-width:0", testo: nomeCompleto }),
    ]),
    el("div", { classe: "riga-meta", style: "margin-top:10px" }, [
      b.eta && el("span", { testo: `${b.eta} anni` }),
      el("span", { testo: `· ${b.citta}` }),
      el("span", { testo: `· ${b.anni_esperienza} anni di esperienza` }),
    ]),
    el("div", { classe: "chips" }, [
      b.abilitato ? chip("Abilitato", "verde") : chip("Nessun brevetto valido", "rosso"),
      b.disponibile_chiamata_singola && chip("Anche turni singoli", "acqua"),
    ]),
    b.bio && el("p", { style: "margin-top:12px", testo: b.bio }),
  ]);

  corpo.replaceChildren(testa);

  if (b.zone.length) {
    corpo.append(
      el("div", { classe: "blocco" }, [
        el("span", { classe: "etichetta", testo: "Zone coperte" }),
        el("div", { classe: "chips" }, b.zone.map((z) => chip(z.nome))),
      ]),
    );
  }

  if (b.brevetti.length) {
    corpo.append(
      el("div", { classe: "blocco" }, [
        el("span", { classe: "etichetta", testo: "Brevetti" }),
        ...b.brevetti.map((br) =>
          el("div", { classe: "voce" }, [
            el("div", { classe: "voce-corpo" }, [
              el("strong", { testo: etichetta("brevetto", br.tipo) }),
              el("div", { classe: "sommesso dato" }, [
                br.data_scadenza ? `scade il ${br.data_scadenza.split("-").reverse().join("/")}` : "senza scadenza",
              ]),
            ]),
            br.valido ? chip("Valido", "verde") : chip("Scaduto", "rosso"),
          ]),
        ),
      ]),
    );
  }

  if (b.esperienze.length) {
    corpo.append(
      el("div", { classe: "blocco" }, [
        el("span", { classe: "etichetta", testo: "Esperienza" }),
        ...b.esperienze.map((e) =>
          el("div", { classe: "voce" }, [
            el("div", { classe: "voce-corpo" }, [
              el("strong", { testo: e.struttura }),
              el("div", { classe: "sommesso" }, [
                [e.mansione, e.zona].filter(Boolean).join(" · "),
              ]),
              el("div", { classe: "sommesso dato" }, [
                periodo(e.data_inizio, e.data_fine) +
                  (e.stagioni ? ` · ${e.stagioni} stagioni` : ""),
              ]),
            ]),
          ]),
        ),
      ]),
    );
  }

  if (b.disponibilita.length) {
    corpo.append(
      el("div", { classe: "blocco" }, [
        el("span", { classe: "etichetta", testo: "Disponibilità settimanale" }),
        ...b.disponibilita.map((d) =>
          el("div", { classe: "voce" }, [
            el("span", { classe: "voce-corpo", testo: GIORNI_LUNGHI[d.giorno_settimana] }),
            el("span", {
              classe: "dato",
              testo: `${oraBreve(d.ora_inizio)}–${oraBreve(d.ora_fine)}`,
            }),
          ]),
        ),
      ]),
    );
  }

  // Recensioni ricevute
  const zonaRecensioni = el("div", { classe: "blocco" }, [
    el("span", { classe: "etichetta", testo: "Recensioni" }),
    caricamento(),
  ]);
  corpo.append(zonaRecensioni);

  api
    .recensioni(b.utente_id)
    .then((r) => {
      zonaRecensioni.replaceChildren(el("span", { classe: "etichetta", testo: "Recensioni" }));
      if (!r.totale) {
        zonaRecensioni.append(el("p", { classe: "sommesso", testo: "Ancora nessuna recensione." }));
        return;
      }
      zonaRecensioni.append(
        el("div", { style: "display:flex;align-items:center;gap:10px;margin-bottom:8px" }, [
          stelle(r.media_stelle),
          el("span", { classe: "dato", testo: r.media_stelle.toFixed(1) }),
          el("span", { classe: "sommesso", testo: `(${r.totale})` }),
        ]),
        ...r.recensioni.map((rec) =>
          el("div", { classe: "voce" }, [
            el("div", { classe: "voce-corpo" }, [
              el("div", { style: "display:flex;gap:8px;align-items:center" }, [
                stelle(rec.stelle),
                el("strong", { style: "font-size:14px", testo: rec.autore_nome ?? "" }),
              ]),
              rec.commento && el("p", { style: "margin-top:4px", testo: rec.commento }),
            ]),
          ]),
        ),
      );
    })
    .catch(() => zonaRecensioni.replaceChildren());

  if (b.utente_id !== stato.utente.id) {
    corpo.append(
      el("div", { classe: "azioni" }, [
        el("button", {
          classe: "btn",
          testo: "Scrivi un messaggio",
          onclick: () => {
            chiudi();
            apriChatCon(b.utente_id, `${b.nome} ${b.cognome}`, navigazione);
          },
        }),
      ]),
    );
  }
}

function periodo(inizio, fine) {
  const anno = (d) => (d ? d.slice(0, 4) : null);
  if (!inizio) return "";
  return fine ? `${anno(inizio)}–${anno(fine)}` : `dal ${anno(inizio)}`;
}
