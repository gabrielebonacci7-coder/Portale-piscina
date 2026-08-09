// Pannello di gestione, visibile solo a chi ha il permesso di staff.
//
// Tre code di lavoro: i brevetti da controllare, gli account, e il registro di
// quello che è già stato fatto. Il registro non è un di più: sospendere un
// account è una decisione che qualcuno prima o poi contesterà, e conviene
// avere scritto chi l'ha presa e perché.

import { api } from "../api.js";
import {
  avviso,
  brindisi,
  caricamento,
  chip,
  el,
  etichetta,
  ora,
  vuoto,
} from "../ui.js";

const SEZIONI = [
  ["brevetti", "Brevetti"],
  ["account", "Account"],
  ["registro", "Registro"],
];

const AZIONI = {
  brevetto_verificato: "Brevetto verificato",
  brevetto_non_verificato: "Verifica brevetto tolta",
  utente_verificato: "Account verificato",
  utente_non_verificato: "Verifica account tolta",
  utente_sospeso: "Account sospeso",
  utente_riattivato: "Account riattivato",
};

export function vistaStaff() {
  const contenitore = el("div");
  const numeri = el("div", { classe: "numeri" });
  const barra = el("div", { classe: "segmenti" });
  const corpo = el("div");
  contenitore.append(numeri, barra, corpo);

  let sezione = "brevetti";

  for (const [id, nome] of SEZIONI) {
    barra.append(
      el("button", {
        type: "button",
        testo: nome,
        "data-sezione": id,
        "aria-pressed": sezione === id,
        onclick: () => {
          sezione = id;
          for (const b of barra.children) {
            b.setAttribute("aria-pressed", b.dataset.sezione === id);
          }
          disegnaSezione();
        },
      }),
    );
  }

  async function caricaNumeri() {
    try {
      const r = await api.staffRiepilogo();
      numeri.replaceChildren(
        // In cima le due code che chiedono un intervento; i totali dopo.
        riquadro("Brevetti da verificare", r.brevetti_da_verificare, r.brevetti_da_verificare > 0),
        riquadro("Account da verificare", r.utenti_da_verificare),
        riquadro("Iscritti", r.utenti, false, `${r.bagnini} bagnini · ${r.piscine} strutture`),
        riquadro("Turni aperti", r.annunci_aperti),
        riquadro("Account sospesi", r.sospesi, r.sospesi > 0),
      );
    } catch (e) {
      numeri.replaceChildren(avviso(e.dettaglio));
    }
  }

  function disegnaSezione() {
    corpo.replaceChildren(
      sezione === "brevetti"
        ? sezioneBrevetti(caricaNumeri)
        : sezione === "account"
          ? sezioneAccount(caricaNumeri)
          : sezioneRegistro(),
    );
  }

  // Alle sezioni si passa solo `caricaNumeri`, non questa: dopo un'azione
  // l'elenco si ricarica da sé, mentre ricostruire la sezione intera
  // azzererebbe ricerca e filtri appena impostati. Qui si riparte da zero solo
  // al primo disegno e quando cambia scheda.
  function ricarica() {
    caricaNumeri();
    disegnaSezione();
  }

  ricarica();
  contenitore.ricarica = ricarica;
  return contenitore;
}

function riquadro(nome, valore, evidenzia = false, dettaglio = null) {
  return el("div", { classe: `numero${evidenzia ? " evidenza" : ""}` }, [
    el("strong", { testo: String(valore) }),
    el("span", { testo: nome }),
    dettaglio && el("small", { testo: dettaglio }),
  ]);
}

// ---------- Brevetti ----------
function sezioneBrevetti(aggiornaNumeri) {
  const contenitore = el("div");
  const elenco = el("div", { classe: "elenco" });
  let soloDaVerificare = true;

  const interruttore = el("label", { classe: "interruttore" }, [
    el("span", { testo: "Mostra solo quelli da verificare" }),
    el("input", {
      type: "checkbox",
      checked: true,
      onchange: (e) => {
        soloDaVerificare = e.target.checked;
        carica();
      },
    }),
  ]);
  contenitore.append(interruttore, elenco);

  async function carica() {
    elenco.replaceChildren(caricamento());
    try {
      const pagina = await api.staffBrevetti({
        solo_da_verificare: soloDaVerificare,
        limit: 50,
      });
      if (!pagina.elementi.length) {
        elenco.replaceChildren(
          vuoto("Nessun brevetto in coda", "Tutti i documenti caricati sono già stati controllati."),
        );
        return;
      }
      elenco.replaceChildren(...pagina.elementi.map((b) => rigaBrevetto(b, carica, aggiornaNumeri)));
    } catch (e) {
      console.error("Coda brevetti:", e);
      elenco.replaceChildren(avviso(e.dettaglio));
    }
  }

  carica();
  return contenitore;
}

function rigaBrevetto(b, ricarica, aggiornaNumeri) {
  const scheda = el("div", { classe: "scheda", style: "cursor:default" }, [
    el("div", { classe: "scheda-testa" }, [
      el("h3", { style: "flex:1", testo: b.nome }),
      chip(etichetta("brevetto", b.tipo)),
    ]),
    el("div", { classe: "riga-meta" }, [
      el("span", { testo: b.email }),
      b.numero && el("span", { classe: "dato", testo: `· n. ${b.numero}` }),
    ]),
    el("div", { classe: "chips" }, [
      chip(b.ente),
      b.data_scadenza
        ? chip(`scade il ${data(b.data_scadenza)}`, b.valido ? "verde" : "rosso")
        : chip("senza scadenza", "ambra"),
      b.verificato ? chip("verificato", "verde") : chip("da verificare", "ambra"),
    ]),
  ]);

  const azioni = el("div", { classe: "azioni" });
  if (!b.verificato) {
    azioni.append(
      el("button", {
        classe: "btn piccolo",
        testo: "Ho visto l'originale",
        onclick: () => cambia(true),
      }),
    );
  } else {
    azioni.append(
      el("button", {
        classe: "btn secondario piccolo",
        testo: "Togli la verifica",
        onclick: () => cambia(false),
      }),
    );
  }
  scheda.append(azioni);

  async function cambia(valore) {
    const motivo = valore
      ? null
      : chiediMotivo("Perché togli la verifica a questo brevetto?");
    if (!valore && motivo === null) return;
    try {
      await api.staffVerificaBrevetto(b.id, valore, motivo || null);
      brindisi(valore ? "Brevetto verificato" : "Verifica tolta");
      ricarica();
      aggiornaNumeri();
    } catch (e) {
      alert(e.dettaglio);
    }
  }

  return scheda;
}

// ---------- Account ----------
function sezioneAccount(aggiornaNumeri) {
  const contenitore = el("div");
  const elenco = el("div", { classe: "elenco" });

  const ricerca = el("input", {
    type: "search",
    placeholder: "Cerca per nome, email o telefono",
    "aria-label": "Cerca account",
  });
  const tipo = el("select", { "aria-label": "Tipo di account" }, [
    el("option", { value: "", testo: "Tutti" }),
    el("option", { value: "bagnino", testo: "Bagnini" }),
    el("option", { value: "piscina", testo: "Strutture" }),
  ]);
  const sospesi = el("input", { type: "checkbox" });

  // La ricerca parte da sola mentre si scrive, ma non a ogni tasto: sul
  // telefono sarebbero decine di richieste per una parola sola.
  let attesa = null;
  ricerca.addEventListener("input", () => {
    clearTimeout(attesa);
    attesa = setTimeout(carica, 350);
  });
  tipo.addEventListener("change", carica);
  sospesi.addEventListener("change", carica);

  contenitore.append(
    el("div", { classe: "campo" }, [ricerca]),
    el("div", { classe: "campo" }, [el("label", { testo: "Tipo" }), tipo]),
    // L'interruttore ha la sua riga: affiancato al menù a tendina il bordo
    // inferiore finiva a mezz'aria accanto al campo.
    el("label", { classe: "interruttore", style: "margin-bottom:var(--sp-4)" }, [
      el("span", { testo: "Solo account sospesi" }),
      sospesi,
    ]),
    elenco,
  );

  async function carica() {
    elenco.replaceChildren(caricamento());
    try {
      const pagina = await api.staffUtenti({
        q: ricerca.value.trim(),
        tipo: tipo.value,
        solo_sospesi: sospesi.checked ? true : "",
        limit: 50,
      });
      if (!pagina.elementi.length) {
        elenco.replaceChildren(vuoto("Nessun account", "Prova a cambiare i filtri."));
        return;
      }
      elenco.replaceChildren(...pagina.elementi.map((u) => rigaAccount(u, carica, aggiornaNumeri)));
    } catch (e) {
      console.error("Elenco account:", e);
      elenco.replaceChildren(avviso(e.dettaglio));
    }
  }

  carica();
  return contenitore;
}

function rigaAccount(u, ricarica, aggiornaNumeri) {
  const chips = el("div", { classe: "chips" }, [
    chip(u.tipo === "bagnino" ? "Bagnino" : "Struttura"),
    u.ruolo === "staff" && chip("staff", "acqua"),
    u.attivo ? null : chip("sospeso", "rosso"),
    u.verificato ? chip("verificato", "verde") : chip("non verificato", "ambra"),
    u.email_verificata ? null : chip("email non confermata", "ambra"),
    u.brevetti_da_verificare > 0 &&
      chip(`${u.brevetti_da_verificare} brevetti da vedere`, "ambra"),
  ]);

  const scheda = el("div", { classe: "scheda", style: "cursor:default" }, [
    el("div", { classe: "scheda-testa" }, [
      el("h3", { style: "flex:1", testo: u.nome || u.email }),
    ]),
    el("div", { classe: "riga-meta" }, [el("span", { testo: u.email })]),
    el("div", { classe: "riga-meta" }, [
      u.telefono && el("span", { classe: "dato", testo: u.telefono }),
      // Data e non "oggi/ieri": qui interessa da quanto uno è iscritto, non
      // quanto tempo fa è successo qualcosa.
      el("span", { testo: `iscritto il ${data(u.creato_il)}` }),
    ]),
    chips,
  ]);

  // Gli account dello staff si gestiscono da riga di comando: qui non si
  // toccano, e il pannello non mostra pulsanti che risponderebbero 403.
  if (u.ruolo !== "staff") {
    scheda.append(
      el("div", { classe: "azioni" }, [
        el("button", {
          classe: u.verificato ? "btn secondario piccolo" : "btn piccolo",
          testo: u.verificato ? "Togli verifica" : "Verifica",
          onclick: () => verifica(!u.verificato),
        }),
        el("button", {
          classe: u.attivo ? "btn pericolo piccolo" : "btn piccolo",
          testo: u.attivo ? "Sospendi" : "Riattiva",
          onclick: () => stato(!u.attivo),
        }),
      ]),
    );
  }

  async function verifica(valore) {
    const motivo = chiediMotivo(
      valore
        ? "Cosa hai controllato? (facoltativo)"
        : "Perché togli la verifica? (facoltativo)",
    );
    if (motivo === null) return;
    await esegui(() => api.staffVerificaUtente(u.id, valore, motivo || null));
  }

  async function stato(attivo) {
    if (attivo) {
      if (!confirm(`Riattivare l'account di ${u.nome || u.email}?`)) return;
      const nota = chiediMotivo("Nota (facoltativa)");
      await esegui(() => api.staffStatoUtente(u.id, true, nota || null));
      return;
    }
    const motivo = chiediMotivo(
      `Motivo della sospensione di ${u.nome || u.email}:\n\nResta scritto nel registro.`,
    );
    // Annullato, oppure lasciato in bianco: il motivo qui è obbligatorio.
    if (!motivo || !motivo.trim()) return;
    await esegui(() => api.staffStatoUtente(u.id, false, motivo));
  }

  async function esegui(azione) {
    try {
      await azione();
      brindisi("Fatto");
      ricarica();
      aggiornaNumeri();
    } catch (e) {
      alert(e.dettaglio);
    }
  }

  return scheda;
}

// ---------- Registro ----------
function sezioneRegistro() {
  const elenco = el("div", { classe: "elenco" });

  (async () => {
    elenco.replaceChildren(caricamento());
    try {
      const pagina = await api.staffRegistro({ limit: 50 });
      if (!pagina.elementi.length) {
        elenco.replaceChildren(
          vuoto("Registro vuoto", "Qui finisce ogni verifica e ogni sospensione."),
        );
        return;
      }
      elenco.replaceChildren(
        el(
          "div",
          { classe: "blocco" },
          pagina.elementi.map((a) =>
            el("div", { classe: "voce" }, [
              el("div", { classe: "voce-corpo" }, [
                el("strong", { testo: AZIONI[a.azione] ?? a.azione }),
                el("div", {
                  classe: "sommesso",
                  testo: a.oggetto_etichetta || `${a.oggetto_tipo} #${a.oggetto_id}`,
                }),
                a.motivo && el("div", { classe: "sommesso", testo: `“${a.motivo}”` }),
                el("div", {
                  classe: "sommesso",
                  testo: `${a.staff_email} · ${data(a.creato_il)} ${ora(a.creato_il)}`,
                }),
              ]),
            ]),
          ),
        ),
      );
    } catch (e) {
      console.error("Registro staff:", e);
      elenco.replaceChildren(avviso(e.dettaglio));
    }
  })();

  return elenco;
}

// ---------- Utilità ----------
/** `prompt` che distingue "annullato" (null) da "lasciato in bianco" (""). */
function chiediMotivo(domanda) {
  const risposta = prompt(domanda);
  return risposta === null ? null : risposta.trim();
}

const data = (iso) => new Date(iso).toLocaleDateString("it-IT");
